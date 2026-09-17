#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"

exec python3 player/server.py \
    --host "${PLAYER_HOST:-0.0.0.0}" \
    --port "${PLAYER_PORT:-8070}" \
    --routes "${PLAYER_ROUTES:-/home/leidx/workspace/projects/Bench2Drive/leaderboard/data/bench2drive_0.0.4_val.xml}" \
    --output "${PLAYER_OUTPUT:-/home/leidx/workspace/outputs/bench2drive-zoo/eval}" \
    --launch-script "${PLAYER_LAUNCH_SCRIPT:-$REPO_ROOT/scripts/run_vad_simulation.sh}"