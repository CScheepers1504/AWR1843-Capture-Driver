#!/usr/bin/env python3
"""
Check that a capture's transmitter slot order matches a reference capture.

    python3 scripts/tx_order_check.py <capture_dir> --ref <reference_dir>
    python3 scripts/tx_order_check.py <capture_dir> --ref <reference_dir> --write-meta

Exit status: 0 same order, 4 rotated or misaligned, 5 unsure, 2 could not run.

WHY THIS EXISTS

On 9 and 13 Sep 2026 the TDM transmitter order rotated between recordings: 3 of
9 captures on 13 Sep started one Tx slot out. The Rx order and the sample
alignment were intact, so every range profile looked perfect and only the MIMO
angles were wrong -- silently. Two captures of the same unmoved room would not
even subtract: -1.7 dB of wall cancellation as recorded, -17.3 dB once the slot
order was shifted back. The data carries no chirp index, so nothing upstream
can see this happen.

HOW

A static room gives every (Tx, Rx) channel its own fixed range-profile
signature. On 13 Sep different Tx differed by 41-51 dB^2 while the same channel
one loop later matched to 0.1-0.2 dB^2, so the slot identity is well defined.
The capture's per-channel signatures are compared with the reference's under
every cyclic shift of the chirp slots.

Each signature has its mean across channels removed, per range bin, first. A
prop or a person that changes the scene changes all channels alike and cancels
there, while a slot rotation reorders the channels and does not. The median
over bins ignores the angle-dependent change that is left.

WHAT IT CANNOT TELL YOU

The order RELATIVE to the reference -- not which physical antenna fired first.
If the reference started late, every capture that passes shares its rotation.
That still keeps a calibration set self-consistent, which is the failure this
prevents, but the estimators assume slot 2 is the raised antenna
(angle_history.m) and array_cal.m's grid assumes slot 1 is not, so a rotated
reference is wrong for them. session.sh records the reference on a fresh launch
with the sensor stopped over serial, the state least likely to join mid-frame.

The reference is valid only while the radar stays put. Moving or re-tilting it
changes every signature: record a new one.
"""

import argparse
import json
import os
import sys

import numpy as np

MARGIN = 1.5   # runner-up distance / best distance needed for a confident verdict


def signature(cap, n_frames, skip_frames):
    """Per-slot range-profile signature, (n_tx*n_rx, bins), mean across slots removed."""
    with open(os.path.join(cap, "meta.json")) as f:
        meta = json.load(f)
    d, cfg = meta["dims"], meta["config"]
    if d["iq"] != 2:
        raise ValueError("%s: complex (I/Q) captures only" % cap)
    ns, nrx, ntx, nl = d["n_samples"], d["n_rx"], d["n_tx"], d["n_loops"]
    i16_per_frame = d["frame_bytes"] // 2
    path = os.path.join(cap, "frames.bin")
    avail = os.path.getsize(path) // 2 // i16_per_frame
    n = min(n_frames, avail - skip_frames)
    if n < 5:
        raise ValueError("%s: only %d frames available" % (cap, avail))

    # Whole frames are skipped, so the start of the read keeps the capture's own
    # alignment -- which is the thing being measured.
    # seek + fromfile(file object), not fromfile(offset=): the offset argument
    # needs numpy >= 1.17 and the Jetson's version is not pinned anywhere.
    with open(path, "rb") as f:
        f.seek(skip_frames * i16_per_frame * 2)
        raw = np.fromfile(f, dtype=np.int16, count=n * i16_per_frame).astype(np.float32)

    # AWR1843 2-lane packing, as fmcw_pipeline.m and array_cal.m read it:
    # groups of four int16 are [I0 I1 Q0 Q1], i.e. two complex samples.
    g = raw.reshape(-1, 4)
    x = np.empty(2 * g.shape[0], np.complex64)
    x[0::2] = g[:, 0] + 1j * g[:, 2]
    x[1::2] = g[:, 1] + 1j * g[:, 3]
    if cfg["adcbufCfg"].get("SampleSwap") == 1:
        x = np.conj(x)

    period = ntx * nrx
    w = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(ns) / (ns - 1))
    spec = np.abs(np.fft.fft(x.reshape(n, nl * period, ns) * w, axis=-1)).mean(axis=0)
    # Stream order within a frame is loop, then Tx, then Rx. Loops are identical
    # for a static scene, so a loop offset is invisible and is averaged away.
    sig = 20 * np.log10(spec.reshape(nl, period, ns).mean(axis=0)[:, 3:ns - 3] + 1e-6)
    return sig - sig.mean(axis=0, keepdims=True), d


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    ap.add_argument("capture")
    ap.add_argument("--ref", required=True, help="reference capture of the same rig")
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--skip-frames", type=int, default=5,
                    help="leading frames ignored (subscription transient)")
    ap.add_argument("--write-meta", action="store_true",
                    help="record the result in the capture's meta.json")
    args = ap.parse_args()

    try:
        sig, d = signature(args.capture, args.frames, args.skip_frames)
        ref, dr = signature(args.ref, args.frames, args.skip_frames)
    except (OSError, ValueError, KeyError) as e:
        print("tx order check could not run: %s" % e)
        return 2
    keys = ("n_tx", "n_rx", "n_loops", "n_samples", "frame_bytes")
    if any(d[k] != dr[k] for k in keys):
        print("tx order check could not run: capture and reference use different profiles")
        return 2

    nrx, nsamp = d["n_rx"], d["n_samples"]
    period = sig.shape[0]
    # np.roll(sig, -s)[c] == sig[(c + s) % period]: capture slot c+s against
    # reference slot c. Dropping s blocks from the capture's start realigns it.
    dist = np.array([np.median((np.roll(sig, -s, axis=0) - ref) ** 2) for s in range(period)])
    best = int(np.argmin(dist))
    runner = float(np.min(np.delete(dist, best)))
    margin = min(runner / max(float(dist[best]), 1e-9), 999.0)
    skip_i16 = 2 * best * nsamp

    if margin < MARGIN:
        verdict, code = "UNSURE", 5
    elif best == 0:
        verdict, code = "MATCH", 0
    elif best % nrx == 0:
        verdict, code = "ROTATED", 4
    else:
        verdict, code = "RX_MISALIGNED", 4

    print("tx order check: %s" % os.path.basename(os.path.normpath(args.capture)))
    print("  reference     %s" % os.path.basename(os.path.normpath(args.ref)))
    order = np.argsort(dist)
    print("  best shifts   " + "   ".join("%d blocks: %.1f dB^2" % (s, dist[s]) for s in order[:3]))
    print("  margin        %.2f (confident at >= %.1f)" % (margin, MARGIN))
    if verdict == "MATCH":
        print("  verdict       MATCH -- same Tx slot order as the reference")
    elif verdict == "ROTATED":
        k, ntx = best // nrx, d["n_tx"]
        print("  verdict       ROTATED by %d of %d Tx slots (= %d the other way). Angles from this capture are WRONG."
              % (k, ntx, ntx - k))
        print("                To realign offline, drop %d blocks = %d int16 from the start." % (best, skip_i16))
    elif verdict == "RX_MISALIGNED":
        print("  verdict       MISALIGNED by %d blocks -- not a whole chirp. Rx order is broken." % best)
    else:
        print("  verdict       UNSURE -- best is %d blocks but the next shift is nearly as good." % best)
        print("                The scene may have changed too much since the reference.")

    if args.write_meta:
        path = os.path.join(args.capture, "meta.json")
        with open(path) as f:
            meta = json.load(f)
        meta["tx_order_check"] = {
            "reference": os.path.normpath(args.ref),
            "verdict": verdict,
            "shift_blocks": best,
            "realign_skip_int16": skip_i16,
            "margin": round(margin, 3),
            "distances_db2": [round(float(v), 2) for v in dist],
        }
        with open(path, "w") as f:
            json.dump(meta, f, indent=2)
    return code


if __name__ == "__main__":
    sys.exit(main())
