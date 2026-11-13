# 工程文档导航（docs/ 唯一索引）

> 2026-11-13 v5：docs 按用途分四类。**新文档先归类，再回本文件登记**。
> 会话入口 = `../PROJECT_STATE.md`；路径地图 = `../PROJECT_MAP.md`。
> 数字唯一来源 = `generate_project/*/EXPERIMENTS.md` + `eval_data/*.json` + `eval/human_scores.csv`。

**FundusGen** — 小样本眼底彩照生成研究：失效机理与医学语义评估，并以可控 severe 图生成完成 HR 分级数据扩充（TSTR）。论文第一、实用性第二。

---

## 一、四类文档

### 10-management —— 项目管理与操作
| 文档 | 内容 | 状态 |
|---|---|:--:|
| [06-Execution-Plan.md](10-management/06-Execution-Plan.md) | Phase A–D + 论文线路线图 | ✅ |
| [08-Work-Guide.md](10-management/08-Work-Guide.md) | 常用命令 + 已知坑 | ⚠️ 正文 2026-08-02 口径，新命令待补 |
| [17-Directory-Standard.md](10-management/17-Directory-Standard.md) | 目录骨架、命名、脚本落点 | ✅ 2026-11-13 |
| [18-Knowledge-Maintenance.md](10-management/18-Knowledge-Maintenance.md) | 四层记忆、入口预算、记录判据、Dreaming 清单 | ✅ 2026-11-13 |
| [19-Progress-Log.md](10-management/19-Progress-Log.md) | 历史里程碑（append-only，不参与加载） | ✅ 2026-11-13 |

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
| [09-Score-Scheme-Design.md](30-evaluation/09-Score-Scheme-Design.md) | 六维门控评分的设计动机（公式本体在 `eval/score_scheme.py`） | ✅ |
| [13-Expert-Evaluation-Protocol.md](30-evaluation/13-Expert-Evaluation-Protocol.md) | 眼科医生盲评方案 | 🟡 草案 |
| [07-Model-Card-Template.md](30-evaluation/07-Model-Card-Template.md) | 模型档案模板 | ✅ 模板 |

### 40-writing —— 写作与答辩
| 文档 | 内容 | 状态 |
|---|---|:--:|
| [11-Paper-Readiness.md](40-writing/11-Paper-Readiness.md) | 论文证据家底、缺口、写作路线 | ✅ |
| [12-Literature-Survey-and-Positioning.md](40-writing/12-Literature-Survey-and-Positioning.md) | 30+ 篇调研与贡献划界 | ✅ |
| [16-Defense-Key-Points.md](40-writing/16-Defense-Key-Points.md) | 一页纸答辩口径 + 六环因果链 | ✅ 2026-11-08 |
| [figures/defense_roadmap.png](40-writing/figures/defense_roadmap.png) | 答辩配图 | — |

> **已归档**：`03`/`04`/`05`/`10` → `_archive/docs/`（历史快照，不再维护）。

---

## 二、docs 之外的文档区

| 区域 | 放什么 | 入口 |
|---|---|---|
| 根目录 | 会话入口、路径地图、门面、协作规则 | `PROJECT_STATE.md` / `PROJECT_MAP.md` / `README.md` / `CLAUDE.md` |
| `paper/` | 论文正文草稿、大纲、引用便签 | [paper/README.md](../paper/README.md) |
| `research-report/` | 交付 docx、构建脚本、审计证据、图 | [research-report/README.md](../research-report/README.md) |
| 方法本地 | 方法族 README + EXPERIMENTS | 各方法目录 |
| `literature/` | 共享 PDF 原件与链接 | [literature/README.md](../literature/README.md) |
| 各项目 literature | 生成线 / 分类线文献笔记 | `generate_project/literature/`、`classify_project/literature/` |

关键路径（数据池、结果、指标、判图）→ 看 [PROJECT_MAP.md](../PROJECT_MAP.md)，本文件不再重复。

---

## 三、更新约定

- **数字**：只在两份 EXPERIMENTS.md / `eval_data/*.json` / `human_scores.csv` 维护；文档只引用不复制。
- **每轮工作结束**：更新 `PROJECT_STATE.md`。
- **文档增删**：先放进对应分类目录，再回本索引登记；跨区文档（paper/report）只登记入口。
- **口径**：拿不准查 [14-Paper-Spine.md](20-research/14-Paper-Spine.md) 第三节；新口径先入表再使用。
