# 校准（ECE / reliability diagram）规范

> test 只有 71 张：校准分析一律标为**探索性**，不得据此宣称"校准改善"或"更可靠"。

## 1. 定义

- confidence：`max(probs)`（文件里的 `probs`，即 softmax 后的四类概率）。
- correctness：`argmax(probs) == y_true`。
- 分箱：**M = 10 个等宽箱**，`[0,1]` 均分；箱号 `min(int(conf*10), 9)`。
- 每箱：样本数 `n_b`、平均置信度 `conf_b`、准确率 `acc_b`。
- `ECE = Σ_b (n_b / N) * |acc_b − conf_b|`。
- reliability diagram：x=平均置信度，y=准确率，附对角线；图上或表里标 `n_b`。

## 2. 必须报告

1. 分箱数 M 与边界（`0, 0.1, …, 1.0`）。
2. 每个箱的 `n_b`、`conf_b`、`acc_b`（空箱要注明）。
3. ECE 数值（保留 3–4 位小数即可）。
4. 逐 arm、逐 seed；不要只给一个平均。
5. 图与表的数据来源（哪个 JSON、哪一行）。

## 3. 小样本限定（必须写进报告）

- 71 张 / 10 箱 → 大多数箱只有个位数样本；ECE 的细微差别在抽样噪声范围内。
- 不同 arm 的 ECE 差异**不能**解释为校准优劣。
- 可以描述"哪个类别的置信度系统性偏高"，但只能作探索性观察。
- 不得用 ECE 选 arm、调参或重选 checkpoint。

## 4. 可选（做了要标注探索性）

- 每类 ECE（按 y_true 分类）；
- Brier score；
- 置信度直方图。
