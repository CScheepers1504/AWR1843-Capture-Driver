#!/usr/bin/env bash
#
# Push the laptop working tree to the Jetson. ONE-WAY -> this script never pulls.
#
# The laptop is the source of truth and the Jetson is a deployment target only.
# Written after a vscode-sftp pull silently truncated all 25 source files to
# zero bytes and that state was committed over the only good copies. The
# zero-byte guard below exists to make that failure mode un-repeatable outbound.
#
# Usage (from the repo root):
#   wsl.exe -e bash deploy.sh          # preferred: uses rsync
#   bash deploy.sh                     # Git Bash: falls back to tar-over-ssh
#   bash deploy.sh --dry-run           # show what would be sent, send nothing
#   bash deploy.sh --prune             # also delete remote files absent locally
#
# Override the target with environment variables:
#   REMOTE=mmwave@10.0.0.5 bash deploy.sh

set -euo pipefail

REMOTE="${REMOTE:-mmwave@192.168.33.30}"
# Laptop and Jetson layouts are deliberately identical: <root>/{src,scripts}.

REMOTE_PATH="${REMOTE_PATH:-/home/mmwave/ssd/chris-launch-monitor}"
PATHS=(src scripts)

# Files that must be executable on the Jetson. The Windows filesystem reports
# every file as mode 777 over DrvFs, so the real exec bits do not survive the
# transfer and must be reasserted remotely. Losing these re-introduces the
# "missing executable bits on node scripts" defect inherited from the 2024 code.
EXEC_GLOBS=(
    'scripts/*.sh'
    'src/mmWave_DRV/src/python/*.py'
)

cd "$(dirname "$0")"

DRY_RUN=0
PRUNE=0
INIT=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --prune)   PRUNE=1 ;;
        --init)    INIT=1 ;;
        *) echo "Unknown option: $arg" >&2; exit 2 ;;
    esac
done

for p in "${PATHS[@]}"; do
    [[ -d "$p" ]] || { echo "ABORT: '$p' not found -- run from the repo root." >&2; exit 1; }
done

# Guard: never deploy a tree containing empty files. An empty file here almost
# always means a botched sync, not an intentional edit, and pushing it would
# overwrite working code on the Jetson.
empty=$(find "${PATHS[@]}" -type f -size 0 -not -name '__init__.py' -not -path '*/__pycache__/*')
if [[ -n "$empty" ]]; then
    echo "ABORT: zero-byte files in the working tree:" >&2
    echo "$empty" | sed 's/^/  /' >&2
    echo "Refusing to deploy. Recover these before pushing." >&2
    exit 1
fi

count=$(find "${PATHS[@]}" -type f -not -path '*/__pycache__/*' | wc -l)
(( count > 0 )) || { echo "ABORT: no files to deploy." >&2; exit 1; }

# Normalise line endings. The laptop is Windows and editors here reintroduce
# CRLF on save; a CRLF shell script fails on the Jetson with the unhelpful
# "$'\r': command not found", and a CRLF Python shebang fails just as badly.
# .gitattributes covers what git touches, but not files edited and deployed
# without a commit in between -- so check on every deploy.
crlf=$(find "${PATHS[@]}" -type f \( -name '*.sh' -o -name '*.py' \) \
        -not -path '*/__pycache__/*' -exec grep -lI $'\r' {} + 2>/dev/null || true)
if [[ -n "$crlf" ]]; then
    echo "Converting CRLF -> LF before deploy:"
    echo "$crlf" | sed 's/^/  /'
    echo "$crlf" | xargs sed -i 's/\r$//'
fi

# Stamp the deployed commit so a capture can be traced back to the code that
# produced it. A dirty tree is allowed but recorded as such.
sha=$(git rev-parse --short HEAD 2>/dev/null || echo "nogit")
git diff --quiet 2>/dev/null || sha="${sha}-dirty"

if (( DRY_RUN )); then
    echo "DRY RUN -- would send $count files to $REMOTE:$REMOTE_PATH as $sha"
    find "${PATHS[@]}" -type f -not -path '*/__pycache__/*' | sed 's/^/  /'
    exit 0
fi

# Guard: refuse to deploy into a directory that is not already the workspace.
# A wrong REMOTE_PATH does not fail loudly -- it silently creates a second copy
# of the tree next to the real one, and the node keeps running the old code.
if (( ! INIT )); then
    if ! ssh "$REMOTE" "test -d '$REMOTE_PATH/src/mmWave_DRV'"; then
        echo "ABORT: $REMOTE:$REMOTE_PATH/src/mmWave_DRV does not exist." >&2
        echo "REMOTE_PATH is probably wrong. Locate the workspace with:" >&2
        echo "  ssh $REMOTE 'find ~ -name package.xml -path \"*mmWave_DRV*\"'" >&2
        echo "Then fix REMOTE_PATH at the top of this script, or pass --init" >&2
        echo "if you really are deploying to a fresh directory." >&2
        exit 1
    fi
fi

echo "Deploying $count files ($sha) to $REMOTE:$REMOTE_PATH"

if command -v rsync >/dev/null 2>&1; then
    # -rlt rather than -a: -a implies -p/-o/-g, which are meaningless coming
    # from DrvFs (everything reads as 777) and would push world-writable files
    # onto a shared machine. --chmod sets sane modes; exec bits fixed below.
    rsync_opts=(-rltvz --chmod=D755,F644
                --exclude='__pycache__' --exclude='*.pyc'
                --exclude='build' --exclude='install' --exclude='log')
    (( PRUNE )) && rsync_opts+=(--delete)
    rsync "${rsync_opts[@]}" "${PATHS[@]}" "$REMOTE:$REMOTE_PATH/"
else
    echo "(rsync not found -- using tar over ssh; --prune has no effect)"
    tar czf - --exclude='__pycache__' --exclude='*.pyc' "${PATHS[@]}" \
      | ssh "$REMOTE" "mkdir -p '$REMOTE_PATH' && tar xzf - -C '$REMOTE_PATH'"
fi

# Reassert exec bits and record the deployed revision.
remote_cmd="cd '$REMOTE_PATH'"
for g in "${EXEC_GLOBS[@]}"; do
    remote_cmd+=" && chmod +x $g 2>/dev/null || true"
done
remote_cmd+=" && echo \"\$(date -u +%FT%TZ)  $sha\" >> '$REMOTE_PATH/DEPLOYED'"
ssh "$REMOTE" "$remote_cmd"

echo "Done. On the Jetson:"
echo "  cd $REMOTE_PATH && colcon build --symlink-install && source install/setup.bash"
