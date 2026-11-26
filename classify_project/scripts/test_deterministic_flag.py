# -*- coding: utf-8 -*-
"""DL-EX-032 预检：`--deterministic` 开关的单元测试（不跑训练）。

用法（仓库根目录）：
    python -X utf8 classify_project/scripts/test_deterministic_flag.py
退出码 0 = 全部通过；非 0 = 有失败。

覆盖：
  1. 不传参 → 全局 torch 状态保持默认（旧行为不变）
  2. 传参 → use_deterministic_algorithms(True) / cudnn.deterministic / 关 benchmark /
     CUBLAS_WORKSPACE_CONFIG 就位
  3. 环境快照含版本与硬件字段（要写入每次训练 JSON）
  4. 命令行解析：--deterministic 默认为 False
"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

REQUIRED_STATE_KEYS = {
    "deterministic_algorithms", "cudnn_deterministic", "cudnn_benchmark",
    "cublas_workspace_config", "torch_version", "cuda_version", "cudnn_version",
    "gpu_name", "device", "cuda_initialized",
}


def _reset() -> None:
    """恢复默认 torch 状态，避免子测试互相污染。"""
    import torch
    torch.use_deterministic_algorithms(False)
    torch.backends.cudnn.deterministic = False
    torch.backends.cudnn.benchmark = False


def test_default_does_not_touch_state() -> None:
    import torch
    import train_classifier as T
    _reset()
    before = torch.are_deterministic_algorithms_enabled()
    T.build_argparser().parse_args(["--data", ".", "--size", "256"])  # 只解析，不该改全局状态
    assert torch.are_deterministic_algorithms_enabled() == before
    st = T.determinism_state()
    assert st["deterministic_algorithms"] is False, st
    assert st["cudnn_deterministic"] is False, st
    assert st["cudnn_benchmark"] is False, st


def test_enable_sets_everything() -> None:
    import torch
    import train_classifier as T
    _reset()
    os.environ.pop("CUBLAS_WORKSPACE_CONFIG", None)
    try:
        T.enable_determinism()
        assert torch.are_deterministic_algorithms_enabled() is True
        assert torch.backends.cudnn.deterministic is True
        assert torch.backends.cudnn.benchmark is False
        assert os.environ.get("CUBLAS_WORKSPACE_CONFIG") == ":4096:8", \
            os.environ.get("CUBLAS_WORKSPACE_CONFIG")
        st = T.determinism_state()
        assert st["deterministic_algorithms"] is True
        assert st["cudnn_deterministic"] is True
        assert st["cudnn_benchmark"] is False
        assert st["cublas_workspace_config"] == ":4096:8"
    finally:
        _reset()


def test_state_has_versions_and_hardware() -> None:
    import train_classifier as T
    st = T.determinism_state()
    missing = REQUIRED_STATE_KEYS - set(st)
    assert not missing, f"缺少字段：{sorted(missing)}"


def test_cli_flag_defaults_false() -> None:
    import train_classifier as T
    base = ["--data", ".", "--size", "256"]
    ap = T.build_argparser()
    assert ap.parse_args(base).deterministic is False
    assert ap.parse_args(base + ["--deterministic"]).deterministic is True


def test_help_lists_flag() -> None:
    import subprocess
    out = subprocess.run(
        [sys.executable, "-X", "utf8", str(HERE / "train_classifier.py"),
         "--data", ".", "--size", "256", "--help"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert out.returncode == 0, out.stderr[-2000:]
    assert "--deterministic" in out.stdout


def main() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception:
            failed += 1
            print(f"  FAIL  {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
