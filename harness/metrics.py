"""
metrics.py — EH-2: Compute all evaluation metrics from results/raw.csv.

The independent variable is *strategy* (model is constant = CLAUDE_MODEL).
Metrics are computed per strategy. Significance test compares strategies pairwise.
Outputs metrics to results/metrics.json and prints tables.
"""

import sys
import json
import logging
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    cohen_kappa_score, confusion_matrix,
)
from scipy.stats import chi2_contingency

logger = logging.getLogger(__name__)
logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(message)s")

RAW_CSV = ROOT / "results" / "raw.csv"
METRICS_JSON = ROOT / "results" / "metrics.json"
LABEL_ORDER = ["recommend", "limit", "avoid"]


def compute_metrics(df: pd.DataFrame, group_name: str) -> dict:
    """Compute all metrics for a subset of the dataframe."""
    y_pred = df["predicted"].str.lower().str.strip()
    y_true = df["gold"].str.lower().str.strip()

    # Normalise unknown/uncertain to avoid for safety
    y_pred = y_pred.replace({"unknown": "avoid", "uncertain": "avoid"})
    y_true = y_true.replace({"unknown": "avoid", "uncertain": "avoid"})

    # Only keep rows with valid labels
    valid = (y_pred.isin(LABEL_ORDER)) & (y_true.isin(LABEL_ORDER))
    y_pred = y_pred[valid]
    y_true = y_true[valid]

    if len(y_pred) == 0:
        return {"n": 0}

    acc = accuracy_score(y_true, y_pred)
    p, r, f, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=LABEL_ORDER, average=None, zero_division=0
    )
    kappa = cohen_kappa_score(y_true, y_pred)

    # Unsafe rate: P(predicted=recommend | gold=avoid)
    gold_avoid_mask = y_true == "avoid"
    unsafe_rate = (y_pred[gold_avoid_mask] == "recommend").mean() if gold_avoid_mask.sum() > 0 else 0.0

    # Consistency: for each (model, strategy, profile_id, food), agreement across k runs
    if "run" in df.columns:
        consistency_rows = []
        for _, g in df[valid].groupby(["model", "strategy", "profile_id", "food"]):
            preds = g["predicted"].str.lower().str.strip().replace({"unknown": "avoid", "uncertain": "avoid"})
            if len(preds) > 1:
                mode_count = preds.value_counts().iloc[0]
                consistency_rows.append(mode_count / len(preds))
        consistency = float(np.mean(consistency_rows)) if consistency_rows else 1.0
    else:
        consistency = 1.0

    mean_latency = df["latency_ms"].mean() if "latency_ms" in df.columns else 0

    return {
        "group": group_name,
        "n": int(len(y_pred)),
        "accuracy": round(float(acc), 4),
        "kappa": round(float(kappa), 4),
        "unsafe_rate": round(float(unsafe_rate), 4),
        "consistency": round(float(consistency), 4),
        "mean_latency_ms": round(float(mean_latency), 1),
        "per_class": {
            label: {
                "precision": round(float(p[i]), 4),
                "recall": round(float(r[i]), 4),
                "f1": round(float(f[i]), 4),
            }
            for i, label in enumerate(LABEL_ORDER)
        },
    }


def run_metrics(csv_path: Path = RAW_CSV) -> dict:
    df = pd.read_csv(csv_path)
    logger.info("Loaded %d rows from %s", len(df), csv_path)

    results = {}

    # Overall
    results["overall"] = compute_metrics(df, "overall")

    # Per strategy (independent variable)
    for strategy, g in df.groupby("strategy"):
        results[f"strategy::{strategy}"] = compute_metrics(g, f"strategy::{strategy}")

    # Per condition
    for cond in ["diabetes", "hypertension", "ckd"]:
        subset = df[df["conditions"].str.contains(cond, na=False)]
        if len(subset):
            results[f"condition::{cond}"] = compute_metrics(subset, f"condition::{cond}")

    # Pairwise McNemar significance tests across strategies
    significance = {}
    strategies = df["strategy"].unique().tolist()
    for i in range(len(strategies)):
        for j in range(i + 1, len(strategies)):
            s1, s2 = strategies[i], strategies[j]
            d1 = df[df["strategy"] == s1]
            d2 = df[df["strategy"] == s2]
            merged = d1.merge(d2, on=["profile_id", "food"], suffixes=("_1", "_2"))
            if len(merged) < 10:
                continue
            correct1 = (merged["predicted_1"].str.lower() == merged["gold_1"].str.lower()).astype(int)
            correct2 = (merged["predicted_2"].str.lower() == merged["gold_2"].str.lower()).astype(int)
            b = int(((correct1 == 1) & (correct2 == 0)).sum())
            c = int(((correct1 == 0) & (correct2 == 1)).sum())
            try:
                from statsmodels.stats.contingency_tables import mcnemar as mcnemar_test
                a = int(((correct1 == 1) & (correct2 == 1)).sum())
                d = int(((correct1 == 0) & (correct2 == 0)).sum())
                result = mcnemar_test([[a, b], [c, d]])
                significance[f"{s1}_vs_{s2}"] = {
                    "test": "mcnemar",
                    "statistic": round(float(result.statistic), 4),
                    "pvalue": round(float(result.pvalue), 4),
                    "significant_p05": bool(result.pvalue < 0.05),
                }
            except Exception as e:
                logger.warning("McNemar failed for %s vs %s: %s", s1, s2, e)

    results["significance_tests"] = significance

    METRICS_JSON.write_text(json.dumps(results, indent=2))
    logger.info("Metrics written to %s", METRICS_JSON)
    return results


if __name__ == "__main__":
    metrics = run_metrics()
    # Print per-strategy summary table
    print(f"\n{'Strategy':<20} {'Acc':>6} {'Kappa':>7} {'Unsafe%':>8} {'Consistency':>12} {'Latency(ms)':>12}")
    print("-" * 70)
    for strategy in ["zero_shot", "structured_role", "few_shot", "rag_grounded"]:
        m = metrics.get(f"strategy::{strategy}", {})
        if m:
            print(f"{strategy:<20} {m['accuracy']:>6.1%} {m['kappa']:>7.4f} "
                  f"{m['unsafe_rate']:>8.1%} {m['consistency']:>12.4f} "
                  f"{m['mean_latency_ms']:>12.1f}")
