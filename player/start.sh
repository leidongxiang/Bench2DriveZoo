#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"

python3 player/progress_writer.py \
    --output "${PLAYER_OUTPUT:-/home/leidx/workspace/outputs/bench2drive-zoo/eval}" \
    --static "$REPO_ROOT/player/static" &
writer_pid=$!

python3 player/server.py \
    --host "${PLAYER_HOST:-0.0.0.0}" \
    --port "${PLAYER_PORT:-8070}" \
    --routes "${PLAYER_ROUTES:-/home/leidx/workspace/projects/Bench2Drive/leaderboard/data/bench2drive_0.0.4_val.xml}" \
    --output "${PLAYER_OUTPUT:-/home/leidx/workspace/outputs/bench2drive-zoo/eval}" \
    --launch-script "${PLAYER_LAUNCH_SCRIPT:-$REPO_ROOT/scripts/run_vad_simulation.sh}" &
server_pid=$!
cleanup() {
    kill "$server_pid" "$writer_pid" 2>/dev/null || true
    wait "$server_pid" "$writer_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
wait "$server_pid"
