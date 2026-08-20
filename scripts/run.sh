#!/usr/bin/env bash
set -e

WS=~/ssd/chris-launch-monitor
source /opt/ros/foxy/setup.bash
source "$WS/install/setup.bash"

# raise socket buffer if it's low (idempotent)
CUR=$(cat /proc/sys/net/core/rmem_max)
if [ "$CUR" -lt 1610612736 ]; then
    sudo sysctl -w net.core.rmem_max=1610612736
fi

cd "$WS"
mkdir -p logs
STAMP=$(date +%Y%m%d_%H%M%S)
ros2 launch mmwave_drv radar_launch.py 2>&1 | tee "logs/launch_$STAMP.log"