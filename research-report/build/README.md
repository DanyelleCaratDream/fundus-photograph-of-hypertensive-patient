# research-report/build —— 报告构建脚本

> 2026-11-12 从 `research-report/` 根层收拢到此。脚本一律用“向上找 `CLAUDE.md`”定位仓库根。

## 脚本 → 产物

| 脚本 | 产物 | 说明 |
|---|---|---|
| `_build_report_dl_v2_20261106.py` | `REPORT_DL_v2.docx` | 以 `REPORT_DL.docx` 为模板重写全文；每次运行会从旧 docx 重新抽取 `_media_dl/` 缓存 |
| `_update_report_dl_v1_20261111.py` | `REPORT_DL.docx`（增量插入） | 插入 §2.11、§5.13.5、第 7 章；不重建全文 |
| `_extract_report_dl_followup_20261111.py` | `REPORT_DL_后续.docx` | 从 §5.12 起原样摘出教师附件 |
| `_make_audit_figs_20261111.py` | `figures/fig_audit_flow.png`、`fig_leakage_demo.png`、`fig_pair_check_20.png` | 输入 = `research-report/audit/a_domain_20261111/` |
| `_make_vertical_figs_20261111.py` | `figures/vert_*.png`（5 张竖版） | 超宽图改竖版，供 v2 内嵌 |
| `_extract_report_dl_text.py` | `REPORT_DL_text.txt` | 从 v1 docx 提取纯文本，供 paper/ 检索（2026-11-13 新增） |

## 运行顺序

1. `_make_audit_figs` → 2. `_make_vertical_figs` → 3. `_build_report_dl_v2`（或 `_update_report_dl_v1`）→ 4. `_extract_report_dl_followup`

## 注意

- `_media_dl/` 是构建缓存（`.gitignore` 已排除），由 v2 构建自动重建；单独跑 `_make_vertical_figs` 前需先跑一次 v2 构建。
- Word 打开生成稿后需 `Ctrl+A → F9` 更新目录域。
- 文中的图路径：`figures/`、`CFM/judgment/`（e2/e3/e4/scan30k/b1 等），移动判图目录会打断构建。
