# PROJECT_MAP —— 项目路径地图

> 两个入口分工：**`PROJECT_STATE.md` = 现在在哪、下一步做什么**；**本文件 = 东西在哪**。
> 目录规则见 [docs/10-management/17-Directory-Standard.md](docs/10-management/17-Directory-Standard.md)；文档总目录见 [docs/00-Doc-Index.md](docs/00-Doc-Index.md)。

## 一、我要找什么 → 去哪

| 我要找… | 去哪 |
|---|---|
| 现在做到哪、下一步 | `PROJECT_STATE.md` |
| 某个实验的数字 / 登记号 | `generate_project/deep_learning/EXPERIMENTS.md`（DL-EX-xxx）、`generate_project/machine_learning/EXPERIMENTS.md`（EX-xxx） |
| 某个生成实验的代码/配置/日志/权重 | `generate_project/deep_learning/Fundus-FlowMatching/CFM/results/<exp>/`（索引：`results/README.md`） |
| 训练入口 / 预设 | `generate_project/deep_learning/Fundus-FlowMatching/CFM/train/train_cfm.py`（预设见 `CFM/README.md`） |
| 当前可跑命令 | `PROJECT_STATE.md` §4（历史命令见 `docs/10-management/08-Work-Guide.md`，正文口径待补） |
| DDPM / D 线历史实验产物 | `generate_project/deep_learning/Fundus-Diffusion/ddpm/`（`results_*/` 为 legacy 命名） |
| 生成样本（评估用） | `eval_data/<exp>/singles/` |
| 指标 JSON / 六维分 | `eval_data/<exp>_{metrics,fundus_metrics,diversity}.json` + `eval_data/_scores.json` |
| 人工判图 / 对照图 | 各方法族 `judgment*/`（CFM：`CFM/judgment/`；DDPM：`ddpm/judgment_<日期>/`；均不入 git） |
| 评估脚本 / 评分体系 | `eval/`（`README.md` 有用法） |
| 数据集 / 数据池 / 冻结名单 | `fundus/`（索引：`fundus/README.md`；口径：`docs/20-research/15-Data-Documentation.md`） |
| 数据卫生 / A 域审计证据 | `research-report/audit/a_domain_20261111/`（索引：`research-report/audit/README.md`） |
| 导师评审答复与证据图 | `research-report/audit/advisor_20261106/` |
| 研究报告（交付物） | `research-report/REPORT_DL.docx`（v1）、`REPORT_DL_v2.docx`（v2）、`REPORT_DL_后续.docx`（教师附件） |
| 报告构建脚本 | `research-report/build/` |
| 给老师的进度稿 | `research-report/汇报_进度_20261111.md` |
| 论文正文 | `paper/`（写作宪法：`docs/20-research/14-Paper-Spine.md`） |
| 文献 PDF / 链接 | `literature/`（`pdf/<generation|classifier|methodology|other>/` + `links.md`） |
| 文献笔记 | 生成线 `generate_project/literature/`；分类线 `classify_project/literature/` |
| 分类器（Phase D） | `classify_project/`（当前协议：`PILOT_PREREG_20261112.md`；代码 `scripts/`、结果 `results/`） |
| 历史归档（不再引用） | `_archive/`（登记：`_archive/ARCHIVE.md`） |

## 二、顶层目录职责

| 目录 | 放什么 | 不放什么 |
|---|---|---|
| `generate_project/` | 生成方法代码 + 实验产物（按方法族） | 评估脚本、报告 |
| `fundus/` | 全部数据池与冻结名单 | 代码 |
| `eval/` + `eval_data/` | 评估代码 / 评估产物与指标 | 训练代码 |
| `research-report/` | 交付 docx、构建脚本、审计证据、图 | 训练代码、原始数据 |
| `paper/` | 论文草稿 | 实验产物 |
| `docs/` | 规范与权威口径，按用途分 10-management / 20-research / 30-evaluation / 40-writing | 一次性记录 |
| `classify_project/` | 分类器代码与预注册 | 生成器代码 |
| `literature/` | 共享 PDF 原件、链接登记、跨线笔记 | 各线专属笔记（去项目 literature） |
| `_archive/` | 已停用但需留档的材料 | 活引用目标 |

## 三、三条硬规则

1. **数字只从登记表取**：`EXPERIMENTS.md` / `eval_data/*.json` / `eval/human_scores.csv`，报告和论文不另写数字。
2. **新实验一个目录**：`results/<exp>/` 必须带 `README.md`（问题/变量/结论/登记号/指标位置），否则视为临时产物。
3. **judgment 不入库**：判图含真实患者图，`**/judgment*/` 已被 `.gitignore` 排除；报告图由 `research-report/build/` 重建。

> **维护约定**：入口文件有行数预算（`PROJECT_STATE` ≤120 行）；历史里程碑只进
> [`docs/10-management/19-Progress-Log.md`](docs/10-management/19-Progress-Log.md)，规则见
> [`docs/10-management/18-Knowledge-Maintenance.md`](docs/10-management/18-Knowledge-Maintenance.md)。


## 四、冷启动 7 问速查

| 问题 | 精确路径 |
|---|---|
| 现在做什么、下一步 | `PROJECT_STATE.md` §1 / §4 |
| 61 张冻结名单 / T0 | `fundus/hrsevere_61_frozen.json`；`CFM/results/cfm128_hrsevere_pilot/models/checkpoint_epoch_000667.pth` |
| 六维公式 / 人工分 / 总分 | `eval/score_scheme.py`（`SCHEME`）；`eval/human_scores.csv`；`eval_data/_scores.json` |
| 分类器 pilot arms | `classify_project/PILOT_PREREG_20261112.md` |
| A 域审计证据 | `research-report/audit/a_domain_20261111/`（索引 `research-report/audit/README.md`） |
| 新增实验放哪、怎么登记 | `docs/10-management/17-Directory-Standard.md` + `CFM/results/README.md` + `EXPERIMENTS.md` |
| 文献 PDF / 一句话结论 | `literature/links.md`；原件 `literature/pdf/<line>/` |
