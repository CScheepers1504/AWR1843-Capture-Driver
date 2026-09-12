#!/usr/bin/env python3
"""
Subscribe to /radar_data and write raw frames to disk.

Writes three files into the session directory:
    frames.bin   - raw frame payloads, concatenated, no padding
    index.csv    - one row per frame: seq, ros_stamp_ns, wall_time_s, byte_offset
    meta.json    - radar config snapshot + derived dimensions

Run AFTER sourcing the workspace, e.g.
    python3 recorder.py --name handwave_01
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

try:
    from mmwave_drv.msg import Frame
except ImportError:
    sys.exit("Cannot import mmwave_drv.msg.Frame -- source install/setup.bash first.")


def count_bits(mask):
    return bin(int(mask)).count("1")


def derive_dims(cfg):
    """Mirror the frame-size arithmetic in radar_data_node.cpp (lines 129-136)."""
    prof = cfg["profileCfg"]
    frm = cfg["frameCfg"]
    n_loops = int(frm["numChirps"])
    n_samples = int(prof["numAdcSamples"])
    n_rx = count_bits(cfg["channelCfg"]["rxChannelEn"])
    n_tx = int(frm["chirpEndIndex"]) - int(frm["chirpStartIndex"]) + 1
    # adcOutputFmt: 0 = complex -> 2 components, 1 = real -> 1
    iq = (int(cfg["adcbufCfg"]["adcOutputFmt"]) + 2) % 3
    bytes_per_sample = 2
    frame_bytes = n_loops * n_samples * bytes_per_sample * iq * n_rx * n_tx
    return {
        "n_loops": n_loops,
        "n_tx": n_tx,
        "n_rx": n_rx,
        "n_samples": n_samples,
        "iq": iq,
        "bytes_per_sample": bytes_per_sample,
        "frame_bytes": frame_bytes,
        "n_chirps_total": n_loops * n_tx,
    }


class Recorder(Node):
    def __init__(self, session_dir, cfg, dims, max_frames):
        super().__init__("radar_recorder")
        self.session_dir = session_dir
        self.dims = dims
        self.max_frames = max_frames

        self.bin_f = open(os.path.join(session_dir, "frames.bin"), "wb")
        self.idx_f = open(os.path.join(session_dir, "index.csv"), "w")
        self.idx_f.write("seq,ros_stamp_ns,wall_time_s,byte_offset,byte_len\n")

        self.offset = 0
        self.count = 0
        self.size_mismatch = 0
        self.first_seq = None
        self.last_seq = None
        self.gaps = 0
        self.missed = 0
        self.seq_unparsed = 0
        self.payload_kind = None
        self.t0 = None

        # Must match the publisher QoS in radar_data_node.cpp. Both sides were
        # default-reliable, which throttled the whole chain to the speed of this
        # Python callback and hid the shortfall (no sequence gaps, just a lower
        # frame rate). Best-effort surfaces any shortfall as gaps instead.
        qos = QoSProfile(
            depth=100,
            history=HistoryPolicy.KEEP_LAST,
            reliability=ReliabilityPolicy.BEST_EFFORT,
        )
        self.sub = self.create_subscription(Frame, "radar_data", self.on_frame, qos)
        self.get_logger().info(
            "Recording to %s (expecting %d B/frame)" % (session_dir, dims["frame_bytes"])
        )

    def on_frame(self, msg):
        now = time.time()
        if self.t0 is None:
            self.t0 = now

        # Which branch runs here is the whole ballgame. Frame.msg declares
        # uint8[], which rclpy deserialises as a numpy array -- one memcpy. It
        # was byte[] (an IDL octet sequence), which is excluded from the numpy
        # fast path and arrives as ~24k single-byte objects to be joined, at
        # roughly 5-6 ms/frame on this Xavier NX. That capped the recorder at
        # 169.5 Hz against a publisher running a rock-steady 333.33 Hz.
        # The branch taken is logged once so a silent regression is visible.
        fd = msg.frame_data
        if isinstance(fd, (bytes, bytearray)):
            data = bytes(fd)
            kind = "bytes"
        elif hasattr(fd, "tobytes"):        # numpy array or array.array
            data = fd.tobytes()
            kind = "numpy/array (fast)"
        else:                                # list of length-1 bytes objects
            data = b"".join(fd)
            kind = "python list (SLOW -- is Frame.msg still byte[]?)"
        if self.payload_kind is None:
            self.payload_kind = kind
            self.get_logger().info("frame_data arrives as: %s" % kind)
        n = len(data)

        if n != self.dims["frame_bytes"]:
            self.size_mismatch += 1
            if self.size_mismatch == 1:
                self.get_logger().warn(
                    "Frame size %d does not match config-derived %d. "
                    "The config on disk may differ from the one the driver loaded."
                    % (n, self.dims["frame_bytes"])
                )

        # header.frame_id carries the driver's incrementing counter.
        #
        # The old fallback here was `seq = self.count` on a parse failure, which
        # is the recorder's OWN callback counter: it increments by exactly 1
        # every callback, so gap detection silently degraded into "count my own
        # callbacks" and could never report a gap. Capture 2026-08-26_17-09-53
        # reported sequence_gaps=0 while dropping 2416 of 4916 published frames.
        # A parse failure is now counted and reported, never papered over.
        try:
            seq = int(msg.header.frame_id)
        except (TypeError, ValueError):
            self.seq_unparsed += 1
            if self.seq_unparsed == 1:
                self.get_logger().error(
                    "header.frame_id %r is not an integer -- LOSS DETECTION IS "
                    "DISABLED for this capture." % (msg.header.frame_id,)
                )
            seq = None

        if seq is not None:
            if self.last_seq is None:
                self.first_seq = seq
            elif seq != self.last_seq + 1:
                self.gaps += 1
                self.missed += seq - self.last_seq - 1
                if self.gaps <= 10:
                    self.get_logger().warn("Sequence gap: %s -> %s" % (self.last_seq, seq))
            self.last_seq = seq

        stamp_ns = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
        self.bin_f.write(data)
        self.idx_f.write("%d,%d,%.6f,%d,%d\n" % (seq, stamp_ns, now, self.offset, n))
        self.offset += n
        self.count += 1

        if self.count % 100 == 0:
            elapsed = now - self.t0
            rate = self.count / elapsed if elapsed > 0 else 0
            self.get_logger().info(
                "%d frames, %.1f MB, %.1f Hz" % (self.count, self.offset / 1e6, rate)
            )

        if self.max_frames and self.count >= self.max_frames:
            self.get_logger().info("Reached --max-frames, stopping.")
            raise SystemExit(0)

    def close(self):
        self.bin_f.close()
        self.idx_f.close()
        elapsed = (time.time() - self.t0) if self.t0 else 0
        rate = self.count / elapsed if elapsed > 0 else 0
        # seq_span is the publisher's own frame count over the same window, so
        # frames/seq_span is the fraction actually captured. Without it a slow
        # subscriber looks identical to a slow radar -- which is exactly how the
        # publisher's true 333 Hz went unnoticed while this reported ~160 Hz.
        span = None
        if self.first_seq is not None and self.last_seq is not None:
            span = self.last_seq - self.first_seq + 1
        summary = {
            "frames": self.count,
            "bytes": self.offset,
            "duration_s": round(elapsed, 3),
            "mean_rate_hz": round(rate, 2),
            "sequence_gaps": self.gaps,
            "frames_missed": self.missed,
            "seq_span": span,
            "capture_fraction": round(self.count / span, 4) if span else None,
            "publisher_rate_hz": round(span / elapsed, 2) if span and elapsed else None,
            "seq_unparsed": self.seq_unparsed,
            "payload_kind": self.payload_kind,
            "size_mismatches": self.size_mismatch,
        }
        path = os.path.join(self.session_dir, "meta.json")
        with open(path) as f:
            meta = json.load(f)
        meta["capture"] = summary
        with open(path, "w") as f:
            json.dump(meta, f, indent=2)
        print("\n--- capture summary ---")
        for k, v in summary.items():
            print("  %-18s %s" % (k, v))
        print("  written to        %s" % self.session_dir)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default=None, help="session name (default: timestamp)")
    ap.add_argument("--out", default=os.path.expanduser("~/ssd/captures"))
    # Derived from this file's location, not hardcoded: recorder.py lives in
    # <ws>/scripts/, so the config sits at <ws>/src/mmWave_DRV/config/. A
    # hardcoded absolute path here broke silently when the tree was moved.
    ap.add_argument(
        "--config",
        default=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "mmWave_DRV", "config", "awr1843_launchmonitor.json",
        ),
    )
    ap.add_argument("--note", default="", help="free-text description of the capture")
    ap.add_argument("--max-frames", type=int, default=0, help="0 = until Ctrl+C")
    args = ap.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)
    dims = derive_dims(cfg)

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    name = "%s_%s" % (stamp, args.name) if args.name else stamp
    session_dir = os.path.join(args.out, name)
    os.makedirs(session_dir, exist_ok=False)

    with open(os.path.join(session_dir, "meta.json"), "w") as f:
        json.dump(
            {
                "session": name,
                "recorded_utc": datetime.utcnow().isoformat() + "Z",
                "note": args.note,
                "config_path": args.config,
                "config": cfg,
                "dims": dims,
            },
            f,
            indent=2,
        )

    rclpy.init()
    node = Recorder(session_dir, cfg, dims, args.max_frames)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
