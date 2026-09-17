# Docker 配置与工作区布局

## 宿主机目录布局

源代码和文档保存在 Git 中；数据集、下载的权重、生成的 checkpoint、评测结果、日志和缓存均放在仓库之外。

```text
/home/leidx/workspace/
├── projects/
│   ├── Bench2Drive/             # 0.0.4 分支
│   └── Bench2DriveZoo/
├── carla/                       # CARLA 0.9.15 + AdditionalMaps
├── data/
│   └── bench2drive -> <Bench2Drive 数据集目录>
├── weights/
│   └── vad/
├── outputs/
│   └── bench2drive-zoo/
└── cache/
    └── bench2drive-zoo/
```

NuScenes 保留在 `/home/ax/datasets/nuscenes`。Docker 以只读方式 bind mount 宿主机数据和权重，并以可读写方式挂载输出与缓存。

## 环境配置

创建本地 Compose 环境文件：

```bash
cd /home/leidx/workspace/projects/Bench2DriveZoo
cp .env.example .env
sed -i "s/^B2D_UID=.*/B2D_UID=$(id -u)/; s/^B2D_GID=.*/B2D_GID=$(id -g)/" .env
```

宿主机的标准环境变量如下：

```bash
export B2D_ROOT=/home/leidx/workspace/data/bench2drive
export VAD_WEIGHTS=/home/leidx/workspace/weights/vad
export B2D_OUTPUT=/home/leidx/workspace/outputs/bench2drive-zoo
export CARLA_ROOT=/home/leidx/workspace/carla
export BENCH2DRIVE_ROOT=/home/leidx/workspace/projects/Bench2Drive
```

`.env.example` 还定义了指向现有共享数据集的 `NUSCENES_ROOT`，以及用于临时缓存的 `B2D_CACHE`。Compose 会将宿主机路径转换为稳定的容器路径，因此容器内同名变量指向：

```text
B2D_ROOT=/workspace/data/bench2drive
VAD_WEIGHTS=/workspace/weights/vad
B2D_OUTPUT=/workspace/outputs/bench2drive-zoo
CARLA_ROOT=/workspace/carla
BENCH2DRIVE_ROOT=/workspace/Bench2Drive
```

## 兼容性链接

现有模型配置使用 `data/bench2drive`、`data/nuscenes`、`data/infos` 和 `ckpts`。运行以下命令创建本地链接，无需修改这些配置：

```bash
export B2D_ROOT=/home/leidx/workspace/data/bench2drive
export NUSCENES_ROOT=/home/ax/datasets/nuscenes
export VAD_WEIGHTS=/home/leidx/workspace/weights/vad
export B2D_OUTPUT=/home/leidx/workspace/outputs/bench2drive-zoo
export CARLA_ROOT=/home/leidx/workspace/carla
export BENCH2DRIVE_ROOT=/home/leidx/workspace/projects/Bench2Drive
bash scripts/setup_workspace.sh
```

这些链接及其目标均被 Git 忽略。已跟踪的 `data/others` 和 `data/splits` 元数据仍保留在仓库中。

## 构建与运行

需要安装 Docker Engine、Docker Compose v2 插件、NVIDIA Container Toolkit，以及兼容 CUDA 11.8 的驱动。构建前请进行验证：

```bash
docker --version
docker compose version
nvidia-smi
```

在 Ubuntu 上，如果缺少 Compose 命令，请根据 Docker Engine 的安装方式，安装发行版提供的 `docker-compose-v2` 包或 Docker 提供的 `docker-compose-plugin` 包。

```bash
docker compose build
docker compose run --rm bench2drive-zoo bash
```

Compose 使用 `.env` 中的 `B2D_UID` 和 `B2D_GID` 运行容器，生成文件归宿主机用户所有；`HOME` 指向可写缓存目录。修改用户的 Docker 组成员身份后，需要重新连接 Remote SSH，旧的 VS Code Server 进程也要退出才能继承新组。

在容器内验证 GPU 和挂载：

```bash
python3.8 -c "import torch; print(torch.__version__, torch.cuda.is_available())"
test -d "$B2D_ROOT/trainval"
test -d "$VAD_WEIGHTS"
mkdir -p "$B2D_OUTPUT/results"
test -x "$CARLA_ROOT/CarlaUE4.sh"
git -C "$BENCH2DRIVE_ROOT" rev-parse --verify HEAD
```

相关命令请参阅[数据集准备](DATA_PREP.md)和[训练与评测](TRAIN_EVAL.md)。所有生成产物都应写入 `$B2D_OUTPUT` 下，不要在仓库内创建 `work_dirs`。

## 权重清单

将所需文件放入 `$VAD_WEIGHTS`。为兼容本地环境，变量名仍保留为该名称；但此目录是三个模型系列共用的 checkpoint 挂载目录，并在旧版配置中显示为 `ckpts`。

| 文件                           | 用途               | 版本/来源                                                                                                                       |
| ------------------------------ | ------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `resnet50-19c8e357.pth`        | VAD backbone       | PyTorch ResNet-50 checkpoint；[项目镜像](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/resnet50-19c8e357.pth)      |
| `r101_dcn_fcos3d_pretrain.pth` | BEVFormer backbone | FCOS3D R101-DCN 预训练权重；[项目镜像](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/r101_dcn_fcos3d_pretrain.pth) |
| `vad_b2d_base.pth`             | VAD Bench2Drive    | 已发布的 Bench2DriveZoo checkpoint；[下载](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/vad_b2d_base.pth)         |
| `uniad_tiny_b2d.pth`           | UniAD Tiny         | 已发布的 Bench2DriveZoo checkpoint；[下载](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/uniad_tiny_b2d.pth)       |
| `uniad_base_b2d.pth`           | UniAD Base         | 已发布的 Bench2DriveZoo checkpoint；[下载](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/uniad_base_b2d.pth)       |
| `bevformer_tiny_b2d.pth`       | BEVFormer Tiny     | 已发布的 Bench2DriveZoo checkpoint；[下载](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/bevformer_tiny_b2d.pth)   |
| `bevformer_base_b2d.pth`       | BEVFormer Base     | 已发布的 Bench2DriveZoo checkpoint；[下载](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/bevformer_base_b2d.pth)   |

为保证可复现性，请将下载文件的 SHA-256 与实验元数据一同记录在 `$B2D_OUTPUT/results` 下；Hugging Face 的 `main` URL 不会固定到不可变的仓库版本。

此工作区安装的具体资产记录在[运行时资产清单](ASSETS.md)中。
