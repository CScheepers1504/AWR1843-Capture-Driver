#!/usr/bin/env bash
# Throughput health check. Run while the driver is streaming.
#
#   scripts/monitor.sh [seconds]        default 10
#   IFACE=enp1s0 scripts/monitor.sh 20  override the capture interface
#
# The wire-rate figure is the important one: it is read from /proc/net/dev and
# is therefore independent of ROS2, DDS, QoS and Python. It reports what the
# DCA1000 is actually delivering, which is the only way to tell a device/config
# problem from a downstream backpressure problem.

# Derived from this script's location -- see the note in run.sh.
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/foxy/setup.bash
source "$WS/install/setup.bash"

DUR=${1:-10}

# The capture NIC is whichever interface holds the DCA1000 host address -- not
# necessarily eth0. Pointing this at the wrong interface reports a confident
# 0.00 MB/s while the radar is streaming perfectly, which reads as a dead radar
# and sends you hunting a fault that is not there (seen 29 Aug 2026).
DCA_SUBNET=${DCA_SUBNET:-192.168.33.}
if [ -z "${IFACE:-}" ]; then
    IFACE=$(ip -o -4 addr show 2>/dev/null             | awk -v s="$DCA_SUBNET" '$4 ~ "^" s {print $2; exit}')
    [ -n "$IFACE" ] && echo "auto-detected capture interface: $IFACE ($DCA_SUBNET*)"
fi
IFACE=${IFACE:-eth0}
# Read the profile path from radar_config.yaml -- the same file the launch
# feeds the driver -- rather than hardcoding one. A hardcoded profile here goes
# quietly stale the moment the driver is pointed at a different one, and then
# every figure below is computed against a frame size the radar is not sending.
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

# Frame size straight from the config the driver loads, so this cannot drift
# out of step with the profile: loops * tx * rx * samples * 4 bytes (complex 16-bit).
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

# NOTE: ros2 topic hz/bw use RELIABLE QoS and Foxy gives them no --qos-reliability
# flag, so they will NOT connect to the best-effort publisher in radar_data_node.
# They are left here only as a liveness check. For the publisher-side rate, use
# the periodic "Published N frames" lines in logs/launch_*.log instead.
echo "(ros2 topic hz omitted: reliable-only in Foxy, incompatible with best-effort publisher)"
