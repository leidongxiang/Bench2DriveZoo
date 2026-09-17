#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

: "${B2D_ROOT:=/home/leidx/workspace/data/bench2drive}"
: "${NUSCENES_ROOT:=/home/ax/datasets/nuscenes}"
: "${VAD_WEIGHTS:=/home/leidx/workspace/weights/vad}"
: "${B2D_OUTPUT:=/home/leidx/workspace/outputs/bench2drive-zoo}"
: "${B2D_CACHE:=/home/leidx/workspace/cache/bench2drive-zoo}"
: "${CARLA_ROOT:=/home/leidx/workspace/carla}"
: "${BENCH2DRIVE_ROOT:=/home/leidx/workspace/projects/Bench2Drive}"

for source_path in "$B2D_ROOT" "$NUSCENES_ROOT" "$VAD_WEIGHTS" "$CARLA_ROOT" "$BENCH2DRIVE_ROOT"; do
    if [[ ! -d "$source_path" ]]; then
        printf 'Missing required directory: %s\n' "$source_path" >&2
        exit 1
    fi
done

mkdir -p \
    "$B2D_OUTPUT/eval" \
    "$B2D_OUTPUT/visualization" \
    "$B2D_OUTPUT/checkpoints" \
    "$B2D_OUTPUT/results" \
    "$B2D_OUTPUT/infos" \
    "$B2D_CACHE" \
    "$REPO_ROOT/data"

ln -sfn "$B2D_ROOT" "$REPO_ROOT/data/bench2drive"
ln -sfn "$NUSCENES_ROOT" "$REPO_ROOT/data/nuscenes"
ln -sfn "$B2D_OUTPUT/infos" "$REPO_ROOT/data/infos"
ln -sfn "$VAD_WEIGHTS" "$REPO_ROOT/ckpts"

printf 'Workspace links created in %s\n' "$REPO_ROOT"
printf 'Runtime output: %s\n' "$B2D_OUTPUT"