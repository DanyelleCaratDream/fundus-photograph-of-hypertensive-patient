#!/usr/bin/env bash
# DL-EX-032：T3 合成 HR-severe 图像分类增强 pilot（9 次训练）
#   用法：bash classify_project/scripts/run_t3_pilot.sh          # 全部 9 次
#         bash classify_project/scripts/run_t3_pilot.sh A1         # 只跑某组
#   前置：T3_代码修改与冒烟_20261117.md 的检查已通过、导师已确认
set -u
cd "$(dirname "$0")/../.."

# 必须在启动 Python（CUDA 初始化）之前生效，供确定性模式的 cuBLAS 使用
export CUBLAS_WORKSPACE_CONFIG=:4096:8

DATA=fundus/HRSG_4_758_sq256
OUT=classify_project/results/t3_pilot
CW="1.15,0.985714,0.985714,0.907895"     # 冻结：由 A0 真实训练集 552 张算出
SEEDS="42 52 62"
DETERMINISTIC="--deterministic"          # DL-EX-032 三组统一
MAX_GPU_TEMP="${MAX_GPU_TEMP:-75}"       # 温度护栏（可用环境变量覆盖；0=关闭）（导师 2026-11-17 批准方案 B）
mkdir -p "$OUT"

run() {
  local tag="$1"; shift
  echo "########## ${tag} ##########"
  python -X utf8 classify_project/scripts/train_classifier.py \
    --data "$DATA" --size 256 --seeds $SEEDS --epochs 30 \
    --batch-size 16 --lr 1e-4 --num-workers 0 --quiet \
    --class-weights "$CW" --arm-label "$tag" $DETERMINISTIC \
    --max-gpu-temp "$MAX_GPU_TEMP" \
    --dump-predictions "$OUT/predictions" \
    --out "$OUT/${tag}_20261117.json" "$@"
}

want="${1:-ALL}"
case "$want" in
  ALL|A0) run A0 ;;
esac
case "$want" in
  ALL|A1) run A1 --extra-train-severe-dir fundus/t3_synth_128 --fixed-draws 552 ;;
esac
case "$want" in
  ALL|A2) run A2 --extra-train-severe-dir fundus/t3_synth_256 --fixed-draws 552 ;;
esac

echo "########## 完成 ##########"
