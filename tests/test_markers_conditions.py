"""
Tests for markers.py and conditions.py
Run with: pytest tests/
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.markers import parse_markers
from backend.conditions import infer_conditions


class TestMarkerParsing:
    def test_hba1c_mmol(self):
        m = parse_markers("HbA1c: 58 mmol/mol")
        assert m.hba1c == 58.0
        assert m.confidence["hba1c"] == 1.0

    def test_hba1c_pct(self):
        m = parse_markers("HbA1c 7.5%")
        assert m.hba1c is not None
        assert 55 <= m.hba1c <= 60  # ~58 mmol/mol

    def test_blood_pressure(self):
        m = parse_markers("Blood pressure: 155/98")
        assert m.bp_systolic == 155
        assert m.bp_diastolic == 98

    def test_egfr(self):
        m = parse_markers("eGFR: 38 mL/min")
        assert m.egfr == 38.0

    def test_potassium(self):
        m = parse_markers("Potassium: 5.8 mmol/L")
        assert m.potassium == 5.8

    def test_allergen_peanut(self):
        m = parse_markers("Patient has peanut allergy. Also shellfish.")
        assert "peanut" in m.allergens
        assert "shellfish" in m.allergens

    def test_missing_markers(self):
        m = parse_markers("No results found.")
        assert m.hba1c is None
        assert m.confidence["hba1c"] == 0.0

    def test_full_report(self):
        text = """
        Patient Report
        HbA1c: 72 mmol/mol
        Fasting blood glucose: 10.3 mmol/L
        Blood pressure: 162/101
        eGFR: 35
        Potassium: 5.9 mmol/L
        """
        m = parse_markers(text)
        assert m.hba1c == 72.0
        assert m.glucose_fasting == 10.3
        assert m.bp_systolic == 162
        assert m.egfr == 35.0
        assert m.potassium == 5.9


class TestConditionInference:
    def _m(self, **kwargs):
        """Create a dict simulating parsed markers."""
        return {
            "hba1c": kwargs.get("hba1c"),
            "glucose_fasting": kwargs.get("glucose_fasting"),
            "bp_systolic": kwargs.get("bp_systolic"),
            "bp_diastolic": kwargs.get("bp_diastolic"),
            "egfr": kwargs.get("egfr"),
            "potassium": kwargs.get("potassium"),
            "allergens": kwargs.get("allergens", []),
        }

    def test_diabetes_from_hba1c(self):
        flags = infer_conditions(self._m(hba1c=58))
        assert flags.diabetes is True
        assert flags.diabetes_severity == "mild"

    def test_pre_diabetes(self):
        flags = infer_conditions(self._m(hba1c=44))
        assert flags.diabetes is True
        assert flags.diabetes_severity == "pre"

    def test_severe_diabetes(self):
        flags = infer_conditions(self._m(hba1c=88))
        assert flags.diabetes_severity == "severe"

    def test_hypertension_stage1(self):
        flags = infer_conditions(self._m(bp_systolic=142, bp_diastolic=91))
        assert flags.hypertension is True
        assert flags.hypertension_severity == "stage1"

    def test_hypertension_stage2(self):
        flags = infer_conditions(self._m(bp_systolic=165, bp_diastolic=102))
        assert flags.hypertension_severity == "stage2"

    def test_ckd_stage3(self):
        flags = infer_conditions(self._m(egfr=38))
        assert flags.ckd is True
        assert flags.ckd_stage == 3

    def test_ckd_stage4(self):
        flags = infer_conditions(self._m(egfr=25))
        assert flags.ckd_stage == 4

    def test_no_conditions(self):
        flags = infer_conditions(self._m(hba1c=36, bp_systolic=118, bp_diastolic=75, egfr=88))
        assert flags.diabetes is False
        assert flags.hypertension is False
        assert flags.ckd is False

    def test_multi_condition(self):
        flags = infer_conditions(self._m(hba1c=72, bp_systolic=162, bp_diastolic=101, egfr=28))
        assert flags.diabetes is True
        assert flags.hypertension is True
        assert flags.ckd is True

    def test_allergens_preserved(self):
        flags = infer_conditions(self._m(allergens=["peanut", "shellfish"]))
        assert "peanut" in flags.allergens


class TestSafetyCheck:
    def test_recommend(self):
        from backend.safety_check import safety_check
        r = safety_check("sashimi", [], [])
        assert r["verdict"] in ("recommend", "limit", "avoid", "unknown")

    def test_avoid_french_fries_diabetes(self):
        from backend.safety_check import safety_check
        r = safety_check("french_fries", ["diabetes", "hypertension"], [])
        assert r["verdict"] == "avoid"

    def test_allergy_triggers_avoid(self):
        from backend.safety_check import safety_check
        r = safety_check("grilled_salmon", [], ["fish"])
        assert r["verdict"] == "avoid"
        assert r["allergy_flag"] is True

    def test_unknown_food(self):
        from backend.safety_check import safety_check
        r = safety_check("xyzfood_notexist_123", [], [])
        assert r["verdict"] == "unknown"
