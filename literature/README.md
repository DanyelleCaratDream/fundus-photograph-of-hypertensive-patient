# literature/ —— 共享文献原件库

> 2026-11-13 起：**这里只放"原始素材"**（PDF、链接、外部文章摘录）。
> **按研究线整理的笔记不在这里**，去各自的 literature 目录：
> - 生成线 → [`generate_project/literature/`](../generate_project/literature/README.md)
> - 分类线 → [`classify_project/literature/`](../classify_project/literature/README.md)
>
> 这样分的原因：PDF 是两条线共用的输入（ECC-DM、数据泄露论文都跨线），集中放一份；
> 而笔记是各线自己的消化产物，跟着线走。

## 目录

```
literature/
├── README.md            # 本文件（规则）
├── links.md             # 链接登记：老师给的 + 自己找到的（按线分节）
├── pdf/
│   ├── generation/      # 生成器文献（4 篇）
│   ├── classifier/      # 分类器文献（5 篇）
│   ├── methodology/     # 方法学/数据卫生（3 篇泄露研究；ISIC 待补）
│   ├── other/           # 暂不归线（1 篇 virtual cells）
│   └── _text/           # 部分 PDF 的纯文本提取缓存（检查用，可删可重建）
└── notes/
    └── other/           # 跨线/暂不归线的笔记（EvoRAD ×2）
```

## 规则

1. **PDF 命名**：`作者年份-简短标题.pdf`，例如 `Cai2024-BPaCo.pdf`。
   PDF 被 `.gitignore` 的 `*.pdf` 排除，**不进 git**，换机器需重新下载（链接都在 `links.md`）。
2. **每篇文献必须在 `links.md` 登记**：链接 + 一句结论 + PDF 相对路径（若已下载）。
   只下载不登记 = 孤儿文件。
3. **新文献放哪**：
   - 原件 → `pdf/<generation|classifier|methodology|other>/`
   - 读后笔记 → 对应项目的 `literature/` 目录（不在这里）。
4. **归属判断**：只服务生成线 → `generation`；只服务分类线 → `classifier`；
   两条线都用（数据泄露、评估方法）→ `methodology`；拿不准 → `other` + 在 `links.md` 注明。
5. **论文定位**不在本目录：`docs/40-writing/12-Literature-Survey-and-Positioning.md`（写作宪法级）；
   引用暂存在 `paper/refs-notes.md`，建 `.bib` 时按本文件命名规则回填。

## 与其他位置的分工

| 想知道 | 去哪 |
|---|---|
| 有哪些 PDF 原件 | 本目录 `pdf/` |
| 外部链接与一句话结论 | 本目录 `links.md` |
| 生成/分类线的文献综述笔记 | `generate_project/literature/`、`classify_project/literature/` |
| 论文定位（哪些贡献已被做过） | `docs/40-writing/12-Literature-Survey-and-Positioning.md` |
| 引用键与出处暂存 | `paper/refs-notes.md` |
