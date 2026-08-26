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
        self.last_seq = None
        self.gaps = 0
        self.t0 = None

        self.sub = self.create_subscription(Frame, "radar_data", self.on_frame, 50)
        self.get_logger().info(
            "Recording to %s (expecting %d B/frame)" % (session_dir, dims["frame_bytes"])
        )

    def on_frame(self, msg):
        now = time.time()
        if self.t0 is None:
            self.t0 = now

        fd = msg.frame_data
        if isinstance(fd, (bytes, bytearray)):
            data = bytes(fd)
        elif hasattr(fd, "tobytes"):        # numpy array or array.array
            data = fd.tobytes()
        else:                                # list of length-1 bytes objects
            data = b"".join(fd)
        n = len(data)

        if n != self.dims["frame_bytes"]:
            self.size_mismatch += 1
            if self.size_mismatch == 1:
                self.get_logger().warn(
                    "Frame size %d does not match config-derived %d. "
                    "The config on disk may differ from the one the driver loaded."
                    % (n, self.dims["frame_bytes"])
                )

        # header.frame_id carries the driver's incrementing counter
        try:
            seq = int(msg.header.frame_id)
        except (TypeError, ValueError):
            seq = self.count
        if self.last_seq is not None and seq != self.last_seq + 1:
            self.gaps += 1
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
        summary = {
            "frames": self.count,
            "bytes": self.offset,
            "duration_s": round(elapsed, 3),
            "mean_rate_hz": round(rate, 2),
            "sequence_gaps": self.gaps,
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
    ap.add_argument(
        "--config",
        default=os.path.expanduser(
            "~/ssd/chris-launch-monitor/src/mmWave_DRV/config/"
            "awr1843_launchmonitor.json"
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
