# 准备 Bench2Drive 数据集

宿主机数据集存放在本仓库之外的 `$B2D_ROOT`。Docker 容器以只读方式将其挂载到 `/workspace/data/bench2drive`，仓库路径 `data/bench2drive` 则是用于兼容现有配置的符号链接。继续之前请参阅 [Docker 配置](DOCKER.md)。

## 下载 Bench2Drive

从[此链接](https://github.com/Thinklab-SJTU/Bench2Drive)下载数据集，并确认数据目录结构如下：

**注意：不同版本的数据目录结构可能略有差异。可能需要使用符号链接（`ln -s`）并修改路径相关代码。**

```
    Bench2DriveZoo
    ├── ...
    ├── data/
    |   ├── bench2drive/
    |   |   ├── trainval/                                          # Bench2Drive v0.4
    |   |   |   ├── Accident_Town03_Route24976_Weather1_02-10-06-35-15/
    |   |   |   ├── Accident_Town06_Route24687_Weather21_02-10-04-51-33/
    |   |   |   └── ...
    |   |   └── maps/                                        # Town 地图
    |   |       ├── Town01_HD_map.npz
    |   |       ├── Town02_HD_map.npz
    |   |       └── ...
    |   ├── others
    |   |       └── b2d_motion_anchor_infos_mode6.pkl        # UniAD 运动锚点
    |   └── splits
    |           └── bench2drive_base_train_val_split.json    # Bench2Drive base 训练/验证集划分

```

## 生成 Bench2Drive 数据信息

在容器内运行以下命令。由于数据集以只读方式挂载，生成的信息文件会写入外部输出卷：

```
docker compose run --rm bench2drive-zoo bash -lc \
    'python3.8 mmcv/datasets/prepare_B2D.py --info_workers 16 --map_workers 12'
```

_注意：默认情况下，此命令会将 `data/splits/bench2drive_base_train_val_split.json` 中所列路线以外的所有路线作为训练集。使用 16 个 worker 生成全部数据约需 1 小时。_

## 代码结构

完成安装和数据准备后，代码结构如下：

```
    Bench2DriveZoo
    ├── adzoo/
    |   ├── bevformer/
    |   ├── uniad/
    |   └── vad/
    ├── ckpts/
    |   ├── r101_dcn_fcos3d_pretrain.pth                   # BEVFormer 预训练权重
    |   ├── resnet50-19c8e357.pth                          # VAD 图像 backbone 预训练权重
    |   ├── bevformer_base_b2d.pth                         # 按需下载的权重
    |   ├── uniad_base_b2d.pth                             # 按需下载的权重
    |   └── ...
    ├── data/
    |   ├── bench2drive/
    │   ├── infos/      # 由 prepare_B2D.py 生成
    │   │   ├── b2d_infos_map/
    |   |   |   ├── Town01.pkl
    |   |   |   ├── Town02.pkl
    |   |   |   └── ...
    │   │   ├── b2d_infos_train/
    |   |   |   ├── Accident_Town03_Route24976_Weather1_02-10-06-35-15.pkl
    |   |   |   ├── Accident_Town06_Route24687_Weather21_02-10-04-51-33.pkl
    |   |   |   └── ...
    │   │   ├── b2d_infos_val/
    |   |   |   ├── Accident_Town12_Route18996_Weather19_02-08-16-15-28.pkl
    |   |   |   ├── AccidentTwoWays_Town13_Route31240_Weather5_02-05-17-48-45.pkl
    |   |   |   └── ...
    |   |   |—— b2d_infos_train_meta.pkl
    │   │   └── b2d_infos_val_meta.pkl
    |   ├── others
    |   |       └── b2d_motion_anchor_infos_mode6.pkl      # UniAD 运动锚点
    |   └── splits
    |           └── bench2drive_base_train_val_split.json  # Bench2Drive base 训练/验证集划分
    ├── docs/
    ├── mmcv/
    ├── team_code/  # 用于 CARLA 闭环评测
```
