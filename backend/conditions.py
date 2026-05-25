"""
conditions.py — Map clinical markers to condition flags + severity.
Implements FR-3: uses NICE / KDOQI guideline thresholds.
"""

from dataclasses import dataclass, field
from typing import Optional
from backend.markers import ClinicalMarkers


@dataclass
class ConditionFlags:
    diabetes: bool = False
    diabetes_severity: str = "none"       # none | pre | mild | moderate | severe
    hypertension: bool = False
    hypertension_severity: str = "none"   # none | stage1 | stage2 | stage3
    ckd: bool = False
    ckd_stage: int = 0                    # 0–5
    allergens: list[str] = field(default_factory=list)

    def active_conditions(self) -> list[str]:
        conds = []
        if self.diabetes:
            conds.append("diabetes")
        if self.hypertension:
            conds.append("hypertension")
        if self.ckd:
            conds.append("ckd")
        return conds

    def to_dict(self) -> dict:
        return {
            "diabetes": self.diabetes,
            "diabetes_severity": self.diabetes_severity,
            "hypertension": self.hypertension,
            "hypertension_severity": self.hypertension_severity,
            "ckd": self.ckd,
            "ckd_stage": self.ckd_stage,
            "allergens": self.allergens,
            "active_conditions": self.active_conditions(),
        }


def infer_conditions(markers: ClinicalMarkers) -> ConditionFlags:
    """
    Apply NICE NG28, NICE NG136, KDOQI 2020 thresholds.
    Also accepts a dict (for harness use).
    """
    # Accept both ClinicalMarkers dataclass and plain dict (from profiles.json)
    if isinstance(markers, dict):
        hba1c = markers.get("hba1c")
        glucose = markers.get("glucose_fasting")
        bp_sys = markers.get("bp_systolic")
        bp_dia = markers.get("bp_diastolic")
        egfr = markers.get("egfr")
        potassium = markers.get("potassium")
        allergens = markers.get("allergens", [])
    else:
        hba1c = markers.hba1c
        glucose = markers.glucose_fasting
        bp_sys = markers.bp_systolic
        bp_dia = markers.bp_diastolic
        egfr = markers.egfr
        potassium = markers.potassium
        allergens = markers.allergens

    flags = ConditionFlags(allergens=list(allergens))

    # ── Diabetes (NICE NG28) ──────────────────────────────────────────────────
    if hba1c is not None:
        if hba1c >= 48:
            flags.diabetes = True
            if hba1c >= 86:
                flags.diabetes_severity = "severe"
            elif hba1c >= 69:
                flags.diabetes_severity = "moderate"
            else:
                flags.diabetes_severity = "mild"
        elif hba1c >= 42:
            flags.diabetes = True  # pre-diabetes still triggers dietary restrictions
            flags.diabetes_severity = "pre"
    elif glucose is not None:
        if glucose >= 7.0:
            flags.diabetes = True
            flags.diabetes_severity = "mild"
        elif glucose >= 6.1:
            flags.diabetes = True
            flags.diabetes_severity = "pre"

    # ── Hypertension (NICE NG136) ─────────────────────────────────────────────
    if bp_sys is not None and bp_dia is not None:
        if bp_sys >= 180 or bp_dia >= 120:
            flags.hypertension = True
            flags.hypertension_severity = "stage3"
        elif bp_sys >= 160 or bp_dia >= 100:
            flags.hypertension = True
            flags.hypertension_severity = "stage2"
        elif bp_sys >= 140 or bp_dia >= 90:
            flags.hypertension = True
            flags.hypertension_severity = "stage1"

    # ── CKD (KDOQI 2020) ──────────────────────────────────────────────────────
    if egfr is not None:
        if egfr < 15:
            flags.ckd = True
            flags.ckd_stage = 5
        elif egfr < 30:
            flags.ckd = True
            flags.ckd_stage = 4
        elif egfr < 45:
            flags.ckd = True
            flags.ckd_stage = 3
        elif egfr < 60:
            flags.ckd = True
            flags.ckd_stage = 3  # stage 3a

    return flags
