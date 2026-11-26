# generate_project/literature —— 生成线文献笔记

> 2026-11-13 从三处收拢而来：`machine_learning/report/01/02/03/07`、
> `pretrained/report-pretrained-lit.md`、`transfer_learning/report-tl-lit.md`、
> `Fundus-FlowMatching/papers/`、`literature/methods-quality-upgrade.md`。
> **这里只放外部文献的调研/综述**；我们自己的分析、规划、答辩材料仍在
> [`machine_learning/report/`](../machine_learning/report/00-README.md)。

## 索引

| 目录/文件 | 内容 | 来源 |
|---|---|---|
| `traditional-ml/01-literature-trad-ml.md` | 传统 ML 图像生成 18 法盘点 | 原 machine_learning/report |
| `traditional-ml/02-literature-fundus.md` | 眼底特异生成 + 新奇算法组合 | 同上 |
| `traditional-ml/03-literature-augment.md` | 小样本医学经典增广证据 | 同上 |
| `pretrained/07-pretrained-gen-models.md` | 预训练生成模型调研（两遍：通用→眼底） | 同上 |
| `pretrained/report-pretrained-lit.md` | 预训练/迁移学习文献归档 | 原 pretrained/ |
| `pretrained/report-tl-lit.md` | 迁移学习文献与定位 | 原 transfer_learning/ |
| `flow-matching/00-cfm-core.md` | 条件流匹配核心文献 | 原 Fundus-FlowMatching/papers/ |
| `flow-matching/01-lit-review-2026-10-23.md` | FM 方法族对比（OT-CFM/SI/SymmFlow 等） | 同上 |
| `flow-matching/reading-list.md` | CFM 阅读清单（奠基→推广→规模化→医学） | 同上 |
| `quality-upgrade.md` | loss 平台期后的质量提升方法清单 | 原 literature/ |

## 规则

- 新增外部文献笔记放这里，按主题归入 `traditional-ml/`、`pretrained/`、`flow-matching/`，或新建主题子目录。
- 原始 PDF 统一放 [`literature/pdf/generation/`](../../literature/pdf/generation/)，并在
  [`literature/links.md`](../../literature/links.md) 登记。
- 方法族的**实验记录**不在这里：去 `deep_learning/EXPERIMENTS.md`；
  实验结论去各 `results/<exp>/README.md`。
- 自己的分析/答辩/章节规划留在 `machine_learning/report/`（04/05/06）。
