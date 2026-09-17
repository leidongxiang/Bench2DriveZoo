# 闭环评测

请按以下步骤在 CARLA 中评测 UniAD 和 VAD：

## 准备工作

- 按照 [Docker 配置](DOCKER.md)构建镜像。
- 使用 Bench2Drive 的 `0.0.4` 分支，具体版本见[运行时资产](ASSETS.md)。
- 使用 `$CARLA_ROOT` 中已验证的 CARLA 0.9.15。

## 容器路径

```bash
docker compose run --rm bench2drive-zoo bash
cd "$BENCH2DRIVE_ROOT"
test -x "$CARLA_ROOT/CarlaUE4.sh"
test -d "$BENCH2DRIVE_ROOT/Bench2DriveZoo/team_code"
```

Compose 会将本仓库同时挂载到 `/workspace/Bench2DriveZoo` 和
`$BENCH2DRIVE_ROOT/Bench2DriveZoo`。这样无需在宿主机的 Bench2Drive 工作树中创建符号链接或未跟踪文件，即可满足评测器要求的目录布局。

由于评测器和 CARLA 通过 TCP 端口通信，Compose 使用宿主机网络。CARLA 由 `-graphicsadapter` 参数控制，而非 `CUDA_VISIBLE_DEVICES`。

## 运行评测

仓库提供了 VAD 冒烟测试启动脚本。它会自动启动或复用宿主机上的 CARLA，并运行随附的 Town12 开发路线：

```bash
bash scripts/run_vad_simulation.sh
```

结果和可选的传感器采集数据会写入 `$B2D_OUTPUT/eval/vad-devtest`。闭环仿真不需要训练数据或 NuScenes。需要时可覆盖默认值：

```bash
GPU_RANK=0 \
ROUTES=/workspace/Bench2Drive/leaderboard/data/bench2drive_0.0.4_val.xml \
RUN_NAME=vad-validation \
bash scripts/run_vad_simulation.sh
```

在此环境中不要直接使用未经修改的上游 `run_evaluation.sh`，因为该文件会设置 `CARLA_ROOT=YOUR_CARLA_PATH`。本地启动脚本会保留 Compose 路径 `/workspace/carla` 并直接调用评测器。
