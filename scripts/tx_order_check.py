#!/usr/bin/env python3
"""
Check that a capture's transmitter slot order matches a reference capture.

    python3 scripts/tx_order_check.py <capture_dir> --ref <reference_dir>
    python3 scripts/tx_order_check.py <capture_dir> --ref <reference_dir> --write-meta

Exit status: 0 same order, 4 rotated or misaligned, 5 unsure, 2 could not run.

The reference is valid only while the radar stays put. Moving or re-tilting it
changes every signature: record a new one.
"""

import argparse
import json
import os
import sys

import numpy as np

import chirp_align_check

MARGIN = 1.5   # runner-up distance / best distance needed for a confident verdict


def block_offset(cap):
    """int16 to drop so the capture starts on an Rx-block boundary.

    From meta.json chirp_align if chirp_align_check.py has stamped it, else
    measured now. A capture with no clear block boundary cannot be compared.
    The 13 Sep 282 Hz takes started 104-292 int16 into a block; compared
    unaligned, a reference like that matched nothing (margin ~1.0).
    """
    with open(os.path.join(cap, "meta.json")) as f:
        meta = json.load(f)
    ca = meta.get("chirp_align")
    if ca is None or ca.get("verdict") not in ("ALIGNED", "OFFSET"):
        ca = chirp_align_check.check(cap, 200, 5)
        ca["verdict"] = "UNSURE" if (ca["contrast"] < chirp_align_check.CONTRAST_MIN or
                                     ca["margin"] < chirp_align_check.MARGIN_MIN) else "measured"
    if ca["verdict"] == "UNSURE":
        raise ValueError("%s: no clear chirp boundary in the samples" % cap)
    return int(ca["drop_int16"]), meta.get("capture", {}).get("burst_slips")


def signature(cap, n_frames, skip_frames, pre_i16=0):
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
        f.seek((skip_frames * i16_per_frame + pre_i16) * 2)
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
        cap_pre, _ = block_offset(args.capture)
        ref_pre, ref_slips = block_offset(args.ref)
        if ref_slips:
            # Relative check only: a reference with a timed whole-chirp slip
            # would pass its rotation on to every capture that matches it.
            print("tx order check could not run: the reference has %d frame starts "
                  "off the frame grid (burst_slips). Record a new reference." % ref_slips)
            return 2
        sig, d = signature(args.capture, args.frames, args.skip_frames, cap_pre)
        ref, dr = signature(args.ref, args.frames, args.skip_frames, ref_pre)
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
    # Total realignment from the start of frames.bin: the sub-block offset, then
    # whole blocks. The reference's own sub-block offset is already removed.
    skip_i16 = cap_pre + 2 * best * nsamp

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
    if cap_pre or ref_pre:
        print("  pre-aligned   capture by %d int16, reference by %d int16 (chirp_align)"
              % (cap_pre, ref_pre))
    order = np.argsort(dist)
    print("  best shifts   " + "   ".join("%d blocks: %.1f dB^2" % (s, dist[s]) for s in order[:3]))
    print("  margin        %.2f (confident at >= %.1f)" % (margin, MARGIN))
    if verdict == "MATCH":
        print("  verdict       MATCH -- same Tx slot order as the reference")
        if cap_pre:
            print("                (after dropping %d int16 to reach a block boundary)" % cap_pre)
    elif verdict == "ROTATED":
        k, ntx = best // nrx, d["n_tx"]
        print("  verdict       ROTATED by %d of %d Tx slots (= %d the other way). Angles from this capture are WRONG."
              % (k, ntx, ntx - k))
        print("                To realign offline, drop %d int16 from the start (%d to the block boundary + %d blocks)."
              % (skip_i16, cap_pre, best))
    elif verdict == "RX_MISALIGNED":
        # A constant offset, not corruption: the 13 Sep 282 Hz bg_d150 sat at
        # 104 int16 + 6 blocks in every 60-frame window across 2000 frames.
        print("  verdict       MISALIGNED by %d blocks -- the take starts mid-chirp, so Rx and Tx"
              % best)
        print("                slots are both shifted as recorded. Angles from it are WRONG.")
        print("                To realign offline, drop %d int16 from the start (%d to the block boundary + %d blocks)."
              % (skip_i16, cap_pre, best))
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
            "block_offset_int16": cap_pre,
            "reference_block_offset_int16": ref_pre,
            "margin": round(margin, 3),
            "distances_db2": [round(float(v), 2) for v in dist],
        }
        with open(path, "w") as f:
            json.dump(meta, f, indent=2)
    return code


if __name__ == "__main__":
    sys.exit(main())
