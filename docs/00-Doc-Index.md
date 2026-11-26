# 工程文档导航（docs/ 唯一索引）

> 2026-11-13 v5：docs 按用途分四类。**新文档先归类，再回本文件登记**。
> 数字唯一来源 = `generate_project/*/EXPERIMENTS.md` + `eval_data/*.json` + `eval_scripts/human_scores.csv`。

**FundusGen** — 小样本眼底彩照生成研究：失效机理与医学语义评估，并以可控 severe 图生成完成 HR 分级数据扩充（TSTR）。论文第一、实用性第二。

---

## 一、四类文档

### 20-research —— 研究规范与权威口径
| 文档 | 内容 | 状态 |
|---|---|:--:|
| [14-Paper-Spine.md](20-research/14-Paper-Spine.md) | ⭐ 写作宪法：主张→证据、16 条口径、术语表 | ✅ |
| [15-Data-Documentation.md](20-research/15-Data-Documentation.md) | ⭐ 数据权威：数据池、卫生、泄漏清单 | ✅（一处口径待导师确认） |
| [01-Project-Overview.md](20-research/01-Project-Overview.md) | 项目需求、目标、定位 | ✅ |
| [02-Technical-Stack.md](20-research/02-Technical-Stack.md) | 技术栈、依赖、显存预算 | ⚠️ 2026-08-01 记录，待更新 |

### 30-evaluation —— 评估方法
| 文档 | 内容 | 状态 |
|---|---|:--:|
| [09-Score-Scheme-Design.md](30-evaluation/09-Score-Scheme-Design.md) | 六维门控评分的设计动机（公式本体在 `eval_scripts/score_scheme.py`） | ✅ |
| [13-Expert-Evaluation-Protocol.md](30-evaluation/13-Expert-Evaluation-Protocol.md) | 眼科医生盲评方案 | 🟡 草案 |
| [07-Model-Card-Template.md](30-evaluation/07-Model-Card-Template.md) | 模型档案模板 | ✅ 模板 |

### 40-writing —— 写作与答辩
| 文档 | 内容 | 状态 |
|---|---|:--:|
| [11-Paper-Readiness.md](40-writing/11-Paper-Readiness.md) | 论文证据家底、缺口、写作路线 | ✅ |
| [12-Literature-Survey-and-Positioning.md](40-writing/12-Literature-Survey-and-Positioning.md) | 30+ 篇调研与贡献划界 | ✅ |
| [16-Defense-Key-Points.md](40-writing/16-Defense-Key-Points.md) | 一页纸答辩口径 + 六环因果链 | ✅ 2026-11-08 |
| [figures/defense_roadmap.png](40-writing/figures/defense_roadmap.png) | 答辩配图 | — |

---

## 二、docs 之外的文档区

| 区域 | 放什么 | 入口 |
|---|---|---|
| 根目录 | 项目门面 | [README.md](../README.md) |
| `paper/` | 论文正文草稿、大纲、引用便签 | [paper/README.md](../paper/README.md) |
| `research-report/` | 总报告、论文送审稿、T3 技术报告 | [REPORT_DL.docx](../research-report/REPORT_DL.docx) |
| 方法本地 | 方法族 README + EXPERIMENTS | 各方法目录 |
| `literature/` | 共享 PDF 原件与链接 | [literature/README.md](../literature/README.md) |
| 各项目 literature | 生成线 / 分类线文献笔记 | `generate_project/literature/`、`classify_project/literature/` |

---

## 三、更新约定

- **数字**：只在两份 EXPERIMENTS.md / `eval_data/*.json` / `human_scores.csv` 维护；文档只引用不复制。
- **文档增删**：先放进对应分类目录，再回本索引登记；跨区文档（paper/report）只登记入口。
- **口径**：拿不准查 [14-Paper-Spine.md](20-research/14-Paper-Spine.md) 第三节；新口径先入表再使用。
