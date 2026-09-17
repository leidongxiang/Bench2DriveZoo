## 安装

此版本支持的运行方式是 Docker。请按照 [Docker 配置与工作区布局](DOCKER.md)准备可复现的 CUDA 11.8/Python 3.8 镜像、外部数据集、权重和输出目录。

以下命令仅作为旧版裸机安装参考保留。

## 旧版裸机环境

- **步骤 1：创建环境**
  ```
  ## 必须使用 Python 3.8。
  conda create -n b2d_zoo python=3.8
  conda activate b2d_zoo
  ```
- **步骤 2：安装 CUDA Toolkit**
  ```
  conda install -c "nvidia/label/cuda-11.8.0" cuda-toolkit
  ```
- **步骤 3：安装 PyTorch**
  ```
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
  ```
- **步骤 4：设置环境变量**
  ```
  # 强烈建议使用 CUDA 11.8 和 GCC 9.4，否则可能遇到错误。
  export PATH=YOUR_GCC_PATH/bin:$PATH
  export CUDA_HOME=YOUR_CUDA_PATH/
  ```
- **步骤 5：安装 ninja 和 packaging**
  ```
  pip install ninja packaging
  ```
- **步骤 6：安装本仓库**

  ```
  pip install -v -e .
  ```

- **步骤 7：准备预训练权重。**
  创建 `ckpts` 目录：

  ```
  mkdir ckpts
  ```

  从 [Hugging Face](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/resnet50-19c8e357.pth)、[百度网盘](https://pan.baidu.com/s/1LlSrbYvghnv3lOlX1uLU5g?pwd=1234)或 PyTorch 官方网站下载 `resnet50-19c8e357.pth`。

  从 [Hugging Face](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/r101_dcn_fcos3d_pretrain.pth)、[百度网盘](https://pan.baidu.com/s/1o7owaQ5G66xqq2S0TldwXQ?pwd=1234)或 BEVFormer 官方仓库下载 `r101_dcn_fcos3d_pretrain.pth`。

- **步骤 8：安装用于闭环评测的 CARLA。**

  ```
  ## 如果已经安装 CARLA，可跳过下载和解压步骤。
  mkdir carla
  cd carla
  wget https://carla-releases.s3.us-east-005.backblazeb2.com/Linux/CARLA_0.9.15.tar.gz
  tar -xvf CARLA_0.9.15.tar.gz
  cd Import && wget https://carla-releases.s3.us-east-005.backblazeb2.com/Linux/AdditionalMaps_0.9.15.tar.gz
  cd .. && bash ImportAssets.sh
  export CARLA_ROOT=YOUR_CARLA_PATH

  ## 重要：否则 Python 环境无法找到 carla 包。
  echo "$CARLA_ROOT/PythonAPI/carla/dist/carla-0.9.15-py3.7-linux-x86_64.egg" >> YOUR_CONDA_PATH/envs/YOUR_CONDA_ENV_NAME/lib/python3.8/site-packages/carla.pth # Python 3.8 同样可用，请设置 YOUR_CONDA_PATH 和 YOUR_CONDA_ENV_NAME

  ```
