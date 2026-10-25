#!/usr/bin/env python3
"""
Record /radar_data to a capture folder: frames.bin (raw frames), index.csv (one row per frame)
and meta.json (profile, dimensions and, on exit, the capture summary).

    python3 recorder.py --name handwave_01 [--max-frames N]      # after sourcing the workspace
"""

import argparse
import json
import os
import shutil
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

NOT_TIMED = -2147483648   # burst_phase value for a frame start the data node could not time


def count_bits(mask):
    return bin(int(mask)).count("1")


def derive_dims(cfg):
    """Frame dimensions from the profile, with the same arithmetic as radar_data_node.cpp."""
    profile = cfg["profileCfg"]
    frame = cfg["frameCfg"]
    n_loops = int(frame["numChirps"])
    n_samples = int(profile["numAdcSamples"])
    n_rx = count_bits(cfg["channelCfg"]["rxChannelEn"])
    n_tx = int(frame["chirpEndIndex"]) - int(frame["chirpStartIndex"]) + 1
    iq = (int(cfg["adcbufCfg"]["adcOutputFmt"]) + 2) % 3     # adcOutputFmt 0 complex -> 2, 1 real -> 1
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
    def __init__(self, capture_dir, cfg, dims, max_frames, no_frames_timeout):
        super().__init__("radar_recorder")
        self.capture_dir = capture_dir
        self.dims = dims
        self.max_frames = max_frames
        self.no_frames_timeout = no_frames_timeout
        self.t_start = time.time()
        self.exit_code = 0

        self.bin_f = open(os.path.join(capture_dir, "frames.bin"), "wb")
        self.idx_f = open(os.path.join(capture_dir, "index.csv"), "w")
        self.idx_f.write("seq,ros_stamp_ns,wall_time_s,byte_offset,byte_len,stream_offset,burst_phase\n")

        # The data node stamps every frame with its stream offset, the DCA1000 byte count of the
        # frame's first byte. Aligned frames sit at multiples of frame_bytes, and consecutive
        # frames differ by exactly one frame_bytes unless the node dropped frames.
        self.first_stream_offset = None
        self.last_stream_offset = None
        self.join_offset = None
        self.zero_filled = 0
        self.misaligned = 0
        self.stream_gaps = 0
        self.stream_frames_skipped = 0
        self.stream_restarts = 0
        # The node also times each frame start from the idle gap between packet bursts
        # (burst_phase, bytes). A slipped take shows phases near a multiple of the chirp size.
        self.burst_phases = []
        self.burst_warned = False
        self.chirp_bytes = dims["n_samples"] * dims["bytes_per_sample"] * dims["iq"] * dims["n_rx"]

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

        # Must match the publisher QoS in radar_data_node.cpp. A reliable pair throttles the
        # whole chain to this callback's speed and shows the shortfall only as a lower frame
        # rate. Best effort shows it as sequence gaps instead.
        qos = QoSProfile(
            depth=100,
            history=HistoryPolicy.KEEP_LAST,
            reliability=ReliabilityPolicy.BEST_EFFORT,
        )
        self.sub = self.create_subscription(Frame, "radar_data", self.on_frame, qos)
        self.get_logger().info(
            "Recording to %s (expecting %d B/frame)" % (capture_dir, dims["frame_bytes"])
        )

        # Without a timeout the recorder waits forever when nothing is publishing, and a dead
        # stream looks exactly like a slow one.
        self.watchdog = None
        if no_frames_timeout > 0:
            self.watchdog = self.create_timer(1.0, self.check_stream)

    def check_stream(self):
        if self.count > 0:
            self.watchdog.cancel()
            return
        if time.time() - self.t_start > self.no_frames_timeout:
            self.get_logger().error(
                "No frames after %.0f s on radar_data: the sensor or the data node is not streaming."
                % self.no_frames_timeout
            )
            self.exit_code = 3
            raise SystemExit(3)

    def on_frame(self, msg):
        now = time.time()
        if self.t0 is None:
            self.t0 = now

        # Frame.msg declares uint8[], which rclpy delivers as a numpy array (one copy). A byte[]
        # field arrives as a list of single-byte objects, slow enough to halve the recorded
        # rate, so the branch taken is logged once.
        payload = msg.frame_data
        if isinstance(payload, (bytes, bytearray)):
            data = bytes(payload)
            kind = "bytes"
        elif hasattr(payload, "tobytes"):        # numpy array or array.array
            data = payload.tobytes()
            kind = "numpy/array (fast)"
        else:                                    # list of length-1 bytes objects
            data = b"".join(payload)
            kind = "python list (slow: is Frame.msg still byte[]?)"
        if self.payload_kind is None:
            self.payload_kind = kind
            self.get_logger().info("frame_data arrives as: %s" % kind)
        n_bytes = len(data)

        if n_bytes != self.dims["frame_bytes"]:
            self.size_mismatch += 1
            if self.size_mismatch == 1:
                self.get_logger().warn(
                    "Frame is %d B but the profile gives %d B: did the driver load another profile?"
                    % (n_bytes, self.dims["frame_bytes"])
                )

        # header.frame_id carries the driver's frame counter. A parse failure is counted and
        # reported rather than replaced by the recorder's own count, which could never show a gap.
        try:
            seq = int(msg.header.frame_id)
        except (TypeError, ValueError):
            self.seq_unparsed += 1
            if self.seq_unparsed == 1:
                self.get_logger().error(
                    "header.frame_id %r is not an integer: dropped frames cannot be counted."
                    % (msg.header.frame_id,)
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

        stream_offset = getattr(msg, "stream_offset", None)
        if stream_offset is not None:
            frame_bytes = self.dims["frame_bytes"]
            if stream_offset % frame_bytes != 0:
                self.misaligned += 1
                if self.misaligned == 1:
                    self.get_logger().error("Frame at stream offset %d is off the frame boundary." % stream_offset)
            if self.last_stream_offset is None:
                self.first_stream_offset = stream_offset
            elif stream_offset < self.last_stream_offset:
                self.stream_restarts += 1
                self.get_logger().error("Stream restarted mid-take (offset %d -> %d)."
                                        % (self.last_stream_offset, stream_offset))
            elif stream_offset != self.last_stream_offset + frame_bytes:
                self.stream_gaps += 1
                self.stream_frames_skipped += (stream_offset - self.last_stream_offset) // frame_bytes - 1
            self.last_stream_offset = stream_offset
            self.join_offset = msg.join_offset
            self.zero_filled = msg.zero_filled
        burst_phase = getattr(msg, "burst_phase", None)
        timed = burst_phase is not None and burst_phase != NOT_TIMED
        if timed:
            self.burst_phases.append(burst_phase)
            if abs(burst_phase) * 2 >= self.chirp_bytes and not self.burst_warned:
                self.burst_warned = True
                self.get_logger().error("Frame start %d B (%.2f chirps) off the frame grid: "
                                        "Tx slot order unreliable."
                                        % (burst_phase, burst_phase / self.chirp_bytes))

        stamp_ns = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
        self.bin_f.write(data)
        self.idx_f.write("%d,%d,%.6f,%d,%d,%s,%s\n" % (seq, stamp_ns, now, self.offset, n_bytes,
                                                      "" if stream_offset is None else stream_offset,
                                                      burst_phase if timed else ""))
        self.offset += n_bytes
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

    def burst_summary(self):
        """Frame-start timing check. burst_slips counts frame starts more than half a chirp off
        the frame grid. On an aligned take it is 0 and burst_phase_min/max sit between minus one
        packet (-1456) and 0."""
        chirp = self.chirp_bytes
        phases = sorted(self.burst_phases)
        if not phases:
            return {"burst_timed_frames": 0, "burst_slips": None}
        slips = sum(1 for v in phases if abs(v) * 2 >= chirp)
        return {
            "burst_timed_frames": len(phases),
            "burst_timed_fraction": round(len(phases) / self.count, 3) if self.count else None,
            "burst_phase_min": phases[0],
            "burst_phase_median": phases[len(phases) // 2],
            "burst_phase_max": phases[-1],
            "burst_phase_chirps": round(phases[len(phases) // 2] / chirp, 2),
            "burst_slips": slips,
        }

    def close(self):
        self.bin_f.close()
        self.idx_f.close()
        elapsed = (time.time() - self.t0) if self.t0 else 0
        rate = self.count / elapsed if elapsed > 0 else 0
        # seq_span is the publisher's own frame count over the same window, so frames / seq_span
        # is the fraction captured. A rate alone cannot tell a slow subscriber from a slow radar.
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
            # aligned: every frame on a frame boundary of the DCA1000 stream.
            # join_offset 0: the node saw this stream from its first byte.
            "aligned": (self.misaligned == 0) if self.first_stream_offset is not None else None,
            "first_stream_offset": self.first_stream_offset,
            "join_offset": self.join_offset,
            "zero_filled_bytes": self.zero_filled,
            "stream_gaps": self.stream_gaps,
            "stream_frames_skipped": self.stream_frames_skipped,
            "stream_restarts": self.stream_restarts,
        }
        summary.update(self.burst_summary())
        path = os.path.join(self.capture_dir, "meta.json")
        with open(path) as f:
            meta = json.load(f)
        meta["capture"] = summary
        with open(path, "w") as f:
            json.dump(meta, f, indent=2)
        print("\n--- capture summary ---")
        for k, v in summary.items():
            print("  %-18s %s" % (k, v))
        print("  written to        %s" % self.capture_dir)

        # An empty capture directory would be pulled and sort as the latest take under its name.
        if self.count == 0:
            shutil.rmtree(self.capture_dir, ignore_errors=True)
            print("  no frames -- removed the empty capture directory")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default=None, help="capture name (default: timestamp)")
    parser.add_argument("--out", default=os.path.expanduser("~/ssd/captures"))
    # The default profile is found relative to this file (<ws>/scripts/recorder.py), so it
    # follows the workspace if the tree moves.
    parser.add_argument(
        "--config",
        default=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "mmWave_DRV", "config", "awr1843_launchmonitor.json",
        ),
    )
    parser.add_argument("--note", default="", help="free-text description of the capture")
    parser.add_argument("--max-frames", type=int, default=0, help="0 = until Ctrl+C")
    # 8 s because DDS discovery takes a second or two to match the publisher.
    parser.add_argument("--no-frames-timeout", type=float, default=8.0,
                        help="exit 3 if no frame arrives within this many seconds (0 = wait forever)")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)
    dims = derive_dims(cfg)

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    name = "%s_%s" % (stamp, args.name) if args.name else stamp
    capture_dir = os.path.join(args.out, name)
    os.makedirs(capture_dir, exist_ok=False)

    with open(os.path.join(capture_dir, "meta.json"), "w") as f:
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
    node = Recorder(capture_dir, cfg, dims, args.max_frames, args.no_frames_timeout)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    # Non-zero on the no-frames timeout, so session.sh can tell a dead stream from a finished take.
    sys.exit(node.exit_code)


if __name__ == "__main__":
    main()
