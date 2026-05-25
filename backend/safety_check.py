"""
safety_check.py — FR-5: food + conditions → recommend/limit/avoid via gold-standard matrix.
"""

import csv
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MATRIX_PATH = Path(__file__).parent.parent / "data" / "gold_standard.csv"

# Cache the matrix in memory at import time
_MATRIX: dict[str, dict] = {}


def _load_matrix() -> dict[str, dict]:
    global _MATRIX
    if _MATRIX:
        return _MATRIX
    if not MATRIX_PATH.exists():
        logger.error("gold_standard.csv not found at %s", MATRIX_PATH)
        return {}
    with open(MATRIX_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            food_key = row["food"].strip().lower()
            _MATRIX[food_key] = row
    logger.info("Loaded %d foods from gold_standard matrix", len(_MATRIX))
    return _MATRIX


def _normalise_food(food_label: str) -> str:
    """Normalise model output to match matrix keys."""
    return food_label.lower().strip().replace(" ", "_").replace("-", "_")


VERDICT_RANK = {"recommend": 0, "limit": 1, "avoid": 2, "unknown": 3}


def safety_check(food_label: str, conditions: list[str], allergens: list[str]) -> dict:
    """
    Returns:
        {
          verdict: recommend|limit|avoid|unknown,
          per_condition: {diabetes: ..., hypertension: ..., ckd: ...},
          allergy_flag: bool,
          reason: str,
          sources: {diabetes: ..., hypertension: ..., ckd: ...}
        }
    """
    matrix = _load_matrix()
    food_key = _normalise_food(food_label)

    # Fuzzy fallback: check if any matrix key is a substring match
    row = matrix.get(food_key)
    if row is None:
        for key in matrix:
            if key in food_key or food_key in key:
                row = matrix[key]
                logger.debug("Fuzzy matched '%s' -> '%s'", food_key, key)
                break

    if row is None:
        logger.warning("Food '%s' not found in gold_standard matrix", food_key)
        return {
            "verdict": "unknown",
            "per_condition": {},
            "allergy_flag": False,
            "reason": "Food not found in dietary guidelines matrix. Please consult a healthcare professional.",
            "sources": {},
        }

    # ── Allergy check ─────────────────────────────────────────────────────────
    matrix_allergy = row.get("allergy_flag", "none").lower().strip()
    allergy_triggered = False
    allergy_detail = ""
    if matrix_allergy != "none" and matrix_allergy:
        for a in allergens:
            if a.lower() in matrix_allergy or matrix_allergy in a.lower():
                allergy_triggered = True
                allergy_detail = f"Contains {matrix_allergy} — you have a {a} allergy."
                break

    if allergy_triggered:
        return {
            "verdict": "avoid",
            "per_condition": {},
            "allergy_flag": True,
            "reason": f"⚠️ ALLERGY ALERT: {allergy_detail}",
            "sources": {},
        }

    # ── Per-condition verdicts ────────────────────────────────────────────────
    per_condition = {}
    sources = {}
    COND_MAP = {
        "diabetes": ("diabetes", "source_diabetes"),
        "hypertension": ("hypertension", "source_hypertension"),
        "ckd": ("ckd", "source_ckd"),
    }

    worst_verdict = "recommend"
    for cond in conditions:
        col, src_col = COND_MAP.get(cond, (None, None))
        if col and col in row:
            verdict = row[col].strip().lower()
            per_condition[cond] = verdict
            sources[cond] = row.get(src_col, "").strip()
            if VERDICT_RANK.get(verdict, 0) > VERDICT_RANK.get(worst_verdict, 0):
                worst_verdict = verdict

    if not conditions:
        # No active conditions → use most conservative across all three
        verdicts = [row.get("diabetes", "recommend"), row.get("hypertension", "recommend"), row.get("ckd", "recommend")]
        worst_verdict = max(verdicts, key=lambda v: VERDICT_RANK.get(v.strip().lower(), 0)).strip().lower()

    # Build reason string from notes
    notes = row.get("notes", "")
    reason_parts = []
    for cond, verd in per_condition.items():
        src = sources.get(cond, "")
        reason_parts.append(f"{cond.title()}: {verd} — {src}")
    reason = "; ".join(reason_parts) if reason_parts else notes

    return {
        "verdict": worst_verdict,
        "per_condition": per_condition,
        "allergy_flag": False,
        "reason": reason or notes,
        "sources": sources,
    }
