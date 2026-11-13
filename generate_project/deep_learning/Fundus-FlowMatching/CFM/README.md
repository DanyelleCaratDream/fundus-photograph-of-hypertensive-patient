# CFM —— 条件流匹配（Conditional Flow Matching，OT 线性路径）

> 本目录 = `Fundus-FlowMatching/` 下的**具体方法族**（对标 `Fundus-GAN/DCGAN`、
> `Fundus-GAN/WGAN-GP` 的组织方式）。本方法族回答：**用条件流匹配替代 DDPM 的噪声预测，
> 能否在同样的 193 张老师数据上得到更真实的 severe 眼底图。**

## 1. 方法标注（我们到底用的是哪一种 Flow Matching）

| 维度 | 我们的选择 | 说明 |
|:--|:--|:--|
| 框架 | **Conditional Flow Matching (CFM)** | Lipman et al., ICLR 2023（arXiv:2210.02747） |
| 概率路径 | **OT 线性插值路径** `x_t=(1−t)x_0+t·x_1` | 与 Rectified Flow（Liu et al., ICLR 2023）的线性路径同形 |
| 耦合方式 | **独立耦合**（x0、x1 各自采样，不做配对） | **不是** OT-CFM 的 minibatch 最优传输耦合（Tong et al., TMLR 2024） |
| 是否 reflow | **否** | 未做 Rectified Flow 的迭代拉直 |
| 条件注入 | **FiLM**（血管 mask，单通道） | 与 Diffusion 线同一 UNet，仅换训练目标 |
| 采样 | **Euler ODE**，50 NFE（评估）/100 NFE（交付） | 与 DDIM 同 NFE 口径对比 |
| 目标场 | 速度场 `v=x_1−x_0` | 不是噪声 ε、不是 score |

**一句话**：我们做的是 **CFM（线性/OT 路径、独立耦合、FiLM 条件、Euler 采样）**；
不包含 minibatch OT 配对、Schrödinger bridge、stochastic interpolants 的方差保持路径、reflow。
后续若要升级，优先试 OT 耦合（batch≥8 才有意义，我们 batch=1–2 时基本退化）。

## 2. 目录结构

```
CFM/
├── README.md                 # 本文件：方法标注 + 结构 + 结果
├── upstream/tta-flow/        # TTA-Flow 官方代码（CFM 应用，未入 git）
├── configs/                  # 3 套预设（单实验配置的唯一真源 = results/<exp>/config.json）
│   ├── cfm128.json
│   ├── cfm256.json
│   └── cfm256_lesion.json
├── train/train_cfm.py        # 训练入口（薄封装 → Fundus-Diffusion/ddpm/train.py --objective cfm）
├── infer/
│   ├── sample_cfm.py         # 纯生成（Euler NFE）
│   ├── sdedit_cfm.py         # 自精修（线性路径加噪 + Euler）
│   └── deliver_cfm.py        # 交付批次（SDEdit 0.8，分批 + 断点续跑）
├── tools/
│   ├── make_lesion_weights.py  # 渗出区域权重图（仅渗出；出血检测未实现）
│   ├── lesion_transplant.py    # 病灶块移植（羽化 alpha + LAB 均值匹配）
│   └── tta_hist_match.py       # TTA-Flow 轨迹对齐直方图匹配（推理期，无需重训）
├── data/
│   ├── conditions_combined_256/  # 256 版血管 mask（193 张）
│   └── lesion_weights_256/       # 渗出权重图（193 张；仅渗出，出血未加权）
├── models/                   # 本族全部模型权重（按实验名命名）
│   ├── cfm128_final_model.pth
│   └── cfm256_final_model.pth
├── results/                  # 每个子目录 = 一个实验，均带 README（索引见 results/README.md）
│   ├── cfm128/ cfm128_align/ cfm128_text/ cfm128_notime/
│   ├── cfm128_featA/ cfm128_featC/          # 128px 六方法消融
│   ├── cfm128_hrsevere_pilot/               # 61 张纯 severe（T0 在此）
│   ├── cfm256/ cfm256_lesion/               # 256 原生 / 渗出加权（仅探索）
│   └── a_domain_clean_cfm128/               # A_clean 预训练（T1 起点）
└── judgment/                 # 评估/对照图（同槽对比、移植对照、交付总览）
```

> 命名约定（2026-10-23）：**模型权重统一放族内 `models/`**，用实验名区分；
> **生成结果放 `results/<实验名>/`**。训练脚本的 `--output_dir` 仍写到 results，
> 训练结束后把 `results/<实验名>/models/*.pth` 移到族 `models/` 并按实验名重命名。

**为什么训练器不在本目录**：CFM 与 Diffusion 共用同一套 FiLM 条件 UNet、数据管线与
温度/EMA 逻辑；复制一份会分叉。`train/train_cfm.py` 是指定 `--objective cfm` 的入口，
真正的实现见 `../../Fundus-Diffusion/ddpm/train.py`（`cfm_path` / `cfm_predict_x1` / `euler_sample`）。

## 3. 三套实验

| 实验 | 初始化 | 数据/条件 | 轮数 | 结果 |
|:--|:--|:--|--:|:--|
| **cfm128** | film_l1lpips final（A 域最佳） | combined_sq128 / mask128 | 320（780→1100） | loss 0.90→0.12–0.14；8/8 结构完整、色彩比 D3 近真实，血管偏软 |
| **cfm256** | cfm128 final | combined_sq256 / mask256 | 320（1100→1420） | loss 0.100；**作者目检 97/100**；锐度 0.00295≈D3 0.00313 |
| **cfm256_lesion** | cfm256 final | 同上 + **渗出**权重 λ=8（仅渗出，出血未加权） | 150（1420→1570） | ⚠️ 结果作废（方法证据）：受 3× 尺度 + 增强错位两缺陷影响；仅探索性记录。修正版见 `cfm256_clean_exudate` |
| **cfm128_align**（消融） | film_l1lpips final | 同 cfm128，但时间轴反转对齐 DDPM | 320（780→1100） | 完成：FID 151.8（vs 基线 178.9，−15%）；时间语义对齐有效 |

> **时间轴问题（2026-10-23 发现）**：DDPM 的 t=0 是干净图、999 是噪声；CFM 的 t=0 是噪声。
> 原实现把 CFM 的 t 直接映射到 0..999，等于让模型“倒着学”时间条件（首轮 loss 0.904≈预测零速度）。
> `--cfm_time_align` 改为 `idx=(1−t)·T`；采样端（generate/sdedit/deliver）会从 checkpoint
> 的 `args.cfm_time_align` 自动读取同一约定。

## 4. 结果摘要（B 域三模型，60 张/模型，severe 参照 72 张）

| 指标 | D3 | CFM@128 | **CFM@256** |
|:--|--:|--:|--:|
| FID ↓（训练分布拟合口径*） | 222.69 | 178.87 | **121.84** |
| KID ↓（2026-11-06 无偏重算，mean±std） | 0.118±0.010 | 0.158±0.007 | **0.084±0.008** |
| 颜色均值距离 ↓ | 0.2996 | 0.0782 | **0.0345** |
| BRISQUE ↓（真实 11.02） | 42.83 | 38.00 | **13.21** |
| 疑似出血像素占比 ↑† | **0.754** | 0.320 | 0.204 |

\* 72 张参照与生成器训练池同源（63/72 内容相同、61 张像素级一致）→ FID 衡量训练分布拟合，非留出泛化。
† 颜色阈值启发式代理指标（R<0.42 且 R−G>0.04 且 R−B>0.04），未经医学标注验证；旧称"出血保留率"。

**结论**：CFM@256 在真实性/分布上全面领先；D3 在疑似病灶像素占比上更强——真实性与病理保真的取舍。
自精修在 256 上有效（SDEdit 0.8：锐度 +9.5%、色彩不变），在 128 上几乎无增益。

> **⚠️ 2026-11-06 训练缺陷披露**：①加权损失分母只计单通道 → 加权项为预期 3×（λ=0 也不等于普通 L1）；
> ②图像随机翻转/旋转时权重图与血管 mask 未跟随 → 权重施加在错位区域。cfm256_lesion 的
> +36%/+24% 与 FID 115.22 **仅作探索性记录，不构成方法证据**；所有条件模型受 ② 影响。
> 修复版代码 + 诊断见 `research-report/audit/advisor_20261106/code/`；修正两臂 preset 为
> `cfm256_clean_ctrl` / `cfm256_clean_exudate`（从零、同步增强，待导师确认后运行）。

## 5. 运行

```bash
# 训练（示例：cfm256_lesion；实际路径以 configs/*.json 为准）
python train/train_cfm.py --preset cfm256_lesion

# 生成 8 张判定图
python infer/sample_cfm.py --ckpt models/cfm256_final_model.pth \
    --num 8 --seed 42 --steps 50 --out judgment/cfm256_8

# 自精修
python infer/sdedit_cfm.py --ckpt models/cfm256_final_model.pth \
    --base judgment/cfm256_8/singles --t_start 0.8 --out judgment/cfm256_s08

# 交付批次（60 张，SDEdit 0.8）
python infer/deliver_cfm.py --base <60 张底图目录> --out judgment/delivery_s08
```

## 6. 纪律

- 采样 NFE 与 DDIM 对齐（50 评估 / 100 交付），不许拿 1000 步打 50 步；
- 生成器只用 train，不碰 val/test；
- 验收次序：**专家目检 > 分类器指标**；
- 温度 ≤70°C（训练器内置每 25 步守护）。


## 7. 判图目录索引（`judgment/`，不入 git）

| 子目录 | 内容 | 对应 |
|---|---|---|
| `D5_cfm256_ema/` | CFM@256 目检 8 张 | F3 / 执行记录 18 |
| `F2_cfm_sr/` | CFM@128 + Real-ESRGAN 超分对照 | F2 / 执行记录 16 |
| `F3_cfm256_sdedit/` | CFM@256 自精修（t=0.8/0.7） | 执行记录 19 |
| `cfm128_hrsevere_pilot_8*/` | T0 各检查点 8 张目检（含 step9600/15000 raw/ema） | 执行记录 22 |
| `e2/ e3/ e4/` | 四 seed 稳定性 / 20,010 步 / 30,000 步 | EX-026 关联 |
| `scan30k/` | 15k–30k 扫描、20k vs 28,500、与真实对比 | 记录 25 |
| `tta_hm/` | 直方图匹配负结果（过曝） | 执行记录 21 |
| `weight_misalign_demo.png`、`pipeline_alignment_check.png` | 增强错位/管线对齐诊断图 | 2026-11-06 自查 |

判图含真实患者图，已在 `.gitignore` 中排除；报告图由 `research-report/build/_make_*` 重新生成。
