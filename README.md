# FundusGen — 小样本眼底彩照生成研究

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)]()
[![PyTorch](https://img.shields.io/badge/PyTorch-2.11+-ee4c2c.svg)]()
[![CUDA](https://img.shields.io/badge/CUDA-13.0+-76b900.svg)]()

> **在约 300 张的小样本设定下（原 330，现存 299，清洗后 258），系统研究眼底彩照生成模型的失效机理（failure mechanisms）与医学语义评估（evaluation），
> 并将可控的 severe 图生成用于 DR 分级数据扩充。**
> 8GB VRAM 笔记本，VAE → GAN → Diffusion 三代模型完整实验记录 + 传统 ML 基线同口径横评。

---

## 🔬 研究要点

1. **失效机理链条**：小样本眼底生成在三代模型上各有死因——VAE 的像素级 MSE 造成模糊天花板（blur ceiling）；
   GAN 的判别器小样本过拟合；扩散模型的 **MSE 溶解病灶**（lesion dissolution）：暗背景摊薄亮病灶梯度，
   出血保留率 0.254（MSE） vs **1.137**（L1+LPIPS），且在完全不同的架构（Palette）上复现 → 是损失函数的天性而非模型缺陷。
   配套 `--loss_type` 开关使该消融可一键复现。
2. **评估方法论**：两层指标（通用分布层 + 眼底专用层）与六维门控综合评分（six-dimension gated composite score）。
   关键现象：**通用指标看不出医学语义差异**——FID 相近的两个模型，出血保留率相差 4.5 倍。
3. **同口径多方法横评**：11 个方法（5 传统 ML + 6 深度）在同一套指标与评分下对比——文献调研确认这是一个没人做过的空白。
4. **数据量假说（进行中）**：76 张 @256 训练 loss 正常收敛但生成全糊（"拟合 ≠ 生成"）；
   D1/D2 单变量对照实验验证数据量是否为瓶颈。

## 📍 当前状态

> ⚠️ 本页只保留项目定位；实时进展以 `EXPERIMENTS.md` 与 `paper/` 为准。

- **生成器主线**：A_clean(258) CFM 预训练进行中 → 完成后跑 T1（A_clean 初始化 vs T0），见 `generate_project/deep_learning/EXPERIMENTS.md`。
- **分类器主线**：DL-EX-027 六个 arm 的 pilot 已预注册，等 GPU 空闲先跑 A0–A2。
- 实验登记表 [EXPERIMENTS.md](generate_project/deep_learning/EXPERIMENTS.md)（DL-EX-001~027）为**全部数字的唯一来源**。
- 论文路线：A《小样本眼底生成：失效机理与评估方法》先行，B（+下游验证）叠加，见 [docs/20-research/14-Paper-Spine.md](docs/20-research/14-Paper-Spine.md)。

### ⚖️ 分数口径声明（勿混用）

本项目有两套 0-100 分，**含义不同，不可混排**：

| 尺度 | 范围 | 说明 |
|:--|:--|:--|
| 人工分（human score） | 单人目测校准 | film_l1lpips 87.5 / film 85 / base_cj 75 / cond 70 / dcgan 20 / vae 10（`eval_scripts/human_scores.csv`，N=6 局限） |
| 六维门控总分（gated composite） | 11 模型可比（现版） | poisson 80.8 / retinex 72.5 / film_l1lpips **45.2** / film 37.2 / cond 35.0 / base_cj 34.5 / vae 26.6 / dcgan 12.9（`eval_data/_scores.json`；⚠️ min-max 相对分，模型库扩大会整体平移） |

---

## 📁 项目结构

```
AI_Model_Project_for_Fundus_Color_Images/
├── generate_project/               # 生成方法库（按方法族分区）
│   ├── deep_learning/              #   深度学习（Phase A/B 完成；Phase D 主力进行中）
│   │   ├── EXPERIMENTS.md          #     ⭐ 实验登记表（所有数字的唯一来源）
│   │   ├── Fundus-VAE/             #     VAE 系列（vanilla / beta）
│   │   ├── Fundus-GAN/             #     GAN 系列（DCGAN / WGAN-GP / StyleGAN2-ADA）
│   │   └── Fundus-Diffusion/       #     Diffusion 系列 ⭐（DDPM + FiLM + L1/LPIPS）
│   ├── machine_learning/           #   传统 ML / OpenCV（PCA / GMM / 补丁 / 泊松 / Retinex）
│   ├── pretrained/                 #   预训练路线（调研报告 07：SD-LoRA 主路线）
│   └── transfer_learning/          #   迁移学习（文献归档）
├── classify_project/               # DR 分级分类器（Phase D：TSTR 验证方案）
├── eval_scripts/                           # 评估体系（通用层 / 专用层 / 综合评分 / 可视化）
├── eval_data/                      # 评估数据（real 快照 + 各模型生成图 + *_metrics.json）
├── fundus/                         # 数据集（git 排除）：A 域网络图 + 老师 HRSG 数据集 + 卫生工具
├── literature/                     # 共享文献原件（pdf/{generation,classifier,methodology,other} + links）
├── docs/                           # 规范文档（00 索引 + 20-research/30-evaluation/40-writing）
├── research-report/                # 交付物：总报告、论文送审稿、T3 技术报告
└── README.md                       # 本文件
```

## 🗺️ 文档地图

| 想了解 | 去哪 |
|:--|:--|
| 文档总索引 | [docs/00-Doc-Index.md](docs/00-Doc-Index.md) |
| 论文主张与口径（写作宪法） | [docs/20-research/14-Paper-Spine.md](docs/20-research/14-Paper-Spine.md) |
| 数据集与数据卫生 | [docs/20-research/15-Data-Documentation.md](docs/20-research/15-Data-Documentation.md) |
| 实验数字 | [EXPERIMENTS.md](generate_project/deep_learning/EXPERIMENTS.md)（深度）＋ [EXPERIMENTS.md](generate_project/machine_learning/EXPERIMENTS.md)（传统） |
| 数据池索引 | [fundus/README.md](fundus/README.md) |
| 文献定位（哪些贡献已被做过） | [docs/40-writing/12-Literature-Survey-and-Positioning.md](docs/40-writing/12-Literature-Survey-and-Positioning.md) |

## 🚀 快速开始

```bash
# 环境
pip install torch torchvision numpy Pillow matplotlib lpips pytorch-fid

# 采样（CFM@256 示例；需 CFM/models/cfm256_final_model.pth 存在）
cd generate_project/deep_learning/Fundus-FlowMatching/CFM
python infer/sample_cfm.py --ckpt models/cfm256_final_model.pth --num 8 --seed 42 --steps 50 --out judgment/cfm256_8

# 评估与六维打分（回到项目根目录）
python eval_scripts/score_scheme.py --scorecard
```

训练/续训命令见各方法目录 README 与 `EXPERIMENTS.md`；本公开仓库只保留可复现所需材料。

## 📖 科研报告

- [`REPORT_DL.docx`](research-report/REPORT_DL.docx) —— 深度学习路线全记录，实验日志体裁（含第 7 章 2026-10-25～11-11 增量）
- [`论文送审稿`](research-report/送审_论文修订稿_20261125/论文全文_20261125.md)、[`T3 技术报告`](research-report/T3_随机性排查_20261117.md)

> 报告为**实验日志体裁**；论文按 claim → evidence 重组，骨架见 [docs/20-research/14-Paper-Spine.md](docs/20-research/14-Paper-Spine.md)。

---

## 📜 许可证

本项目代码仅供学术研究和教育用途。数据集版权归提供方所有。

## 🙏 致谢

感谢指导老师提供的眼底彩照数据集（A 域网络图 + HRSG 分级数据集）与研究方向的指导。
