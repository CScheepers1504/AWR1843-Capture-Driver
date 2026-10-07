// Standard Includes
#include <algorithm>
#include <cerrno>
#include <climits>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <ctime>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <signal.h>
#include <sys/socket.h>
#include <unistd.h>

#include <jsoncpp/json/json.h>

// ROS2 Includes
#include <rclcpp/rclcpp.hpp>
#include <ament_index_cpp/get_package_share_directory.hpp>

// Package Includes
#include "mmwave_drv/msg/frame.hpp"

// Defines
#define PORT 4098
#define DCA_IP_ADDR "192.168.33.30"      // host address the DCA1000 streams to; we bind to it
#define HEADER_BYTES 10                  // 4 B sequence number + 6 B byte count
#define MAX_PACKET_DATA_SIZE 1456
// Room for a datagram larger than expected: it must be reported, not silently
// truncated (recvfrom with MSG_TRUNC returns the real length).
#define RECV_PACKET_BUF (HEADER_BYTES + MAX_PACKET_DATA_SIZE + 64)
// Requested socket buffer. The old request (512 MB x 3 = 1.6 GB) exceeds what
// some kernels can double without overflowing an int; the value actually
// granted is read back and logged.
#define RECV_BUFFER_REQUEST (256 * 1024 * 1024)
#define RING_FRAMES 8

// FRAME ALIGNMENT
//
// Every DCA1000 raw-mode packet carries, after its 4-byte sequence number, a
// 6-byte BYTE COUNT: the stream position of the packet's first payload byte,
// counted from RECORD_START. 
//
// Frames are cut at stream positions that are multiples of the frame
// size. A late join (first byte count != 0) discards bytes up to the next
// frame boundary. A dropped packet is zero-filled by exactly the number of
// bytes the byte count says are missing. Each published frame carries its
// stream offset, so the recorder can verify alignment and contiguity.
//
// BURST PHASE 
// checks it from the radar's own timing instead. A
// frame's chirps arrive as one burst of packets, then the link is idle until
// the next frame. The first packet after an idle gap therefore starts at a
// frame boundary IN THE RADAR'S STREAM. Its byte count says where that is in
// the DCA1000's count. burst_phase = that byte count minus the nearest multiple
// of the frame size: ~0 on an aligned take (or down to minus one packet, if
// the card holds a part-filled packet until the next burst), a multiple of the
// chirp size after a whole-chirp slip. Packet times are kernel receive
// timestamps (SO_TIMESTAMPNS), so a backlog in this thread does not hide the gap.

class MMWaveDataNode : public rclcpp::Node
{
  public:
    MMWaveDataNode()
    : Node("RADAR_data_node")
    {
        RCLCPP_INFO(get_logger(), "RADAR DATA NODE: starting.");

        // Socket ------------------------------------------------------------------------------
        sockfd = socket(AF_INET, SOCK_DGRAM, 0);
        if (sockfd < 0) {
          throw std::runtime_error(std::string("could not create socket: ") + strerror(errno));
        }
        int optval = 1;
        setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &optval, sizeof(optval));

        // 2 s receive timeout: an idle period of this length ends a stream.
        struct timeval tv;
        tv.tv_sec = 2;
        tv.tv_usec = 0;
        setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

        int recvbuf = RECV_BUFFER_REQUEST;
        setsockopt(sockfd, SOL_SOCKET, SO_RCVBUF, &recvbuf, sizeof(recvbuf));
        int granted = 0;
        socklen_t glen = sizeof(granted);
        getsockopt(sockfd, SOL_SOCKET, SO_RCVBUF, &granted, &glen);
        RCLCPP_INFO(get_logger(), "UDP receive buffer: requested %d B, granted %d B%s",
                    recvbuf, granted,
                    granted < 16 * 1024 * 1024 ? "  (LOW: raise net.core.rmem_max)" : "");

        // Kernel receive timestamps, for the burst-phase check. Without them
        // the check falls back to the time recvmsg returns, which a backlog
        // in this thread compresses.
        int tsOn = 1;
        kernelStamps = setsockopt(sockfd, SOL_SOCKET, SO_TIMESTAMPNS, &tsOn, sizeof(tsOn)) == 0;
        if (!kernelStamps) {
          RCLCPP_WARN(get_logger(), "SO_TIMESTAMPNS unavailable (%s): burst phase uses user-space "
                      "receive times and may miss frame starts under load.", strerror(errno));
        }

        struct sockaddr_in serveraddr;
        std::memset(&serveraddr, 0, sizeof(serveraddr));
        serveraddr.sin_addr.s_addr = inet_addr(DCA_IP_ADDR);
        serveraddr.sin_family = AF_INET;
        serveraddr.sin_port = htons(PORT);
        if (bind(sockfd, (struct sockaddr *)&serveraddr, sizeof(serveraddr)) < 0) {
          // Previously logged and ignored: the node then ran with a socket that
          // could never receive, which reads as "radar not streaming".
          throw std::runtime_error(std::string("bind to ") + DCA_IP_ADDR + ":" +
                                   std::to_string(PORT) + " failed: " + strerror(errno));
        }

        // Config ------------------------------------------------------------------------------
        std::string share_directory = ament_index_cpp::get_package_share_directory("mmwave_drv");
        declare_parameter("dev_cfg_file_path", share_directory + "/config/cfgDev.json");
        declare_parameter<std::string>("devNAME", "radar");
        declare_parameter<std::string>("devSERV", "control_radar");
        declare_parameter<std::string>("devSPUB", "radar_status");
        declare_parameter<std::string>("devDPUB", "radar_data");
        declare_parameter<std::string>("devLOGG", "radar: ");
        devDPUB = get_parameter("devDPUB").as_string();

        if (!loadConfig()) {
          throw std::runtime_error("device config could not be loaded -- see the error above");
        }
        allocateRing();

        // Publisher ---------------------------------------------------------------------------
        // Best-effort, not reliable: with reliable QoS a slow subscriber blocks
        // publish() and stalls this capture thread, so frames are lost at the
        // socket while the published sequence stays contiguous. 
        // The subscriber QoS in recorder.py must match.
        auto data_qos = rclcpp::QoS(rclcpp::KeepLast(100)).best_effort();
        data_publisher = create_publisher<mmwave_drv::msg::Frame>(devDPUB, data_qos);

        std::thread(&MMWaveDataNode::capture_loop, this).detach();
        RCLCPP_INFO(get_logger(), "Capture thread running.");
    }

  private:
    // ---- config -------------------------------------------------------------------------------
    bool loadConfig() {
      std::string path = get_parameter("dev_cfg_file_path").as_string();
      std::ifstream f(path);
      if (!f) {
        RCLCPP_ERROR(get_logger(), "cannot open device config %s", path.c_str());
        return false;
      }
      Json::Value cfg;
      Json::Reader reader;
      if (!reader.parse(f, cfg)) {
        // a malformed file gave a
        // frame size of 0 and the node silently published nothing.
        RCLCPP_ERROR(get_logger(), "device config %s does not parse: %s",
                     path.c_str(), reader.getFormattedErrorMessages().c_str());
        return false;
      }
      int numLoops   = cfg["frameCfg"]["numChirps"].asInt();
      int numSamples = cfg["profileCfg"]["numAdcSamples"].asInt();
      int iq         = (cfg["adcbufCfg"]["adcOutputFmt"].asInt() + 2) % 3;   // 0=complex -> 2, 1=real -> 1
      int numRx      = maskToNum(cfg["channelCfg"]["rxChannelEn"].asInt());
      int numTx      = cfg["frameCfg"]["chirpEndIndex"].asInt() - cfg["frameCfg"]["chirpStartIndex"].asInt() + 1;
      if (numLoops <= 0 || numSamples <= 0 || iq <= 0 || numRx <= 0 || numTx <= 0) {
        RCLCPP_ERROR(get_logger(), "device config %s gives a non-positive dimension "
                     "(loops %d, samples %d, iq %d, rx %d, tx %d)",
                     path.c_str(), numLoops, numSamples, iq, numRx, numTx);
        return false;
      }
      size_t newFrame = (size_t)numLoops * numSamples * 2 * iq * numRx * numTx;

      // Idle gap that marks a frame start: 40 % of the radar's quiet time per
      // frame. The DCA1000's packet pacing stretches each burst past the chirps
      // (lowfs: 0.54 ms of chirps, ~1.1 ms of packets at 25 us delay, 3 ms
      // period), so the gap seen here is shorter than the radar's.
      double chirpUs  = cfg["profileCfg"]["idleTime"].asDouble() + cfg["profileCfg"]["rampEndTime"].asDouble();
      double periodUs = cfg["frameCfg"]["framePeriod"].asDouble() * 1000.0;
      double quietUs  = periodUs - numLoops * numTx * chirpUs;
      int64_t newGap  = quietUs >= 400.0 ? (int64_t)(0.4 * quietUs * 1000.0) : 0;

      if (newFrame != frameSize || newGap != burstGapNs) {
        RCLCPP_INFO(get_logger(), "Config %s: %d loops x %d Tx x %d Rx x %d samples -> frame %zu B",
                    path.c_str(), numLoops, numTx, numRx, numSamples, newFrame);
        if (newGap > 0) {
          RCLCPP_INFO(get_logger(), "Burst phase: a gap over %.0f us marks a frame start "
                      "(%.0f us quiet per %.0f us frame).", newGap / 1000.0, quietUs, periodUs);
        } else {
          RCLCPP_WARN(get_logger(), "Burst phase OFF: only %.0f us quiet per frame, too little "
                      "to find frame starts by timing.", quietUs);
        }
      }
      frameSize = newFrame;
      chirpBytes = (size_t)numSamples * 2 * iq * numRx;
      burstGapNs = newGap;
      return true;
    }

    void allocateRing() {
      ringSize = frameSize * RING_FRAMES;
      ring.assign(ringSize, 0);
      readPtr = writePtr = unread = 0;
      RCLCPP_INFO(get_logger(), "Ring buffer: %zu B (%d frames).", ringSize, RING_FRAMES);
    }

    static int maskToNum(int n) {
      int sum = 0;
      for (int i = 0; i < 4; i++) { sum += n & 1; n >>= 1; }
      return sum;
    }

    // ---- stream state -------------------------------------------------------------------------
    void resetStream(const char *why) {
      if (inStream || unread != 0) {
        RCLCPP_INFO(get_logger(),
            "Stream ended (%s): %llu B received, %llu B zero-filled, unpublished tail %zu B "
            "(%.2f chirps), last packet %u.",
            why, (unsigned long long)(expectedOffset - joinOffset),
            (unsigned long long)zeroFilled, unread,
            chirpBytes ? (double)unread / chirpBytes : 0.0, lastSeq);
        logBurstPhase("Stream");
      }
      readPtr = writePtr = unread = 0;
      inStream = false;
      expectedOffset = joinOffset = alignSkip = zeroFilled = nextFrameOffset = 0;
      lastSeq = 0;
      lastPacketNs = 0;
      burstCount = burstSlips = 0;
      burstMin = INT64_MAX;
      burstMax = INT64_MIN;
      pendingBursts.clear();
    }

    // A packet after an idle gap starts a frame in the radar's stream.
    void noteBurst(uint64_t byteCount) {
      uint64_t k = (byteCount + frameSize / 2) / frameSize;
      int64_t phase = (int64_t)byteCount - (int64_t)(k * frameSize);
      // Held until that frame is published: the packet that starts frame k
      // usually also completes frame k-1, so frame k is published later.
      pendingBursts.emplace_back(k * frameSize, phase);
      if (pendingBursts.size() > RING_FRAMES + 2) pendingBursts.pop_front();
      burstCount++;
      burstMin = std::min(burstMin, phase);
      burstMax = std::max(burstMax, phase);
      // Half a chirp: a part-filled packet held over (at most one packet,
      // 1456 B) stays inside it for every profile with chirps over 2912 B.
      if ((uint64_t)std::llabs(phase) >= chirpBytes / 2) {
        if (++burstSlips == 1 || burstSlips % 100 == 0) {
          RCLCPP_ERROR(get_logger(),
              "Frame start at byte %llu is %lld B (%.2f chirps) off the frame grid: the stream is "
              "NOT aligned to the radar's frames (%llu such bursts so far).",
              (unsigned long long)byteCount, (long long)phase, (double)phase / chirpBytes,
              (unsigned long long)burstSlips);
        }
      }
    }

    void logBurstPhase(const char *what) {
      if (burstGapNs == 0) return;
      if (burstCount == 0) {
        RCLCPP_WARN(get_logger(), "%s: no frame starts found by timing (gap threshold %.0f us).",
                    what, burstGapNs / 1000.0);
        return;
      }
      RCLCPP_INFO(get_logger(), "%s: burst phase %lld..%lld B over %llu frame starts, %llu off-grid.",
                  what, (long long)burstMin, (long long)burstMax,
                  (unsigned long long)burstCount, (unsigned long long)burstSlips);
    }

    void startStream(uint32_t seq, uint64_t byteCount, int payload) {
      inStream = true;
      joinOffset = byteCount;
      expectedOffset = byteCount;
      alignSkip = (frameSize - byteCount % frameSize) % frameSize;
      nextFrameOffset = byteCount + alignSkip;
      lastSeq = seq;
      if (byteCount == 0 && seq == 1) {
        RCLCPP_INFO(get_logger(), "Stream started: packet 1 at byte 0, %d B payload. Aligned.", payload);
      } else {
        // Either packets were lost before this one, or the card's counters did
        // not restart. Byte counts still place everything exactly; only the
        // partial frame before the next boundary is discarded.
        RCLCPP_WARN(get_logger(),
            "Stream started LATE: first packet %u at byte %llu (%.2f frames in). "
            "Discarding %llu B to the next frame boundary.",
            seq, (unsigned long long)byteCount, (double)byteCount / frameSize,
            (unsigned long long)alignSkip);
      }
    }

    // Append stream bytes, honouring the pending alignment skip.
    void feed(const unsigned char *data, size_t len) {
      if (alignSkip > 0) {
        size_t k = std::min<uint64_t>(alignSkip, len);
        data += k;
        len -= k;
        alignSkip -= k;
      }
      if (len > 0) ringWrite(data, len);
    }

    void feedZeros(uint64_t count) {
      static const unsigned char zeros[MAX_PACKET_DATA_SIZE] = {0};
      while (count > 0) {
        size_t k = std::min<uint64_t>(count, sizeof(zeros));
        feed(zeros, k);
        count -= k;
      }
    }

    void ringWrite(const unsigned char *data, size_t len) {
      // If the publisher has fallen behind, drop the OLDEST whole frames. That
      // keeps every remaining frame aligned, and the jump in stream_offset tells
      // the recorder exactly what was lost. (The old buffer overwrote unread
      // bytes mid-frame.)
      while (unread + len > ringSize && unread >= frameSize) {
        readPtr = (readPtr + frameSize) % ringSize;
        unread -= frameSize;
        nextFrameOffset += frameSize;
        if (++overflowFrames % 100 == 1) {
          RCLCPP_ERROR(get_logger(), "Ring buffer full: dropped oldest frame (%llu so far).",
                       (unsigned long long)overflowFrames);
        }
      }
      size_t first = std::min(len, ringSize - writePtr);
      std::memcpy(ring.data() + writePtr, data, first);
      std::memcpy(ring.data(), data + first, len - first);
      writePtr = (writePtr + len) % ringSize;
      unread += len;
    }

    // ---- capture ------------------------------------------------------------------------------
    void capture_loop() {
      for (;;) {
        receive_packet();
        publish_ready();
      }
    }

    void receive_packet() {
      struct iovec iov;
      iov.iov_base = packet;
      iov.iov_len = sizeof(packet);
      alignas(struct cmsghdr) char ctrl[CMSG_SPACE(sizeof(struct timespec))];
      struct msghdr mh;
      std::memset(&mh, 0, sizeof(mh));
      mh.msg_iov = &iov;
      mh.msg_iovlen = 1;
      mh.msg_control = ctrl;
      mh.msg_controllen = sizeof(ctrl);
      ssize_t n = recvmsg(sockfd, &mh, MSG_TRUNC);
      if (n < 0) {
        if (errno == EAGAIN || errno == EWOULDBLOCK) {
          // Idle. End any stream, and pick up a changed config while nothing
          // is flowing (this path used to leak both buffers on every timeout).
          resetStream("idle 2 s");
          size_t before = frameSize;
          if (loadConfig() && frameSize != before) allocateRing();
        } else {
          RCLCPP_ERROR(get_logger(), "recvfrom failed: %s", strerror(errno));
        }
        return;
      }
      if ((size_t)n > sizeof(packet)) {
        RCLCPP_ERROR(get_logger(), "Datagram of %zd B truncated to %zu B -- packet size config "
                     "does not match; data is now misaligned.", n, sizeof(packet));
        n = sizeof(packet);
      }
      if (n <= HEADER_BYTES) return;
      int64_t tNs = receiveTimeNs(mh);

      uint32_t seq = 0;
      for (int i = 0; i < 4; i++) seq |= (uint32_t)packet[i] << (8 * i);
      uint64_t byteCount = 0;
      for (int i = 0; i < 6; i++) byteCount |= (uint64_t)packet[4 + i] << (8 * i);
      size_t payload = (size_t)n - HEADER_BYTES;

      // A new stream without an idle gap in between: the card restarts both
      // counters at RECORD_START. Byte 0 arriving mid-stream marks it; so does
      // the sequence number jumping back by more than 64 packets (~2 frames),
      // which also catches a restart whose first packet was lost. A single
      // reordered packet is only a few packets behind and is not taken for one.
      bool restarted = inStream &&
          ((byteCount == 0 && expectedOffset > 0) ||
           byteCount < joinOffset ||
           (uint64_t)seq + 64 < lastSeq);
      if (restarted) {
        resetStream("counters restarted");
      }
      if (!inStream) startStream(seq, byteCount, (int)payload);

      // The first packet of a stream has no previous packet to time against;
      // a duplicate or reordered packet is not a burst start.
      if (burstGapNs > 0 && lastPacketNs != 0 && byteCount >= expectedOffset &&
          tNs - lastPacketNs > burstGapNs) {
        noteBurst(byteCount);
      }
      lastPacketNs = tNs;

      if (byteCount > expectedOffset) {
        uint64_t gap = byteCount - expectedOffset;
        zeroFilled += gap;
        RCLCPP_WARN(get_logger(),
            "Dropped packets %u..%u: zero-filling exactly %llu B (%llu B so far this stream).",
            lastSeq + 1, seq - 1, (unsigned long long)gap, (unsigned long long)zeroFilled);
        feedZeros(gap);
      } else if (byteCount < expectedOffset) {
        RCLCPP_WARN(get_logger(), "Packet %u at byte %llu is behind the stream (expected %llu): "
                    "duplicate or reordered, dropped.", seq,
                    (unsigned long long)byteCount, (unsigned long long)expectedOffset);
        return;
      }
      feed(packet + HEADER_BYTES, payload);
      expectedOffset = byteCount + payload;
      lastSeq = seq;
    }

    void publish_ready() {
      while (unread >= frameSize) {
        auto message = mmwave_drv::msg::Frame();
        message.frame_data.resize(frameSize);
        size_t first = std::min(frameSize, ringSize - readPtr);
        std::memcpy(message.frame_data.data(), ring.data() + readPtr, first);
        std::memcpy(message.frame_data.data() + first, ring.data(), frameSize - first);
        readPtr = (readPtr + frameSize) % ringSize;
        unread -= frameSize;

        message.frame_size = frameSize;
        message.stream_offset = nextFrameOffset;
        message.join_offset = joinOffset;
        message.zero_filled = zeroFilled;
        message.burst_phase = INT32_MIN;
        while (!pendingBursts.empty() && pendingBursts.front().first < nextFrameOffset) {
          pendingBursts.pop_front();
        }
        if (!pendingBursts.empty() && pendingBursts.front().first == nextFrameOffset) {
          message.burst_phase = (int32_t)std::max<int64_t>(
              std::min<int64_t>(pendingBursts.front().second, INT32_MAX), INT32_MIN + 1);
          pendingBursts.pop_front();
        }
        nextFrameOffset += frameSize;
        message.header.stamp = get_clock()->now();
        message.header.frame_id = std::to_string(count);
        count++;
        // Periodic only: a per-frame RCLCPP_INFO here is a synchronous write
        // into run.sh's tee pipe and stalls the thread draining the socket.
        if (count % 500 == 0) {
          RCLCPP_INFO(get_logger(), "Published %llu frames.", (unsigned long long)count);
          logBurstPhase("  so far");
        }
        data_publisher->publish(std::move(message));
      }
    }

    int64_t receiveTimeNs(const struct msghdr &mh) {
      if (kernelStamps) {
        for (struct cmsghdr *c = CMSG_FIRSTHDR(&mh); c; c = CMSG_NXTHDR(const_cast<struct msghdr *>(&mh), c)) {
          if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SCM_TIMESTAMPNS) {
            struct timespec ts;
            std::memcpy(&ts, CMSG_DATA(c), sizeof(ts));
            return (int64_t)ts.tv_sec * 1000000000LL + ts.tv_nsec;
          }
        }
      }
      struct timespec ts;
      clock_gettime(CLOCK_REALTIME, &ts);
      return (int64_t)ts.tv_sec * 1000000000LL + ts.tv_nsec;
    }

    // ROS2
    std::string devDPUB;
    rclcpp::Publisher<mmwave_drv::msg::Frame>::SharedPtr data_publisher;
    unsigned long long count = 0;

    // Frame geometry
    size_t frameSize = 0;
    size_t chirpBytes = 0;

    // Ring buffer
    std::vector<unsigned char> ring;
    size_t ringSize = 0, readPtr = 0, writePtr = 0, unread = 0;
    unsigned long long overflowFrames = 0;

    // Stream state, all in DCA1000 byte-count coordinates
    bool inStream = false;
    uint32_t lastSeq = 0;
    uint64_t expectedOffset = 0;   // position of the next byte we expect
    uint64_t joinOffset = 0;       // byte count of the first packet of this stream
    uint64_t alignSkip = 0;        // bytes still to discard before the first frame boundary
    uint64_t nextFrameOffset = 0;  // stream position of the next frame to publish
    uint64_t zeroFilled = 0;       // bytes zero-filled for dropped packets, this stream

    // Burst phase (frame starts found by packet timing), this stream
    bool kernelStamps = false;
    int64_t burstGapNs = 0;        // idle gap that marks a frame start; 0 = check off
    int64_t lastPacketNs = 0;      // receive time of the previous packet; 0 = none yet
    // Timed frame starts not yet published: (frame-grid position, byte count minus it)
    std::deque<std::pair<uint64_t, int64_t>> pendingBursts;
    uint64_t burstCount = 0, burstSlips = 0;
    int64_t burstMin = INT64_MAX, burstMax = INT64_MIN;

    // Socket
    int sockfd = -1;
    unsigned char packet[RECV_PACKET_BUF];
};

void signal_callback_handler(int signum) {
   std::cout << "Ending data collection." << std::endl;
   exit(signum);
}

int main(int argc, char * argv[])
{
  signal(SIGINT, signal_callback_handler);
  rclcpp::init(argc, argv);
  rclcpp::Node::SharedPtr node = std::make_shared<MMWaveDataNode>();
  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  executor.spin();
  rclcpp::shutdown();
  return EXIT_SUCCESS;
}
