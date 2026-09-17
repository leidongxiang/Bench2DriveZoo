# 运行时资产清单

本文档记录了 2026-09-15 在此工作区中验证过的运行时输入。大型二进制文件保留在 Git 仓库之外。

## CARLA

| 项目                   | 值                                                                 |
| ---------------------- | ------------------------------------------------------------------ |
| 版本                   | 0.9.15                                                             |
| 安装位置               | `/home/leidx/workspace/carla`                                      |
| 安装大小               | 约 44 GB                                                           |
| 基础归档               | `/home/leidx/workspace/carla/CARLA_0.9.15.tar.gz`                  |
| 基础归档大小           | 8,386,636,048 字节                                                 |
| Base archive SHA-256   | `7b2f432ce74b251593f95dcc8dee6d99ad9625c2a71a2d6d48f24d879de19ef7` |
| AdditionalMaps 归档    | `/home/leidx/workspace/carla/Import/AdditionalMaps_0.9.15.tar.gz`  |
| AdditionalMaps 大小    | 7,375,946,087 字节                                                 |
| AdditionalMaps SHA-256 | `49db78d14fef1f403f69fe1a13f1f1802f2111a6d98161826b2ae0d6dd96bba8` |

`ImportAssets.sh` 已成功完成。当前安装包含 Town11、Town12、Town13 和 Town15。

## Bench2Drive 评测器

| 项目 | 值                                           |
| ---- | -------------------------------------------- |
| 仓库 | `/home/leidx/workspace/projects/Bench2Drive` |
| 分支 | `0.0.4`                                      |
| 提交 | `7ec25d1c9f7522d923ce5f3420986cef1cb2d956`   |

记录此清单时，工作树处于干净状态。

## VAD 检查点（checkpoint）

| 项目    | 值                                                                                                              |
| ------- | --------------------------------------------------------------------------------------------------------------- |
| 文件    | `/home/leidx/workspace/weights/vad/vad_b2d_base.pth`                                                            |
| 大小    | 699,792,372 字节                                                                                                |
| SHA-256 | `0f2d48b5c6cdb06d0dffb21612791fe740f3f5c7273b3b5e78e1f19e4a527eab`                                              |
| 来源    | [Hugging Face 上的 Bench2DriveZoo](https://huggingface.co/rethinklab/Bench2DriveZoo/blob/main/vad_b2d_base.pth) |

摘要值与 Hugging Face 上发布的文件一致。
