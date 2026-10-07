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
    def __init__(self, session_dir, cfg, dims, max_frames, no_frames_timeout):
        super().__init__("radar_recorder")
        self.session_dir = session_dir
        self.dims = dims
        self.max_frames = max_frames
        self.no_frames_timeout = no_frames_timeout
        self.t_start = time.time()
        self.exit_code = 0

        self.bin_f = open(os.path.join(session_dir, "frames.bin"), "wb")
        self.idx_f = open(os.path.join(session_dir, "index.csv"), "w")
        self.idx_f.write("seq,ros_stamp_ns,wall_time_s,byte_offset,byte_len,stream_offset,burst_phase\n")

        # Alignment, from the stream_offset the data node stamps on every frame
        # (DCA1000 byte count of the frame's first byte). Aligned frames sit at
        # multiples of frame_bytes; consecutive frames differ by exactly one
        # frame_bytes unless frames were dropped in the node.
        self.first_stream_offset = None
        self.last_stream_offset = None
        self.join_offset = None
        self.zero_filled = 0
        self.misaligned = 0
        self.stream_gaps = 0
        self.stream_frames_skipped = 0
        self.stream_restarts = 0
        # Frame starts timed by the data node from the idle gap between packet
        # bursts (burst_phase, bytes; INT32_MIN = not timed). A slipped take
        # shows phases near a multiple of the chirp size instead of near 0.
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

        # Without this the recorder waits forever when nothing is publishing,
        # and a dead stream looks exactly like a slow one. On 13 Sep that hang
        # was Ctrl-C'd three times over ssh, orphaning a recorder each time.
        self.watchdog = None
        if no_frames_timeout > 0:
            self.watchdog = self.create_timer(1.0, self.check_stream)

    def check_stream(self):
        if self.count > 0:
            self.watchdog.cancel()
            return
        if time.time() - self.t_start > self.no_frames_timeout:
            self.get_logger().error(
                "NO FRAMES after %.0f s -- nothing is publishing on radar_data. "
                "The sensor is not streaming, or the data node is not publishing."
                % self.no_frames_timeout
            )
            self.exit_code = 3
            raise SystemExit(3)

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

        so = getattr(msg, "stream_offset", None)
        if so is not None:
            fb = self.dims["frame_bytes"]
            if so % fb != 0:
                self.misaligned += 1
                if self.misaligned == 1:
                    self.get_logger().error("Frame at stream offset %d is NOT on a frame boundary." % so)
            if self.last_stream_offset is None:
                self.first_stream_offset = so
            elif so < self.last_stream_offset:
                self.stream_restarts += 1
                self.get_logger().error("Stream restarted mid-take (offset %d -> %d)." % (self.last_stream_offset, so))
            elif so != self.last_stream_offset + fb:
                self.stream_gaps += 1
                self.stream_frames_skipped += (so - self.last_stream_offset) // fb - 1
            self.last_stream_offset = so
            self.join_offset = msg.join_offset
            self.zero_filled = msg.zero_filled
        bp = getattr(msg, "burst_phase", None)
        if bp is not None and bp != -2147483648:
            self.burst_phases.append(bp)
            if abs(bp) * 2 >= self.chirp_bytes and not self.burst_warned:
                self.burst_warned = True
                self.get_logger().error("Frame start %d B (%.2f chirps) off the frame grid: "
                                        "Tx slot order NOT trustworthy." % (bp, bp / self.chirp_bytes))

        stamp_ns = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
        self.bin_f.write(data)
        self.idx_f.write("%d,%d,%.6f,%d,%d,%s,%s\n" % (seq, stamp_ns, now, self.offset, n,
                                                      "" if so is None else so,
                                                      "" if bp is None or bp == -2147483648 else bp))
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

    def burst_summary(self):
        """Frame-start timing check. burst_slips counts frame starts more than half
        a chirp off the frame grid; on an aligned take it is 0 and burst_phase_min/max
        sit between minus one packet (-1456) and 0."""
        chirp = self.chirp_bytes
        p = sorted(self.burst_phases)
        if not p:
            return {"burst_timed_frames": 0, "burst_slips": None}
        slips = sum(1 for v in p if abs(v) * 2 >= chirp)
        return {
            "burst_timed_frames": len(p),
            "burst_timed_fraction": round(len(p) / self.count, 3) if self.count else None,
            "burst_phase_min": p[0],
            "burst_phase_median": p[len(p) // 2],
            "burst_phase_max": p[-1],
            "burst_phase_chirps": round(p[len(p) // 2] / chirp, 2),
            "burst_slips": slips,
        }

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
            # Frame alignment (data node stream offsets). aligned = every frame
            # on a frame boundary of the DCA1000 stream; join_offset 0 = the node
            # saw this stream from its first byte.
            "aligned": (self.misaligned == 0) if self.first_stream_offset is not None else None,
            "first_stream_offset": self.first_stream_offset,
            "join_offset": self.join_offset,
            "zero_filled_bytes": self.zero_filled,
            "stream_gaps": self.stream_gaps,
            "stream_frames_skipped": self.stream_frames_skipped,
            "stream_restarts": self.stream_restarts,
        }
        summary.update(self.burst_summary())
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

        # An empty capture directory is worse than none: the pull copies it and
        # it sorts as the "latest" take under that name.
        if self.count == 0:
            shutil.rmtree(self.session_dir, ignore_errors=True)
            print("  no frames -- removed the empty capture directory")


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
    # 8 s, not 2: Foxy's DDS discovery takes a second or two to match the
    # publisher, and a false timeout would cost a good take.
    ap.add_argument("--no-frames-timeout", type=float, default=8.0,
                    help="exit 3 if no frame arrives within this many seconds (0 = wait forever)")
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
    node = Recorder(session_dir, cfg, dims, args.max_frames, args.no_frames_timeout)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    # Non-zero on the no-frames timeout, so session.sh can tell a dead stream
    # from a finished take instead of pulling nothing and calling it done.
    sys.exit(node.exit_code)


if __name__ == "__main__":
    main()
