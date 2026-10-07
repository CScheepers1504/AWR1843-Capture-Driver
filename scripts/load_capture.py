#!/usr/bin/env python3
"""
Read a capture's frames.bin as int16, realigned to the radar's chirp grid.

    from load_capture import load_capture
    raw, meta, info = load_capture(capture_dir)
    raw, meta, info = load_capture(capture_dir, allow_unsure=True)   # range-only work
    raw, meta, info = load_capture(capture_dir, skip_int16=N)        # manual override

    python3 scripts/load_capture.py <capture_dir> [...]              # print what it would do

Python twin of Sports-Ball-Analysis/matlab/load_capture.m -- keep the two in step.

  chirp_align     chirp_align_check.py --write-meta: offset to the Rx-block
                  boundary, measured from the samples
  tx_order_check  tx_order_check.py --write-meta: whole-block rotation against a
                  reference. Its realign_skip_int16 already includes the block offset.

"""

import json
import os
import sys

import numpy as np


class CaptureRefused(ValueError):
    pass


def realign_skip(meta, allow_unsure=False):
    """(skip_int16, source, notes) from the stamps in meta.json."""
    notes = []
    ca, tx = meta.get("chirp_align"), meta.get("tx_order_check")
    name = meta.get("session", "?")

    ca_drop = 0
    if ca is None:
        notes.append("chirp alignment NOT checked -- run scripts/chirp_align_check.py --write-meta")
    elif ca.get("verdict") == "UNSURE":
        notes.append("chirp alignment UNSURE (no clear block boundary) -- treated as 0")
    else:
        ca_drop = int(ca["drop_int16"])

    if tx is None:
        notes.append("Tx slot order NOT checked -- angles rest on the recorded order")
        return ca_drop, "chirp_align only", notes

    new_stamp = "block_offset_int16" in tx
    ref = os.path.basename(os.path.normpath(str(tx.get("reference", "?"))))
    if not new_stamp and ca_drop != 0:
        # Stamped before tx_order_check pre-aligned to the block boundary: its
        # shift was measured on misaligned samples and means nothing.
        raise CaptureRefused(
            "%s: tx_order_check predates block pre-alignment and the capture is %d int16 off "
            "a block boundary. Re-run scripts/tx_order_check.py --write-meta, or pass skip_int16."
            % (name, ca_drop))

    verdict = tx["verdict"]
    if verdict == "MATCH":
        skip = int(tx["realign_skip_int16"]) if new_stamp else ca_drop
        return skip, "Tx order MATCH vs %s" % ref, notes
    if verdict in ("ROTATED", "RX_MISALIGNED"):
        return (int(tx["realign_skip_int16"]),
                "Tx order %s by %d blocks vs %s" % (verdict, int(tx["shift_blocks"]), ref), notes)
    if not allow_unsure:
        raise CaptureRefused(
            "%s: Tx order check was %s (margin %.2f vs %s): the slot order is unknown. Re-run "
            "scripts/tx_order_check.py --write-meta against a valid reference, or pass "
            "allow_unsure=True (block offset only) for range-only work."
            % (name, verdict, tx.get("margin", float("nan")), ref))
    notes.append("Tx slot order UNKNOWN -- do not use angles from this capture")
    skip = int(tx["block_offset_int16"]) if new_stamp else ca_drop
    return skip, "Tx order UNSURE, allowed: block offset only", notes


def load_capture(cap, allow_unsure=False, skip_int16=None, quiet=False):
    """(raw int16 whole frames, meta, info). info: skip_int16, frame_shift, t0, n_frames, source, notes."""
    with open(os.path.join(cap, "meta.json")) as f:
        meta = json.load(f)
    fb = int(meta["dims"]["frame_bytes"])
    T = float(meta["config"]["frameCfg"]["framePeriod"]) * 1e-3

    if skip_int16 is None:
        skip, source, notes = realign_skip(meta, allow_unsure)
    else:
        # Manual: the stamps are not consulted (they may be UNSURE against a
        # reference from another rig geometry; the caller has its own evidence).
        skip, source, notes = int(skip_int16), "manual skip_int16, stamps ignored", []
    if skip >= fb // 2:
        raise CaptureRefused("%s: realignment of %d int16 is a frame or more (%d int16/frame) -- "
                             "check the stamps in meta.json" % (cap, skip, fb // 2))

    # seek + fromfile(file object): the offset= argument needs numpy >= 1.17.
    with open(os.path.join(cap, "frames.bin"), "rb") as f:
        f.seek(2 * skip)
        raw = np.fromfile(f, dtype=np.int16)
    nf = raw.size // (fb // 2)
    raw = raw[: nf * (fb // 2)]

    info = {"skip_int16": skip, "frame_shift": skip / (fb // 2), "t0": skip / (fb // 2) * T,
            "n_frames": nf, "source": source, "notes": notes}
    if not quiet:
        print("alignment    : drop %d int16 (%s)" % (skip, source))
        for n in notes:
            print("  ^^ " + n)
    return raw, meta, info


if __name__ == "__main__":
    rc = 0
    for cap in sys.argv[1:]:
        print(os.path.basename(os.path.normpath(cap)))
        try:
            _, _, info = load_capture(cap)
            print("  %d frames" % info["n_frames"])
        except CaptureRefused as e:
            print("  REFUSED: %s" % e)
            rc = 1
    sys.exit(rc)
