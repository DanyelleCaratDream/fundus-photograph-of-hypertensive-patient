#!/usr/bin/env bash
# 分类器 pilot A0–A2（PILOT_PREREG_20261112.md §4；DL-EX-027）
# 用法：bash classify_project/scripts/run_pilot_a0_a2.sh
# 预算：3 seeds × 30 epochs / arm，约 0.5 h/arm（8GB 卡，GPU 空闲时跑）
set -u
cd "$(dirname "$0")/../.."   # 项目根
mkdir -p classify_project/results

run() {
  local tag="$1"; shift
  echo "########## ${tag} ##########"
  python -X utf8 classify_project/scripts/train_classifier.py \
    --data fundus/HRSG_4_758_sq256 --size 256 \
    --seeds 42 52 62 --epochs 30 --num-workers 0 \
    --out "classify_project/results/pilot_${tag}_20261115.json" "$@"
}

run A0
run A1 --logit-adjust
run A2 --drc --drc-stage2-epochs 10 --drc-stage2-lr 1e-3

echo "########## 全部完成 ##########"
