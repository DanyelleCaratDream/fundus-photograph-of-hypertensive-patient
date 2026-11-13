#!/usr/bin/env python
"""训练完成验收（A_clean 预训练 / T1 迁移训练通用）。

用法
  # A_clean：780 轮 × 51 步
  python tools/verify_training.py --run-dir results/a_domain_clean_cfm128 \
      --expect-epochs 780 --steps-per-epoch 51

  # T1：667 轮 × 30 步（61 张 / batch2 / drop_last）
  python tools/verify_training.py --run-dir results/cfm128_hrsevere_t1_ac \
      --expect-epochs 667 --steps-per-epoch 30

检查项（对应导师验收清单）
  1 final_model.pth 存在
  2 epoch 数正确
  3 步数 = epochs × steps_per_epoch（续训不恢复 global_step 时如实报告偏差）
  4 raw 权重 strict 加载（UNet 架构重建后 load_state_dict 无缺失/多余）
  5 training.log 完整、无 NaN
  6 无 checkpoint_INTERRUPTED.pth 残留

退出码 0 = 全部通过；1 = 有失败项。
"""
import argparse
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CFM = Path(__file__).resolve().parents[1]
DL = CFM.parents[1]  # generate_project/deep_learning
DDPM = DL / "Fundus-Diffusion" / "ddpm"
sys.path.insert(0, str(DDPM))

import torch  # noqa: E402
from train import UNet  # noqa: E402


def build_model(args):
    """按 checkpoint 里保存的 args 重建 UNet（CPU，避免占用训练中的 GPU）。"""
    return UNet(
        T=args.timesteps,
        channels=args.channels,
        base_dim=args.base_dim,
        dim_mults=tuple(args.dim_mults),
        attn_layers=tuple(args.attn_layers),
        dropout=args.dropout,
        cond_channels=1 if getattr(args, "cond_path", None) else 0,
        use_scale_shift_norm=not getattr(args, "no_scale_shift_norm", False),
        text_dim=(1024 if getattr(args, "use_text_cond", False)
                  else (getattr(args, "feat_dim", 0) if getattr(args, "feat_cond_dir", None) else 0)),
        use_time_cond=not getattr(args, "no_time_cond", False),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, help="结果目录，如 results/a_domain_clean_cfm128")
    ap.add_argument("--expect-epochs", type=int, required=True)
    ap.add_argument("--steps-per-epoch", type=int, required=True)
    a = ap.parse_args()

    rd = Path(a.run_dir)
    if not rd.is_absolute():
        rd = (CFM / rd).resolve()
    models, logs = rd / "models", rd / "logs"
    final = models / "final_model.pth"
    expect_steps = a.expect_epochs * a.steps_per_epoch

    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))
        ok = ok and bool(cond)

    print(f"== 验收目录: {rd}")
    check("final_model.pth 存在", final.is_file(), str(final))
    if not final.is_file():
        print("\n结论: FAIL（无最终模型）")
        return 1

    cp = torch.load(final, map_location="cpu", weights_only=False)
    args = cp.get("args")
    epoch = int(cp.get("epoch", -1))
    gs = int(cp.get("global_step", -1))

    check("epoch 数", epoch + 1 == a.expect_epochs,
          f"ckpt epoch={epoch} → 完成 {epoch + 1} 轮，期望 {a.expect_epochs}")
    check("步数", gs == expect_steps,
          f"global_step={gs}，期望 {expect_steps}"
          + ("" if gs == expect_steps else "  ← 续训未恢复 global_step 时属已知偏差，按 epoch×步数核算"))

    if args is not None:
        try:
            model = build_model(args)
            missing, unexpected = model.load_state_dict(cp["model_state_dict"], strict=False)
            check("raw strict 加载", not missing and not unexpected,
                  f"missing={len(missing)} unexpected={len(unexpected)}")
        except Exception as e:  # noqa: BLE001
            check("raw strict 加载", False, f"重建/加载异常: {e}")
    else:
        check("raw strict 加载", False, "checkpoint 未保存 args，无法重建架构")

    log = logs / "training.log"
    if log.is_file():
        text = log.read_text(encoding="utf-8", errors="replace")
        epochs = [int(m) for m in re.findall(r"^Epoch\s+(\d+):", text, re.M)]
        uniq = sorted(set(epochs))
        check("log 覆盖到末轮", bool(uniq) and uniq[-1] >= a.expect_epochs - 1,
              f"最大 epoch={uniq[-1] if uniq else 'NA'}，记录 {len(epochs)} 行 / 去重 {len(uniq)} 轮")
        check("log 无 NaN", not re.search(r"\bnan\b", text, re.I), "日志中未发现 nan")
        check("log 无中断标记", "训练被中断" not in text, "未出现 KeyboardInterrupt 记录")
    else:
        check("training.log 存在", False, str(log))

    check("无 checkpoint_INTERRUPTED.pth", not (models / "checkpoint_INTERRUPTED.pth").exists())

    print(f"\n结论: {'PASS — 可以进入下一步' if ok else 'FAIL — 见上方失败项'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
