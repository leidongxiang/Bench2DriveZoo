#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"

: "${GPU_RANK:=0}"
: "${CARLA_PORT:=30000}"
: "${TM_PORT:=50000}"
: "${ROUTES:=/workspace/Bench2Drive/leaderboard/data/routes_devtest.xml}"
: "${RUN_NAME:=vad-devtest}"
: "${CARLA_ROOT:=/home/leidx/workspace/carla}"
: "${B2D_OUTPUT:=/home/leidx/workspace/outputs/bench2drive-zoo}"

CARLA_PID=""
cleanup() {
    if [[ -n "$CARLA_PID" ]]; then
        kill "$CARLA_PID" 2>/dev/null || true
        wait "$CARLA_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

mkdir -p "$B2D_OUTPUT/eval/$RUN_NAME"
if ! ss -ltn "sport = :$CARLA_PORT" | grep -q LISTEN; then
    "$CARLA_ROOT/CarlaUE4.sh" \
        -RenderOffScreen \
        -nosound \
        -carla-rpc-port="$CARLA_PORT" \
        -graphicsadapter="$GPU_RANK" \
        >"$B2D_OUTPUT/eval/$RUN_NAME/carla.log" 2>&1 &
    CARLA_PID=$!

    for _ in $(seq 1 60); do
        ss -ltn "sport = :$CARLA_PORT" | grep -q LISTEN && break
        kill -0 "$CARLA_PID" 2>/dev/null || {
            tail -50 "$B2D_OUTPUT/eval/$RUN_NAME/carla.log"
            exit 1
        }
        sleep 1
    done
    ss -ltn "sport = :$CARLA_PORT" | grep -q LISTEN || {
        echo "CARLA did not listen on port $CARLA_PORT within 60 seconds" >&2
        exit 1
    }
fi

docker run --rm \
    --user "$(id -u):$(id -g)" \
    --gpus all \
    --network host \
    --ipc host \
    --shm-size 32g \
    -v "$REPO_ROOT:/src/Bench2DriveZoo:ro" \
    -v "${VAD_WEIGHTS:-/home/leidx/workspace/weights/vad}:/workspace/weights/vad:ro" \
    -v "$B2D_OUTPUT:/workspace/outputs/bench2drive-zoo" \
    -v "$CARLA_ROOT:/workspace/carla" \
    -v "${BENCH2DRIVE_ROOT:-/home/leidx/workspace/projects/Bench2Drive}:/workspace/Bench2Drive:ro" \
    -e GPU_RANK="$GPU_RANK" \
    -e CARLA_PORT="$CARLA_PORT" \
    -e TM_PORT="$TM_PORT" \
    -e ROUTES="$ROUTES" \
    -e RUN_NAME="$RUN_NAME" \
    -e IS_BENCH2DRIVE=1 \
    -e B2D_OUTPUT=/workspace/outputs/bench2drive-zoo \
    -e HOME=/tmp/home \
    -e XDG_CACHE_HOME=/tmp/cache \
    -e PYTHON_EGG_CACHE=/tmp/cache/Python-Eggs \
    bench2drive-zoo:runtime bash -lc '
        set -euo pipefail
        mkdir -p "$HOME" "$XDG_CACHE_HOME" "$PYTHON_EGG_CACHE"
        mkdir -p /tmp/runtime
        cp -a /src/Bench2DriveZoo /tmp/runtime/Bench2DriveZoo
        cp /usr/local/lib/python3.8/dist-packages/mmcv/_ext*.so /tmp/runtime/Bench2DriveZoo/mmcv/
        cp /usr/local/lib/python3.8/dist-packages/mmcv/ops/iou3d_det/iou3d_cuda*.so /tmp/runtime/Bench2DriveZoo/mmcv/ops/iou3d_det/
        cp /usr/local/lib/python3.8/dist-packages/mmcv/ops/roiaware_pool3d/roiaware_pool3d_ext*.so /tmp/runtime/Bench2DriveZoo/mmcv/ops/roiaware_pool3d/

        export CARLA_ROOT=/workspace/carla
        export BENCH2DRIVE_ROOT=/workspace/Bench2Drive
        export PYTHONPATH=/tmp/runtime/Bench2DriveZoo:/tmp/runtime:$BENCH2DRIVE_ROOT:$CARLA_ROOT/PythonAPI/carla:$CARLA_ROOT/PythonAPI/carla/dist/carla-0.9.15-py3.7-linux-x86_64.egg

        CONFIG=/tmp/runtime/Bench2DriveZoo/adzoo/vad/configs/VAD/VAD_base_e2e_b2d.py
        CHECKPOINT=/workspace/weights/vad/vad_b2d_base.pth
        AGENT=/tmp/runtime/Bench2DriveZoo/team_code/vad_b2d_agent.py
        RUN_DIR="$B2D_OUTPUT/eval/$RUN_NAME"

        test -x "$CARLA_ROOT/CarlaUE4.sh"
        test -f "$CHECKPOINT"
        test -f "$ROUTES"
        mkdir -p "$RUN_DIR/sensors"

        cd "$BENCH2DRIVE_ROOT"
        export SAVE_PATH="$RUN_DIR/sensors"
        export SCENARIO_RUNNER_ROOT="$BENCH2DRIVE_ROOT/scenario_runner"
        export LEADERBOARD_ROOT="$BENCH2DRIVE_ROOT/leaderboard"
        export PYTHONPATH="$PYTHONPATH:$LEADERBOARD_ROOT:$LEADERBOARD_ROOT/team_code:$SCENARIO_RUNNER_ROOT"

        CUDA_VISIBLE_DEVICES="$GPU_RANK" python3.8 \
            "$LEADERBOARD_ROOT/leaderboard/leaderboard_evaluator.py" \
            --routes="$ROUTES" \
            --repetitions=1 \
            --track=SENSORS \
            --checkpoint="$RUN_DIR/results.json" \
            --debug-checkpoint="$RUN_DIR/live_results.txt" \
            --agent="$AGENT" \
            --agent-config="$CONFIG+$CHECKPOINT+$RUN_NAME" \
            --debug=0 \
            --resume=True \
            --external-server \
            --port="$CARLA_PORT" \
            --traffic-manager-port="$TM_PORT" \
            --gpu-rank="$GPU_RANK"
    '