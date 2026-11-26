# -*- coding: utf-8 -*-
"""A1（logit adjustment）/ A2（DRC）的快速自检。

只测纯函数与冻结逻辑，不跑训练。用法：
    python classify_project/scripts/test_pilot_arms.py
"""
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

import train_classifier as tc


def test_metrics_perfect_prediction():
    y = np.array([0, 1, 2, 3, 3, 2])
    m = tc.metrics_from_preds(y, y)
    assert m["qwk"] == 1.0
    assert m["acc"] == 1.0
    assert m["severe_recall"] == 1.0
    assert m["n"] == 6
    assert "confusion" in m


def test_logit_adjust_identity():
    prior = np.array([0.7, 0.1, 0.1, 0.1])
    z = np.array([[2.0, 1.5, 0.0, 0.0]])
    assert tc.apply_logit_adjust(z, prior, 0.0).argmax(1)[0] == 0


def test_logit_adjust_pushes_away_from_majority():
    prior = np.array([0.7, 0.1, 0.1, 0.1])
    z = np.array([[2.0, 1.5, 0.0, 0.0]])
    # tau 足够大时，多数类 prior 的惩罚会让 class 1 反超
    assert tc.apply_logit_adjust(z, prior, 3.0).argmax(1)[0] == 1


def test_tune_tau_returns_grid_value():
    prior = np.array([0.7, 0.1, 0.1, 0.1])
    z = np.array([[2.0, 1.5, 0.0, 0.0], [0.0, 0.0, 1.0, 3.0]])
    y = np.array([1, 3])
    tau, m = tc.tune_tau(z, y, prior)
    assert tau in (0.0, 0.25, 0.5, 0.75, 1.0)
    assert "qwk" in m


def test_balanced_sampler_weights_and_draw():
    items = [(Path("x"), y) for y in ([0] * 80 + [1] * 10 + [2] * 5 + [3] * 5)]
    s = tc.make_balanced_sampler(items)
    w = s.weights.numpy()
    assert np.allclose(w[:80], 1 / 80)
    assert np.allclose(w[80:90], 1 / 10)
    idx = torch.multinomial(s.weights, 4000, replacement=True).numpy()
    freq = np.bincount([items[i][1] for i in idx], minlength=4) / 4000
    assert np.all(np.abs(freq - 0.25) < 0.03), freq


def test_freeze_backbone_reset_head():
    model = tc.build_model(64, pretrained=False)
    old_fc_w = model.fc.weight.detach().clone()
    tc.freeze_backbone_reset_head(model, "cpu")
    assert all(not p.requires_grad for n, p in model.named_parameters() if not n.startswith("fc."))
    assert all(p.requires_grad for p in model.fc.parameters())
    assert model.fc.out_features == tc.NUM_CLASSES
    assert not torch.equal(old_fc_w, model.fc.weight.detach())  # 已重初始化
    with torch.no_grad():
        out = model(torch.zeros(2, 3, 64, 64))
    assert out.shape == (2, tc.NUM_CLASSES)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n  {len(tests)} 项自检全部通过")
