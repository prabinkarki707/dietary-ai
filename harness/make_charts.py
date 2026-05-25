"""
make_charts.py — EH-3: Generate Chapter 4 figures from results/raw.csv.

Independent variable = strategy (model is constant = CLAUDE_MODEL).
Figures:
  Fig 4.1 — Accuracy by strategy
  Fig 4.2 — Confusion matrix per strategy (2×2 grid)
  Fig 4.3 — Unsafe-recommendation rate by strategy  ← headline
  Fig 4.4 — Consistency by strategy
  Fig 4.5 — Latency by strategy
  Fig 5.1 — Accuracy vs Unsafe-rate scatter (4 points, one per strategy)
"""

import sys
import json
import logging
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sklearn.metrics import confusion_matrix

logger = logging.getLogger(__name__)
logging.basicConfig(level="INFO")

RAW_CSV = ROOT / "results" / "raw.csv"
FIGS_DIR = ROOT / "results" / "figures"
FIGS_DIR.mkdir(parents=True, exist_ok=True)

LABEL_ORDER = ["recommend", "limit", "avoid"]
STRATEGY_ORDER = ["zero_shot", "structured_role", "few_shot", "rag_grounded"]
STRATEGY_LABELS = {
    "zero_shot": "Zero-shot",
    "structured_role": "Structured",
    "few_shot": "Few-shot",
    "rag_grounded": "RAG-grounded",
}
PALETTE = {"recommend": "#34C759", "limit": "#FF9500", "avoid": "#FF3B30"}
BAR_COLORS = ["#1C1C1E", "#636366", "#AEAEB2", "#D1D1D6"]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "#F2F2F7",
    "grid.linewidth": 1,
    "figure.dpi": 150,
})


def load_data():
    df = pd.read_csv(RAW_CSV)
    df["predicted"] = df["predicted"].str.lower().str.strip().replace({"unknown": "avoid", "uncertain": "avoid"})
    df["gold"] = df["gold"].str.lower().str.strip().replace({"unknown": "avoid", "uncertain": "avoid"})
    df = df[df["predicted"].isin(LABEL_ORDER) & df["gold"].isin(LABEL_ORDER)]
    return df


def _strategy_labels(df):
    """Return strategies in canonical order, filtered to what exists in df."""
    return [s for s in STRATEGY_ORDER if s in df["strategy"].unique()]


# ── Fig 4.1: Accuracy by strategy ─────────────────────────────────────────────
def fig_accuracy_by_strategy(df: pd.DataFrame):
    strategies = _strategy_labels(df)
    accs = [(df[df["strategy"] == s]["predicted"] == df[df["strategy"] == s]["gold"]).mean()
            for s in strategies]
    labels = [STRATEGY_LABELS.get(s, s) for s in strategies]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(labels, accs, color=BAR_COLORS[:len(strategies)], width=0.5)
    for bar, acc in zip(bars, accs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                f"{acc:.1%}", ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("Accuracy")
    ax.set_ylim(0, 1.1)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
    ax.set_title("Fig 4.1 — Overall Accuracy by Prompting Strategy", fontweight="bold", pad=12)
    fig.tight_layout()
    out = FIGS_DIR / "fig4_1_accuracy_by_strategy.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


# ── Fig 4.2: Confusion matrix per strategy ────────────────────────────────────
def fig_confusion_matrices(df: pd.DataFrame):
    strategies = _strategy_labels(df)
    n = len(strategies)
    ncols = min(n, 2)
    nrows = (n + 1) // 2
    fig, axes = plt.subplots(nrows, ncols, figsize=(5.5 * ncols, 4.5 * nrows))
    axes = np.array(axes).flatten()

    for ax, strategy in zip(axes, strategies):
        sub = df[df["strategy"] == strategy]
        cm = confusion_matrix(sub["gold"], sub["predicted"], labels=LABEL_ORDER)
        sns.heatmap(
            cm, annot=True, fmt="d", cmap="Greys",
            xticklabels=LABEL_ORDER, yticklabels=LABEL_ORDER,
            ax=ax, cbar=False, linewidths=0.5, linecolor="#E5E5EA"
        )
        ax.set_title(STRATEGY_LABELS.get(strategy, strategy), fontweight="bold")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Gold")

    for ax in axes[len(strategies):]:
        ax.set_visible(False)

    fig.suptitle("Fig 4.2 — Confusion Matrices by Prompting Strategy", fontweight="bold", y=1.01)
    fig.tight_layout()
    out = FIGS_DIR / "fig4_2_confusion_matrices.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


# ── Fig 4.3: Unsafe-rate by strategy ──────────────────────────────────────────
def fig_unsafe_rate(df: pd.DataFrame):
    strategies = _strategy_labels(df)
    rows = []
    for s in strategies:
        g = df[df["strategy"] == s]
        gold_avoid = g[g["gold"] == "avoid"]
        unsafe = (gold_avoid["predicted"] == "recommend").mean() if len(gold_avoid) else 0
        rows.append({"strategy": STRATEGY_LABELS.get(s, s), "unsafe_rate": unsafe})
    udf = pd.DataFrame(rows).sort_values("unsafe_rate", ascending=False)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = ["#FF3B30" if v > 0.1 else "#FF9500" if v > 0.05 else "#34C759"
              for v in udf["unsafe_rate"]]
    ax.bar(udf["strategy"], udf["unsafe_rate"], color=colors, width=0.5)
    ax.axhline(0.1, color="#FF3B30", linestyle="--", linewidth=1.2, label="10% threshold")
    for i, v in enumerate(udf["unsafe_rate"]):
        ax.text(i, v + 0.002, f"{v:.1%}", ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("Unsafe Rate  P(recommend | gold=avoid)")
    ax.set_ylim(0, max(udf["unsafe_rate"].max() + 0.08, 0.25))
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
    ax.set_title("Fig 4.3 — Unsafe Recommendation Rate by Prompting Strategy", fontweight="bold", pad=12)
    ax.legend()
    fig.tight_layout()
    out = FIGS_DIR / "fig4_3_unsafe_rate.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


# ── Fig 4.4: Consistency by strategy ──────────────────────────────────────────
def fig_consistency(df: pd.DataFrame):
    rows = []
    for (strategy, pid, food), g in df.groupby(["strategy", "profile_id", "food"]):
        if len(g) > 1:
            mode_freq = g["predicted"].value_counts().iloc[0] / len(g)
            rows.append({"strategy": STRATEGY_LABELS.get(strategy, strategy), "consistency": mode_freq})
    cdf = pd.DataFrame(rows)
    if cdf.empty:
        logger.warning("No multi-run data for consistency plot")
        return

    fig, ax = plt.subplots(figsize=(7, 4.5))
    order = [STRATEGY_LABELS.get(s, s) for s in STRATEGY_ORDER if STRATEGY_LABELS.get(s, s) in cdf["strategy"].unique()]
    sns.boxplot(data=cdf, x="strategy", y="consistency", order=order,
                palette=dict(zip(order, BAR_COLORS)), ax=ax)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Label Consistency (across k runs)")
    ax.set_xlabel("")
    ax.set_title("Fig 4.4 — Response Consistency by Prompting Strategy", fontweight="bold", pad=12)
    fig.tight_layout()
    out = FIGS_DIR / "fig4_4_consistency.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


# ── Fig 4.5: Latency by strategy ──────────────────────────────────────────────
def fig_latency(df: pd.DataFrame):
    strategies = _strategy_labels(df)
    rows = [{"strategy": STRATEGY_LABELS.get(s, s),
             "mean_ms": df[df["strategy"] == s]["latency_ms"].mean(),
             "p95_ms": df[df["strategy"] == s]["latency_ms"].quantile(0.95)}
            for s in strategies]
    ldf = pd.DataFrame(rows).sort_values("mean_ms")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(ldf))
    ax.bar(x, ldf["mean_ms"] / 1000, color="#1C1C1E", label="Mean", width=0.5)
    ax.scatter(x, ldf["p95_ms"] / 1000, color="#FF3B30", zorder=5, s=60, label="P95")
    ax.set_xticks(x)
    ax.set_xticklabels(ldf["strategy"], rotation=15, ha="right")
    ax.set_ylabel("Latency (seconds)")
    ax.set_title("Fig 4.5 — Mean and P95 Latency by Prompting Strategy", fontweight="bold", pad=12)
    ax.legend()
    fig.tight_layout()
    out = FIGS_DIR / "fig4_5_latency.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


# ── Fig 5.1: Accuracy vs Unsafe-rate scatter (4 points) ───────────────────────
def fig_accuracy_vs_unsafe(df: pd.DataFrame):
    strategies = _strategy_labels(df)
    rows = []
    for s in strategies:
        g = df[df["strategy"] == s]
        acc = (g["predicted"] == g["gold"]).mean()
        gold_avoid = g[g["gold"] == "avoid"]
        unsafe = (gold_avoid["predicted"] == "recommend").mean() if len(gold_avoid) else 0
        rows.append({"strategy": STRATEGY_LABELS.get(s, s), "accuracy": acc, "unsafe_rate": unsafe})
    sdf = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(7, 6))
    for i, row in sdf.iterrows():
        ax.scatter(row["unsafe_rate"], row["accuracy"],
                   c=BAR_COLORS[i % len(BAR_COLORS)], s=140,
                   edgecolors="white", linewidths=1, zorder=5)
        ax.annotate(row["strategy"], (row["unsafe_rate"], row["accuracy"]),
                    textcoords="offset points", xytext=(6, 4), fontsize=9)

    ax.axhline(0.7, color="#AEAEB2", linestyle="--", linewidth=1, label="70% accuracy")
    ax.axvline(0.1, color="#FF3B30", linestyle="--", linewidth=1, label="10% unsafe threshold")
    ax.set_xlabel("Unsafe Rate  (↓ better)")
    ax.set_ylabel("Accuracy  (↑ better)")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
    ax.set_title("Fig 5.1 — Accuracy vs Unsafe Rate per Prompting Strategy", fontweight="bold", pad=12)
    ax.legend(fontsize=9)
    fig.tight_layout()
    out = FIGS_DIR / "fig5_1_accuracy_vs_unsafe.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def make_all_charts():
    if not RAW_CSV.exists():
        logger.error("raw.csv not found at %s — run run_experiment.py first", RAW_CSV)
        return

    df = load_data()
    logger.info("Loaded %d valid rows", len(df))

    fig_accuracy_by_strategy(df)
    fig_confusion_matrices(df)
    fig_unsafe_rate(df)
    fig_consistency(df)
    fig_latency(df)
    fig_accuracy_vs_unsafe(df)

    logger.info("All figures saved to %s", FIGS_DIR)


if __name__ == "__main__":
    make_all_charts()

