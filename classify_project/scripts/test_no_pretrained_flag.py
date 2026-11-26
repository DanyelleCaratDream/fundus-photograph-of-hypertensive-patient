# -*- coding: utf-8 -*-
"""`--no-pretrained` 开关的回归测试（不跑真实训练）。

用法（仓库根目录）：
    python -X utf8 classify_project/scripts/test_no_pretrained_flag.py
退出码 0 = 全部通过；非 0 = 有失败。

背景：2026-11-24 组员 B 实现审计（B2-10）发现，`--no-pretrained` 只在 argparse
与训练 JSON 里出现，`train_one` 构建模型时未传递该参数 → 开关永远无效，
模型恒为 ImageNet 预训练。本测试锁住修复后的行为。

覆盖：
  1. build_model(pretrained=False) 不加载 ImageNet 权重
  2. build_model(pretrained=True) 使用 ImageNet 权重
  3. train_one 把 pretrained 形参转发给 build_model
  4. main() 把 args.no_pretrained 传给 train_one（源码级守护，防再次漏传）
"""
from __future__ import annotations

import inspect
import sys
import traceback
from pathlib import Path

import torch
import torch.nn as nn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import train_classifier as tc  # noqa: E402


# ---------------------------------------------------------------- 替身
class _FakeResNet(nn.Module):
    """只保留 build_model 需要的 .fc。"""

    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(512, 1000)


class _ToyModel(nn.Module):
    """训练循环用的极小模型：整图展平后接 4 类线性头。"""

    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(3 * 32 * 32, 4)

    def forward(self, x):  # noqa: D401
        return self.fc(x.flatten(1))


class _FakeDS(torch.utils.data.Dataset):
    """替代 FundusFolder：只提供 items / is_synth / __len__ / __getitem__。"""

    def __init__(self, n: int):
        self.items = [(Path(f"fake{i}.jpg"), i % 4) for i in range(n)]
        self.is_synth = [False] * n

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, i):
        return torch.zeros(3, 32, 32), self.items[i][1]


# ---------------------------------------------------------------- 测试
def test_build_model_pretrained_false() -> None:
    seen: dict = {}

    def fake_resnet18(**kw):
        seen.update(kw)
        return _FakeResNet()

    orig = tc.models.resnet18
    tc.models.resnet18 = fake_resnet18
    try:
        tc.build_model(32, pretrained=False)
    finally:
        tc.models.resnet18 = orig

    assert "weights" in seen, "build_model 未把 weights 传给 resnet18"
    assert seen["weights"] is None, f"pretrained=False 却传了 {seen['weights']!r}"


def test_build_model_pretrained_true() -> None:
    seen: dict = {}

    def fake_resnet18(**kw):
        seen.update(kw)
        return _FakeResNet()

    orig = tc.models.resnet18
    tc.models.resnet18 = fake_resnet18
    try:
        tc.build_model(32, pretrained=True)
    finally:
        tc.models.resnet18 = orig

    assert seen.get("weights") == tc.models.ResNet18_Weights.IMAGENET1K_V1, \
        f"pretrained=True 未使用 ImageNet 权重：{seen.get('weights')!r}"


def test_train_one_forwards_pretrained() -> None:
    seen: dict = {}

    def fake_build(size, pretrained=True):
        seen["pretrained"] = pretrained
        return _ToyModel()

    orig_folder, orig_build = tc.FundusFolder, tc.build_model
    tc.FundusFolder = lambda root, split, size, train: _FakeDS(8 if split == "train" else 4)
    tc.build_model = fake_build
    try:
        tc.train_one(size=32, root=Path("."), seed=42, epochs=1, bs=2,
                     lr=1e-3, weight_decay=0.0, device="cpu", weighted=False,
                     num_workers=0, quiet=True, max_gpu_temp=0,
                     pretrained=False)
    finally:
        tc.FundusFolder, tc.build_model = orig_folder, orig_build

    assert seen.get("pretrained") is False, \
        f"train_one 未把 pretrained=False 传给 build_model（收到 {seen.get('pretrained')!r}）"


def test_main_passes_no_pretrained() -> None:
    src = inspect.getsource(tc.main)
    assert "pretrained=not args.no_pretrained" in src, \
        "main() 没有把 args.no_pretrained 传给 train_one（开关会再次静默失效）"


TESTS = [
    test_build_model_pretrained_false,
    test_build_model_pretrained_true,
    test_train_one_forwards_pretrained,
    test_main_passes_no_pretrained,
]


def main() -> int:
    failed = 0
    for fn in TESTS:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {fn.__name__}: {type(e).__name__}: {e}")
            traceback.print_exc(limit=2)
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
