<h2 align="center">
  <img src="assets/bench2drive.jpg" style="width: 100%; height: auto;">
</h2>
<h2 align="center">
Bench2DriveZoo（以 Think2Drive 作为教师模型）
</h2>
<h2 align="center">
  <img src="assets/bench2drivezoo.png" style="width: 100%; height: auto;">
</h2>

# 项目简介

- 本仓库包含 [Bench2Drive](https://github.com/Thinklab-SJTU/Bench2Drive) 中 [BEVFormer](https://github.com/fundamentalvision/BEVFormer)、[UniAD](https://github.com/OpenDriveLab/UniAD) 和 [VAD](https://github.com/hustvl/VAD) 的训练、开环评测与闭环评测代码。**所有模型均为世界模型强化学习教师模型 [Think2Drive](https://arxiv.org/abs/2402.16720) 的学生模型。**
- 我们将 UniAD 和 VAD 的多个依赖（包括 mmcv、mmseg、mmdet 和 mmdet3d v0.17.1）合并为一个库，因此可以支持较新的 PyTorch，并可使用 DeepSpeed 等高级框架进行加速。
- 使用 `git checkout tcp/admlp` 可获取对应的训练与评测代码。
- **若要计算平顺性和效率指标**，请在自己的 team code agent 中实现与 `self.metric_info` 相关的代码。这两个指标需要以 20 Hz 记录每一步的自车状态。若要节省磁盘空间，可以注释保存传感器数据的相关代码。

# 引用 <a name="citation"></a>

如果本项目对您的研究有帮助，请考虑引用以下论文：

```bibtex
@article{jia2024bench,
  title={Bench2Drive: Towards Multi-Ability Benchmarking of Closed-Loop End-To-End Autonomous Driving},
  author={Xiaosong Jia and Zhenjie Yang and Qifeng Li and Zhiyuan Zhang and Junchi Yan},
  journal={arXiv preprint arXiv:2406.03877},
  year={2024}
}

@inproceedings{li2024think,
  title={Think2Drive: Efficient Reinforcement Learning by Thinking in Latent World Model for Quasi-Realistic Autonomous Driving (in CARLA-v2)},
  author={Qifeng Li and Xiaosong Jia and Shaobo Wang and Junchi Yan},
  booktitle={ECCV},
  year={2024}
}
```

# 快速开始

- [Docker 配置与工作区布局](docs/DOCKER.md)
- [安装参考](docs/INSTALL.md)
- [准备数据集](docs/DATA_PREP.md)
- [训练与开环评测](docs/TRAIN_EVAL.md)
- [在 CARLA 中进行闭环评测](docs/EVAL_IN_CARLA.md)
- [将 NuScenes 代码迁移至 Bench2Drive](docs/CONVERT_GUIDE.md)

# 结果与预训练模型

## UniAD 与 VAD

根据 2024 年 8 月 27 日发布的[公告](https://github.com/Thinklab-SJTU/Bench2Drive)，项目修复了若干问题并调整了评测协议，因此旧版闭环性能数据已弃用。

|    方法    | L2 (m) 2s |      驾驶得分       |     成功率（%）     |                          配置                          |                                                                                下载                                                                                |            评测 JSON             |
| :--------: | :-------: | :-----------------: | :-----------------: | :----------------------------------------------------: | :----------------------------------------------------------------------------------------------------------------------------------------------------------------: | :------------------------------: |
| UniAD-Tiny |   0.80    | 40.73（旧版 32.00） | 13.18（旧版 9.54）  | [配置](adzoo/uniad/configs/stage2_e2e/base_e2e_b2d.py) | [Hugging Face](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/uniad_tiny_b2d.pth)/[百度网盘](https://pan.baidu.com/s/1psr7AKYHD7CitZ30Bz-9sA?pwd=1234) | [新版](analysis/UniAD-Tiny.json) |
| UniAD-Base |   0.73    | 45.81（旧版 37.72） | 16.36（旧版 9.54）  | [配置](adzoo/uniad/configs/stage2_e2e/tiny_e2e_b2d.py) | [Hugging Face](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/uniad_base_b2d.pth)/[百度网盘](https://pan.baidu.com/s/11p9IUGqTax1f4W_qsdLCRw?pwd=1234) | [新版](analysis/UniAD-Base.json) |
|    VAD     |   0.91    | 42.35（旧版 39.42） | 15.00（旧版 10.00） |   [配置](adzoo/vad/configs/VAD/VAD_base_e2e_b2d.py)    |  [Hugging Face](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/vad_b2d_base.pth)/[百度网盘](https://pan.baidu.com/s/1rK7Z_D-JsA7kBJmEUcMMyg?pwd=1234)  |    [新版](analysis/VAD.json)     |

## BEVFormer

|      方法      | mAP  | NDS  |                              配置                               |                                                                                  下载                                                                                  |
| :------------: | :--: | :--: | :-------------------------------------------------------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| BEVFormer-Tiny | 0.37 | 0.43 | [配置](adzoo/bevformer/configs/bevformer/bevformer_tiny_b2d.py) | [Hugging Face](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/bevformer_tiny_b2d.pth)/[百度网盘](https://pan.baidu.com/s/1TWMs9YgKYm2DF5YfXF8i3g?pwd=1234) |
| BEVFormer-Base | 0.63 | 0.67 | [配置](adzoo/bevformer/configs/bevformer/bevformer_base_b2d.py) | [Hugging Face](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/bevformer_base_b2d.pth)/[百度网盘](https://pan.baidu.com/s/1Y4VkE1gc8BU0zJ4z2fmIkQ?pwd=1234) |

# 失败案例分析

我们在[这里](analysis/analysis.md)提供了 TCP-traj、UniAD-Base 和 VAD-Base 的可视化视频与定性分析。您可以参考 https://github.com/Thinklab-SJTU/Bench2DriveZoo/blob/uniad/vad/team_code/vad_b2d_agent_visualize.py 编写自己的可视化代码。

# 相关资源

- [Bench2Drive](https://github.com/Thinklab-SJTU/Bench2Drive)
- [BEVFormer](https://github.com/fundamentalvision/BEVFormer)
- [UniAD](https://github.com/OpenDriveLab/UniAD)
- [VAD](https://github.com/hustvl/VAD)
