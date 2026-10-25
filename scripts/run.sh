#!/usr/bin/env bash
set -e

# Workspace root, from this script's location, so the scripts follow the tree.
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/foxy/setup.bash
source "$WS/install/setup.bash"

# Raise the socket receive buffer if it is low, so the data node does not drop UDP packets.
CUR=$(cat /proc/sys/net/core/rmem_max)
if [ "$CUR" -lt 1610612736 ]; then
    sudo sysctl -w net.core.rmem_max=1610612736
fi

cd "$WS"
mkdir -p logs
STAMP=$(date +%Y%m%d_%H%M%S)
ros2 launch mmwave_drv radar_launch.py 2>&1 | tee "logs/launch_$STAMP.log"