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

直接运行 `server.py` 时，需另起 `python3 player/progress_writer.py --output /path/to/output/eval --static player/static` 才能显示运行中进度；使用 `start.sh` 会自动启动。

## 功能与约束

- 默认从 `bench2drive_0.0.4_val.xml` 加载完整的 220 条验证路线，可按 Town、Route ID 和场景筛选。
- 在 Town 地图上点击起点、途经点和终点。网页吸附并显示提交给 evaluator 的路径点，然后生成单路线 XML；实际轨迹由 CARLA GlobalRoutePlanner 在推理时计算。
- 自定义路线地图显示 OpenDRIVE 道路底图与路径点，不绘制可能与实际推理不同的路径线；最终可驾驶性仍由 evaluator 校验。
- 导入仅含一条 `<route>` 的 XML。
- CARLA/GPU 推理任务串行运行；检测到外部 `leaderboard_evaluator.py` 时拒绝启动新任务。
- 运行中显示已生成帧数和累计行驶距离；进度条不显示百分比，因为自定义路线的实际道路长度在推理结束前没有可靠数值。评测进程退出且七路图像与 JSON 帧号交集非空后，结果可播放；路线未完成时结果卡会另行标注评测状态。
- 新推理结果逐帧保存 VAD 地图矢量、其他车辆/行人的六模态未来轨迹、CARLA GT 三维框、VAD 预测三维框的投影轮廓和自车规划轨迹；右侧 BEV 以 Canvas 矢量绘制，不使用顶视相机作为底图。旧结果保留原顶视相机画面。
- 新推理结果逐帧保存 CARLA 车辆/行人 GT 三维框、VAD 预测三维框的投影轮廓和规划轨迹；播放器可分别显示 GT/预测框，并显示六种驾驶命令。旧结果若没有角点数据，会回退显示二维外接框；重新推理后显示三维线框。
- 整个播放器可全屏查看；全屏时保留播放控制、GT/推理框开关和驾驶命令。
- 页面显示输出文件系统的可用空间、总空间和使用率。
- 删除接口只接受服务端生成或发现的 run ID，并限制在配置的输出根目录内。普通删除会原子移动到 `<output>/.trash/`。
- 回收站支持恢复和永久删除；只有回收站内的条目才能执行永久删除。

运行清单与生成的单路线 XML 保存在输出目录的 `.player/<run-id>/` 中。推理输出仍保存在 `<output>/<run-name>/`。
