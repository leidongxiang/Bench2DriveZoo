# 代码迁移指南

本文档说明将基于 NuScenes 或其他数据集的代码迁移到 Bench2Drive 时需要注意的重要事项。

## 模型

我们已将多个 MMCV 依赖集成到 `mmcv` 目录中，不再安装原始库。可以参考现有方法使用这些模块，并将自己的模型和工具放入 `mmcv` 目录后完成注册。请确认该目录包含所需的全部模块；如有缺失，需要自行补充。

## 脚本与配置

各方法的配置、脚本和工具均可放在 `adzoo` 中，以便统一管理。

## 配置细节

为 Bench2Drive 数据集创建配置时，请注意：

- 配置中已直接包含 Bench2Drive 的名称到类别映射及评测设置，可以直接使用或按需修改。
- NuScenes 使用 10 个类别，而 Bench2Drive 使用 9 个类别。
- UniAD 和 VAD 等方法在 NuScenes 上使用 3 种指令，而 Bench2Drive 使用从 CARLA 获取的 6 种指令。

## 数据集

- Bench2Drive 数据的坐标系与 BEVFormer/UniAD/VAD 使用的坐标系差异较大，详情见[标注说明](https://github.com/Thinklab-SJTU/Bench2Drive/blob/main/docs/anno.md)。在 `mmcv/datasets/prepare_B2D.py` 中，我们转换了世界坐标系、自车坐标系和传感器坐标系，包括车辆坐标、边界框坐标及传感器外参，使其与这些模型使用的坐标系一致。数据对齐方式可参考该代码。
- NuScenes 的关键帧频率为 2 Hz；Bench2Drive 以 10 Hz 运行，且每帧都有标注。为复现 UniAD 和 VAD，我们将窗口长度（过去和未来轨迹中相邻点之间的时间间隔）设为 0.5 秒，将窗口偏移设为 0.1 秒（任意帧均可作为当前帧）。这样既能充分利用 Bench2Drive 数据，也能使轨迹与 NuScenes 对齐。
- Bench2Drive 使用矢量化地图。地图的使用方式（例如提取一定范围内的地图元素）可参考现有代码。

## 团队 Agent（team agent）

要在 CARLA 中执行闭环评测，需要配置传感器从 CARLA 采集数据，使用这些数据计算模型所需的全部输入，再将模型输出转换为 `carla.VehicleControl` 对象。
