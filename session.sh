#!/usr/bin/env bash
#
# One command: deploy -> build -> launch -> SETUP/START -> record -> STOP -> check -> pull.
#
#   wsl.exe -e bash session.sh <name> "<note>" [--frames N]
#
# The driver stays up between takes, so only the first take deploys, builds and launches.
# Use --restart after changing code and --clean after changing a .msg.
#
#   --frames N     max frames to record        (default 2000)
#   --restart      redeploy, rebuild, relaunch even if the driver is up
#   --clean        wipe build/install/log first (REQUIRED after a .msg change)
#   --no-deploy    skip the file push
#   --no-pull      leave the capture on the Jetson
#   --monitor      also sample the wire rate during the capture
#   --reference    record an EMPTY-scene Tx-order reference for this rig, on a
#                  fresh relaunch (name optional). Every later take is checked
#                  against it until the radar is moved.
#   --stop         stop the sensor AND the driver, then exit (no recording)
#   --reset        kill everything, probe the CLI port, stop the sensor over serial
#   --dest PATH    where to pull captures to
#
# Environment overrides: REMOTE, REMOTE_PATH, CAPTURES, DEST.
#
# Every take's chirp alignment and Tx slot order are checked, and a take whose slot order
# differs from the reference is renamed *_TXSLIP.

set -euo pipefail

# set -e exits silently, so report the line and command that failed.
trap 'rc=$?; echo; echo "session.sh FAILED at line $LINENO (exit $rc)" >&2; echo "  command: $BASH_COMMAND" >&2' ERR

REMOTE="${REMOTE:-mmwave@192.168.33.30}"
REMOTE_PATH="${REMOTE_PATH:-/home/mmwave/ssd/chris-launch-monitor}"
CAPTURES="${CAPTURES:-/home/mmwave/ssd/captures}"
cd "$(dirname "$0")"

NAME=""; NOTE=""; FRAMES=2000
DO_DEPLOY=1; DO_PULL=1; RESTART=0; CLEAN=0; MONITOR=0; STOP_ONLY=0; RESET=0
REFERENCE=0
DEST_ARG=""
ARMED=0; LOG=""

while [[ $# -gt 0 ]]; do
    arg="$1"
    # PowerShell users type -frames, not --frames, and PowerShell passes it
    # through verbatim. Accept either. Single-character flags (-h) are left
    # alone so they keep their usual meaning.
    case "$arg" in
        --*) ;;
        -[a-zA-Z][a-zA-Z]*) arg="-$arg" ;;
    esac
    case "$arg" in
        --frames)  FRAMES="$2"; shift 2 ;;
        --dest)    DEST_ARG="$2"; shift 2 ;;
        --restart) RESTART=1; shift ;;
        --clean)   CLEAN=1; RESTART=1; shift ;;
        --no-deploy) DO_DEPLOY=0; shift ;;
        --no-pull) DO_PULL=0; shift ;;
        --monitor) MONITOR=1; shift ;;
        --verbose|-v) set -x; shift ;;
        --stop)    STOP_ONLY=1; shift ;;
        --reset)   RESET=1; shift ;;
        --reference) REFERENCE=1; RESTART=1; shift ;;
        -h|--help) awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; exit 0 ;;
        -*) echo "unknown option: $arg" >&2; exit 2 ;;
        *) if [[ -z "$NAME" ]]; then NAME="$arg"; elif [[ -z "$NOTE" ]]; then NOTE="$arg"; fi; shift ;;
    esac
done

# Where captures land locally: the Windows Desktop results folder, else the WSL home.
if [[ -n "$DEST_ARG" ]]; then
    DEST="$DEST_ARG"
else
    DEST="${DEST:-}"
    if [[ -z "$DEST" ]]; then
        mapfile -t cand < <(ls -d /mnt/c/Users/*/Desktop/results 2>/dev/null || true)
        if [[ ${#cand[@]} -eq 1 ]]; then DEST="${cand[0]}"; else DEST="$HOME/radar-data"; fi
    fi
fi

# ssh multiplexing: every phase below is a separate ssh call, so one master
# connection is shared and torn down at exit.
SOCK="/tmp/.session-$$-ssh"
SSH=(ssh -o ControlMaster=auto -o "ControlPath=$SOCK" -o ControlPersist=60
     -o ConnectTimeout=8 -o BatchMode=no)
cleanup() { ssh -O exit -o "ControlPath=$SOCK" "$REMOTE" 2>/dev/null || true; }
trap cleanup EXIT

r() { "${SSH[@]}" "$REMOTE" "$@"; }                       # run remote
rsrc() { r "cd '$REMOTE_PATH' && source /opt/ros/foxy/setup.bash && source install/setup.bash && $1"; }

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

if ! r true; then
    echo "cannot reach $REMOTE: check the radar-subnet link and ssh key auth (ssh-copy-id $REMOTE)" >&2
    exit 1
fi

# Driver state. Both nodes must be up: a launch whose control node has exited
# would make the arm step wait forever for a service that never appears.
# The patterns are bracketed ('[r]adar') because pgrep -f matches whole command
# lines, and an unbracketed pattern would match the ssh shell running it.
driver_up() { r "pgrep -f '[r]adar_data' >/dev/null 2>&1 && pgrep -f '[r]adar_ctrl_node' >/dev/null 2>&1"; }

# Kill every node and recorder. An orphaned radar_ctrl_node keeps UDP 4096 (the
# DCA1000 command port) bound, so the next control node cannot bind and SETUP
# fails later with a misleading serial error. An orphaned recorder competes for
# CPU with the next take's.
kill_all() {
    r "pkill -f '[r]ecorder.py' || true; pkill -f '[r]os2 launch mmwave_drv' || true; pkill -f '[r]adar_ctrl_node' || true; pkill -f '[r]adar_term_cli' || true; pkill -f '[r]adar_gui_cli' || true; pkill -f '[r]adar_data' || true"
    sleep 2
    r "pkill -9 -f '[r]ecorder.py' || true; pkill -9 -f '[r]adar_ctrl_node' || true; pkill -9 -f '[r]adar_data' || true"
    sleep 1
    # Whatever still holds 4096 will break the next launch. Say so now.
    if r "ss -uln 2>/dev/null | grep -q :4096"; then
        echo "  WARNING: UDP 4096 is still bound after the kill." >&2
        r "ss -ulnp 2>/dev/null | grep :4096" >&2 || true
    fi
}

# Killing the nodes does not stop the sensor: it keeps chirping with no host, and
# the next SETUP's flushCfg then fails. So every path that kills the driver ends
# here, over raw serial. The nodes must already be down, or radar_ctrl_node still
# holds the port.
serial_stop() {
    echo "  stopping the sensor over raw serial ..."
    r "cd '$REMOTE_PATH' && python3 scripts/sensor_stop.py" 2>&1 | sed 's/^/    /' \
        || echo "  sensor stop not confirmed: if SETUP fails next, power-cycle the radar" >&2
}

latest_log() { r "ls -t '$REMOTE_PATH'/logs/launch_*.log 2>/dev/null | head -1" | tr -d '\r'; }
log_lines()  { r "wc -l < '$LOG' 2>/dev/null || echo 0" | tr -d '\r '; }

SVC_NAME="${SVC_NAME:-/control_radar}"

svc() {  # svc <0|1|2> <label> [timeout_s]
    local out new_log n0
    printf %s "  $2 ..."
    [[ -n "$LOG" ]] || LOG=$(latest_log)
    n0=$(log_lines)
    # timeout, because ros2 service call blocks forever on a service that never
    # appears. SETUP uploads the whole profile one serial command at a time.
    out=$(rsrc "timeout ${3:-30} ros2 service call $SVC_NAME mmwave_drv/srv/SendDeviceControlCommand '{command: $1}'" 2>&1) || true
    if grep -q "status=True" <<<"$out"; then
        echo " ok"
        return 0
    fi

    # Only what the driver logged in response to this command.
    sleep 0.5
    new_log=$(r "tail -n +$((n0 + 1)) '$LOG'" 2>/dev/null || true)

    # "Error -54: Sensor has already been started or stopped". For STOP that is
    # the desired end state. For SETUP it means the sensor is chirping and the CLI
    # refused flushCfg.
    if [[ "$1" == 0 ]] && grep -q "already been started or stopped" <<<"$new_log"; then
        echo " already stopped"
        return 0
    fi
    # For START it means the sensor was chirping before the DCA1000 was told to
    # record, so the capture can join the stream mid-frame with the Tx slots rotated.
    if [[ "$1" == 1 ]] && grep -q "already been started or stopped" <<<"$new_log"; then
        echo " FAILED: the sensor was already chirping, so a recording could start mid-frame"
        return 1
    fi

    echo " FAILED"
    sed "s/^/    /" <<<"$out" >&2
    if grep -q "status=False" <<<"$out"; then
        echo "  command failed. Control node log:" >&2
        grep -iE "Error|Ignored|failed|not been started|Device is running" <<<"$new_log" | tail -12 | sed "s/^/    /" >&2 || true
        if grep -q "invalid response" <<<"$new_log"; then
            echo "  'invalid response': no CLI reply in 0.25 s, usually a sensor still chirping." >&2
            echo "  If it persists on a fresh driver, the CLI port may have moved: --reset" >&2
        fi
    else
        echo "  no response: the control node is blocked. Services:" >&2
        rsrc "ros2 service list" 2>&1 | grep -v parameter | sed "s/^/    /" >&2 || true
    fi
    return 1
}

# Graceful STOP through the node if it is up, then kill every node, then stop the
# sensor over serial whether or not the STOP succeeded, since a wedged node is
# exactly when this is needed.
stop_driver() {
    if driver_up; then
        svc 0 STOP 10 || echo "  (graceful stop failed, stopping over serial)"
    fi
    ARMED=0
    kill_all
    serial_stop
}

launch_driver() {
    if (( DO_DEPLOY )); then
        say "deploy"
        bash deploy.sh
    fi

    say "build"
    if (( CLEAN )); then
        echo "  wiping build/ install/ log/ (needed after a .msg change)"
        r "cd '$REMOTE_PATH' && rm -rf build install log"
    fi
    r "cd '$REMOTE_PATH' && source /opt/ros/foxy/setup.bash && colcon build --symlink-install" \
        | tail -5

    say "launch"
    # stop_driver, not kill_all, so the sensor is stopped too
    stop_driver

    # run.sh raises net.core.rmem_max with sudo, which cannot prompt over a
    # non-interactive ssh, and the value resets on reboot. Warn rather than run a
    # driver that will drop UDP packets.
    echo "  checking socket buffer ..."
    RMEM=$(r "cat /proc/sys/net/core/rmem_max" | tr -d "\r")
    if [[ "$RMEM" -lt 1610612736 ]]; then
        echo "  WARNING: net.core.rmem_max = $RMEM, want 1610612736. To set it permanently:"
        echo "    ssh $REMOTE \"echo net.core.rmem_max=1610612736 | sudo tee /etc/sysctl.d/99-radar.conf && sudo sysctl --system\""
    fi

    STAMP=$(date +%Y%m%d_%H%M%S)
    LOG="$REMOTE_PATH/logs/launch_$STAMP.log"
    # setsid + </dev/null so the driver survives this ssh closing.
    # use_client:=false keeps radar_term_cli.py out of the launch. It arms the radar
    # from its own __init__, which would race this script as a second controller.
    echo "  starting driver ..."
    # timeout(1) runs a binary, not a shell function, so ssh is called directly.
    if ! timeout 25 "${SSH[@]}" "$REMOTE" "cd '$REMOTE_PATH' && mkdir -p logs && ( setsid bash -lc 'source /opt/ros/foxy/setup.bash && source install/setup.bash && exec ros2 launch mmwave_drv radar_launch.py use_client:=false' </dev/null >'$LOG' 2>&1 & ) ; echo launched"; then
        echo "  ssh returned non-zero, checking the log anyway"
    fi

    echo "  log: $LOG"
    echo "  waiting for the data node (up to 40 s) ..."
    local ready=0 i
    for i in $(seq 1 40); do
        if r "grep -q 'Capture thread running' '$LOG' 2>/dev/null"; then ready=1; break; fi
        sleep 1
    done
    if [[ $ready -eq 0 ]]; then
        echo "  driver did NOT come up. Last 25 log lines:"
        r "tail -25 '$LOG' 2>/dev/null" || echo "  (log empty or missing)"
        exit 1
    fi
    echo "  ready after ${i}s"
}

# Ctrl-C kills the local ssh only, and the recorder on the Jetson would wait for
# frames forever. It gets SIGINT rather than SIGTERM so it still writes its
# capture summary. The sensor is stopped too, or the next take's SETUP fails.
on_interrupt() {
    trap - INT TERM ERR
    say "interrupted: cleaning up on the Jetson (Ctrl-C again to abandon)"
    r "pkill -INT -f '[r]ecorder.py'; true" \
        || echo "  could not reach the Jetson. Run there: pkill -f '[r]ecorder.py'" >&2
    if (( ARMED )); then
        svc 0 STOP 10 || echo "  STOP failed: the next take will stop the sensor and relaunch" >&2
    fi
    exit 130
}
trap on_interrupt INT TERM

if (( RESET )); then
    say "sensor reset (direct serial, no ROS)"
    # The driver must be down first or it holds /dev/ttyACM0 open.
    kill_all
    sleep 2
    bash deploy.sh >/dev/null
    rsrc "python3 scripts/sensor_stop.py --flush" || true
    echo "  now take again; the driver will relaunch"
    exit 0
fi

if (( STOP_ONLY )); then
    say "stopping sensor and driver"
    stop_driver
    echo "  driver stopped"
    exit 0
fi

if (( REFERENCE )) && [[ -z "$NAME" ]]; then NAME="txref"; fi
[[ -n "$NAME" ]] || { echo "usage: session.sh <session-name> [note] [options]" >&2; exit 2; }

if (( RESTART )) || ! driver_up; then
    # --reference always relaunches: a fresh launch on a sensor just stopped over
    # serial is the state least likely to join the stream mid-frame.
    launch_driver
else
    say "driver running, reusing it (--restart to rebuild)"
    LOG=$(latest_log)
fi

# Leftover recorders from an interrupted take would cost this take frames.
STALE=$(r "pgrep -af '[r]ecorder.py'; true" | tr -d '\r')
if [[ -n "$STALE" ]]; then
    echo "  WARNING: killing leftover recorder(s) on the Jetson:" >&2
    sed 's/^/    /' <<<"$STALE" >&2
    r "pkill -f '[r]ecorder.py'; sleep 1; pkill -9 -f '[r]ecorder.py'; true"
fi

# Arm the radar. SETUP uploads the whole profile over serial and takes about
# 4 s. Both commands are idempotent, so re-arming an armed radar is harmless.
arm() {
    svc 2 SETUP || return 1
    sleep 1
    svc 1 START || return 1
    ARMED=1
    sleep 1
}

say "arm"
if ! arm; then
    # A failed STOP or a Ctrl-C can leave the sensor chirping and the node's
    # record flag stale, which SETUP cannot recover from inside the node. A fresh
    # driver on a sensor stopped over serial can.
    say "arm failed: stopping the sensor and relaunching once"
    DO_DEPLOY=0; CLEAN=0
    launch_driver
    say "arm (after relaunch)"
    if ! arm; then
        echo "  arm failed again after a relaunch. Try: session.sh --reset" >&2
        exit 1
    fi
fi

# Record
say "record: $NAME ($FRAMES frames)"
MONPID=""
if (( MONITOR )); then
    ( rsrc "IFACE= scripts/monitor.sh 5" 2>&1 | sed 's/^/  [wire] /' ) &
    MONPID=$!
fi
REC_RC=0
# The capture directory is only known from the recorder's "Recording to <dir>"
# line, and the Tx-order check below needs it.
RECLOG=$(mktemp)
rsrc "scripts/record.sh '$NAME' '$NOTE' --max-frames $FRAMES" 2>&1 | tee "$RECLOG" | sed 's/^/  /' || REC_RC=$?
CAPDIR=$(grep -o 'Recording to [^ ]*' "$RECLOG" | tail -1 | cut -d' ' -f3 || true)
rm -f "$RECLOG"
if [[ -n "$MONPID" ]]; then wait "$MONPID" 2>/dev/null || true; fi

# Exit 3 is the recorder's no-frames timeout. Sample the wire before stopping,
# while the fault is still live.
if (( REC_RC == 3 )); then
    echo "  no frames reached the recorder. Wire rate:" >&2
    rsrc "IFACE= scripts/monitor.sh 3" 2>&1 | sed 's/^/  [wire] /' || true
    echo "  about 0 MB/s: radar or DCA1000 not streaming. About 14 MB/s: data node not publishing." >&2
fi

say "stop"
if svc 0 STOP; then
    ARMED=0
else
    # A failed STOP can leave the sensor chirping, and the next take's SETUP then
    # fails with "invalid response", far from the cause. Stop everything now.
    echo "  WARNING: STOP failed, stopping the sensor over serial. The next take relaunches." >&2
    stop_driver
fi

if (( REC_RC != 0 )); then
    echo >&2
    echo "  recording FAILED (recorder exit $REC_RC), nothing pulled." >&2
    exit 1
fi

# Chirp alignment, from the samples: does the take start on an Rx-block boundary?
# The data node aligns on the DCA1000's byte count, which cannot see bytes the
# card never counted.
if [[ -n "$CAPDIR" ]]; then
    say "chirp alignment"
    CA_RC=0
    rsrc "python3 scripts/chirp_align_check.py '$CAPDIR' --write-meta" 2>&1 | sed 's/^/  /' || CA_RC=$?
    case "$CA_RC" in
        0) ;;
        4)
            echo "  TAKE STARTS OFF A CHIRP BOUNDARY: angles are wrong as recorded. Re-take it." >&2
            echo "  (The first take after power-up often does this. The next is normally clean.)" >&2
            if (( REFERENCE )); then echo "  Do not keep it as the Tx-order reference." >&2; fi
            ;;
        5) echo "  UNSURE: no clear chirp boundary (empty or saturated scene?)." >&2 ;;
        *) echo "  chirp alignment not checked (exit $CA_RC)." >&2 ;;
    esac
fi

# Tx slot order, relative to the rig's reference (see tx_order_check.py).
REF_FILE="$CAPTURES/.txorder_ref"
if [[ -z "$CAPDIR" ]]; then
    echo "  WARNING: capture directory not found in the recorder output, Tx order not checked." >&2
elif (( REFERENCE )); then
    say "Tx-order reference"
    # A misaligned reference would silently disable the check for every later
    # take, so accept one only if the samples are aligned and no frame start was
    # timed off the frame grid.
    SLIPS=$(r "python3 -c 'import json,sys; c=json.load(open(sys.argv[1])).get(\"capture\",{}); print(c.get(\"burst_slips\") or 0)' '$CAPDIR/meta.json'" | tr -d '\r' || echo "?")
    if [[ "$CA_RC" != 0 || "$SLIPS" != 0 ]]; then
        echo "  NOT accepted as the reference (alignment exit $CA_RC, burst_slips $SLIPS)." >&2
        echo "  The previous reference is kept. Record again: session.sh --reference" >&2
    else
        r "echo '$CAPDIR' > '$REF_FILE'"
        echo "  reference: $CAPDIR"
        echo "  Valid until the radar is moved. The scene must be empty."
    fi
else
    say "Tx-order check"
    REF=$(r "cat '$REF_FILE' 2>/dev/null; true" | tr -d '\r')
    if [[ -z "$REF" ]]; then
        echo "  Tx order not checked: no reference. With the scene empty, run: session.sh --reference" >&2
    elif ! r "test -f '$REF/meta.json'"; then
        echo "  Tx order not checked: reference $REF is missing. Run: session.sh --reference" >&2
    else
        TX_RC=0
        rsrc "python3 scripts/tx_order_check.py '$CAPDIR' --ref '$REF' --write-meta" 2>&1 | sed 's/^/  /' || TX_RC=$?
        case "$TX_RC" in
            0) ;;
            4)
                r "mv '$CAPDIR' '${CAPDIR}_TXSLIP'"
                echo "  TX ORDER DIFFERS FROM THE REFERENCE: renamed *_TXSLIP, angles unusable." >&2
                echo "  Stopping the driver so the next take relaunches." >&2
                stop_driver
                ;;
            5)
                echo "  UNSURE: the scene or the radar may have changed since the reference." >&2
                ;;
            *)
                echo "  Tx order not checked (exit $TX_RC)." >&2
                ;;
        esac
    fi
fi

if (( DO_PULL )); then
    say "pull -> $DEST"
    mkdir -p "$DEST"
    # -rltv, not -a: permissions mean nothing on DrvFs. No -z: raw I/Q barely
    # compresses and the CPU cost lands on the Jetson. There is deliberately no
    # fallback path, so a wrong CAPTURES fails loudly.
    rsync -rltv --partial -e "ssh -o ControlPath=$SOCK" \
        "$REMOTE:$CAPTURES/" "$DEST/"
    LATEST=$(ls -dt "$DEST"/*_"$NAME" "$DEST"/*_"$NAME"_TXSLIP 2>/dev/null | head -1 || true)
    [[ -n "$LATEST" ]] && echo "  latest: $LATEST"
fi

say "done. Driver left running, next take: session.sh <name>"
