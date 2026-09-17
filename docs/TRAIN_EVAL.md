# 模型训练与评测

可以使用以下命令训练和验证 [BEVFormer](https://github.com/fundamentalvision/BEVFormer)、[UniAD](https://github.com/OpenDriveLab/UniAD) 和 [VAD](https://github.com/hustvl/VAD)。

请在容器中运行这些命令（`docker compose run --rm bench2drive-zoo bash`）。`$B2D_OUTPUT` 挂载在仓库之外。BEVFormer 和 VAD 需要传入 `--work-dir`；UniAD 的封装脚本会自动使用 `$B2D_OUTPUT`。

## BEVFormer

### 训练

```bash
# 训练 BEVFormer base
./adzoo/bevformer/dist_train.sh ./adzoo/bevformer/configs/bevformer/bevformer_base_b2d.py 8 --work-dir "$B2D_OUTPUT/checkpoints/bevformer/base"
# 训练 BEVFormer tiny
./adzoo/bevformer/dist_train.sh ./adzoo/bevformer/configs/bevformer/bevformer_tiny_b2d.py 8 --work-dir "$B2D_OUTPUT/checkpoints/bevformer/tiny"
```

### 开环评测

```bash
# 评测 BEVFormer base
./adzoo/bevformer/dist_test.sh ./adzoo/bevformer/configs/bevformer/bevformer_base_b2d.py ./ckpts/bevformer_base_b2d.pth 8
# 评测 BEVFormer tiny
./adzoo/bevformer/dist_test.sh ./adzoo/bevformer/configs/bevformer/bevformer_tiny_b2d.py ./ckpts/bevformer_tiny_b2d.pth 8
```

## UniAD

### 第一阶段训练

```bash
# 训练 UniAD base
./adzoo/uniad/uniad_dist_train.sh  ./adzoo/uniad/configs/stage1_track_map/base_track_map_b2d.py 8
# 训练 UniAD tiny
./adzoo/uniad/uniad_dist_train.sh  ./adzoo/uniad/configs/stage1_track_map/tiny_track_map_b2d.py 8
```

### 第二阶段训练

```bash
# 训练 UniAD base
./adzoo/uniad/uniad_dist_train.sh  ./adzoo/uniad/configs/stage2_e2e/base_e2e_b2d.py 8
# 训练 UniAD tiny
./adzoo/uniad/uniad_dist_train.sh  ./adzoo/uniad/configs/stage2_e2e/tiny_e2e_b2d.py 8
```

### 开环评测

```bash
# 评测 UniAD base
./adzoo/uniad/uniad_dist_eval.sh ./adzoo/uniad/configs/stage2_e2e/base_e2e_b2d.py ./ckpts/uniad_base_b2d.pth 8
# 评测 UniAD tiny
./adzoo/uniad/uniad_dist_eval.sh ./adzoo/uniad/configs/stage2_e2e/tiny_e2e_b2d.py ./ckpts/uniad_tiny_b2d.pth 8
```

## VAD

### 训练

```bash
./adzoo/vad/dist_train.sh ./adzoo/vad/configs/VAD/VAD_base_e2e_b2d.py 8 --work-dir "$B2D_OUTPUT/checkpoints/vad/base"
```

### 开环评测

```bash
./adzoo/vad/dist_test.sh ./adzoo/vad/configs/VAD/VAD_base_e2e_b2d.py ./ckpts/vad_b2d_base.pth 8
```

**注意**：UniAD 和 VAD 计算 Planning L2 时采用不同定义。UniAD 计算各时间点（0.5 s、1.0 s、1.5 s……）的 L2，而 VAD 计算各时间区间（0-0.5 s、0-1.0 s、0-1.5 s……）内的平均值。代码保留了原始计算逻辑，但报告结果时会将 UniAD 的 Planning L2 转换为 VAD 的定义。
