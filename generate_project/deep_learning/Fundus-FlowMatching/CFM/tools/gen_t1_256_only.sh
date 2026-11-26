#!/usr/bin/env bash
# T1-256 只生成（不训练）——自动生成阶段失败（OOM / 中断）后的补跑脚本
#
#   run_t1_256.sh 的生成段用 generate.py 默认批量 8；8GB 卡在 256px 下可能 OOM。
#   本脚本默认 --gen_batch_size 4（训练时预览用的档位，已验证可用）。
#
# 用法
#   bash tools/gen_t1_256_only.sh --dry-run
#   bash tools/gen_t1_256_only.sh                 # 只跑缺失的 seed
#   bash tools/gen_t1_256_only.sh --force         # 删掉已有 singles 重跑
#   BATCH=2 bash tools/gen_t1_256_only.sh         # 更保守的批量
set -euo pipefail

CFM="D:/AI_Model_Project_for_Fundus_Color_Images/generate_project/deep_learning/Fundus-FlowMatching/CFM"
DL="D:/AI_Model_Project_for_Fundus_Color_Images/generate_project/deep_learning"
CKPT="$CFM/results/cfm256_hrsevere_t1_ac/models/final_model.pth"
CONDS="$CFM/data/conditions_hrsevere_61_256"
JUDGE="$CFM/judgment/t1_256"
SEEDS=(42 1042 2042 3042)
PY="${PY:-python}"
BATCH="${BATCH:-4}"

DRY=0
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --force) FORCE=1 ;;
    *) echo "未知参数: $arg"; exit 2 ;;
  esac
done

[ -f "$CKPT" ] || { echo "[FAIL] 找不到权重: $CKPT"; exit 1; }
[ -d "$CONDS" ] || { echo "[FAIL] 找不到条件图: $CONDS"; exit 1; }

echo "权重: $CKPT"
echo "批量: $BATCH（seed × 8 条件 = 32 张，raw / Euler 50 NFE）"

for s in "${SEEDS[@]}"; do
  OUT="$JUDGE/cfm256_hrsevere_t1_ac_raw_seed$s"
  n=$(ls "$OUT/singles"/*.png 2>/dev/null | wc -l | tr -d ' ')
  if [ "$FORCE" = "1" ] && [ -d "$OUT" ]; then
    echo "[FORCE] 删除已有输出: $OUT"
    [ "$DRY" = "1" ] || rm -rf "$OUT"
    n=0
  fi
  if [ "$n" -ge 8 ]; then
    echo "[SKIP] seed$s 已有 $n 张"
    continue
  fi
  echo "+ seed$s 生成"
  [ "$DRY" = "1" ] && continue
  "$PY" "$DL/Fundus-Diffusion/ddpm/generate.py" \
    --checkpoint "$CKPT" \
    --num_images 8 \
    --seed "$s" \
    --sampling_steps 50 \
    --img_size 256 \
    --base_dim 128 \
    --cond_path "$CONDS" \
    --output_dir "$OUT" \
    --grid_size 0 \
    --sampler auto \
    --gen_batch_size "$BATCH" \
    --use_raw
done

echo
echo "生成段结束。下一步：python tools/make_t1_256_blind_sheet.py（盲评拼图 + key）"
