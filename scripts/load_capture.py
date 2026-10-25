#!/usr/bin/env python3
"""
Read a capture's frames.bin as int16, realigned by the chirp_align and tx_order_check stamps
in meta.json.

    raw, meta, info = load_capture(capture_dir)                      # refuses an unknown slot order
    raw, meta, info = load_capture(capture_dir, allow_unsure=True)   # range-only work
    raw, meta, info = load_capture(capture_dir, skip_int16=N)        # manual offset

    python3 scripts/load_capture.py <capture_dir> [...]              # print what it would do
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
    align, tx_check = meta.get("chirp_align"), meta.get("tx_order_check")
    name = meta.get("session", "?")

    align_drop = 0
    if align is None:
        notes.append("chirp alignment not checked (run chirp_align_check.py --write-meta)")
    elif align.get("verdict") == "UNSURE":
        notes.append("chirp alignment unsure, treated as 0")
    else:
        align_drop = int(align["drop_int16"])

    if tx_check is None:
        notes.append("Tx slot order not checked, recorded order assumed")
        return align_drop, "chirp_align only", notes

    new_stamp = "block_offset_int16" in tx_check
    ref = os.path.basename(os.path.normpath(str(tx_check.get("reference", "?"))))
    if not new_stamp and align_drop != 0:
        # Older tx_order_check stamps were measured on samples not yet moved to a block
        # boundary, so their shift means nothing on an offset capture.
        raise CaptureRefused(
            "%s: the tx_order_check stamp predates block alignment and the capture is %d int16 "
            "off a boundary. Re-run tx_order_check.py --write-meta or pass skip_int16."
            % (name, align_drop))

    verdict = tx_check["verdict"]
    if verdict == "MATCH":
        skip = int(tx_check["realign_skip_int16"]) if new_stamp else align_drop
        return skip, "Tx order MATCH vs %s" % ref, notes
    if verdict in ("ROTATED", "RX_MISALIGNED"):
        return (int(tx_check["realign_skip_int16"]),
                "Tx order %s by %d blocks vs %s" % (verdict, int(tx_check["shift_blocks"]), ref), notes)
    if not allow_unsure:
        raise CaptureRefused(
            "%s: Tx slot order unknown (check %s, margin %.2f vs %s). Re-run tx_order_check.py, "
            "or pass allow_unsure=True for range-only work."
            % (name, verdict, tx_check.get("margin", float("nan")), ref))
    notes.append("Tx slot order unknown: angles unusable")
    skip = int(tx_check["block_offset_int16"]) if new_stamp else align_drop
    return skip, "Tx order UNSURE, allowed: block offset only", notes


def load_capture(cap, allow_unsure=False, skip_int16=None, quiet=False):
    """(raw int16 whole frames, meta, info). info: skip_int16, frame_shift, t0, n_frames, source, notes."""
    with open(os.path.join(cap, "meta.json")) as f:
        meta = json.load(f)
    frame_bytes = int(meta["dims"]["frame_bytes"])
    frame_period_s = float(meta["config"]["frameCfg"]["framePeriod"]) * 1e-3

    if skip_int16 is None:
        skip, source, notes = realign_skip(meta, allow_unsure)
    else:
        # The caller has its own evidence, so the stamps are not consulted.
        skip, source, notes = int(skip_int16), "manual skip_int16, stamps ignored", []
    if skip >= frame_bytes // 2:
        raise CaptureRefused("%s: realignment of %d int16 is a frame or more (%d per frame). "
                             "Check the meta.json stamps." % (cap, skip, frame_bytes // 2))

    # seek + fromfile because fromfile's offset argument needs numpy >= 1.17.
    with open(os.path.join(cap, "frames.bin"), "rb") as f:
        f.seek(2 * skip)
        raw = np.fromfile(f, dtype=np.int16)
    n_frames = raw.size // (frame_bytes // 2)
    raw = raw[: n_frames * (frame_bytes // 2)]

    info = {"skip_int16": skip, "frame_shift": skip / (frame_bytes // 2),
            "t0": skip / (frame_bytes // 2) * frame_period_s,
            "n_frames": n_frames, "source": source, "notes": notes}
    if not quiet:
        print("alignment    : drop %d int16 (%s)" % (skip, source))
        for n in notes:
            print("  note: " + n)
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
