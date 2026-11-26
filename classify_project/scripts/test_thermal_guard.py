# -*- coding: utf-8 -*-
"""GPU 温度护栏的单元测试（不占 GPU、不跑训练）。

用法（仓库根目录）：
    python -X utf8 classify_project/scripts/test_thermal_guard.py
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


class FakeTemps:
    def __init__(self, seq):
        self.seq = list(seq)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.seq.pop(0) if self.seq else self.last

    last = 60.0


def test_disabled_makes_no_reads():
    import train_classifier as T
    temps = FakeTemps([99])
    sleeps = []
    g = T.ThermalGuard(max_temp=0, temp_fn=temps, sleep_fn=sleeps.append)
    for i in range(10):
        g.step(i)
    assert temps.calls == 0 and sleeps == [] and g.stats()["enabled"] is False


def test_waits_until_below_hysteresis():
    import train_classifier as T
    temps = FakeTemps([80, 80, 78, 70])   # 逐步降温
    sleeps = []
    g = T.ThermalGuard(max_temp=75, poll_every=1, sleep_s=5, temp_fn=temps,
                       sleep_fn=sleeps.append, log=None)
    g.step(0)                             # 首次读数 80 → 等待
    assert sleeps == [5, 5, 5], sleeps
    assert g.stats()["waits"] == 1
    assert g.stats()["max_observed_c"] == 80
    assert g.stats()["sleep_total_s"] == 15


def test_no_wait_below_threshold():
    import train_classifier as T
    temps = FakeTemps([60])
    sleeps = []
    g = T.ThermalGuard(max_temp=75, poll_every=1, temp_fn=temps, sleep_fn=sleeps.append)
    g.step(0)
    assert sleeps == [] and g.stats()["waits"] == 0


def test_poll_every_skips_batches():
    import train_classifier as T
    temps = FakeTemps([60, 60, 60])
    g = T.ThermalGuard(max_temp=75, poll_every=5, temp_fn=temps, sleep_fn=lambda s: None)
    for i in range(6):
        g.step(i)                          # 只有 i=0、i=5 检查
    assert temps.calls == 2


def test_max_wait_cap_does_not_hang():
    import train_classifier as T
    temps = FakeTemps([90] * 20)
    temps.last = 90
    sleeps = []
    g = T.ThermalGuard(max_temp=75, poll_every=1, sleep_s=5, max_wait_s=10,
                       temp_fn=temps, sleep_fn=sleeps.append)
    g.step(0)
    assert sleeps == [5, 5], sleeps      # 到上限即继续
    assert g.stats()["max_wait_hits"] == 1


def test_unknown_temperature_is_ignored():
    import train_classifier as T
    g = T.ThermalGuard(max_temp=75, poll_every=1, temp_fn=lambda: None,
                       sleep_fn=lambda s: None)
    g.step(0)
    assert g.stats()["waits"] == 0 and g.stats()["max_observed_c"] is None


def test_cli_defaults_to_75():
    import train_classifier as T
    a = T.build_argparser().parse_args(["--data", ".", "--size", "256"])
    assert a.max_gpu_temp == 75.0
    assert a.thermal_poll_every >= 1


def main() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t(); print(f"  PASS  {t.__name__}")
        except Exception as e:
            failed += 1; print(f"  FAIL  {t.__name__}: {e}")
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
