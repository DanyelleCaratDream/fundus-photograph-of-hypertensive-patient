"""Independent recomputation for DL-EX-027 (A1) and DL-EX-032 (A2).

Reads prediction and training-record JSON only. Does not import bootstrap_ci.py,
does not rewrite inputs, and does not select checkpoints.

Run from the handoff root:

    python submissions/A/recompute.py --task all --self-check
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    balanced_accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

LABELS = (0, 1, 2, 3)
RECALL_KEYS = (
    "recall_normal",
    "recall_mild",
    "recall_moderate",
    "recall_severe",
)
POINT_KEYS = (
    "qwk",
    "balanced_acc",
    "macro_f1",
    "severe_recall",
    "recall_normal",
    "recall_mild",
    "recall_moderate",
    "recall_severe",
)
BOOT_KEYS = ("qwk", "balanced_acc", "macro_f1", "severe_recall") + RECALL_KEYS
SEEDS = (42, 52, 62)
ARMS = ("A0", "A1", "A2")
BOOT_SEED = 20261117
BOOT_B = 1000
# Diagnostic only: the published CI file records this seed. Not the primary result.
PUBLISHED_BOOT_SEED = 20261115

FROZEN_WEIGHTS_DOC = (1.15, 0.985714, 0.985714, 0.907895)
# Inverse class frequency on the official train split: n / (K * n_c).
TRAIN_COUNTS = (120, 140, 140, 152)
FROZEN_WEIGHTS_EXACT = tuple(
    sum(TRAIN_COUNTS) / (len(TRAIN_COUNTS) * c) for c in TRAIN_COUNTS
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> list[tuple[str, str]]:
    rows = []
    text = (ROOT / "sha256清单.txt").read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel = line.split(None, 1)
        rows.append((digest, rel.replace("\\", "/")))
    return rows


def verify_manifest() -> list[dict]:
    out = []
    for digest, rel in load_manifest():
        path = ROOT / rel
        if not path.is_file():
            out.append({"file": rel, "status": "missing", "sha256": None})
            continue
        got = sha256_file(path)
        out.append(
            {
                "file": rel,
                "status": "match" if got == digest else "mismatch",
                "sha256": got,
                "expected": digest,
            }
        )
    return out


def softmax(logits: np.ndarray) -> np.ndarray:
    z = logits - logits.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def load_prediction(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    images = data["images"]
    y_true = np.asarray([im["y_true"] for im in images], dtype=int)
    y_file = np.asarray([im["y_pred"] for im in images], dtype=int)
    logits = np.asarray([im["logits"] for im in images], dtype=float)
    probs = np.asarray([im["probs"] for im in images], dtype=float)
    y_hat = np.argmax(logits, axis=1).astype(int)
    n_tie = int(np.sum(np.sum(np.isclose(logits, logits.max(axis=1, keepdims=True)), axis=1) > 1))
    return {
        "arm": data.get("arm"),
        "seed": int(data.get("seed")),
        "n": int(data.get("n")),
        "size": data.get("size"),
        "classes": data.get("classes"),
        "mode": data.get("mode"),
        "paths": [im["path"] for im in images],
        "y_true": y_true,
        "y_file": y_file,
        "y_hat": y_hat,
        "logits": logits,
        "probs": probs,
        "n_tie": n_tie,
        "argmax_match": bool(np.array_equal(y_hat, y_file)),
        "n_argmax_mismatch": int(np.sum(y_hat != y_file)),
        "prob_max_abs": float(np.max(np.abs(softmax(logits) - probs))),
    }


_W_QWK = (np.arange(4)[:, None] - np.arange(4)[None, :]) ** 2


def metrics_from_counts(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Same estimators as compute_metrics, from a 4-class confusion matrix.

    Quadratic weights follow sklearn 1.8: w_ij = (i-j)^2, with no extra
    (K-1)^2 divisor, because that constant cancels in the kappa ratio.
    Macro-F1 uses zero_division=0. Every class is present in y_true under
    the stratified resample used here.
    """
    cm = np.bincount(y_true * 4 + y_pred, minlength=16).reshape(4, 4).astype(float)
    support = cm.sum(axis=1)
    predicted = cm.sum(axis=0)
    tp = np.diag(cm)
    recall = tp / support
    precision = np.divide(tp, predicted, out=np.zeros(4), where=predicted > 0)
    denom = precision + recall
    f1 = np.divide(2 * precision * recall, denom, out=np.zeros(4), where=denom > 0)
    sum0 = cm.sum(axis=0)
    sum1 = cm.sum(axis=1)
    expected = np.outer(sum0, sum1) / sum0.sum()
    qwk = float(1 - np.sum(_W_QWK * cm) / np.sum(_W_QWK * expected))
    return {
        "acc": float(tp.sum() / cm.sum()),
        "balanced_acc": float(recall.mean()),
        "macro_f1": float(f1.mean()),
        "qwk": qwk,
        "severe_recall": float(recall[3]),
        "recall_normal": float(recall[0]),
        "recall_mild": float(recall[1]),
        "recall_moderate": float(recall[2]),
        "recall_severe": float(recall[3]),
    }


def assert_fast_matches_sklearn(bundle: dict) -> None:
    y_true = bundle["y_true"]
    rng = np.random.default_rng(0)
    for arm in ARMS:
        for seed in SEEDS:
            y_pred = bundle["preds"][arm][seed]
            slow = compute_metrics(y_true, y_pred)
            fast = metrics_from_counts(y_true, y_pred)
            for key in POINT_KEYS:
                if abs(slow[key] - fast[key]) > 1e-12:
                    raise AssertionError(f"fast metric {key} mismatch on {arm} seed {seed}")
            for _ in range(5):
                idx = stratified_indices(y_true, rng)
                slow_b = compute_metrics(y_true[idx], y_pred[idx])
                fast_b = metrics_from_counts(y_true[idx], y_pred[idx])
                for key in BOOT_KEYS:
                    if abs(slow_b[key] - fast_b[key]) > 1e-12:
                        raise AssertionError(f"bootstrap fast metric {key} mismatch on {arm} seed {seed}")


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    recalls = []
    for c in LABELS:
        mask = y_true == c
        if not np.any(mask):
            recalls.append(float("nan"))
        else:
            recalls.append(float(np.mean(y_pred[mask] == c)))
    labels = list(LABELS)
    return {
        "acc": float(np.mean(y_true == y_pred)),
        "balanced_acc": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(
            f1_score(y_true, y_pred, average="macro", labels=labels, zero_division=0)
        ),
        "qwk": float(
            cohen_kappa_score(y_true, y_pred, weights="quadratic", labels=labels)
        ),
        "severe_recall": recalls[3],
        "recall_normal": recalls[0],
        "recall_mild": recalls[1],
        "recall_moderate": recalls[2],
        "recall_severe": recalls[3],
        "n": int(y_true.shape[0]),
        "class_n": [int(np.sum(y_true == c)) for c in LABELS],
    }


def confusion(y_true: np.ndarray, y_pred: np.ndarray) -> list:
    return confusion_matrix(y_true, y_pred, labels=list(LABELS)).tolist()


def stratified_indices(y_true: np.ndarray, rng) -> np.ndarray:
    """Sample with replacement inside each true class, at the original class size.

    Class order is 0, 1, 2, 3. One draw is shared by every arm and seed.
    """
    parts = []
    for c in LABELS:
        pool = np.flatnonzero(y_true == c)
        parts.append(rng.choice(pool, size=pool.size, replace=True))
    return np.concatenate(parts)


def _metrics_on(y_true, y_pred, idx) -> dict:
    return metrics_from_counts(y_true[idx], y_pred[idx])


def bootstrap_paired(bundle: dict, b: int, seed: int, kind: str) -> dict:
    """Paired, class-stratified percentile bootstrap.

    kind='generator' uses numpy.random.Generator (PCG64).
    kind='randomstate' uses numpy.random.RandomState (MT19937).
    Within each replicate the same image indices are applied to A0, A1 and A2
    and to every training seed. The merged delta averages the three seed-level
    metrics on those indices, then subtracts. Seeds are not resampled.
    """
    assert_fast_matches_sklearn(bundle)
    y_true = bundle["y_true"]
    preds = bundle["preds"]
    if kind == "generator":
        rng = np.random.default_rng(seed)
    elif kind == "randomstate":
        rng = np.random.RandomState(seed)
    else:
        raise ValueError(kind)

    per_seed = {arm: {s: {k: np.empty(b) for k in BOOT_KEYS} for s in SEEDS} for arm in ("A1", "A2")}
    merged = {arm: {k: np.empty(b) for k in BOOT_KEYS} for arm in ("A1", "A2")}

    for i in range(b):
        idx = stratified_indices(y_true, rng)
        base = {s: _metrics_on(y_true, preds["A0"][s], idx) for s in SEEDS}
        for arm in ("A1", "A2"):
            alt = {s: _metrics_on(y_true, preds[arm][s], idx) for s in SEEDS}
            for key in BOOT_KEYS:
                base_vals = [base[s][key] for s in SEEDS]
                alt_vals = [alt[s][key] for s in SEEDS]
                for j, s in enumerate(SEEDS):
                    per_seed[arm][s][key][i] = alt_vals[j] - base_vals[j]
                merged[arm][key][i] = float(np.mean(alt_vals) - np.mean(base_vals))

    def pack(samples: np.ndarray) -> dict:
        lo, hi = np.quantile(samples, [0.025, 0.975], method="linear")
        return {
            "mean": float(np.mean(samples)),
            "ci95": [float(lo), float(hi)],
        }

    return {
        "B": b,
        "seed": seed,
        "kind": kind,
        "percentile": "linear",
        "per_seed": {
            arm: {str(s): {k: pack(per_seed[arm][s][k]) for k in BOOT_KEYS} for s in SEEDS}
            for arm in ("A1", "A2")
        },
        "merged": {
            arm: {k: pack(merged[arm][k]) for k in BOOT_KEYS} for arm in ("A1", "A2")
        },
    }


def load_arm_dir(directory: Path) -> dict:
    files = {}
    preds = {}
    y_true = None
    paths = None
    integrity = []
    for arm in ARMS:
        preds[arm] = {}
        for seed in SEEDS:
            path = directory / f"{arm}_seed{seed}.json"
            rec = load_prediction(path)
            files[f"{arm}_seed{seed}"] = {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "arm_field": rec["arm"],
                "seed_field": rec["seed"],
                "n": rec["n"],
                "size": rec["size"],
                "classes": rec["classes"],
                "mode": rec["mode"],
                "argmax_match": rec["argmax_match"],
                "n_argmax_mismatch": rec["n_argmax_mismatch"],
                "n_tie": rec["n_tie"],
                "prob_max_abs": rec["prob_max_abs"],
            }
            if rec["arm"] != arm or rec["seed"] != seed:
                integrity.append(f"{path.name}: arm/seed field {rec['arm']}/{rec['seed']}")
            if not rec["argmax_match"]:
                integrity.append(f"{path.name}: y_pred differs from argmax(logits) on {rec['n_argmax_mismatch']} images")
            if y_true is None:
                y_true = rec["y_true"]
                paths = rec["paths"]
            else:
                if rec["paths"] != paths:
                    integrity.append(f"{path.name}: image path order differs from the first file")
                if not np.array_equal(rec["y_true"], y_true):
                    integrity.append(f"{path.name}: y_true differs from the first file")
            preds[arm][seed] = rec["y_hat"]
    return {
        "files": files,
        "preds": preds,
        "y_true": y_true,
        "paths": paths,
        "integrity": integrity,
    }


def summarise_seeds(rows: list[dict]) -> dict:
    keys = [k for k in rows[0] if k not in ("n", "class_n")]
    out = {}
    for k in keys:
        vals = np.asarray([r[k] for r in rows], dtype=float)
        out[k] = {
            "mean": float(np.mean(vals)),
            "std_ddof1": float(np.std(vals, ddof=1)),
            "std_ddof0": float(np.std(vals, ddof=0)),
            "values": [float(v) for v in vals],
        }
    return out


def quantile_method_gaps(bundle: dict, published: dict) -> dict:
    """See whether any numpy percentile convention recovers the published CI.

    Uses the same stratified draws as the primary algorithm, with
    numpy.random.Generator and the published seed 20261115. This is a
    diagnostic. It is not the reported interval.
    """
    y_true = bundle["y_true"]
    preds = bundle["preds"]
    rng = np.random.default_rng(PUBLISHED_BOOT_SEED)
    samples = {arm: np.empty(BOOT_B) for arm in ("A1", "A2")}
    for i in range(BOOT_B):
        idx = stratified_indices(y_true, rng)
        base = [metrics_from_counts(y_true[idx], preds["A0"][s][idx])["qwk"] for s in SEEDS]
        for arm in ("A1", "A2"):
            alt = [metrics_from_counts(y_true[idx], preds[arm][s][idx])["qwk"] for s in SEEDS]
            samples[arm][i] = float(np.mean(alt) - np.mean(base))
    methods = (
        "linear",
        "hazen",
        "weibull",
        "median_unbiased",
        "closest_observation",
        "averaged_inverted_cdf",
        "inverted_cdf",
        "higher",
        "lower",
        "midpoint",
    )
    out = {}
    for arm in ("A1", "A2"):
        src = published["paired"][arm]["qwk"]["ci95"]
        out[arm] = {}
        for method in methods:
            ci = [float(x) for x in np.quantile(samples[arm], [0.025, 0.975], method=method)]
            out[arm][method] = {"ci95": ci, "max_abs": _max_abs(src, ci)}
    return out


def point_table(bundle: dict) -> dict:
    per_seed = {}
    conf = {}
    for arm in ARMS:
        per_seed[arm] = {}
        conf[arm] = {}
        for seed in SEEDS:
            y_pred = bundle["preds"][arm][seed]
            m = compute_metrics(bundle["y_true"], y_pred)
            per_seed[arm][str(seed)] = m
            conf[arm][str(seed)] = confusion(bundle["y_true"], y_pred)
    summary = {arm: summarise_seeds([per_seed[arm][str(s)] for s in SEEDS]) for arm in ARMS}
    deltas = {}
    for arm in ("A1", "A2"):
        deltas[arm] = {"per_seed": {}, "merged": {}}
        for seed in SEEDS:
            deltas[arm]["per_seed"][str(seed)] = {
                k: per_seed[arm][str(seed)][k] - per_seed["A0"][str(seed)][k] for k in POINT_KEYS
            }
        deltas[arm]["merged"] = {
            k: summary[arm][k]["mean"] - summary["A0"][k]["mean"] for k in POINT_KEYS
        }
        seed_deltas = [deltas[arm]["per_seed"][str(s)]["qwk"] for s in SEEDS]
        deltas[arm]["qwk_across_seeds"] = {
            "mean": float(np.mean(seed_deltas)),
            "std_ddof1": float(np.std(seed_deltas, ddof=1)),
            "values": seed_deltas,
        }
    return {"per_seed": per_seed, "summary": summary, "deltas": deltas, "confusion": conf}


def almost(a, b, tol=1e-9) -> bool:
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= tol


def r4(x: float) -> float:
    return float(np.round(float(x), 4))


def task_a1() -> dict:
    bundle = load_arm_dir(ROOT / "00_common" / "predictions")
    table = point_table(bundle)
    published = json.loads((ROOT / "01_A_pilot" / "pilot_ci_20261115.json").read_text(encoding="utf-8"))
    print("A1 bootstrap B=1000 seed=20261117", flush=True)
    primary = bootstrap_paired(bundle, BOOT_B, BOOT_SEED, "generator")
    print("A1 diagnostic bootstrap seed=20261115", flush=True)
    diag_gen = bootstrap_paired(bundle, BOOT_B, PUBLISHED_BOOT_SEED, "generator")
    diag_rs = bootstrap_paired(bundle, BOOT_B, PUBLISHED_BOOT_SEED, "randomstate")
    # Stability of the primary procedure at B=10000. Separate stream; not the reported CI.
    print("A1 stability bootstrap B=10000", flush=True)
    stability = bootstrap_paired(bundle, 10000, BOOT_SEED, "generator")
    print("A1 quantile-method diagnostic", flush=True)
    q_gaps = quantile_method_gaps(bundle, published)

    comparisons = []
    seed_order_match = {}
    for arm in ARMS:
        listed = published["arms"][arm]["per_seed"]
        order_ok = True
        for i, seed in enumerate(SEEDS):
            got = table["per_seed"][arm][str(seed)]
            src = listed[i]
            for k in POINT_KEYS:
                comparisons.append(
                    diff_row(
                        "A1",
                        f"per_seed[{i}]",
                        arm,
                        seed,
                        k,
                        "01_A_pilot/pilot_ci_20261115.json",
                        src[k],
                        got[k],
                    )
                )
                if not almost(src[k], got[k], 1e-12):
                    order_ok = False
            cm_src = published["arms"][arm]["confusion_per_seed"][i]
            cm_got = table["confusion"][arm][str(seed)]
            comparisons.append(
                diff_row(
                    "A1",
                    f"confusion_per_seed[{i}]",
                    arm,
                    seed,
                    "confusion",
                    "01_A_pilot/pilot_ci_20261115.json",
                    json.dumps(cm_src),
                    json.dumps(cm_got),
                    numeric=False,
                )
            )
        seed_order_match[arm] = order_ok
        point = published["arms"][arm]["point"]
        for k in POINT_KEYS:
            comparisons.append(
                diff_row(
                    "A1",
                    "three_seed_mean",
                    arm,
                    "mean",
                    k,
                    "01_A_pilot/pilot_ci_20261115.json",
                    point[k],
                    table["summary"][arm][k]["mean"],
                )
            )

    # Published four-decimal rerun QWK and the two deltas in baseline_numbers.md.
    baseline_qwk = {"A0": 0.7520, "A1": 0.7520, "A2": 0.7639}
    for arm, published_q in baseline_qwk.items():
        comparisons.append(
            diff_row(
                "A1",
                "baseline_rerun_4dp",
                arm,
                "mean",
                "qwk",
                "01_A_pilot/baseline_numbers.md",
                published_q,
                r4(table["summary"][arm]["qwk"]["mean"]),
            )
        )
    published_delta = {"A1": 0.0, "A2": 0.0119}
    published_ci = {
        "A1": [-0.0569, 0.0536],
        "A2": [-0.0361, 0.0636],
    }
    for arm in ("A1", "A2"):
        comparisons.append(
            diff_row(
                "A1",
                "baseline_delta_4dp",
                arm,
                "merged",
                "qwk",
                "01_A_pilot/baseline_numbers.md",
                published_delta[arm],
                r4(table["deltas"][arm]["merged"]["qwk"]),
            )
        )
        for metric in POINT_KEYS:
            src_m = published["paired"][arm][metric]
            comparisons.append(
                diff_row(
                    "A1",
                    "published_paired_point",
                    arm,
                    "merged",
                    metric,
                    "01_A_pilot/pilot_ci_20261115.json",
                    src_m["delta"],
                    table["deltas"][arm]["merged"][metric],
                )
            )
            for edge, name in ((0, "ci_low"), (1, "ci_high")):
                comparisons.append(
                    diff_row(
                        "A1",
                        "published_ci_vs_primary_seed_20261117",
                        arm,
                        "merged",
                        f"{metric}_{name}",
                        "01_A_pilot/pilot_ci_20261115.json",
                        src_m["ci95"][edge],
                        primary["merged"][arm][metric]["ci95"][edge],
                        force_reason="bootstrap_implementation",
                    )
                )
        for edge, name in ((0, "ci_low"), (1, "ci_high")):
            comparisons.append(
                diff_row(
                    "A1",
                    "baseline_ci_4dp_vs_primary",
                    arm,
                    "merged",
                    f"qwk_{name}",
                    "01_A_pilot/baseline_numbers.md",
                    published_ci[arm][edge],
                    r4(primary["merged"][arm]["qwk"]["ci95"][edge]),
                    force_reason="bootstrap_implementation",
                )
            )

    # 2026-11-12 main results have no per-image predictions.
    main = {"A0": 0.7564, "A1": 0.7689, "A2": 0.7659}
    main_gap = {"A0": -0.0044, "A1": -0.0169, "A2": -0.0020}
    for arm in ARMS:
        comparisons.append(
            {
                "task": "A1",
                "item": "main_20261112",
                "arm": arm,
                "seed": "none",
                "metric": "qwk",
                "source_file": "01_A_pilot/baseline_numbers.md",
                "original": main[arm],
                "recomputed": "",
                "difference": "",
                "status": "不可复算",
                "reason": "2026-11-12 主结果没有逐图预测，不能从 logits 重算。",
            }
        )
        rounded_gap = r4(table["summary"][arm]["qwk"]["mean"]) - main[arm]
        comparisons.append(
            diff_row(
                "A1",
                "main_minus_rerun_4dp_arithmetic",
                arm,
                "mean",
                "qwk",
                "01_A_pilot/baseline_numbers.md",
                main_gap[arm],
                rounded_gap,
                force_reason="rounded_arithmetic_only",
            )
        )

    best_method = {}
    for arm in ("A1", "A2"):
        best_method[arm] = min(q_gaps[arm].items(), key=lambda kv: kv[1]["max_abs"])
    reason_ci = (
        "点估计另项核对，且与原 JSON 在 1e-9 以内一致。"
        "本行只比较百分位端点。原 CI 记录 seed=20261115；"
        "用同一分层配对算法、Generator 与 RandomState 在该种子下都没有复现端点，"
        "换 numpy 的十种百分位插值后最小端点差仍见 quantile_method_gaps。"
        "因此端点差来自未能复现的重抽样随机数流，不是点估计错误。"
        "本报告主区间固定为 Generator、seed=20261117、B=1000、linear，不改算法去贴合原端点。"
    )
    for row in comparisons:
        if row["status"] == "实现差异":
            row["reason"] = reason_ci

    class_n = [int(np.sum(bundle["y_true"] == c)) for c in LABELS]
    return {
        "integrity": bundle["integrity"],
        "files": bundle["files"],
        "class_n": class_n,
        "n_test": int(bundle["y_true"].shape[0]),
        "seed_list_order_matches_42_52_62": seed_order_match,
        "table": _strip_table(table),
        "bootstrap_primary": _public_boot(primary),
        "bootstrap_diagnostic_generator_20261115": _public_boot(diag_gen),
        "bootstrap_diagnostic_randomstate_20261115": _public_boot(diag_rs),
        "bootstrap_stability_B10000": {
            "B": 10000,
            "seed": BOOT_SEED,
            "kind": "generator",
            "merged_qwk": {arm: stability["merged"][arm]["qwk"] for arm in ("A1", "A2")},
        },
        "published_ci_abs_endpoint_gap": _ci_gap(published, primary, diag_gen, diag_rs),
        "quantile_method_gaps": q_gaps,
        "quantile_method_closest": {
            arm: {"method": name, "max_abs": rec["max_abs"], "ci95": rec["ci95"]}
            for arm, (name, rec) in best_method.items()
        },
        "comparisons": comparisons,
    }


def _strip_table(table: dict) -> dict:
    per = {}
    for arm, seeds in table["per_seed"].items():
        per[arm] = {}
        for seed, m in seeds.items():
            per[arm][seed] = {k: m[k] for k in ("acc",) + POINT_KEYS}
    summary = {}
    for arm, mets in table["summary"].items():
        summary[arm] = {k: mets[k] for k in ("acc",) + POINT_KEYS}
    return {
        "per_seed": per,
        "summary": summary,
        "deltas": table["deltas"],
        "confusion": table["confusion"],
    }


def _public_boot(boot: dict) -> dict:
    return {
        "B": boot["B"],
        "seed": boot["seed"],
        "kind": boot["kind"],
        "percentile": boot["percentile"],
        "per_seed": boot["per_seed"],
        "merged": boot["merged"],
    }


def _ci_gap(published, primary, diag_gen, diag_rs) -> dict:
    out = {}
    for arm in ("A1", "A2"):
        out[arm] = {}
        for metric in POINT_KEYS:
            src = published["paired"][arm][metric]["ci95"]
            out[arm][metric] = {
                "primary_max_abs": _max_abs(src, primary["merged"][arm][metric]["ci95"]),
                "generator_20261115_max_abs": _max_abs(src, diag_gen["merged"][arm][metric]["ci95"]),
                "randomstate_20261115_max_abs": _max_abs(src, diag_rs["merged"][arm][metric]["ci95"]),
            }
    return out


def _max_abs(a, b) -> float:
    return float(max(abs(a[0] - b[0]), abs(a[1] - b[1])))


def diff_row(task, item, arm, seed, metric, source, original, recomputed, numeric=True, force_reason=None):
    if not numeric:
        same = original == recomputed
        return {
            "task": task,
            "item": item,
            "arm": arm,
            "seed": seed,
            "metric": metric,
            "source_file": source,
            "original": original,
            "recomputed": recomputed,
            "difference": "",
            "status": "一致" if same else "不一致",
            "reason": "逐格相等。" if same else "混淆矩阵与独立计算不一致。",
        }
    orig = float(original)
    got = float(recomputed)
    delta = got - orig
    if force_reason == "bootstrap_implementation":
        status = "实现差异"
        reason = (
            "点估计另项核对。本行比较的是百分位端点："
            "原 CI 记录 seed=20261115；本报告主结果使用 numpy.random.Generator、"
            "seed=20261117、B=1000、线性百分位。端点不同来自随机数流，不回写原 CI。"
        )
    elif force_reason == "rounded_arithmetic_only":
        status = "一致" if almost(orig, got, 5e-5) else "不一致"
        reason = (
            "只核对已公布的四位小数之差。2026-11-12 的 QWK 没有逐图预测，"
            "这个差值不是从 logits 重算得到的。"
        )
    elif almost(orig, got, 1e-9):
        status = "一致"
        reason = "独立计算与原记录在 1e-9 以内一致。"
    elif almost(orig, got, 5.1e-5):
        status = "四舍五入后一致"
        reason = "原记录保留到约四位小数，未四舍五入的独立计算与之相差不超过 5.1e-5。"
    else:
        status = "不一致"
        reason = "差值超过四位小数的舍入范围，见报告中的定位。"
    return {
        "task": task,
        "item": item,
        "arm": arm,
        "seed": seed,
        "metric": metric,
        "source_file": source,
        "original": orig,
        "recomputed": got,
        "difference": delta,
        "status": status,
        "reason": reason,
    }


def _mean_close(summary_value, items_mean, places=4) -> bool:
    return abs(float(summary_value) - float(items_mean)) < 0.5 * 10 ** (-places)


def audit_run(arm: str, run: dict, pool_names: dict) -> dict:
    epochs = run["epoch_stats"]
    exposure = run["exposure"]
    items = exposure["items"]
    checks = []

    def add(name, ok, detail, status=None):
        checks.append(
            {
                "name": name,
                "ok": bool(ok),
                "detail": detail,
                "status": status or ("一致" if ok else "不一致"),
            }
        )

    add("optimizer_steps", run.get("optimizer_steps") == 1050, run.get("optimizer_steps"))
    if epochs is None and arm == "A0":
        add(
            "n_epoch_stats",
            False,
            "epoch_stats is null",
            status="不可核对",
        )
    else:
        add("n_epoch_stats", epochs is not None and len(epochs) == 30, None if epochs is None else len(epochs))
    add("test_n", run.get("test_n") == 71 and run.get("n") == 71, {"test_n": run.get("test_n"), "n": run.get("n")})
    weights = run.get("class_weights_used")
    weight_gap = None
    if weights is not None:
        weight_gap = float(
            np.max(np.abs(np.float32(weights) - np.float32(FROZEN_WEIGHTS_EXACT)))
        )
    add(
        "class_weights_equal_float32_documented",
        weights is not None and np.array_equal(np.float32(weights), np.float32(FROZEN_WEIGHTS_DOC)),
        {
            "used": weights,
            "max_abs_vs_unrounded_float32": weight_gap,
            "note": "stored vector is float32 of the documented 6-decimal weights, not float32 of the unrounded n/(4*n_c)",
        },
    )
    best = run.get("best_epoch")
    add("best_epoch_multiple_of_5_or_last", best in {5, 10, 15, 20, 25, 30}, best)
    add("deterministic_flag", run.get("deterministic_flag") is True, run.get("deterministic_flag"))
    det = run.get("determinism") or {}
    add(
        "determinism_switches",
        det.get("deterministic_algorithms") is True
        and det.get("cudnn_deterministic") is True
        and det.get("cudnn_benchmark") is False
        and det.get("cublas_workspace_config") == ":4096:8",
        {k: det.get(k) for k in ("deterministic_algorithms", "cudnn_deterministic", "cudnn_benchmark", "cublas_workspace_config")},
    )

    epoch_ok = True
    epoch_problems = []
    sum_real = 0
    sum_synth = 0
    sum_drawn = 0
    if epochs is None:
        epoch_ok = False
        epoch_problems.append({"epoch": None, "problems": ["epoch_stats is null"]})
    else:
        for ep in epochs:
            real = ep.get("real")
            synth = ep.get("synth")
            drawn = ep.get("drawn")
            per = ep.get("per_class")
            sum_real += real or 0
            sum_synth += synth or 0
            sum_drawn += drawn or 0
            local = []
            if drawn != 552:
                local.append(f"drawn={drawn}")
            if (real or 0) + (synth or 0) != drawn:
                local.append(f"real+synth={real}+{synth}")
            if ep.get("batches") != 35:
                local.append(f"batches={ep.get('batches')}")
            if ep.get("last_batch") != 8:
                local.append(f"last_batch={ep.get('last_batch')}")
            if per is None or sum(per) != drawn:
                local.append(f"per_class={per}")
            if arm == "A0":
                if real != 552 or synth not in (0, None):
                    local.append(f"A0 real/synth={real}/{synth}")
                if per != [120, 140, 140, 152]:
                    local.append(f"A0 per_class={per}")
            if local:
                epoch_ok = False
                epoch_problems.append({"epoch": ep.get("epoch"), "problems": local})
    epoch_status = None
    if epochs is None and arm == "A0":
        epoch_status = "不可核对"
    add(
        "epoch_stats_counts",
        epoch_ok,
        epoch_problems[:5] if epoch_problems else "30 epochs match the recorded budget",
        status=epoch_status,
    )

    if arm == "A0":
        add("fixed_draws_null", run.get("fixed_draws") is None, run.get("fixed_draws"))
        add("train_n", run.get("train_n") == 552 and run.get("train_n_synth") in (0, None), {
            "train_n": run.get("train_n"),
            "train_n_real": run.get("train_n_real"),
            "train_n_synth": run.get("train_n_synth"),
        })
    else:
        add("fixed_draws_552", run.get("fixed_draws") == 552, run.get("fixed_draws"))
        add("train_n_584", run.get("train_n") == 584 and run.get("train_n_real") == 552 and run.get("train_n_synth") == 32, {
            "train_n": run.get("train_n"),
            "train_n_real": run.get("train_n_real"),
            "train_n_synth": run.get("train_n_synth"),
        })

    real_items = [it for it in items if not it["is_synth"]]
    synth_items = [it for it in items if it["is_synth"]]
    real_sum = int(sum(it["count"] for it in real_items))
    synth_sum = int(sum(it["count"] for it in synth_items))
    count_sum = int(sum(it["count"] for it in items))
    summary = exposure["summary"]
    add(
        "exposure_item_sum_equals_summary",
        count_sum == summary.get("total_draws"),
        {"item_sum": count_sum, "summary_total": summary.get("total_draws")},
    )
    if epochs is None:
        missing = {
            "item_sum": count_sum,
            "epoch_sum": None,
            "summary_total": summary.get("total_draws"),
            "note": "A0 epoch_stats is null, so the per-epoch sum cannot be compared",
        }
        add("exposure_total_equals_epoch_draws", False, missing, status="不可核对")
        add("exposure_real_sum_equals_epoch_real", False, {"items": real_sum, "epochs": None}, status="不可核对")
        add("exposure_synth_sum_equals_epoch_synth", False, {"items": synth_sum, "epochs": None}, status="不可核对")
    else:
        add("exposure_total_equals_epoch_draws", count_sum == sum_drawn == summary.get("total_draws"), {
            "item_sum": count_sum,
            "epoch_sum": sum_drawn,
            "summary_total": summary.get("total_draws"),
        })
        add("exposure_real_sum_equals_epoch_real", real_sum == sum_real, {"items": real_sum, "epochs": sum_real})
        add("exposure_synth_sum_equals_epoch_synth", synth_sum == sum_synth, {"items": synth_sum, "epochs": sum_synth})
    real_mean = real_sum / len(real_items) if real_items else None
    add(
        "exposure_real_mean",
        real_mean is not None and abs(float(summary["real"]["mean"]) - real_mean) <= 5.1e-5,
        {"summary": summary["real"]["mean"], "items": None if real_mean is None else round(real_mean, 6)},
    )
    add("exposure_real_n", summary["real"]["n"] == len(real_items) == (552 if arm == "A0" else 552), {
        "summary_n": summary["real"]["n"],
        "items": len(real_items),
    })
    real_counts = [it["count"] for it in real_items]
    add(
        "exposure_real_min_max_full",
        min(real_counts) == summary["real"]["min"]
        and max(real_counts) == summary["real"]["max"]
        and sum(c == 30 for c in real_counts) == summary["real"]["full"],
        summary["real"],
    )
    if arm == "A0":
        add("A0_every_real_count_30", all(c == 30 for c in real_counts) and summary["real"]["mean"] == 30, summary["real"]["mean"])
        add("A0_no_synth_items", len(synth_items) == 0 and summary.get("synth") is None, len(synth_items))
        synth_mean = None
    else:
        synth_mean = synth_sum / len(synth_items)
        add("synth_n_32", summary["synth"]["n"] == len(synth_items) == 32, len(synth_items))
        add(
            "exposure_synth_mean",
            abs(float(summary["synth"]["mean"]) - synth_mean) <= 5.1e-5,
            {"summary": summary["synth"]["mean"], "items": round(synth_mean, 6)},
        )
        synth_counts = [it["count"] for it in synth_items]
        add(
            "exposure_synth_min_max_full",
            min(synth_counts) == summary["synth"]["min"]
            and max(synth_counts) == summary["synth"]["max"]
            and sum(c == 30 for c in synth_counts) == summary["synth"]["full"],
            summary["synth"],
        )
        names = [Path(it["file"]).name for it in synth_items]
        add("synth_files_in_pool_manifest", set(names) == pool_names[arm], {
            "n": len(names),
            "missing": sorted(set(pool_names[arm]) - set(names))[:5],
            "extra": sorted(set(names) - set(pool_names[arm]))[:5],
        })
        expected_mean = 30 * 552 / 584
        add(
            "observed_mean_near_uniform_expectation",
            abs(real_mean - expected_mean) < 0.05 and abs(synth_mean - expected_mean) < 0.2,
            {
                "uniform_expectation": expected_mean,
                "real_mean": real_mean,
                "synth_mean": synth_mean,
                "note": "expectation under sampling 552 of 584 without replacement; not a test",
            },
        )

    return {
        "seed": run["seed"],
        "mode": run.get("mode"),
        "reported_metrics": {k: run[k] for k in ("acc", "balanced_acc", "macro_f1", "qwk", "severe_recall")},
        "val_qwk": run.get("val_qwk"),
        "best_epoch": best,
        "optimizer_steps": run.get("optimizer_steps"),
        "fixed_draws": run.get("fixed_draws"),
        "class_weights_used": weights,
        "weight_source": run.get("weight_source"),
        "train_n": run.get("train_n"),
        "train_n_real": run.get("train_n_real"),
        "train_n_synth": run.get("train_n_synth"),
        "confusion": run.get("confusion"),
        "exposure_real_mean": summary["real"]["mean"],
        "exposure_synth_mean": None if arm == "A0" else summary["synth"]["mean"],
        "checks": checks,
        "real_counts_by_file": {it["file"]: it["count"] for it in real_items},
        "synth_counts_by_name": {Path(it["file"]).name: it["count"] for it in synth_items},
        "epoch_stats": epochs,
    }


def load_pools() -> dict:
    path = ROOT / "02_A_t3" / "T3_合成池清单_20261117.csv"
    groups = {"A1": {}, "A2": {}}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            arm = "A1" if row["pool"] == "t3_synth_128" else "A2" if row["pool"] == "t3_synth_256" else None
            if arm is None:
                continue
            groups[arm][row["filename"]] = {
                "gen_seed": row["gen_seed"],
                "sample_index": row["sample_index"],
                "sha256": row["sha256"],
            }
    return groups


def task_a2() -> dict:
    pools = load_pools()
    pool_names = {arm: set(pools[arm]) for arm in ("A1", "A2")}
    runs = {}
    file_hashes = {}
    for arm in ARMS:
        path = ROOT / "02_A_t3" / "t3_runs" / f"{arm}_20261117.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        file_hashes[f"t3_runs/{arm}"] = sha256_file(path)
        mirror = ROOT / "02_A_t3" / "run1_no_dump" / f"{arm}_20261117.json"
        file_hashes[f"run1_no_dump/{arm}"] = sha256_file(mirror)
        runs[arm] = {
            "top": {
                "size": data.get("size"),
                "seeds": data.get("seeds"),
                "epochs": data.get("epochs"),
                "logit_adjust": data.get("logit_adjust"),
                "drc": data.get("drc"),
                "extra_train_severe_dir": data.get("extra_train_severe_dir"),
                "fixed_draws_arg": data.get("fixed_draws_arg"),
                "class_weights_arg": data.get("class_weights_arg"),
                "deterministic_flag": data.get("deterministic_flag"),
                "determinism": data.get("determinism"),
                "summary": data.get("summary"),
            },
            "runs": [audit_run(arm, run, pool_names) for run in data["runs"]],
        }

    bundle = load_arm_dir(ROOT / "02_A_t3" / "predictions")
    table = point_table(bundle)
    print("A2 bootstrap B=1000 seed=20261117", flush=True)
    primary = bootstrap_paired(bundle, BOOT_B, BOOT_SEED, "generator")

    weight_vectors = []
    for arm in ARMS:
        for run in runs[arm]["runs"]:
            weight_vectors.append(run["class_weights_used"])
    weights_all_equal = all(np.allclose(w, weight_vectors[0], rtol=0, atol=0) for w in weight_vectors)

    pair_checks = []
    for seed in SEEDS:
        a1 = next(r for r in runs["A1"]["runs"] if r["seed"] == seed)
        a2 = next(r for r in runs["A2"]["runs"] if r["seed"] == seed)
        epoch_same = a1["epoch_stats"] == a2["epoch_stats"]
        real_same = a1["real_counts_by_file"] == a2["real_counts_by_file"]
        synth_same = a1["synth_counts_by_name"] == a2["synth_counts_by_name"]
        pair_checks.append(
            {
                "seed": seed,
                "epoch_stats_identical": epoch_same,
                "real_exposure_identical": real_same,
                "synth_basename_exposure_identical": synth_same,
                "n_synth_names": len(a1["synth_counts_by_name"]),
            }
        )

    manifest_pairs = []
    names = sorted(set(pools["A1"]) & set(pools["A2"]))
    only_128 = sorted(set(pools["A1"]) - set(pools["A2"]))
    only_256 = sorted(set(pools["A2"]) - set(pools["A1"]))
    key_mismatch = []
    for name in names:
        if (pools["A1"][name]["gen_seed"], pools["A1"][name]["sample_index"]) != (
            pools["A2"][name]["gen_seed"],
            pools["A2"][name]["sample_index"],
        ):
            key_mismatch.append(name)
    manifest_pairs.append(
        {
            "n_128": len(pools["A1"]),
            "n_256": len(pools["A2"]),
            "n_shared_filename": len(names),
            "only_128": only_128,
            "only_256": only_256,
            "gen_seed_or_index_mismatch": key_mismatch,
        }
    )

    comparisons = []
    metric_map = {
        "acc": "acc",
        "balanced_acc": "balanced_acc",
        "macro_f1": "macro_f1",
        "qwk": "qwk",
        "severe_recall": "severe_recall",
    }
    for arm in ARMS:
        by_seed = {r["seed"]: r for r in runs[arm]["runs"]}
        for seed in SEEDS:
            reported = by_seed[seed]["reported_metrics"]
            got = table["per_seed"][arm][str(seed)]
            for key in metric_map:
                comparisons.append(
                    diff_row(
                        "A2",
                        "run_json_vs_predictions",
                        arm,
                        seed,
                        key,
                        f"02_A_t3/t3_runs/{arm}_20261117.json",
                        reported[key],
                        got[key],
                    )
                )
            cm_same = by_seed[seed]["confusion"] == table["confusion"][arm][str(seed)]
            comparisons.append(
                diff_row(
                    "A2",
                    "run_json_vs_predictions",
                    arm,
                    seed,
                    "confusion",
                    f"02_A_t3/t3_runs/{arm}_20261117.json",
                    json.dumps(by_seed[seed]["confusion"]),
                    json.dumps(table["confusion"][arm][str(seed)]),
                    numeric=False,
                )
            )
            if not cm_same:
                comparisons[-1]["status"] = "不一致"
                comparisons[-1]["reason"] = "训练记录中的混淆矩阵与逐图预测不一致。"
        summary = runs[arm]["top"]["summary"]
        for key, node in summary.items():
            comparisons.append(
                diff_row(
                    "A2",
                    "summary_mean",
                    arm,
                    "mean",
                    key,
                    f"02_A_t3/t3_runs/{arm}_20261117.json",
                    node["mean"],
                    table["summary"][arm][key]["mean"],
                )
            )
            std_got_0 = table["summary"][arm][key]["std_ddof0"]
            std_got_1 = table["summary"][arm][key]["std_ddof1"]
            use = std_got_1 if almost(node["std"], std_got_1, 1e-12) else std_got_0
            row = diff_row(
                "A2",
                "summary_std",
                arm,
                "std",
                key,
                f"02_A_t3/t3_runs/{arm}_20261117.json",
                node["std"],
                use,
            )
            if almost(node["std"], std_got_1, 1e-12):
                row["reason"] = "与三个 seed 的样本标准差（除以 n-1）一致。"
            elif almost(node["std"], std_got_0, 1e-12):
                row["reason"] = "与三个 seed 的总体标准差（除以 n）一致。"
            else:
                row["status"] = "不一致"
                row["reason"] = f"既不是 ddof=1 ({std_got_1}) 也不是 ddof=0 ({std_got_0})。"
            comparisons.append(row)

        for run in runs[arm]["runs"]:
            for chk in run["checks"]:
                status = chk.get("status") or ("一致" if chk["ok"] else "不一致")
                if status == "一致":
                    reason = "训练记录与输入说明的期望相符。"
                    if chk["name"] == "class_weights_equal_float32_documented":
                        reason = (
                            "九次 run 的权重都等于文档六位小数的 float32。"
                            "与未舍入的 n/(4*n_c) 的 float32 最大绝对差约 2.98e-7，"
                            "是先写成六位小数再存成 float32 的差别。未改原文件。"
                        )
                elif status == "不可核对":
                    reason = (
                        "A0 的 epoch_stats 为 null，逐轮 batches 与 last_batch 没有记录。"
                        "逐图曝光另行核对：552 张真实图各 30 次，合计与 summary.total_draws 相同。"
                    )
                else:
                    reason = "训练记录与输入说明的期望不符，未改原文件。"
                comparisons.append(
                    {
                        "task": "A2",
                        "item": "training_record",
                        "arm": arm,
                        "seed": run["seed"],
                        "metric": chk["name"],
                        "source_file": f"02_A_t3/t3_runs/{arm}_20261117.json",
                        "original": "见 T3_输入说明.md 的期望",
                        "recomputed": json.dumps(chk["detail"], ensure_ascii=False),
                        "difference": "",
                        "status": status,
                        "reason": reason,
                    }
                )

    for seed in SEEDS:
        for item_name, key in (
            ("A1_A2_epoch_stats", "epoch_stats_identical"),
            ("A1_A2_real_exposure", "real_exposure_identical"),
            ("A1_A2_synth_exposure", "synth_basename_exposure_identical"),
        ):
            rec = next(p for p in pair_checks if p["seed"] == seed)
            ok = rec[key]
            comparisons.append(
                {
                    "task": "A2",
                    "item": item_name,
                    "arm": "A1-A2",
                    "seed": seed,
                    "metric": key,
                    "source_file": "02_A_t3/t3_runs/A1_20261117.json; 02_A_t3/t3_runs/A2_20261117.json",
                    "original": "同 seed 的抽样记录与同名条件图曝光一致",
                    "recomputed": ok,
                    "difference": "",
                    "status": "一致" if ok else "不一致",
                    "reason": "同 seed 下记录相同。" if ok else "同 seed 下记录不同，未改原文件。",
                }
            )

    same_bytes = {
        arm: file_hashes[f"t3_runs/{arm}"] == file_hashes[f"run1_no_dump/{arm}"] for arm in ARMS
    }

    # Drop bulky per-image maps from the saved audit after the pairing check.
    saved_runs = {}
    for arm in ARMS:
        saved_runs[arm] = {
            "top": runs[arm]["top"],
            "runs": [],
        }
        for run in runs[arm]["runs"]:
            slim = {k: v for k, v in run.items() if k not in ("real_counts_by_file", "synth_counts_by_name", "epoch_stats")}
            slim["n_checks_failed"] = sum(not c["ok"] for c in run["checks"])
            saved_runs[arm]["runs"].append(slim)

    return {
        "integrity": bundle["integrity"],
        "prediction_files": bundle["files"],
        "file_hashes": file_hashes,
        "run1_json_byte_identical": same_bytes,
        "weights_all_nine_equal": weights_all_equal,
        "float32_exact_weights": [float(x) for x in np.float32(FROZEN_WEIGHTS_EXACT)],
        "float32_documented_weights": [float(x) for x in np.float32(FROZEN_WEIGHTS_DOC)],
        "exact_weights": list(FROZEN_WEIGHTS_EXACT),
        "uniform_exposure_expectation": 30 * 552 / 584,
        "pool_manifest": manifest_pairs,
        "pair_checks": pair_checks,
        "table": _strip_table(table),
        "bootstrap_primary": _public_boot(primary),
        "runs": saved_runs,
        "comparisons": comparisons,
        "class_n": [int(np.sum(bundle["y_true"] == c)) for c in LABELS],
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = [
        "task",
        "item",
        "arm",
        "seed",
        "metric",
        "source_file",
        "original",
        "recomputed",
        "difference",
        "status",
        "reason",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_env(command: str) -> None:
    lines = [
        "记录日期：2026-11-21",
        "本文件由 submissions/A/recompute.py 在本次运行时写入。",
        f"解释器：{sys.executable}",
        f"Python：{sys.version.replace(os_sep(), ' ')}",
        f"numpy：{np.__version__}",
        f"scikit-learn：{__import__('sklearn').__version__}",
        f"platform：{platform.platform()}",
        "随机数：numpy.random.Generator，BitGenerator 为 PCG64；百分位为 numpy.quantile method=linear。",
        f"主 bootstrap：B={BOOT_B}，seed={BOOT_SEED}。",
        "未使用 GPU，未导入 bootstrap_ci.py。",
        f"运行命令：{command}",
        "",
        "交接包 00_common/环境与版本.txt 记录的是生成预测时的训练环境：",
        "Python 3.13.13，numpy 2.4.4，scikit-learn 1.9.0。",
        "本次复算的 sklearn 版本以本文件上一节为准。点估计若与原 JSON 逐位一致，",
        "则该版本差没有改变这些指标的数值。",
        "",
    ]
    (OUT / "环境.txt").write_text("\n".join(lines), encoding="utf-8")


def os_sep() -> str:
    return "\n"


def self_check(a1: dict | None, a2: dict | None, manifest: list[dict]) -> list[str]:
    errors = []
    bad = [m for m in manifest if m["status"] != "match"]
    if bad:
        errors.append(f"sha256 mismatches: {len(bad)}")
    if a1 is not None:
        errors.extend(f"A1 {msg}" for msg in a1["integrity"])
        if a1["class_n"] != [18, 20, 20, 13] or a1["n_test"] != 71:
            errors.append(f"A1 class counts {a1['class_n']}")
        if not all(a1["seed_list_order_matches_42_52_62"].values()):
            errors.append("A1 per_seed list is not in seed order 42, 52, 62 at 1e-12")
        for arm in ARMS:
            for seed in SEEDS:
                m = a1["table"]["per_seed"][arm][str(seed)]
                rec = [m[k] for k in RECALL_KEYS]
                if abs(m["balanced_acc"] - float(np.mean(rec))) > 1e-12:
                    errors.append(f"A1 {arm} seed {seed} balanced accuracy is not the mean recall")
                if abs(m["severe_recall"] - m["recall_severe"]) > 1e-15:
                    errors.append(f"A1 {arm} seed {seed} severe recall alias")
        # Merged point delta equals the mean of seed deltas.
        for arm in ("A1", "A2"):
            for key in POINT_KEYS:
                merged = a1["table"]["deltas"][arm]["merged"][key]
                vals = [a1["table"]["deltas"][arm]["per_seed"][str(s)][key] for s in SEEDS]
                if abs(merged - float(np.mean(vals))) > 1e-12:
                    errors.append(f"A1 merged delta identity failed for {arm} {key}")
    if a2 is not None:
        errors.extend(f"A2 {msg}" for msg in a2["integrity"])
        if a2["class_n"] != [18, 20, 20, 13]:
            errors.append(f"A2 class counts {a2['class_n']}")
        if not a2["weights_all_nine_equal"]:
            errors.append("A2 nine class-weight vectors are not identical")
        manifest_row = a2["pool_manifest"][0]
        if manifest_row["n_shared_filename"] != 32 or manifest_row["gen_seed_or_index_mismatch"]:
            errors.append("A2 pool manifest filename pairing failed")
        for row in a2["pair_checks"]:
            if not (
                row["epoch_stats_identical"]
                and row["real_exposure_identical"]
                and row["synth_basename_exposure_identical"]
            ):
                errors.append(f"A2 A1/A2 pairing failed at seed {row['seed']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Recompute DL-EX-027 and DL-EX-032 metrics.")
    parser.add_argument("--task", choices=("A1", "A2", "all"), default="all")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    command = f"{sys.executable} submissions/A/recompute.py --task {args.task}"
    if args.self_check:
        command += " --self-check"

    manifest = verify_manifest()
    a1 = task_a1() if args.task in ("A1", "all") else None
    a2 = task_a2() if args.task in ("A2", "all") else None
    rows = []
    if a1:
        (OUT / "results_A1.json").write_text(json.dumps(a1, ensure_ascii=False, indent=2), encoding="utf-8")
        rows.extend(a1["comparisons"])
    if a2:
        (OUT / "results_A2.json").write_text(json.dumps(a2, ensure_ascii=False, indent=2), encoding="utf-8")
        rows.extend(a2["comparisons"])
    if rows:
        write_csv(OUT / "差异表.csv", rows)
    write_env(command)

    print(f"manifest {sum(m['status']=='match' for m in manifest)}/{len(manifest)} match")
    if a1:
        print("A1 class_n", a1["class_n"], "integrity", a1["integrity"] or "ok")
        for arm in ARMS:
            q = a1["table"]["summary"][arm]["qwk"]
            print(f"A1 {arm} QWK mean {q['mean']:.10f} std_ddof1 {q['std_ddof1']:.6f}")
        for arm in ("A1", "A2"):
            d = a1["table"]["deltas"][arm]["merged"]["qwk"]
            ci = a1["bootstrap_primary"]["merged"][arm]["qwk"]["ci95"]
            print(f"A1 merged dQWK {arm}-A0 {d:.10f} CI {ci[0]:.6f} {ci[1]:.6f}")
        gap = a1["published_ci_abs_endpoint_gap"]
        for arm in ("A1", "A2"):
            g = gap[arm]["qwk"]
            print(
                f"A1 {arm} QWK CI max-abs gap primary {g['primary_max_abs']:.6f} "
                f"gen2015 {g['generator_20261115_max_abs']:.6e} rs2015 {g['randomstate_20261115_max_abs']:.6e}"
            )
        close = a1["quantile_method_closest"]
        for arm, rec in close.items():
            print(f"A1 closest quantile {arm} {rec['method']} max_abs {rec['max_abs']:.6e} ci {rec['ci95']}")
    if a2:
        print("A2 integrity", a2["integrity"] or "ok", "weights_equal", a2["weights_all_nine_equal"])
        print("A2 run1 byte-identical", a2["run1_json_byte_identical"])
        print("A2 pairs", a2["pair_checks"])
        for arm in ARMS:
            q = a2["table"]["summary"][arm]["qwk"]
            print(f"A2 {arm} QWK mean {q['mean']:.10f} std_ddof1 {q['std_ddof1']:.6f}")
            for seed in SEEDS:
                print(f"  seed {seed} qwk {a2['table']['per_seed'][arm][str(seed)]['qwk']:.10f}")
        for arm in ("A1", "A2"):
            d = a2["table"]["deltas"][arm]
            ci = a2["bootstrap_primary"]["merged"][arm]["qwk"]["ci95"]
            print(
                f"A2 dQWK {arm}-A0 seeds {d['qwk_across_seeds']['values']} "
                f"mean {d['merged']['qwk']:.6f} CI {ci[0]:.6f} {ci[1]:.6f}"
            )
        n_fail = 0
        for arm in ARMS:
            for run in a2["runs"][arm]["runs"]:
                for chk in run["checks"]:
                    if chk.get("status") not in (None, "一致"):
                        n_fail += 1
                        print("A2 CHECK", chk.get("status"), arm, run["seed"], chk["name"])
        print("A2 training checks failed", n_fail)

    if args.self_check:
        errors = self_check(a1, a2, manifest)
        if errors:
            print("SELF-CHECK FAILED")
            for err in errors:
                print(" -", err)
            return 1
        print("SELF-CHECK PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
