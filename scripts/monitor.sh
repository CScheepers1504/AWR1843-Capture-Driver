#!/usr/bin/env bash
# Throughput health check. Run while the driver is streaming.
#
#   scripts/monitor.sh [seconds]        default 10
#   IFACE=enp1s0 scripts/monitor.sh 20  override the capture interface
#
# The wire rate is read from /proc/net/dev, so it does not depend on ROS2, DDS,
# QoS or Python. It is what the DCA1000 actually delivers, which separates a
# device or config problem from a downstream one.

# Workspace root, from this script's location.
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/foxy/setup.bash
source "$WS/install/setup.bash"

DUR=${1:-10}

# The capture interface is whichever one holds the DCA1000 host address, not
# necessarily eth0. The wrong interface reports 0.00 MB/s while the radar streams.
DCA_SUBNET=${DCA_SUBNET:-192.168.33.}
if [ -z "${IFACE:-}" ]; then
    IFACE=$(ip -o -4 addr show 2>/dev/null             | awk -v s="$DCA_SUBNET" '$4 ~ "^" s {print $2; exit}')
    [ -n "$IFACE" ] && echo "auto-detected capture interface: $IFACE ($DCA_SUBNET*)"
fi
IFACE=${IFACE:-eth0}
# The profile comes from radar_config.yaml, the same file the launch gives the
# driver, so the figures below use the frame size the radar is actually sending.
CFG=${CFG:-$(python3 -c "
import yaml
try:
    d = yaml.safe_load(open('$WS/src/mmWave_DRV/config/radar_config.yaml'))
    print(d['/**']['ros__parameters']['dev_cfg_file_path'])
except Exception:
    print('$WS/src/mmWave_DRV/config/awr1843_launchmonitor.json')
")}
echo "profile source: $CFG"

if ! grep -q "^ *$IFACE:" /proc/net/dev; then
    echo "Interface '$IFACE' not found. Available:"
    awk -F: '/:/ {gsub(/ /,"",$1); if ($1!="") print "  " $1}' /proc/net/dev
    echo "Re-run as: IFACE=<name> $0 $DUR"
    exit 1
fi

# Frame size from that profile: loops * tx * rx * samples * 4 bytes (complex 16-bit).
FRAME_BYTES=$(python3 -c "
import json
c = json.load(open('$CFG'))
p, f = c['profileCfg'], c['frameCfg']
tx = f['chirpEndIndex'] - f['chirpStartIndex'] + 1
rx = bin(c['channelCfg']['rxChannelEn']).count('1')
print(f['numChirps'] * tx * rx * p['numAdcSamples'] * 4)
")
PERIOD_MS=$(python3 -c "import json;print(json.load(open('$CFG'))['frameCfg']['framePeriod'])")

echo "profile: ${FRAME_BYTES} B/frame, framePeriod ${PERIOD_MS} ms"
echo "measuring $IFACE for ${DUR}s ..."

A=$(grep "^ *$IFACE:" /proc/net/dev | tr -s ' ' | cut -d' ' -f2- | awk '{print $1}')
sleep "$DUR"
B=$(grep "^ *$IFACE:" /proc/net/dev | tr -s ' ' | cut -d' ' -f2- | awk '{print $1}')

echo "$A $B $DUR $FRAME_BYTES $PERIOD_MS" | awk '{
    mbs   = ($2-$1)/$3/1048576
    fps   = ($2-$1)/$4/$3
    want  = 1000/$5
    printf "  wire rate     %.2f MB/s\n", mbs
    printf "  implied rate  %.1f frames/s  (configured %.1f Hz, %.0f%%)\n", fps, want, fps/want*100
}'

# ros2 topic hz/bw use reliable QoS, and Foxy gives them no flag to change it, so
# they cannot connect to the best-effort publisher. For the publisher-side rate,
# use the "Published N frames" lines in logs/launch_*.log.
