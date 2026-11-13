# 目录规范（Directory Standard）

> 2026-11-12 建立。目的：同类文件夹长得一样，找文件不靠记忆。
> 适用范围：**新实验一律照做；老目录只加 README 说明，不改名**（改名会打断脚本与历史引用）。
> 路径地图见 [../../PROJECT_MAP.md](../../PROJECT_MAP.md)。

---

## 一、方法族骨架

```
generate_project/deep_learning/<MethodFamily>/<Method>/
├── README.md        # 必须：状态、结论、入口、产物地图
├── STANDARDS.md     # 可选：超参/CLI 技术规范
├── train/           # 训练入口
├── infer/           # 采样 / 自精修 / 交付
├── tools/           # 诊断、出图、一次性工具
├── configs/         # 预设配置（不是单实验配置）
├── data/            # 条件图 / 权重图等派生数据（可重建）
├── models/          # 方法族共享权重（按实验名命名）
├── results/         # 每个实验一个子目录
└── judgment/        # 判图（不入 git）
```

现状：**只有 `Fundus-FlowMatching/CFM/` 完整符合**。Diffusion 用 `results_D*` / `judgment_<日期>` 的 legacy 命名；
GAN / VAE 已停用，仅有代码与 STANDARDS。这些目录的 README 已标注 legacy，不再改造。

---

## 二、实验目录骨架（最重要）

```
<results_root>/<exp_name>/
├── README.md        # 必须，5 行：问题 / 变量 / 结论 / 登记号 / 指标位置
├── config.json      # 单实验配置的唯一真源
├── logs/            # training.log + loss_curve*.png
├── models/          # 本实验检查点（可空；共享 final 也可在族 models/）
├── samples/         # 训练预览与生成样本（老目录叫 images/，不改名）
├── eval/            # 本实验评估产物（总表仍在根 eval_data/）
└── judgment/        # 本实验判图（可选；实际多在族 judgment/）
```

**判定标准**：没有 `README.md` 的 `results/<dir>/` 视为临时产物，不得作为结论依据。

### 命名

- `<family>_<resolution>_<variant>`，全小写、下划线分隔：`cfm128_text`、`cfm256_lesion`、`a_domain_clean_cfm128`。
- 消融前缀保持一致（`cfm128_*`），方便通配与排序。
- 实验名必须能回查到 `EXPERIMENTS.md` 的 DL-EX 编号（写进该实验 README）。

---

## 三、文档三分

| 层 | 位置 | 放什么 | 生命周期 |
|---|---|---|---|
| 规范/权威 | `docs/` | 14 论文脊柱、15 数据、17 本文件 | 长期维护 |
| 交付物 | `research-report/` | docx、`build/` 构建脚本、`figures/`、`audit/` 证据 | 随报告更新 |
| 历史 | `_archive/` | 已停用的报告、规划、一次性脚本 | 只增不改 |

**不再新建** `advisor_review_<日期>/` 这类根目录一次性文件夹：导师材料统一进 `research-report/audit/<日期>_<topic>/`。

---

## 四、数据层

- `fundus/` 每个数据池必须在 `fundus/README.md` 登记：数量 / 分辨率 / 来源 / 用途 / 可否重建 / 状态。
- 状态用四档：`规范`（训练/评估默认）、`派生`（可由规范池重建）、`墓园`（移出但可回滚）、`legacy`（不再使用）。

---

## 五、脚本落点

| 类型 | 位置 |
|---|---|
| 方法训练/推理/诊断 | 方法族 `train/ infer/ tools/` |
| 跨方法评估 | `eval/` |
| 报告构建与出图 | `research-report/build/` |
| 已完成的一次性运维脚本 | 不保留（`_archive/` 或删除） |
| 跨文档/仓库检查 | `tools/`（如 `check_docs.py`） |

脚本一律用“向上找 `CLAUDE.md`”定位仓库根，不写 `parents[N]`、不写绝对路径：

```python
def _repo_root():
    p = Path(__file__).resolve().parent
    while not (p / "CLAUDE.md").exists():
        p = p.parent
    return p
```

---

---

## 六、文献与笔记

| 类型 | 位置 | 规则 |
|---|---|---|
| 原始 PDF | `literature/pdf/{generation,classifier,methodology,other}/` | 两条线共用；`*.pdf` 不入 git；命名 `作者年份-标题.pdf` |
| 链接与一句话结论 | `literature/links.md` | 每篇必须登记，否则视为孤儿文件 |
| 生成线笔记 | `generate_project/literature/` | traditional-ml / pretrained / flow-matching / quality-upgrade |
| 分类线笔记 | `classify_project/literature/` | surveys/ 放组员调研；收件箱 `classify_project/for_classify/` |
| 论文定位（规范） | `docs/40-writing/12-Literature-Survey-and-Positioning.md` | 写作宪法级，不搬 |
| 引用暂存 | `paper/refs-notes.md` | 建 .bib 前的中转站 |

**判断规则**：原始素材 → `literature/`；按线消化后的笔记 → 各项目 `literature/`；
我们自己的分析/规划/答辩 → 留在实验项目（如 `machine_learning/report/`），不算文献。

---

## 七、检查清单（新增实验时逐条勾）

- [ ] `results/<exp>/` 有 `README.md`（5 行齐全）
- [ ] `config.json` 已落盘（含 resume / seed / 轮数）
- [ ] `EXPERIMENTS.md` 已登记 DL-EX 编号
- [ ] `logs/training.log` 有完整轨迹（无 NaN、无静默从 0 重启）
- [ ] 评估产物落 `eval_data/<exp>_*.json`
- [ ] 判图在 `judgment/`（确认未被 git 跟踪）

---

## 八、docs/ 自身分类

`docs/` 是“我们自己的文档”的唯一规范区，按用途分四类：

| 目录 | 放什么 | 例子 |
|---|---|---|
| `10-management/` | 路线、操作手册、目录规范 | 06 / 08 / 17 |
| `20-research/` | 权威口径（写错会出事） | 14 脊柱 / 15 数据 / 01 / 02 |
| `30-evaluation/` | 评分设计与评估协议 | 09 / 13 / 07 |
| `40-writing/` | 写作、文献定位、答辩 | 11 / 12 / 16 |

- 入口只有 `docs/00-Doc-Index.md`；新文档先归类，再回 00 登记。
- 文件名保留原编号（`NN-Name.md`），不二次改名。
- 交付物（`research-report/`）、论文稿（`paper/`）、方法本地 README 不属于 docs。


---

## 九、知识层与维护

- 四层知识模型、入口预算（`PROJECT_STATE` ≤120 行等）、记什么/不记什么、轻量检查与完整 Dreaming 清单：
  见 [18-Knowledge-Maintenance.md](18-Knowledge-Maintenance.md)。
- 历史里程碑只进 [19-Progress-Log.md](19-Progress-Log.md)（不参与会话加载），不追加到 `PROJECT_STATE`。
- 每次 `/handoff` 运行 `python tools/check_docs.py`；超预算时把最旧的已完成 `[x]` 下沉到 19。
