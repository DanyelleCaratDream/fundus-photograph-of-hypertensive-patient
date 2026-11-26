# classify_project/literature —— 分类线文献与调研

> 2026-11-13 建立。分类器专属的调研材料放这里；**原始 PDF 仍在** `literature/pdf/classifier/`
> 与 `literature/pdf/methodology/`（两条线共用，集中存放）。

## 组员调研（`surveys/`）

| 文件 | 覆盖 | 结论摘要 |
|---|---|---|
| `彩照病症等级分类_顶会论文调研.docx` | 5 篇 MICCAI DR 分级（Galdran'20 / Liu'20 / Yu'24 / Che'23 / Playout'24） | 共同假设上万标注；我们 severe 仅几十张，只能借代价正则 + 图卷积思路 |
| `彩照病症等级分类_顶会论文调研(1).docx` | 4 篇（BPaCo / AOR-DR / ECC-DM / CMPB'25） | ECC-DM 语义筛选最贴 TSTR；AOR-DR 自报 42% 与表格不符；CMPB HRSG=354≠我们 758 |
| `论文调研.docx` | 5 篇 HR 分级 | **只有 CMPB'25 是真 KWB 四级**；其余 AVR/二分类/非分级；数字全部不可比 |
| `医学影像数据泄露与重复图像检索.docx` | 4 篇泄露/重复研究 | OCT/MRI/ISIC/DermaMNIST；直接支撑我们的数据卫生披露 |

逐条链接、关键数字与 PDF 路径 → [`literature/links.md`](../../literature/links.md) 的
「数据泄露」「HR 分级」两节。

## 相关但不在本目录

| 内容 | 去哪 |
|---|---|
| 分类器协议与预注册 | `PILOT_PREREG_20261112.md`（项目根） |
| 可下载 PDF（BPaCo/AOR-DR/ECC-DM/Mobile-HR/Triple-Stream） | `literature/pdf/classifier/` |
| 数据泄露/重复方法学 PDF | `literature/pdf/methodology/` |
| 论文定位与 Related Work 口径 | `docs/40-writing/12-Literature-Survey-and-Positioning.md` |
| 引用暂存 | `paper/refs-notes.md` |

## 规则

- 组员新交的材料先进 `classify_project/for_classify/`（收件箱），过一遍后：
  调研类搬到本目录 `surveys/`，原始 PDF 放 `literature/pdf/classifier/`，并在 `links.md` 登记。
- 不再新建根目录 `*_review_<日期>/` 一次性文件夹。
