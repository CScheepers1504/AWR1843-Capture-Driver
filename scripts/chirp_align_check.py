#!/usr/bin/env python3
"""
Check from the samples themselves that a capture starts on an Rx-block boundary.

    python3 scripts/chirp_align_check.py <capture_dir>
    python3 scripts/chirp_align_check.py <capture_dir> --write-meta

Exit status: 0 aligned, 4 offset found, 5 unsure, 2 could not run.

"""

import argparse
import json
import os
import sys

import numpy as np

CONTRAST_MIN = 2.0   # boundary peak / median position needed for a verdict
MARGIN_MIN = 1.3     # boundary peak / runner-up position


def block_profile(raw, ns, phase):
    """Mean |dx| per position within an Rx block, for one int16 packing phase."""
    y = raw[phase:]
    y = y[: (len(y) // 4) * 4].reshape(-1, 4)
    x = np.empty(2 * y.shape[0], np.complex64)
    x[0::2] = y[:, 0] + 1j * y[:, 2]
    x[1::2] = y[:, 1] + 1j * y[:, 3]
    x = x[: (len(x) // ns) * ns]
    dx = np.abs(np.diff(x))
    pos = np.arange(len(dx)) % ns
    return np.bincount(pos, weights=dx, minlength=ns) / np.bincount(pos, minlength=ns)


def check(cap, n_frames, skip_frames):
    with open(os.path.join(cap, "meta.json")) as f:
        meta = json.load(f)
    d = meta["dims"]
    if d["iq"] != 2:
        raise ValueError("%s: complex (I/Q) captures only" % cap)
    ns = d["n_samples"]
    i16_per_frame = d["frame_bytes"] // 2
    path = os.path.join(cap, "frames.bin")
    avail = os.path.getsize(path) // 2 // i16_per_frame
    n = min(n_frames, avail - skip_frames)
    if n < 3:
        raise ValueError("%s: only %d frames available" % (cap, avail))
    with open(path, "rb") as f:
        f.seek(skip_frames * i16_per_frame * 2)
        raw = np.fromfile(f, dtype=np.int16, count=n * i16_per_frame).astype(np.float32)

    best = None
    for phase in range(4):
        prof = block_profile(raw, ns, phase)
        order = np.argsort(prof)[::-1]
        peak, runner, med = prof[order[0]], prof[order[1]], np.median(prof)
        contrast = peak / max(med, 1e-9)
        if best is None or contrast > best["contrast"]:
            best = {"phase": phase, "pos": int(order[0]), "contrast": float(contrast),
                    "margin": float(peak / max(runner, 1e-9))}

    # Peak at position p = jump between x[p] and x[p+1]: x[p+1] starts a block, so the
    # (phase-shifted) stream begins a = ns-1-p samples into a block. Dropping
    # phase + 2*((ns - a) % ns) int16 from the start puts it on a block boundary.
    a = (ns - 1 - best["pos"]) % ns
    drop_i16 = (best["phase"] + 2 * ((ns - a) % ns)) % (2 * ns)
    best.update({"drop_int16": int(drop_i16), "drop_bytes": int(2 * drop_i16),
                 "block_bytes": 4 * ns, "frames_used": int(n)})
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    ap.add_argument("capture")
    ap.add_argument("--frames", type=int, default=200)
    ap.add_argument("--skip-frames", type=int, default=5,
                    help="leading frames ignored (subscription transient)")
    ap.add_argument("--write-meta", action="store_true",
                    help="record the result in the capture's meta.json")
    args = ap.parse_args()

    try:
        r = check(args.capture, args.frames, args.skip_frames)
    except (OSError, ValueError, KeyError) as e:
        print("chirp alignment check could not run: %s" % e)
        return 2

    if r["contrast"] < CONTRAST_MIN or r["margin"] < MARGIN_MIN:
        verdict, code = "UNSURE", 5
    elif r["drop_int16"] == 0:
        verdict, code = "ALIGNED", 0
    else:
        verdict, code = "OFFSET", 4
    r["verdict"] = verdict

    print("chirp alignment check: %s" % os.path.basename(os.path.normpath(args.capture)))
    print("  verdict       %s" % verdict)
    print("  boundary      contrast %.1f (need %.1f), margin %.2f (need %.2f), packing phase %d"
          % (r["contrast"], CONTRAST_MIN, r["margin"], MARGIN_MIN, r["phase"]))
    if verdict == "OFFSET":
        print("  realign       drop %d int16 (%d B) from the start; offset is modulo one Rx block (%d B)"
              % (r["drop_int16"], r["drop_bytes"], r["block_bytes"]))
    if args.write_meta:
        path = os.path.join(args.capture, "meta.json")
        with open(path) as f:
            meta = json.load(f)
        meta["chirp_align"] = r
        with open(path, "w") as f:
            json.dump(meta, f, indent=2)
    return code


if __name__ == "__main__":
    sys.exit(main())
