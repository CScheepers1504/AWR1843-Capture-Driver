#!/usr/bin/env python3
"""
Check that a capture's Tx slot order matches the rig's reference capture.

    python3 scripts/tx_order_check.py <capture_dir> --ref <reference_dir> [--write-meta]

Exit status: 0 same order, 4 rotated or misaligned, 5 unsure, 2 could not run.
The reference holds only while the radar stays where it was recorded.
"""

import argparse
import json
import os
import sys

import numpy as np

import chirp_align_check

MARGIN = 1.5   # runner-up distance over best distance needed for a confident verdict


def block_offset(cap):
    """int16 to drop to reach an Rx-block boundary, and the capture's slipped frame starts."""
    with open(os.path.join(cap, "meta.json")) as f:
        meta = json.load(f)
    align = meta.get("chirp_align")
    if align is None or align.get("verdict") not in ("ALIGNED", "OFFSET"):
        align = chirp_align_check.check(cap, 200, 5)
        unsure = (align["contrast"] < chirp_align_check.CONTRAST_MIN
                  or align["margin"] < chirp_align_check.MARGIN_MIN)
        align["verdict"] = "UNSURE" if unsure else "measured"
    if align["verdict"] == "UNSURE":
        raise ValueError("%s: no clear chirp boundary in the samples" % cap)
    return int(align["drop_int16"]), meta.get("capture", {}).get("burst_slips")


def signature(cap, n_frames, skip_frames, pre_int16=0):
    """Per-slot range-profile signature, (n_tx * n_rx, bins) in dB, mean across slots removed."""
    with open(os.path.join(cap, "meta.json")) as f:
        meta = json.load(f)
    dims, cfg = meta["dims"], meta["config"]
    if dims["iq"] != 2:
        raise ValueError("%s: complex (I/Q) captures only" % cap)
    n_samples, n_rx, n_tx, n_loops = dims["n_samples"], dims["n_rx"], dims["n_tx"], dims["n_loops"]
    frame_int16 = dims["frame_bytes"] // 2
    path = os.path.join(cap, "frames.bin")
    available = os.path.getsize(path) // 2 // frame_int16
    n = min(n_frames, available - skip_frames)
    if n < 5:
        raise ValueError("%s: only %d frames available" % (cap, available))

    # Whole frames are skipped, so the read keeps the capture's own alignment, which is what is
    # being measured. seek + fromfile because fromfile's offset argument needs numpy >= 1.17.
    with open(path, "rb") as f:
        f.seek((skip_frames * frame_int16 + pre_int16) * 2)
        raw = np.fromfile(f, dtype=np.int16, count=n * frame_int16).astype(np.float32)

    # AWR1843 two-lane packing: each group of four int16 is [I0 I1 Q0 Q1], two complex samples.
    words = raw.reshape(-1, 4)
    iq = np.empty(2 * words.shape[0], np.complex64)
    iq[0::2] = words[:, 0] + 1j * words[:, 2]
    iq[1::2] = words[:, 1] + 1j * words[:, 3]
    if cfg["adcbufCfg"].get("SampleSwap") == 1:
        iq = np.conj(iq)

    slots = n_tx * n_rx
    window = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(n_samples) / (n_samples - 1))
    spectrum = np.abs(np.fft.fft(iq.reshape(n, n_loops * slots, n_samples) * window, axis=-1)).mean(axis=0)
    # Stream order within a frame is loop, then Tx, then Rx. Loops are identical for a static
    # scene, so a loop offset is invisible and is averaged away.
    sig = 20 * np.log10(spectrum.reshape(n_loops, slots, n_samples).mean(axis=0)[:, 3:n_samples - 3] + 1e-6)
    return sig - sig.mean(axis=0, keepdims=True), dims


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().split("\n\n")[0])
    parser.add_argument("capture")
    parser.add_argument("--ref", required=True, help="reference capture of the same rig")
    parser.add_argument("--frames", type=int, default=60)
    parser.add_argument("--skip-frames", type=int, default=5,
                        help="leading frames ignored (subscription transient)")
    parser.add_argument("--write-meta", action="store_true",
                        help="record the result in the capture's meta.json")
    args = parser.parse_args()

    try:
        cap_pre, _ = block_offset(args.capture)
        ref_pre, ref_slips = block_offset(args.ref)
        if ref_slips:
            # A reference with a slipped frame start would pass its rotation on to every match.
            print("tx order check could not run: the reference has %d slipped frame starts. "
                  "Record a new reference." % ref_slips)
            return 2
        sig, dims = signature(args.capture, args.frames, args.skip_frames, cap_pre)
        ref, ref_dims = signature(args.ref, args.frames, args.skip_frames, ref_pre)
    except (OSError, ValueError, KeyError) as e:
        print("tx order check could not run: %s" % e)
        return 2
    keys = ("n_tx", "n_rx", "n_loops", "n_samples", "frame_bytes")
    if any(dims[k] != ref_dims[k] for k in keys):
        print("tx order check could not run: capture and reference use different profiles")
        return 2

    n_rx, n_samples = dims["n_rx"], dims["n_samples"]
    slots = sig.shape[0]
    # np.roll(sig, -s)[c] == sig[(c + s) % slots]: capture slot c + s against reference slot c.
    # Dropping s blocks from the capture's start realigns it.
    dist = np.array([np.median((np.roll(sig, -s, axis=0) - ref) ** 2) for s in range(slots)])
    best = int(np.argmin(dist))
    runner_up = float(np.min(np.delete(dist, best)))
    margin = min(runner_up / max(float(dist[best]), 1e-9), 999.0)
    # Total realignment from the start of frames.bin: the sub-block offset, then whole blocks.
    skip_int16 = cap_pre + 2 * best * n_samples

    if margin < MARGIN:
        verdict, code = "UNSURE", 5
    elif best == 0:
        verdict, code = "MATCH", 0
    elif best % n_rx == 0:
        verdict, code = "ROTATED", 4
    else:
        verdict, code = "RX_MISALIGNED", 4

    print("tx order check: %s" % os.path.basename(os.path.normpath(args.capture)))
    print("  reference     %s" % os.path.basename(os.path.normpath(args.ref)))
    if cap_pre or ref_pre:
        print("  pre-aligned   capture by %d int16, reference by %d int16 (chirp_align)"
              % (cap_pre, ref_pre))
    ranked = np.argsort(dist)
    print("  best shifts   " + "   ".join("%d blocks: %.1f dB^2" % (s, dist[s]) for s in ranked[:3]))
    print("  margin        %.2f (confident at >= %.1f)" % (margin, MARGIN))
    if verdict == "MATCH":
        print("  verdict       MATCH -- same Tx slot order as the reference")
        if cap_pre:
            print("                (after dropping %d int16 to reach a block boundary)" % cap_pre)
    elif verdict == "ROTATED":
        k, n_tx = best // n_rx, dims["n_tx"]
        print("  verdict       ROTATED by %d of %d Tx slots: angles are wrong as recorded" % (k, n_tx))
        print("  realign       drop %d int16 (%d to the block boundary + %d blocks)" % (skip_int16, cap_pre, best))
    elif verdict == "RX_MISALIGNED":
        # A constant offset, not corruption: the whole take starts mid-chirp.
        print("  verdict       MISALIGNED by %d blocks (starts mid-chirp): angles are wrong as recorded" % best)
        print("  realign       drop %d int16 (%d to the block boundary + %d blocks)" % (skip_int16, cap_pre, best))
    else:
        print("  verdict       UNSURE: %d blocks fits best, but not clearly. Has the scene or radar changed?" % best)

    if args.write_meta:
        path = os.path.join(args.capture, "meta.json")
        with open(path) as f:
            meta = json.load(f)
        meta["tx_order_check"] = {
            "reference": os.path.normpath(args.ref),
            "verdict": verdict,
            "shift_blocks": best,
            "realign_skip_int16": skip_int16,
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
