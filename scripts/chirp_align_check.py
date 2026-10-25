#!/usr/bin/env python3
"""
Check from the samples that a capture starts on an Rx-block boundary.

    python3 scripts/chirp_align_check.py <capture_dir> [--write-meta]

Exit status: 0 aligned, 4 offset found, 5 unsure, 2 could not run.
"""

import argparse
import json
import os
import sys

import numpy as np

CONTRAST_MIN = 2.0   # boundary peak over the median position, needed for a verdict
MARGIN_MIN = 1.3     # boundary peak over the runner-up position


def block_profile(raw, n_samples, phase):
    """Mean |x[n+1] - x[n]| at each position within an Rx block, for one int16 packing phase."""
    words = raw[phase:]
    words = words[: (len(words) // 4) * 4].reshape(-1, 4)
    iq = np.empty(2 * words.shape[0], np.complex64)
    iq[0::2] = words[:, 0] + 1j * words[:, 2]
    iq[1::2] = words[:, 1] + 1j * words[:, 3]
    iq = iq[: (len(iq) // n_samples) * n_samples]
    jump = np.abs(np.diff(iq))
    position = np.arange(len(jump)) % n_samples
    return np.bincount(position, weights=jump, minlength=n_samples) / np.bincount(position, minlength=n_samples)


def check(cap, n_frames, skip_frames):
    with open(os.path.join(cap, "meta.json")) as f:
        meta = json.load(f)
    dims = meta["dims"]
    if dims["iq"] != 2:
        raise ValueError("%s: complex (I/Q) captures only" % cap)
    n_samples = dims["n_samples"]
    frame_int16 = dims["frame_bytes"] // 2
    path = os.path.join(cap, "frames.bin")
    available = os.path.getsize(path) // 2 // frame_int16
    n = min(n_frames, available - skip_frames)
    if n < 3:
        raise ValueError("%s: only %d frames available" % (cap, available))
    with open(path, "rb") as f:
        f.seek(skip_frames * frame_int16 * 2)
        raw = np.fromfile(f, dtype=np.int16, count=n * frame_int16).astype(np.float32)

    best = None
    for phase in range(4):
        profile = block_profile(raw, n_samples, phase)
        ranked = np.argsort(profile)[::-1]
        peak, runner_up, median = profile[ranked[0]], profile[ranked[1]], np.median(profile)
        contrast = peak / max(median, 1e-9)
        if best is None or contrast > best["contrast"]:
            best = {"phase": phase, "pos": int(ranked[0]), "contrast": float(contrast),
                    "margin": float(peak / max(runner_up, 1e-9))}

    # A peak at position p is the jump from x[p] to x[p+1], so x[p+1] starts a block and the
    # phase-shifted stream begins `into_block` samples into one. Dropping
    # phase + 2 * ((n_samples - into_block) % n_samples) int16 puts it on a boundary.
    into_block = (n_samples - 1 - best["pos"]) % n_samples
    drop_int16 = (best["phase"] + 2 * ((n_samples - into_block) % n_samples)) % (2 * n_samples)
    best.update({"drop_int16": int(drop_int16), "drop_bytes": int(2 * drop_int16),
                 "block_bytes": 4 * n_samples, "frames_used": int(n)})
    return best


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().split("\n\n")[0])
    parser.add_argument("capture")
    parser.add_argument("--frames", type=int, default=200)
    parser.add_argument("--skip-frames", type=int, default=5,
                        help="leading frames ignored (subscription transient)")
    parser.add_argument("--write-meta", action="store_true",
                        help="record the result in the capture's meta.json")
    args = parser.parse_args()

    try:
        result = check(args.capture, args.frames, args.skip_frames)
    except (OSError, ValueError, KeyError) as e:
        print("chirp alignment check could not run: %s" % e)
        return 2

    if result["contrast"] < CONTRAST_MIN or result["margin"] < MARGIN_MIN:
        verdict, code = "UNSURE", 5
    elif result["drop_int16"] == 0:
        verdict, code = "ALIGNED", 0
    else:
        verdict, code = "OFFSET", 4
    result["verdict"] = verdict

    print("chirp alignment check: %s" % os.path.basename(os.path.normpath(args.capture)))
    print("  verdict       %s" % verdict)
    print("  boundary      contrast %.1f (need %.1f), margin %.2f (need %.2f), packing phase %d"
          % (result["contrast"], CONTRAST_MIN, result["margin"], MARGIN_MIN, result["phase"]))
    if verdict == "OFFSET":
        print("  realign       drop %d int16 (%d B) to reach a block boundary"
              % (result["drop_int16"], result["drop_bytes"]))
    if args.write_meta:
        path = os.path.join(args.capture, "meta.json")
        with open(path) as f:
            meta = json.load(f)
        meta["chirp_align"] = result
        with open(path, "w") as f:
            json.dump(meta, f, indent=2)
    return code


if __name__ == "__main__":
    sys.exit(main())
