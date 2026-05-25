"""
test_conditions.py — pytest tests for FR-3: condition inference.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.conditions import infer_conditions


def _m(hba1c=None, glucose=None, bp_sys=None, bp_dia=None, egfr=None, potassium=None, allergens=None):
    return {
        "hba1c": hba1c,
        "glucose_fasting": glucose,
        "bp_systolic": bp_sys,
        "bp_diastolic": bp_dia,
        "egfr": egfr,
        "potassium": potassium,
        "allergens": allergens or [],
    }


def test_diabetes_from_hba1c():
    flags = infer_conditions(_m(hba1c=58))
    assert flags.diabetes is True
    assert flags.diabetes_severity == "mild"


def test_prediabetes():
    flags = infer_conditions(_m(hba1c=44))
    assert flags.diabetes is True
    assert flags.diabetes_severity == "pre"


def test_severe_diabetes():
    flags = infer_conditions(_m(hba1c=90))
    assert flags.diabetes_severity == "severe"


def test_hypertension_stage1():
    flags = infer_conditions(_m(bp_sys=142, bp_dia=88))
    assert flags.hypertension is True
    assert flags.hypertension_severity == "stage1"


def test_hypertension_stage2():
    flags = infer_conditions(_m(bp_sys=162, bp_dia=102))
    assert flags.hypertension_severity == "stage2"


def test_ckd_stage3():
    flags = infer_conditions(_m(egfr=38))
    assert flags.ckd is True
    assert flags.ckd_stage == 3


def test_ckd_stage4():
    flags = infer_conditions(_m(egfr=22))
    assert flags.ckd_stage == 4


def test_ckd_stage5():
    flags = infer_conditions(_m(egfr=10))
    assert flags.ckd_stage == 5


def test_multi_condition():
    flags = infer_conditions(_m(hba1c=72, bp_sys=162, bp_dia=101, egfr=35))
    assert flags.diabetes
    assert flags.hypertension
    assert flags.ckd


def test_no_conditions():
    flags = infer_conditions(_m(hba1c=36, bp_sys=118, bp_dia=74, egfr=90))
    assert not flags.diabetes
    assert not flags.hypertension
    assert not flags.ckd


def test_allergens_propagated():
    flags = infer_conditions(_m(allergens=["peanut", "shellfish"]))
    assert "peanut" in flags.allergens
    assert "shellfish" in flags.allergens


def test_active_conditions_list():
    flags = infer_conditions(_m(hba1c=65, bp_sys=155, bp_dia=96))
    active = flags.active_conditions()
    assert "diabetes" in active
    assert "hypertension" in active
