FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        libgl1 \
        libglib2.0-0 \
        libvulkan1 \
        ninja-build \
        python3.8 \
        python3.8-dev \
        python3-pip \
        vulkan-tools \
    && rm -rf /var/lib/apt/lists/* \
    && python3.8 -m pip install --no-cache-dir --upgrade pip setuptools wheel

WORKDIR /workspace/Bench2DriveZoo

COPY requirements.txt setup.py ./
COPY mmcv ./mmcv
RUN python3.8 -m pip install --no-cache-dir \
    torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 \
        --index-url https://download.pytorch.org/whl/cu118 \
    && python3.8 -m pip install --no-cache-dir ninja packaging \
    && python3.8 -m pip install --no-cache-dir -r requirements.txt \
    && python3.8 -m pip install --no-cache-dir \
        pexpect \
        psutil \
        pygame \
        requests \
        'Shapely==1.7.1' \
        'xmlschema==1.0.18'

COPY . .
RUN FORCE_CUDA=1 TORCH_CUDA_ARCH_LIST=8.9 python3.8 -m pip install --no-cache-dir -v .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    B2D_ROOT=/workspace/data/bench2drive \
    NUSCENES_ROOT=/workspace/data/nuscenes \
    VAD_WEIGHTS=/workspace/weights/vad \
    B2D_OUTPUT=/workspace/outputs/bench2drive-zoo \
    B2D_CACHE=/workspace/cache/bench2drive-zoo \
    CARLA_ROOT=/workspace/carla \
    BENCH2DRIVE_ROOT=/workspace/Bench2Drive \
    IS_BENCH2DRIVE=1 \
    PYTHONPATH=/workspace/Bench2Drive:/workspace/Bench2DriveZoo:/workspace/carla/PythonAPI/carla:/workspace/carla/PythonAPI/carla/dist/carla-0.9.15-py3.7-linux-x86_64.egg

CMD ["bash"]