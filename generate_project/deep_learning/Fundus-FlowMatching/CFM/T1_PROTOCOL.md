# T1 迁移实验协议与验收清单

> 登记：`EXPERIMENTS.md` DL-EX-026｜上游：A_clean(258) 780 轮预训练（`a_domain_clean_cfm128`）

## 1. 设计（预注册，导师 2026-11-11 批准）

| 项目 | T0（冻结，不重跑训练） | T1 |
|---|---|---|
| 初始化 | 随机 | A_clean `final_model.pth` 的 **raw** 权重 |
| 数据 / 分辨率 | 61 张 HR severe / 128px / batch2 | 同左 |
| 轮数 | 667 × 30 = **20,010 步** | 667 × 30 = **20,010 步** |
| 损失 | L1 + LPIPS 0.1 + color 0.01，seed 42 | 同左 |
| 生成权重 | raw | raw |
| 检查点 | `results/cfm128_hrsevere_pilot/models/checkpoint_epoch_000667.pth` | `results/cfm128_hrsevere_t1_ac/models/final_model.pth` |

**唯一变量 = 初始化来源。** 优化器全新、EMA 从加载权重重建（`--init_weights_only` 行为）。

## 2. 执行

```bash
cd generate_project/deep_learning/Fundus-FlowMatching/CFM

bash tools/run_t1.sh --dry-run   # 先看命令
bash tools/run_t1.sh             # 训练 667 轮 → 验收 → 生成 32 张
```

产物：

| 内容 | 路径 |
|---|---|
| T1 训练 | `results/cfm128_hrsevere_t1_ac/`（models / logs / images） |
| T1 生成 32 张 | `judgment/t1/cfm128_hrsevere_t1_ac_raw_seed{S}/singles/` |
| T0 生成 32 张（**已存在，复用**） | `judgment/e3/cfm128_hrsevere_20000_raw_seed{S}/singles/` |
| 指标 | `judgment/t1/metrics_t1.json` |
| 拼图 | `judgment/t1/T0_vs_T1_sheet.png`、`T0_vs_T1_seed{S}.png` |

seed 组：`42 / 1042 / 2042 / 3042`；条件 = `conditions_hrsevere_61_128` 排序前 8 张（1:1）。

## 3. 验收清单

### 3.1 A_clean 预训练（780 轮）

```bash
python tools/verify_training.py --run-dir results/a_domain_clean_cfm128 \
    --expect-epochs 780 --steps-per-epoch 51
```

- [ ] final epoch = 780
- [ ] 步数：`global_step` 与 39,780 对比；续训未恢复时按 epoch×51 核算，**如实记录偏差**
- [ ] raw strict 加载（无 missing / unexpected）
- [ ] `training.log` 覆盖到末轮、无 NaN、无中断标记
- [ ] 无 `checkpoint_INTERRUPTED.pth`

### 3.2 T1 训练（667 轮）

```bash
python tools/verify_training.py --run-dir results/cfm128_hrsevere_t1_ac \
    --expect-epochs 667 --steps-per-epoch 30
```

- [ ] 同上五项，期望步数 20,010
- [ ] 日志首行确认 `[init_weights_only] strict=True 加载成功`
- [ ] 日志确认 `epoch=0、优化器全新、EMA 已从加载权重重建`

### 3.3 生成完整性

- [ ] 4 个 seed 目录各 8 张，共 32 张
- [ ] 与 T0 同 seed 图片尺寸 / 条件顺序一致（拼图逐列对齐）
- [ ] 指标脚本正常产出（无缺失目录 WARN）

## 4. 人工评分（五维分开，不打综合分）

对每个 seed 的 T0/T1 各 8 张，五维**分别** 1–5 分：

| 维度 | 说明 | T0 均分 | T1 均分 | 备注 |
|---|---|---|---|---|
| 整体外观 | 是否像眼底彩照（光照、色调、边界） | | | |
| 血管细节 | 血管走行连续性、分支清晰度 | | | |
| 视盘结构 | 视盘位置、边界、亮度是否合理 | | | |
| 伪影 | 断裂、糊块、重复纹理、边框伪影 | | | |
| 多样性 | 同条件跨 seed、跨条件的差异是否足够 | | | |

评分表：`judgment/t1/评分表_T1.md`（跑完拼图后按 seed 填）。

**判定口径**：T1 在「血管细节 / 视盘结构」至少一项稳定优于 T0，且整体外观不劣化，才记为迁移有效；单一维度波动不作为证据。客观指标（梯度能量 / 中心外环比 / 多样性）只作辅助，不替代人工判读。

> ⚠️ **指标口径**：`tools/pilot_metrics.py` 的绝对值与 E2/E3 旧记录（梯度能量 0.011–0.013、中心外环 2.8–3.1）**不完全同源**——旧脚本已丢失，本脚本按文档描述重写。**只用于 T0/T1 之间的内部对比，不得与旧记录横向比较**；如需复现旧口径，先找回原脚本。
