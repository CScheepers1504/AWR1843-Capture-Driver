#!/usr/bin/env bash
#
# One command: deploy -> build -> launch -> SETUP/START -> record -> STOP -> pull.
#
#   wsl.exe -e bash session.sh swipe_01 "hand swipe at 2.3 m"
#   wsl.exe -e bash session.sh walk_01  "walking past at 1.4 m/s" --frames 3000
#
# THE POINT: the driver is left running between takes. The first invocation
# pays for deploy + build + launch (~40 s); every take after that is just
# record + pull (~5 s). Use --restart only when you have changed code, and
# --clean only when a .msg has changed.
#
#   --frames N     max frames to record        (default 2000, ~6 s at 333 Hz)
#   --restart      redeploy, rebuild, relaunch even if the driver is up
#   --clean        wipe build/install/log first (REQUIRED after a .msg change)
#   --no-deploy    skip the file push
#   --no-pull      leave the capture on the Jetson
#   --monitor      also sample the wire rate during the capture
#   --stop         stop the driver and exit (no recording)
#   --dest PATH    where to pull captures to
#
# Environment overrides: REMOTE, REMOTE_PATH, CAPTURES, DEST.

set -euo pipefail

# set -e exits silently: no line, no command, no clue -- which is exactly how
# this script kept dying at "== launch" with a bare prompt. Report before
# leaving. Every failure below is now attributable.
trap 'rc=$?; echo; echo "session.sh FAILED at line $LINENO (exit $rc)" >&2; echo "  command: $BASH_COMMAND" >&2' ERR

REMOTE="${REMOTE:-mmwave@192.168.33.30}"
REMOTE_PATH="${REMOTE_PATH:-/home/mmwave/ssd/chris-launch-monitor}"
CAPTURES="${CAPTURES:-/home/mmwave/ssd/captures}"
cd "$(dirname "$0")"

NAME=""; NOTE=""; FRAMES=2000
DO_DEPLOY=1; DO_PULL=1; RESTART=0; CLEAN=0; MONITOR=0; STOP_ONLY=0 RESET=0
DEST_ARG=""

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
        -h|--help) sed -n '2,25p' "$0" | sed 's/^# \?//'; exit 0 ;;
        -*) echo "unknown option: $arg" >&2; exit 2 ;;
        *) if [[ -z "$NAME" ]]; then NAME="$arg"; elif [[ -z "$NOTE" ]]; then NOTE="$arg"; fi; shift ;;
    esac
done

# Where captures land locally. Prefer an existing Desktop/results (there is
# normally exactly one Windows user under /mnt/c/Users) and fall back to the
# WSL home, so this works without configuration on this machine and does not
# silently invent a path on another.
if [[ -n "$DEST_ARG" ]]; then
    DEST="$DEST_ARG"
else
    DEST="${DEST:-}"
    if [[ -z "$DEST" ]]; then
        mapfile -t cand < <(ls -d /mnt/c/Users/*/Desktop/results 2>/dev/null || true)
        if [[ ${#cand[@]} -eq 1 ]]; then DEST="${cand[0]}"; else DEST="$HOME/radar-data"; fi
    fi
fi

# --- ssh multiplexing -----------------------------------------------------
# Every phase below is a separate ssh invocation. Without a shared connection
# that is 6+ authentications per take, which with password auth is exactly the
# friction this script exists to remove. One master, reused, torn down at exit.
SOCK="/tmp/.session-$$-ssh"
SSH=(ssh -o ControlMaster=auto -o "ControlPath=$SOCK" -o ControlPersist=60
     -o ConnectTimeout=8 -o BatchMode=no)
cleanup() { ssh -O exit -o "ControlPath=$SOCK" "$REMOTE" 2>/dev/null || true; }
trap cleanup EXIT

r() { "${SSH[@]}" "$REMOTE" "$@"; }                       # run remote
rsrc() { r "cd '$REMOTE_PATH' && source /opt/ros/foxy/setup.bash && source install/setup.bash && $1"; }

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

if ! r true; then
    echo "cannot reach $REMOTE." >&2
    echo "  check the radar-subnet link is up, and that key auth works:" >&2
    echo "    ssh-copy-id $REMOTE" >&2
    exit 1
fi

# --- driver state ---------------------------------------------------------
# BOTH nodes must be up. pgrep on the data node alone will happily "reuse" a
# half-dead launch whose control node has exited -- and the arm step then
# blocks forever inside ros2 service call waiting for a service that will
# never appear. That is the hang this check prevents.
# pgrep -f matches the whole command line, so an unbracketed pattern matches
# the very shell running it over ssh: driver_up returned true with nothing
# running, and pkill killed its own session (and the ssh master with it).
driver_up() { r "pgrep -f '[r]adar_data' >/dev/null 2>&1 && pgrep -f '[r]adar_ctrl_node' >/dev/null 2>&1"; }

# Kill EVERY node, not just the launch and the data node. An orphaned
# radar_ctrl_node keeps UDP 4096 (the DCA1000 command port) bound, so the next
# ctrl node fails to bind with EADDRINUSE, its DCA1000 setup fails, and SETUP
# then fails downstream with a misleading serial error. driver_up() needs BOTH
# nodes, so a lone orphan reads as "nothing running" and gets launched on top.
kill_all() {
    r "pkill -f '[r]os2 launch mmwave_drv' || true; pkill -f '[r]adar_ctrl_node' || true; pkill -f '[r]adar_term_cli' || true; pkill -f '[r]adar_gui_cli' || true; pkill -f '[r]adar_data' || true"
    sleep 2
    r "pkill -9 -f '[r]adar_ctrl_node' || true; pkill -9 -f '[r]adar_data' || true"
    sleep 1
    # Whatever still holds 4096 will break the next launch. Say so now.
    if r "ss -uln 2>/dev/null | grep -q :4096"; then
        echo "  WARNING: UDP 4096 is still bound after the kill." >&2
        r "ss -ulnp 2>/dev/null | grep :4096" >&2 || true
    fi
}

SVC_NAME="${SVC_NAME:-/control_radar}"

svc() {  # svc <0|1|2> <label> [timeout_s]
    local out tail_log
    printf %s "  $2 ..."
    # timeout, because ros2 service call blocks indefinitely on a service that
    # never appears rather than failing. SETUP uploads the whole profile one
    # serial command at a time and legitimately takes ~4 s, so allow 30.
    out=$(rsrc "timeout ${3:-30} ros2 service call $SVC_NAME mmwave_drv/srv/SendDeviceControlCommand '{command: $1}'" 2>&1) || true
    if grep -q "status=True" <<<"$out"; then
        echo " ok"
        return 0
    fi

    tail_log=$(r "tail -40 \$(ls -t $REMOTE_PATH/logs/launch_*.log | head -1)" 2>/dev/null || true)

    # "Error -54: Sensor has already been started or stopped" is the radar
    # saying it is ALREADY in the state we asked for. For START and STOP that
    # is the desired end state, not a failure -- and treating it as one is how
    # a good capture got thrown away on 29 Aug. SETUP is different: there -54
    # means the sensor is chirping and the CLI refused flushCfg.
    if [[ "$1" != 2 ]] && grep -q "already been started or stopped" <<<"$tail_log"; then
        echo " already in that state -- continuing"
        return 0
    fi

    echo " FAILED"
    sed "s/^/    /" <<<"$out" >&2
    if grep -q "status=False" <<<"$out"; then
        echo "  The radar REJECTED this command (the control node answered fine)." >&2
        echo "  Driver log says:" >&2
        grep -iE "Error|Ignored|failed|not been started" <<<"$tail_log" | tail -12 | sed "s/^/    /" >&2 || true
        echo "  If that is 'Sensor has already been started', a SECOND client is" >&2
        echo "  driving /control_radar -- radar_term_cli.py arms the radar from" >&2
        echo "  its own __init__. This script launches use_client:=false to stop" >&2
        echo "  that, so a stale driver from before the fix is the likely cause:" >&2
        echo "    .\session --restart <name>" >&2
        echo "  Otherwise the sensor is chirping and the CLI refuses flushCfg:" >&2
        echo "    .\session --reset" >&2
    else
        echo "  No response at all -- the control node is blocked." >&2
        echo "  services advertised:" >&2
        rsrc "ros2 service list" 2>&1 | grep -v parameter | sed "s/^/    /" >&2 || true
    fi
    return 1
}

if (( RESET )); then
    say "sensor reset (direct serial, no ROS)"
    # The driver must be down first or it holds /dev/ttyACM0 open.
    kill_all
    sleep 2
    bash deploy.sh >/dev/null
    rsrc "python3 scripts/sensor_stop.py --flush" || true
    echo "  now re-run with -restart"
    exit 0
fi

if (( STOP_ONLY )); then
    say "stopping driver"
    # Best-effort graceful stop, then kill regardless. Gating the kill on the
    # service succeeding is how you end up unable to stop a wedged node -- and
    # a wedged node is the single most likely reason to be running --stop.
    driver_up && svc 0 STOP 10 || echo "  (graceful stop unavailable -- killing)"
    kill_all
    echo "  driver stopped"
    exit 0
fi

[[ -n "$NAME" ]] || { echo "usage: session.sh <session-name> [note] [options]" >&2; exit 2; }

if (( RESTART )) || ! driver_up; then
    if (( DO_DEPLOY )); then
        say "deploy"
        bash deploy.sh
    fi

    say "build"
    if (( CLEAN )); then
        echo "  wiping build/ install/ log/ -- required after a .msg change, or"
        echo "  stale generated bindings survive and you debug a ghost."
        r "cd '$REMOTE_PATH' && rm -rf build install log"
    fi
    r "cd '$REMOTE_PATH' && source /opt/ros/foxy/setup.bash && colcon build --symlink-install" \
        | tail -5

    say "launch"
    kill_all

    # run.sh raises net.core.rmem_max, but it does that with sudo, which cannot
    # prompt over a non-interactive ssh -- so launching the driver from here
    # skips it entirely. rmem_max also resets on every reboot. Check and warn
    # rather than silently running a driver that will drop UDP packets.
    echo "  checking socket buffer ..."
    RMEM=$(r "cat /proc/sys/net/core/rmem_max" | tr -d "\r")
    if [[ "$RMEM" -lt 1610612736 ]]; then
        echo "  WARNING: net.core.rmem_max = $RMEM, want 1610612736."
        echo "  Make it permanent once, and it survives reboots:"
        echo "    ssh $REMOTE \"echo net.core.rmem_max=1610612736 | sudo tee /etc/sysctl.d/99-radar.conf && sudo sysctl --system\""
    fi

    STAMP=$(date +%Y%m%d_%H%M%S)
    LOG="$REMOTE_PATH/logs/launch_$STAMP.log"
    # setsid + </dev/null: survive this ssh closing.
    #
    # use_client:=false is load-bearing. radar_term_cli.py arms the radar from
    # its own __init__ (sleep 3 -> SETUP, sleep 4 -> START) with no flag and no
    # prompt, so leaving it in the launch makes it a second controller racing
    # this script. On 29 Aug its START won and ours came back "Error -54,
    # Sensor has already been started", aborting a take whose radar was
    # already running at 333 Hz. This script is the only client now.
    echo "  starting driver ..."
    # timeout(1) execs a binary, so it cannot wrap the r() shell function --
    # it fails with "failed to execute process". Call ssh directly here.
    if ! timeout 25 "${SSH[@]}" "$REMOTE" "cd '$REMOTE_PATH' && mkdir -p logs && ( setsid bash -lc 'source /opt/ros/foxy/setup.bash && source install/setup.bash && exec ros2 launch mmwave_drv radar_launch.py use_client:=false' </dev/null >'$LOG' 2>&1 & ) ; echo launched"; then
        echo "  note: ssh returned non-zero starting the launch; checking the log anyway"
    fi

    echo "  log: $LOG"
    echo "  waiting for the data node (up to 40 s) ..."
    READY=0
    for i in $(seq 1 40); do
        if r "grep -q 'Daemon is running' '$LOG' 2>/dev/null"; then READY=1; break; fi
        sleep 1
    done
    if [[ $READY -eq 0 ]]; then
        echo "  driver did NOT come up. Last 25 log lines:"
        r "tail -25 '$LOG' 2>/dev/null" || echo "  (log empty or missing)"
        exit 1
    fi
    echo "  ready after ${i}s"
else
    say "driver already running -- reusing it (--restart to force a rebuild)"
fi

# --- arm the radar --------------------------------------------------------
# SETUP uploads the whole profile over the serial link one command at a time
# and takes ~4 s; do not shorten the wait. Both are idempotent, so re-arming
# an already-armed radar is harmless.
say "arm"
svc 2 SETUP
sleep 1
svc 1 START
sleep 1

# --- record ---------------------------------------------------------------
say "record: $NAME ($FRAMES frames)"
if (( MONITOR )); then
    ( rsrc "IFACE= scripts/monitor.sh 5" 2>&1 | sed 's/^/  [wire] /' ) &
    MONPID=$!
fi
rsrc "scripts/record.sh '$NAME' '$NOTE' --max-frames $FRAMES" 2>&1 | sed 's/^/  /'
(( MONITOR )) && wait "$MONPID" 2>/dev/null || true

svc 0 STOP || true

# --- pull -----------------------------------------------------------------
if (( DO_PULL )); then
    say "pull -> $DEST"
    mkdir -p "$DEST"
    # -rltv, not -a: -a implies -p/-o/-g which are meaningless on DrvFs
    # (everything reads 777) and only add noise. No -z: raw I/Q barely
    # compresses and the CPU cost lands on the Jetson.
    # record.sh writes to ~/ssd/captures, one level up from the workspace.
    # No "|| try another path" fallback here on purpose: it would turn a wrong
    # REMOTE_PATH into a silent half-success, which is exactly the failure
    # mode this codebase keeps producing.
    rsync -rltv --partial -e "ssh -o ControlPath=$SOCK" \
        "$REMOTE:$CAPTURES/" "$DEST/"
    LATEST=$(ls -dt "$DEST"/*_"$NAME" 2>/dev/null | head -1 || true)
    [[ -n "$LATEST" ]] && echo "  latest: $LATEST"
fi

say "done -- driver left running; next take is just:  session.sh <name>"
