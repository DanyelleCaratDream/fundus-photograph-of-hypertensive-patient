# 知识层与维护规范（Knowledge Maintenance）

> 2026-11-13 建立。回答两个问题：**什么东西该记在哪一层**、**什么时候做离线对账**。
> 核心原则：入口只放轻量索引，历史与细节下沉到不参与加载的底账；过期笔记必须定期清理。

---

## 一、四层知识模型

| 层 | 作用 | 本项目对应物 | 是否每次会话加载 |
|---|---|---|---|
| **L1 原始底账** | 唯一事实来源，不可改写 | git 历史、`EXPERIMENTS.md`、`eval_data/*.json`、`logs/training.log`、审计原始清单 | 否（按需查） |
| **L2 笔记** | 单次任务的显著结论 | `results/<exp>/README.md`、`PROJECT_STATE` §3、审计笔记 | 部分 |
| **L3 归纳** | 跨实验的规则与口径 | `docs/20-research/14` 脊柱、`15` 数据、`docs/10-management/17` 目录 | 按需 |
| **L4 入口** | 开局导航，只放摘要与指针 | `PROJECT_STATE.md`、`PROJECT_MAP.md`、`CLAUDE.md`、`docs/00-Doc-Index.md`、`MEMORY.md` | 是 |

判断口诀：**数字去 L1，单次结论去 L2，规则去 L3，入口只放“去哪找”。**

---

## 二、入口预算（硬上限）

| 文件 | 上限（行） | 超出时怎么办 |
|---|---:|---|
| `PROJECT_STATE.md` | 120 | 把 §2 最旧的已完成 `[x]` 搬进 `19-Progress-Log.md` |
| `PROJECT_MAP.md` | 80 | 合并重复行；细节转 `docs/00` |
| `CLAUDE.md` | 60 | 只留约束，解释放 `docs/18` |
| `docs/00-Doc-Index.md` | 100 | 分类表只留一行一条，细节转各目录 README |
| `MEMORY.md`（Claude 记忆索引） | 100 | 合并同类记忆 |
| `results/README.md` | 100 | 只留实验一览，细节转各实验 README |

预算由 `python tools/check_docs.py` 自动检查。

---

## 三、记什么 / 不记什么

### 不记（易变事实，Ephemeral Facts）
- epoch / step / loss / 单次耗时；
- 某次 FID / KID / 分数的具体数值（去 `EXPERIMENTS.md` / `eval_data/*.json`）；
- 临时路径（`D:\tmp\...`）与当前进程状态；
- 逐日勾选的流水账（去 `19-Progress-Log.md` 一行概括）。

### 记（隐性规则，Latent Rules）
- 会导致静默错误的坑：`--resume` 必须绝对路径、`global_step` 续训归零、增强时 mask 必须跟随；
- 口径与边界：两套 0-100 分不可混排、生成器只能见 train、TSTR 主指标是 QWK；
- 已被证伪的路线与原因：去时间条件在眼底不成立、AVR 管线不适合 KW-IV；
- 决策的理由，而不是决策的流水。

---

## 四、轻量检查（每次 `/handoff`，约 2 分钟）

1. `python tools/check_docs.py` —— 死链、入口预算、过期路径；
2. 新增文件是否已登记：`docs/00`（docs 类）、`literature/links.md`（文献）、`results/README.md`（实验）；
3. `PROJECT_STATE` 是否 ≤120 行；超出则按 §五 下沉。

---

## 五、完整 Dreaming（里程碑 / 每月一次，约 30 分钟）

1. **冷启动测试**（可选，每季度）：让一个零上下文 agent 只靠入口文件回答 7 个定位问题；失败点即文档缺口。
2. **过期文档**：最后更新 >1 个月、且依赖旧结论的，加横幅或归档（参照 2026-11-13 的 README/classify 处理）。
3. **数字对账**：文档里的关键数字抽查 3 条，必须能在 `EXPERIMENTS.md` / `eval_data/*.json` 找到。
4. **死链与索引覆盖**：`tools/check_docs.py` 全绿；新文档在 `docs/00` 有一行。
5. **归档**：过期材料移 `_archive/` 并登记 `ARCHIVE.md`；一次性脚本删除。
6. **记录**：在 `19-Progress-Log.md` 追加一行“Dreaming 日期 + 处理了什么”。

---

## 六、触发与记录

| 时机 | 动作 |
|---|---|
| 每次会话收尾 `/handoff` | 轻量检查；`PROJECT_STATE` >120 行则下沉历史 |
| 实验里程碑（T0/T1、pilot、报告交付） | Dreaming 全检 + 更新 `19` 一行 |
| 每月 / 投稿前 | Dreaming 全检 + 冷启动测试 |

历史只进 `19-Progress-Log.md`，**不再追加到 `PROJECT_STATE`**；入口保持恒定大小。
