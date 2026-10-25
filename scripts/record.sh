#!/usr/bin/env bash
# Record a capture session from the running radar driver.
#
#   scripts/record.sh handwave_01 "hand waving at ~1 m, 20 Hz profile"
#   scripts/record.sh drop_test    "ball dropped from 2 m"   --max-frames 400
#
# Requires the driver to already be running (scripts/run.sh) and set to RECORD.

set -e

# Workspace root, from this script's location.
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME=${1:?usage: record.sh <session-name> [note] [extra args...]}
NOTE=${2:-}
shift 2 2>/dev/null || shift 1

source /opt/ros/foxy/setup.bash
source "$WS/install/setup.bash"

mkdir -p ~/ssd/captures

# The profile comes from radar_config.yaml, the same file the launch gives the
# driver, so the recorder expects the frame size the radar is actually sending.
# Override with CFG=/path/to/profile.json.
CFG=${CFG:-$(python3 -c "
import yaml
try:
    d = yaml.safe_load(open('$WS/src/mmWave_DRV/config/radar_config.yaml'))
    print(d['/**']['ros__parameters']['dev_cfg_file_path'])
except Exception:
    print('$WS/src/mmWave_DRV/config/awr1843_launchmonitor.json')
")}
echo "profile: $CFG"

python3 "$WS/scripts/recorder.py" \
    --name "$NAME" \
    --note "$NOTE" \
    --out ~/ssd/captures \
    --config "$CFG" \
    "$@"
