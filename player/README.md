# Bench2Drive Route Lab

本机 VAD 闭环推理控制台与 PNG + JSON 结果播放器。播放器只发布已完成任务；播放时按帧读取六路相机、BEV 和 `meta/*.json`，不生成 MP4。

## 启动

```bash
./player/start.sh
```

本机浏览器打开 `http://localhost:8070`。同一局域网的其他机器使用服务器地址 `http://10.10.20.154:8070`。

`8070` 是网页和结果文件的 HTTP 端口；CARLA 推理仍通过独立的 RPC 端口 `30000`。两者必须同时存在，职责不同，并不冲突。

可覆盖默认路径：

```bash
python3 player/server.py \
  --port 8070 \
  --routes /path/to/routes.xml \
  --output /path/to/output/eval \
  --launch-script scripts/run_vad_simulation.sh
```

## 功能与约束

- 默认从 `bench2drive_0.0.4_val.xml` 加载完整的 220 条验证路线，可按 Town、Route ID 和场景筛选。
- 在 Town 地图上点击起点、途经点和终点。网页把画布位置反算为 `{x, y, z}` CARLA 世界坐标并生成单路线 XML。
- 地图参考线来自完整验证集在对应 Town 的路线轨迹，并非完整 OpenDRIVE 道路底图；最终可驾驶性仍由 evaluator 校验。
- 导入仅含一条 `<route>` 的 XML。
- CARLA/GPU 推理任务串行运行；检测到外部 `leaderboard_evaluator.py` 时拒绝启动新任务。
- 任务成功结束并且七路图像与 JSON 帧号交集非空后，状态才变为 `ready`。
- 页面显示输出文件系统的可用空间、总空间和使用率。
- 删除接口只接受服务端生成或发现的 run ID，并限制在配置的输出根目录内。普通删除会原子移动到 `<output>/.trash/`。
- 回收站支持恢复和永久删除；只有回收站内的条目才能执行永久删除。

运行清单与生成的单路线 XML 保存在输出目录的 `.player/<run-id>/` 中。推理输出仍保存在 `<output>/<run-name>/`。
