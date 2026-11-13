# CFM/results —— 实验目录索引

> 每个子目录 = 一个训练实验，**必须自带 `README.md`**（问题 / 变量 / 结论 / 登记号 / 指标位置）。
> 新实验按 `docs/10-management/17-Directory-Standard.md` 建；老实验的 `images/` 沿用旧名（新实验用 `samples/`）。

## 统一结构

```
results/<exp_name>/
├── README.md        # 本实验 5 行摘要（问题/变量/结论/登记号/指标位置）
├── config.json      # 单实验配置的唯一真源（configs/ 只是预设）
├── logs/            # training.log + loss_curve*.png
├── models/          # 检查点（可空；常驻权重也可能在 CFM/models/）
├── images/          # 训练过程预览网格
├── eval/            # 本实验的评估产物（可选；总表在根 eval_data/）
└── judgment/        # 人工判图（可选；实际判图多在 CFM/judgment/）
```

## 实验一览（2026-11-12）

| 目录 | 一句话 | 状态 | 指标来源 |
|---|---|---|---|
| `a_domain_clean_cfm128/` | A_clean(258) 从零预训练，T1 起点 | 🔵 训练中 | 待评估 |
| `cfm128/` | CFM@128 基线（F2） | ✅ | `eval_data/cfm128_*` |
| `cfm128_align/` | 时间轴对齐消融 | ✅ | `eval_data/cfm128_align_*` |
| `cfm128_text/` | 文本条件消融（128px 最佳） | ✅ | `eval_data/cfm128_text_*` |
| `cfm128_notime/` | 去时间条件（负结果） | ✅ | `eval_data/cfm128_notime_*` |
| `cfm128_featC/` | 手工特征检索（病理保真路线） | ✅ | `eval_data/cfm128_featC_*` |
| `cfm128_featA/` | RETFound 特征检索 | ✅ | `eval_data/cfm128_featA_*` |
| `cfm128_hrsevere_pilot/` | 61 张纯 severe 从零（T0 = 667 轮） | ✅ | `eval_data/cfm128_hrsevere_pilot_*` |
| `cfm256/` | CFM@256 原生（F3，分布最佳） | ✅ | `eval_data/cfm256_*` |
| `cfm256_lesion/` | 渗出加权（仅探索性，有缺陷） | ⚠️ 不作证据 | `eval_data/cfm256_lesion_*` |

- 非训练产物（直方图匹配投影等）不进 `results/`，放 `CFM/judgment/<topic>/`。
- 全量指标以根目录 `eval_data/<exp>_{metrics,fundus_metrics,diversity}.json` 为准；
  跨方法横评与图见 `eval/plot_metrics.py`、`eval/score_scheme.py`。
- 实验数字登记：`generate_project/deep_learning/EXPERIMENTS.md`。
