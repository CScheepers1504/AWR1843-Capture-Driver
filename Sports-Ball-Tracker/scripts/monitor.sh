#!/usr/bin/env bash
source /opt/ros/foxy/setup.bash
source ~/ssd/chris-launch-monitor/install/setup.bash

DUR=${1:-10}

A=$(grep eth0 /proc/net/dev | awk '{print $2}')
sleep "$DUR"
B=$(grep eth0 /proc/net/dev | awk '{print $2}')
echo "eth0 receive rate: $(echo "$A $B $DUR" | awk '{printf "%.2f MB/s", ($2-$1)/$3/1048576}')"

timeout 10 ros2 topic hz /radar_data
timeout 10 ros2 topic bw /radar_data