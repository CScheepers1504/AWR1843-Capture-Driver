#!/usr/bin/env bash
#
# One command: deploy -> build -> launch -> SETUP/START -> record -> STOP -> pull.
#
#   wsl.exe -e bash session.sh [folder name] "[comment]"
#   wsl.exe -e bash session.sh [folder name]  "[comment]" --frames [number of frames]
#
# The driver is left running between takes. The first run
# pays for deploy + build + launch. Every take after that is just
# record + pull. Use --restart only when you have changed code, and
# --clean only when a .msg has changed.
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
# FAILURE HANDLING 
#   1. A failed STOP was ignored (`|| true`). The sensor could be left chirping
#      with the node's RECRD flag stale, and the next SETUP then timed out.
#      A failed STOP now stops the sensor over raw serial and kills the driver.
#   2. --restart killed the nodes but never stopped the sensor, so it failed
#      SETUP the same way. Every relaunch now stops the sensor first.
#   3. A SETUP/START failure now triggers one automatic relaunch before giving
#      up -- what "--stop, then take again" did by hand.
#   4. Ctrl-C killed the local ssh and orphaned the recorder on the Jetson;
#      three had piled up. Ctrl-C now stops the remote recorder and the
#      sensor, and leftover recorders are swept before every take.
#   5. "already started or stopped" was matched anywhere in the last 40 log
#      lines, so a STALE Error -54 could pass a NEW failure as success, and the
#      recorder then waited forever. Only lines logged after the command count.
#   6. START answering "already started" is now a FAILURE, not "already in that
#      state". The sensor was chirping before the DCA1000 armed, so the capture
#      can join mid-frame
#   7. Every take's Tx slot order is checked against a per-rig reference
#      (scripts/tx_order_check.py). A rotated take is
#      renamed *_TXSLIP and the driver is stopped so the next take relaunches.
# The recorder also gives up after 8 s with no frames (exit 3) instead of
# hanging, and this script samples the wire before stopping so the dead stage
# is identifiable.

set -euo pipefail

# set -e exits silently: Every failure below is now attributable.
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

# Where captures land locally and fall back to the WSL home
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
# Recorders too: one left subscribed competes for CPU with the next take's.
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

# Killing the nodes does NOT stop the sensor: it keeps chirping with no host
# attached, and the next SETUP's flushCfg then fails. So every path that kills
# the driver finishes here, over raw serial with no ROS in the way. The nodes
# must already be down, or radar_ctrl_node still holds the port.
serial_stop() {
    echo "  stopping the sensor over raw serial ..."
    r "cd '$REMOTE_PATH' && python3 scripts/sensor_stop.py" 2>&1 | sed 's/^/    /' \
        || echo "  sensor_stop.py did not confirm a stop -- if SETUP fails next, power-cycle the radar" >&2
}

latest_log() { r "ls -t '$REMOTE_PATH'/logs/launch_*.log 2>/dev/null | head -1" | tr -d '\r'; }
log_lines()  { r "wc -l < '$LOG' 2>/dev/null || echo 0" | tr -d '\r '; }

SVC_NAME="${SVC_NAME:-/control_radar}"

svc() {  # svc <0|1|2> <label> [timeout_s]
    local out new_log n0
    printf %s "  $2 ..."
    [[ -n "$LOG" ]] || LOG=$(latest_log)
    n0=$(log_lines)
    # timeout, because ros2 service call blocks indefinitely on a service that
    # never appears rather than failing. SETUP uploads the whole profile one
    # serial command at a time.
    out=$(rsrc "timeout ${3:-30} ros2 service call $SVC_NAME mmwave_drv/srv/SendDeviceControlCommand '{command: $1}'" 2>&1) || true
    if grep -q "status=True" <<<"$out"; then
        echo " ok"
        return 0
    fi

    # Only what the driver logged in response to THIS command.
    sleep 0.5
    new_log=$(r "tail -n +$((n0 + 1)) '$LOG'" 2>/dev/null || true)

    # "Error -54: Sensor has already been started or stopped" is the radar
    # saying it is ALREADY in the state we asked for. For START and STOP that
    # is the desired end state, not a failure. SETUP is different: there -54
    # means the sensor is chirping and the CLI refused flushCfg.
    if [[ "$1" == 0 ]] && grep -q "already been started or stopped" <<<"$new_log"; then
        echo " already stopped -- continuing"
        return 0
    fi
    # START is NOT the same. "Already started" means the sensor was chirping
    # before the DCA1000 was told to record, so the capture can join the stream
    # mid-frame with the Tx slots rotated.
    if [[ "$1" == 1 ]] && grep -q "already been started or stopped" <<<"$new_log"; then
        echo " FAILED -- the sensor was already chirping"
        echo "  Recording now could join the stream mid-frame and rotate the Tx order." >&2
        return 1
    fi

    echo " FAILED"
    sed "s/^/    /" <<<"$out" >&2
    if grep -q "status=False" <<<"$out"; then
        echo "  The control node answered, but the command failed. It logged:" >&2
        grep -iE "Error|Ignored|failed|not been started|Device is running" <<<"$new_log" | tail -12 | sed "s/^/    /" >&2 || true
        if grep -q "invalid response" <<<"$new_log"; then
            echo "  'invalid response' = NO reply on the CLI serial port within 0.25 s." >&2
            echo "  Usually the sensor is still chirping from an earlier take. If it" >&2
            echo "  persists on a fresh driver, the CLI port may have moved:  --reset" >&2
        fi
    else
        echo "  No response at all -- the control node is blocked." >&2
        echo "  services advertised:" >&2
        rsrc "ros2 service list" 2>&1 | grep -v parameter | sed "s/^/    /" >&2 || true
    fi
    return 1
}

# Graceful STOP through the node if it is up, then kill every node, then stop
# the sensor over serial REGARDLESS. Not gated on the STOP succeeding: a wedged
# node is exactly when this is needed
stop_driver() {
    if driver_up; then
        svc 0 STOP 10 || echo "  (graceful stop failed -- killing and stopping over serial)"
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
        echo "  wiping build/ install/ log/ -- required after a .msg change, or"
        echo "  stale generated bindings survive and you debug a ghost."
        r "cd '$REMOTE_PATH' && rm -rf build install log"
    fi
    r "cd '$REMOTE_PATH' && source /opt/ros/foxy/setup.bash && colcon build --symlink-install" \
        | tail -5

    say "launch"
    # stop_driver, not kill_all: kill_all alone left the sensor chirping
    stop_driver

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
    # this script. This script is the only client now.
    echo "  starting driver ..."
    # timeout(1) execs a binary, so it cannot wrap the r() shell function --
    # it fails with "failed to execute process". Call ssh directly here.
    if ! timeout 25 "${SSH[@]}" "$REMOTE" "cd '$REMOTE_PATH' && mkdir -p logs && ( setsid bash -lc 'source /opt/ros/foxy/setup.bash && source install/setup.bash && exec ros2 launch mmwave_drv radar_launch.py use_client:=false' </dev/null >'$LOG' 2>&1 & ) ; echo launched"; then
        echo "  note: ssh returned non-zero starting the launch; checking the log anyway"
    fi

    echo "  log: $LOG"
    echo "  waiting for the data node (up to 40 s) ..."
    local ready=0 i
    for i in $(seq 1 40); do
        if r "grep -q 'Daemon is running' '$LOG' 2>/dev/null"; then ready=1; break; fi
        sleep 1
    done
    if [[ $ready -eq 0 ]]; then
        echo "  driver did NOT come up. Last 25 log lines:"
        r "tail -25 '$LOG' 2>/dev/null" || echo "  (log empty or missing)"
        exit 1
    fi
    echo "  ready after ${i}s"
}

# --- Ctrl-C ---------------------------------------------------------------
# Ctrl-C kills the LOCAL ssh only. The recorder on the Jetson has no terminal,
# receives no signal, and waits for frames forever. SIGINT rather than SIGTERM so
# it still writes its capture summary. The sensor is stopped too: left armed,
# it makes the next take's SETUP fail.
on_interrupt() {
    trap - INT TERM ERR
    say "interrupted -- cleaning up on the Jetson (Ctrl-C again to abandon)"
    r "pkill -INT -f '[r]ecorder.py'; true" \
        || echo "  could not reach the Jetson -- run there:  pkill -f '[r]ecorder.py'" >&2
    if (( ARMED )); then
        svc 0 STOP 10 || echo "  STOP failed -- the next take will stop the sensor and relaunch" >&2
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
    # --reference always lands here: a fresh launch on a sensor just stopped
    # over serial is the state least likely to join the stream mid-frame, so
    # it is the best available guess at a correctly ordered reference.
    launch_driver
else
    say "driver already running -- reusing it (--restart to force a rebuild)"
    LOG=$(latest_log)
fi

# --- leftover recorders ---------------------------------------------------
# One Python recorder only just keeps up at [frame rate] on this Xavier NX, so an
# orphan from an earlier interrupted take costs this take frames. Sweep.
STALE=$(r "pgrep -af '[r]ecorder.py'; true" | tr -d '\r')
if [[ -n "$STALE" ]]; then
    echo "  WARNING: leftover recorder(s) on the Jetson -- killing them:" >&2
    sed 's/^/    /' <<<"$STALE" >&2
    r "pkill -f '[r]ecorder.py'; sleep 1; pkill -9 -f '[r]ecorder.py'; true"
fi

# --- arm the radar --------------------------------------------------------
# SETUP uploads the whole profile over the serial link one command at a time
# and takes ~4 s. Both are idempotent, so re-arming
# an already-armed radar is harmless.
arm() {
    svc 2 SETUP || return 1
    sleep 1
    svc 1 START || return 1
    ARMED=1
    sleep 1
}

say "arm"
if ! arm; then
    # A previous take's failed STOP, or a Ctrl-C, leaves the sensor chirping
    # and the node's RECRD flag stale, and SETUP cannot recover either from
    # inside the node. A fresh driver on a sensor stopped over serial can.
    say "arm failed -- stopping the sensor and relaunching once"
    DO_DEPLOY=0; CLEAN=0
    launch_driver
    say "arm (after relaunch)"
    if ! arm; then
        echo "  arm failed after a relaunch too, so this is not stale state." >&2
        echo "  Next:  session.sh --reset   (probes the CLI port and baud)" >&2
        exit 1
    fi
fi

# --- record ---------------------------------------------------------------
say "record: $NAME ($FRAMES frames)"
MONPID=""
if (( MONITOR )); then
    ( rsrc "IFACE= scripts/monitor.sh 5" 2>&1 | sed 's/^/  [wire] /' ) &
    MONPID=$!
fi
REC_RC=0
# tee a copy: the capture directory is only known from the recorder's own
# "Recording to <dir>" line, and the Tx-order check below needs it.
RECLOG=$(mktemp)
rsrc "scripts/record.sh '$NAME' '$NOTE' --max-frames $FRAMES" 2>&1 | tee "$RECLOG" | sed 's/^/  /' || REC_RC=$?
CAPDIR=$(grep -o 'Recording to [^ ]*' "$RECLOG" | tail -1 | cut -d' ' -f3 || true)
rm -f "$RECLOG"
if [[ -n "$MONPID" ]]; then wait "$MONPID" 2>/dev/null || true; fi

# Exit 3 is the recorder's no-frames timeout. Sample the wire BEFORE stopping,
# while the fault is still live: once STOP runs the evidence is gone.
if (( REC_RC == 3 )); then
    echo "  NO FRAMES reached the recorder. Sampling the wire to find the dead stage:" >&2
    rsrc "IFACE= scripts/monitor.sh 3" 2>&1 | sed 's/^/  [wire] /' || true
    echo "  ~0 MB/s  -> radar or DCA1000 not streaming (START did not really happen)" >&2
    echo "  ~14 MB/s -> DCA1000 streaming, data node not publishing" >&2
fi

# --- stop -----------------------------------------------------------------
say "stop"
if svc 0 STOP; then
    ARMED=0
else
    # This used to be `|| true`. A failed STOP can leave the sensor chirping and
    # the node's RECRD flag stale, and the NEXT take's SETUP then fails with
    # "invalid response" -- far from the cause. Stop everything now instead.
    echo "  WARNING: STOP failed. Stopping the sensor over serial and killing the" >&2
    echo "  driver, so the next take relaunches clean (~20 s)." >&2
    stop_driver
fi

if (( REC_RC != 0 )); then
    echo >&2
    echo "  recording FAILED (recorder exit $REC_RC) -- nothing pulled." >&2
    exit 1
fi

# --- chirp alignment ------------------------------------------------------
# From the samples: does the take start on an Rx-block boundary? The data node
# aligns on the DCA1000's byte count, which cannot see bytes the card never
# counted. See chirp_align_check.py.
if [[ -n "$CAPDIR" ]]; then
    say "chirp alignment"
    CA_RC=0
    rsrc "python3 scripts/chirp_align_check.py '$CAPDIR' --write-meta" 2>&1 | sed 's/^/  /' || CA_RC=$?
    case "$CA_RC" in
        0) ;;
        4)
            echo "  ************************************************************" >&2
            echo "  TAKE DOES NOT START ON A CHIRP BOUNDARY. Its angles are wrong" >&2
            echo "  as recorded (the realign offset is in meta.json chirp_align)." >&2
            echo "  Re-take it; if this was the first take since power-up, that" >&2
            echo "  is the known 282 Hz mode -- the next take is normally clean." >&2
            if (( REFERENCE )); then echo "  Do NOT keep it as the Tx-order reference: record it again." >&2; fi
            echo "  ************************************************************" >&2
            ;;
        5) echo "  UNSURE: no clear chirp boundary in the samples (empty or saturated scene?)." >&2 ;;
        *) echo "  chirp alignment check could not run (exit $CA_RC) -- NOT checked." >&2 ;;
    esac
fi

# --- Tx slot order --------------------------------------------------------
# RELATIVE check only: see the tx_order_check.py docstring.
REF_FILE="$CAPTURES/.txorder_ref"
if [[ -z "$CAPDIR" ]]; then
    echo "  WARNING: could not find the capture directory in the recorder output; Tx order NOT checked." >&2
elif (( REFERENCE )); then
    say "Tx-order reference"
    # A misaligned reference silently disables the check for every later take:
    # Accept a reference only if the samples are aligned AND no frame start was
    # timed off the frame grid.
    SLIPS=$(r "python3 -c 'import json,sys; c=json.load(open(sys.argv[1])).get(\"capture\",{}); print(c.get(\"burst_slips\") or 0)' '$CAPDIR/meta.json'" | tr -d '\r' || echo "?")
    if [[ "$CA_RC" != 0 || "$SLIPS" != 0 ]]; then
        echo "  ************************************************************" >&2
        echo "  NOT accepted as the reference (chirp alignment exit $CA_RC," >&2
        echo "  burst_slips $SLIPS). The previous reference, if any, is kept." >&2
        echo "  Record the reference again:  session.sh --reference" >&2
        echo "  ************************************************************" >&2
    else
        r "echo '$CAPDIR' > '$REF_FILE'"
        echo "  $CAPDIR"
        echo "  is now the reference for this rig. It must be an EMPTY scene, and it is"
        echo "  valid only until the radar is moved or re-tilted -- then record a new one."
    fi
else
    say "Tx-order check"
    REF=$(r "cat '$REF_FILE' 2>/dev/null; true" | tr -d '\r')
    if [[ -z "$REF" ]]; then
        echo "  NOT CHECKED -- no reference for this rig. With the scene empty, run once:" >&2
        echo "    session.sh --reference" >&2
    elif ! r "test -f '$REF/meta.json'"; then
        echo "  NOT CHECKED -- the reference $REF no longer exists. Record a new one:  session.sh --reference" >&2
    else
        TX_RC=0
        rsrc "python3 scripts/tx_order_check.py '$CAPDIR' --ref '$REF' --write-meta" 2>&1 | sed 's/^/  /' || TX_RC=$?
        case "$TX_RC" in
            0) ;;
            4)
                r "mv '$CAPDIR' '${CAPDIR}_TXSLIP'"
                echo "  ************************************************************" >&2
                echo "  Tx ORDER DIFFERS FROM THE REFERENCE. Renamed to *_TXSLIP." >&2
                echo "  Do not use its angles. Stopping the driver so the next take" >&2
                echo "  relaunches -- it is not known whether the slip persists." >&2
                echo "  ************************************************************" >&2
                stop_driver
                ;;
            5)
                echo "  UNSURE: the scene may have changed too much since the reference," >&2
                echo "  or the radar was moved. If it was moved, record a new reference." >&2
                ;;
            *)
                echo "  Tx-order check could not run (exit $TX_RC) -- order NOT checked." >&2
                ;;
        esac
    fi
fi

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
    LATEST=$(ls -dt "$DEST"/*_"$NAME" "$DEST"/*_"$NAME"_TXSLIP 2>/dev/null | head -1 || true)
    [[ -n "$LATEST" ]] && echo "  latest: $LATEST"
fi

say "done -- driver left running; next take is just:  session.sh <name>"
