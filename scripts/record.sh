#!/usr/bin/env bash
# Record a capture session from the running radar driver.
#
#   scripts/record.sh handwave_01 "hand waving at ~1 m, 20 Hz profile"
#   scripts/record.sh drop_test    "ball dropped from 2 m"   --max-frames 400
#
# Requires the driver to already be running (scripts/run.sh) and set to RECORD.

set -e

WS=~/ssd/chris-launch-monitor
NAME=${1:?usage: record.sh <session-name> [note] [extra args...]}
NOTE=${2:-}
shift 2 2>/dev/null || shift 1

source /opt/ros/foxy/setup.bash
source "$WS/install/setup.bash"

mkdir -p ~/ssd/captures

python3 "$WS/scripts/recorder.py" \
    --name "$NAME" \
    --note "$NOTE" \
    --out ~/ssd/captures \
    --config "$WS/src/mmWave_DRV/config/awr1843_launchmonitor.json" \
    "$@"
