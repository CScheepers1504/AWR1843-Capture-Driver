#!/usr/bin/env python3
"""
Derive and constraint-check an AWR1843 chirp profile from its config JSON.

    python3 profile_check.py ../src/mmWave_DRV/config/awr1843_wideband.json
    python3 profile_check.py <old.json> <new.json>      # side-by-side

The four constraints that bind, in the order they bite:

  1. BAND      slope * rampEndTime must fit inside 77-81 GHz.
  2. ADC WIN   adcStartTime + numAdcSamples/fs must fit inside rampEndTime.
  3. LVDS      one chirp's payload must stream out within one chirp period.
               This is the one people forget, and it is what forces idleTime
               up -- not VCO settling.
  4. MIGRATION the ball must not cross much more than one range bin during the
               chirp burst, or the range peak smears across bins.
  5. HPF       the signal must land ABOVE the IF high-pass corner.

freqSlopeConst = 0 selects CW: a constant tone, no range information, and the
"range FFT" becomes a Doppler FFT over the ADC dwell. Range-derived figures are
suppressed in that mode rather than divided by zero.
"""
import json
import math
import sys

INF = float("inf")

C = 299792458.0
BAND_LO_GHZ, BAND_HI_GHZ = 77.0, 81.0
# A chirp must sweep within ONE synthesizer VCO: 76-78 GHz (VCO1) or 77-81 GHz
# (VCO2). mmwavelink rl_sensor.h, rlProfileCfg.rampEndTime, SDK 03.06.02.
# So a 76 GHz start allows at most 2 GHz; more than 2 GHz needs >= 77 GHz.
VCO_BANDS_GHZ = ((76.0, 78.0), (77.0, 81.0))
LVDS_GBPS = 1.2          # xWR18xx: 2 lanes x 600 Mbps.
LVDS_DERATE = 0.90       # headroom for framing / inter-chirp overhead
ADCBUF_BYTES = 32768     # xWR18xx ADC buffer, shared across Rx

# IF-chain high-pass corners, from the profileCfg field encodings. Both stages
# are in series, so the BINDING corner is the higher of the two.
HPF1_HZ = {0: 175e3, 1: 235e3, 2: 350e3, 3: 700e3}
HPF2_HZ = {0: 350e3, 1: 700e3, 2: 1.4e6, 3: 2.8e6}


def bits(mask):
    return bin(int(mask)).count("1")


def derive(cfg):
    p, f, ch = cfg["profileCfg"], cfg["frameCfg"], cfg["channelCfg"]
    d = {}

    d["n_rx"] = bits(ch["rxChannelEn"])
    d["n_tx"] = int(f["chirpEndIndex"]) - int(f["chirpStartIndex"]) + 1
    d["n_loops"] = int(f["numChirps"])
    d["n_samples"] = int(p["numAdcSamples"])

    # adcbufCfg.adcOutputFmt: 0 = complex -> I and Q, 1 = real -> I only.
    # Same expression as radar_data_node.cpp:218 and recorder.py derive_dims().
    d["iq"] = (int(cfg["adcbufCfg"]["adcOutputFmt"]) + 2) % 3
    d["bytes_per_sample"] = 2 * d["iq"]

    slope = float(p["freqSlopeConst"])                 # MHz/us
    fs = float(p["digOutSampleRate"]) / 1000.0         # ksps -> Msps == samples/us
    d["slope_mhz_us"] = slope
    d["fs_msps"] = fs
    d["cw"] = (slope == 0.0)       # constant tone: no ramp, so no range

    d["t_sample_us"] = d["n_samples"] / fs
    d["t_adc_end_us"] = float(p["adcStartTime"]) + d["t_sample_us"]
    d["ramp_us"] = float(p["rampEndTime"])
    d["idle_us"] = float(p["idleTime"])
    d["t_chirp_us"] = d["idle_us"] + d["ramp_us"]

    d["b_ramp_mhz"] = slope * d["ramp_us"]             # total excursion
    d["b_sampled_mhz"] = slope * d["t_sample_us"]      # what actually sets resolution
    d["f_start_ghz"] = float(p["startFreq"])
    d["f_stop_ghz"] = d["f_start_ghz"] + d["b_ramp_mhz"] / 1000.0
    d["range_res_m"] = INF if d["cw"] else C / (2 * d["b_sampled_mhz"] * 1e6)
    d["band_used_pct"] = 100.0 * d["b_sampled_mhz"] / ((BAND_HI_GHZ - BAND_LO_GHZ) * 1000)

    f_c_hz = d["f_start_ghz"] * 1e9 + d["b_ramp_mhz"] * 1e6 / 2.0
    d["lambda_m"] = C / f_c_hz

    # unambiguous range from the beat-frequency limit (fs for complex sampling)
    d["r_max_m"] = INF if d["cw"] else (fs * 1e6) * C / (2 * slope * 1e12)

    # --- CW: the ADC dwell is the coherent integration, so it sets velocity
    #     resolution directly. Unambiguity comes from complex Nyquist (fs/2),
    #     which is why CW does not fold the way TDM-MIMO FMCW does.
    d["dwell_us"] = d["t_sample_us"]
    d["v_res_cw_ms"] = d["lambda_m"] / (2 * d["dwell_us"] * 1e-6)
    d["v_max_cw_ms"] = d["lambda_m"] * (fs * 1e6) / 4

    # --- IF high-pass. Cascaded stages -> the higher corner binds.
    d["hpf1_hz"] = HPF1_HZ[int(p["hpfCornerFreq1"])]
    d["hpf2_hz"] = HPF2_HZ[int(p["hpfCornerFreq2"])]
    d["hpf_hz"] = max(d["hpf1_hz"], d["hpf2_hz"])
    # FMCW: beat = 2*R*slope/c  -> minimum range that clears the corner.
    d["r_hpf_m"] = INF if d["cw"] else d["hpf_hz"] * C / (2 * slope * 1e12)
    # CW: beat = 2*v/lambda     -> minimum speed that clears the corner.
    d["v_hpf_ms"] = d["lambda_m"] * d["hpf_hz"] / 2

    # --- LVDS: one chirp's payload must clear within one chirp period ---
    d["chirp_bytes"] = d["n_samples"] * d["bytes_per_sample"] * d["n_rx"]
    d["lvds_gbps"] = d["chirp_bytes"] * 8 / (d["t_chirp_us"] * 1e-6) / 1e9
    d["lvds_pct"] = 100.0 * d["lvds_gbps"] / LVDS_GBPS
    d["t_chirp_min_us"] = d["chirp_bytes"] * 8 / (LVDS_GBPS * LVDS_DERATE * 1e9) * 1e6

    # --- frame / burst ---
    d["chirps_per_frame"] = d["n_loops"] * d["n_tx"]
    d["burst_us"] = d["chirps_per_frame"] * d["t_chirp_us"]
    d["frame_period_ms"] = float(f["framePeriod"])
    d["frame_rate_hz"] = 1000.0 / d["frame_period_ms"]
    d["duty_pct"] = 100.0 * d["burst_us"] / (d["frame_period_ms"] * 1000)
    d["frame_bytes"] = d["chirp_bytes"] * d["chirps_per_frame"]
    d["wire_mbs"] = d["frame_bytes"] * d["frame_rate_hz"] / 1e6

    # --- Doppler. TDM-MIMO: each Tx revisits every n_tx chirps ---
    d["pri_us"] = d["n_tx"] * d["t_chirp_us"]
    d["v_max_ms"] = d["lambda_m"] / (4 * d["pri_us"] * 1e-6)
    d["v_res_ms"] = 2 * d["v_max_ms"] / d["n_loops"]

    # --- range-Doppler coupling: r_meas(t) = r(t) + k*rdot(t) ~= r(t + k) ---
    d["rd_coupling_s"] = 0.0 if d["cw"] else C / (d["lambda_m"] * slope * 1e12)

    # --- TDM phase: radial-velocity accuracy needed for <10 deg residual on the
    #     Tx-to-Tx phase, if the elevated Tx is not temporally centred ---
    d["tdm_dv_tol_ms"] = math.radians(10) * d["lambda_m"] / (4 * math.pi * d["t_chirp_us"] * 1e-6)
    return d


def report(cfg, d, label):
    print("\n" + "=" * 68)
    print(label)
    print("=" * 68)
    print("  chirp        slope %g MHz/us, ramp %g us, idle %g us  -> T_c %.1f us"
          % (d["slope_mhz_us"], d["ramp_us"], d["idle_us"], d["t_chirp_us"]))
    print("  sweep        %.2f -> %.2f GHz  (%.0f MHz excursion)"
          % (d["f_start_ghz"], d["f_stop_ghz"], d["b_ramp_mhz"]))
    if d["cw"]:
        print("  MODE         CW -- freqSlopeConst = 0, constant tone, NO RANGE")
        print("  dwell        %.1f us (%d samples at %g ksps)"
              % (d["dwell_us"], d["n_samples"], d["fs_msps"] * 1000))
        print("  VELOCITY RES %.2f m/s   (= lambda / 2T, T = the ADC dwell)"
              % d["v_res_cw_ms"])
        print("  unamb vel    +/-%.0f m/s  (complex Nyquist -- CW does not fold)"
              % d["v_max_cw_ms"])
    else:
        print("  sampled BW   %.0f MHz  (%.0f%% of the 4 GHz band)"
              % (d["b_sampled_mhz"], d["band_used_pct"]))
        print("  RANGE RES    %.2f cm     (floor at a full 4 GHz sweep = %.2f cm)"
              % (d["range_res_m"] * 100, C / (2 * 4e9) * 100))
        print("  unamb range  %.1f m" % d["r_max_m"])
    print("  frame        %d loops x %d Tx x %d Rx x %d samples = %s B"
          % (d["n_loops"], d["n_tx"], d["n_rx"], d["n_samples"], format(d["frame_bytes"], ",")))
    print("  rate         %.1f Hz, burst %.0f us, duty %.1f%%"
          % (d["frame_rate_hz"], d["burst_us"], d["duty_pct"]))
    print("  wire rate    %.1f MB/s" % d["wire_mbs"])
    if not d["cw"]:
        print("  doppler      v_max +/-%.2f m/s, %d bins of %.2f m/s"
              % (d["v_max_ms"], d["n_loops"], d["v_res_ms"]))
        print("  rd coupling  %.0f us apparent time shift (uniform -> harmless to the r^2(t) fit)"
              % (d["rd_coupling_s"] * 1e6))
    print("  IF high-pass %.0f kHz binding (hpf1 %.0f kHz, hpf2 %.0f kHz, cascaded)"
          % (d["hpf_hz"] / 1e3, d["hpf1_hz"] / 1e3, d["hpf2_hz"] / 1e3))

    print("\n  constraints")
    state = {"ok": True}

    def chk(name, cond, detail):
        state["ok"] = state["ok"] and cond
        print("    [%s] %-12s %s" % ("ok " if cond else "FAIL", name, detail))

    in_vco = [lo for lo, hi in VCO_BANDS_GHZ
              if d["f_start_ghz"] >= lo - 1e-9 and d["f_stop_ghz"] <= hi + 1e-9]
    chk("band", bool(in_vco),
        "sweeps %.2f-%.2f GHz; must lie within 76-78 or 77-81 GHz (one VCO)"
        % (d["f_start_ghz"], d["f_stop_ghz"]))
    chk("adc window", d["t_adc_end_us"] <= d["ramp_us"] + 1e-9,
        "ADC ends %.2f us, ramp ends %.2f us (guard %.2f us)"
        % (d["t_adc_end_us"], d["ramp_us"], d["ramp_us"] - d["t_adc_end_us"]))
    chk("adcbuf", d["chirp_bytes"] <= ADCBUF_BYTES,
        "%s B/chirp vs %s B buffer" % (format(d["chirp_bytes"], ","), format(ADCBUF_BYTES, ",")))
    chk("chirp align", (d["n_samples"] * d["bytes_per_sample"]) % 16 == 0,
        "%d B per Rx per chirp, needs a multiple of 16"
        % (d["n_samples"] * d["bytes_per_sample"]))
    chk("lvds", d["lvds_gbps"] <= LVDS_GBPS * LVDS_DERATE,
        "%.3f Gbps = %.0f%% of %g Gbps (needs T_c >= %.1f us)"
        % (d["lvds_gbps"], d["lvds_pct"], LVDS_GBPS, d["t_chirp_min_us"]))
    if d["cw"]:
        # In CW the beat frequency IS the Doppler shift, so the IF high-pass
        # becomes a minimum SPEED. No ball in scope goes anywhere near it.
        chk("hpf", d["v_hpf_ms"] <= 70.0,
            "CW needs %.0f m/s to clear the %.0f kHz corner; fastest ball in "
            "scope is 70 m/s (= %.1f kHz)"
            % (d["v_hpf_ms"], d["hpf_hz"] / 1e3, 2 * 70 / d["lambda_m"] / 1e3))
    else:
        print("    [--- ] %-12s targets nearer than %.2f m fall under the %.0f kHz "
              "corner" % ("hpf", d["r_hpf_m"], d["hpf_hz"] / 1e3))
        print("           (informational: compare against your range gate, not a limit)")

    if d["cw"]:
        print("\n  doppler frequency vs the IF high-pass corner")
        for v in (30, 45, 70):
            fd = 2 * v / d["lambda_m"]
            print("    %3d m/s   f_d = %6.1f kHz  %s (corner %.0f kHz, %.1fx above)"
                  % (v, fd / 1e3, "PASSES" if fd >= d["hpf_hz"] else "BLOCKED",
                     d["hpf_hz"] / 1e3, d["hpf_hz"] / fd))
        print("    velocity resolution %.2f m/s over a %.0f us dwell"
              % (d["v_res_cw_ms"], d["dwell_us"]))
        print("    to halve it, double the dwell: more samples or a lower fs,")
        print("    bounded by rampEndTime and the %s B ADC buffer."
              % format(ADCBUF_BYTES, ","))
        print()
        return state["ok"]

    print("\n  range migration over one burst, and where the target folds in doppler")
    span = 2 * d["v_max_ms"]
    for v in (30, 45, 70):
        m = v * d["burst_us"] * 1e-6
        n = m / d["range_res_m"]
        # apparent (aliased) radial velocity, wrapped into +/- v_max
        alias = (v + d["v_max_ms"]) % span - d["v_max_ms"]
        # Velocity-resolution floor. Holding migration to one range bin caps the
        # coherent dwell at T <= c/(2*B*v); with dv = lambda/(2T) that gives
        #     dv >= lambda*B*v/c,  i.e.  dv/v >= lambda/(2*dR).
        # Finer range resolution therefore makes fractional velocity resolution
        # strictly WORSE. Independent of PRF, loop count and frame rate.
        floor = d["lambda_m"] * d["b_sampled_mhz"] * 1e6 * v / C
        print("    %3d m/s   migration %5.2f cm = %.2f bins%s"
              % (v, m * 100, n, "  <-- smeared" if n > 1.2 else ""))
        print("              folds to %+6.2f m/s%s;  dv floor %.2f m/s"
              % (alias,
                 "  <-- INTO THE CLUTTER BIN" if abs(alias) < d["v_res_ms"] / 2 else "",
                 floor))
    print("    fractional floor  dv/v >= lambda/(2*dR) = %.1f%%"
          % (100 * d["lambda_m"] / (2 * d["range_res_m"])))

    print("\n  TDM elevation: needs radial velocity known to %.2f m/s for <10 deg residual"
          % d["tdm_dv_tol_ms"])
    masks = [cfg["chirpCfg_%d" % i]["chirpAntennaEnMask"] for i in range(d["n_tx"])]
    centred = d["n_tx"] == 3 and masks == [1, 2, 4]
    print("    Tx firing order %s -> elevated Tx2 temporally %s"
          % (masks, "CENTRED: first-order Doppler phase self-cancels"
             if centred else "NOT centred"))
    return state["ok"]


def main():
    paths = sys.argv[1:]
    if not paths:
        print(__doc__)
        return 2
    allok = True
    for p in paths:
        with open(p) as fh:
            cfg = json.load(fh)
        allok = report(cfg, derive(cfg), p) and allok
    print()
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
