# research-report —— 交付报告与证据

> 本目录只放**交付物**（docx）、构建脚本、配图与审计证据。
> **数字不在这里**：实验数字以 `generate_project/*/EXPERIMENTS.md` 与 `eval_data/*.json` 为准。

## 报告版本（双轨并行）

| 文件 | 定位 | 说明 |
|---|---|---|
| `REPORT_DL.docx`（v1） | 实验日志体裁 | 完整历史 + 第 7 章「2026-10-25～11-11」；也是 v2 构建的模板/取图来源 |
| `REPORT_DL_v2.docx`（v2） | 论文向重写 | Q1–Q4 框架 + 第 8 章后期实验演进；**当前正式稿** |
| `REPORT_DL_后续.docx` | 教师附件 | 从 v1 §5.12 起原样摘出，供老师快速看进展 |
| `汇报_进度_20261111.md` | 给老师的消息稿 | 生成器四条主线 + 分类器文献分层 |
| `REPORT_DL_text.txt` | v1 纯文本提取 | 2026-11-13 由 `build/_extract_report_dl_text.py` 生成，供 `paper/` 检索 |

> ⚠️ Word 打开生成稿后需 `Ctrl+A → F9` 更新目录域。
> `REPORT_DL_v2.docx`、`REPORT_DL_后续.docx`、`汇报_进度_20261111.md` 按作者口径暂不入 git。

## 其他

| 目录 | 内容 |
|---|---|
| `build/` | 构建与出图脚本（见 [build/README.md](build/README.md)） |
| `figures/` | 报告内嵌图（`eval/plot_metrics.py`、`_make_*` 生成） |
| `audit/` | 导师评审答复 + A 域审计证据（见 [audit/README.md](audit/README.md)） |
| `_media_dl/` | v2 构建缓存（gitignore，可自动重建） |

历史报告（`_archive/reports/evaluation_report.md`、`CONTINUE_GUIDE_NEW.md`、`interview-prep.docx` 等）在 `_archive/reports/`。
