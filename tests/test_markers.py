"""
test_markers.py — pytest tests for FR-2: marker parsing.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.markers import parse_markers


def test_hba1c_mmol():
    text = "HbA1c: 58 mmol/mol"
    m = parse_markers(text)
    assert m.hba1c == 58.0
    assert m.confidence["hba1c"] == 1.0


def test_hba1c_percent_conversion():
    text = "HbA1c 7.5%"
    m = parse_markers(text)
    # (7.5 - 2.15) * 10.929 ≈ 58.5
    assert m.hba1c is not None
    assert 55 < m.hba1c < 62
    assert m.confidence["hba1c"] == 0.9


def test_blood_pressure():
    text = "Blood Pressure: 150/95 mmHg"
    m = parse_markers(text)
    assert m.bp_systolic == 150
    assert m.bp_diastolic == 95
    assert m.confidence["blood_pressure"] == 1.0


def test_egfr():
    text = "eGFR 38 mL/min"
    m = parse_markers(text)
    assert m.egfr == 38.0
    assert m.confidence["egfr"] == 1.0


def test_glucose():
    text = "Fasting glucose: 8.2 mmol/L"
    m = parse_markers(text)
    assert m.glucose_fasting == 8.2


def test_potassium():
    text = "Potassium: 5.8 mmol/L"
    m = parse_markers(text)
    assert m.potassium == 5.8


def test_allergens():
    text = "Known allergies: peanut, shellfish"
    m = parse_markers(text)
    assert "peanut" in m.allergens
    assert "shellfish" in m.allergens


def test_missing_returns_none():
    text = "No clinical data here."
    m = parse_markers(text)
    assert m.hba1c is None
    assert m.bp_systolic is None
    assert m.confidence["hba1c"] == 0.0


def test_full_report():
    text = """
    Patient Name: John Smith
    HbA1c: 65 mmol/mol
    Fasting Glucose: 9.1 mmol/L
    Blood Pressure: 158/98 mmHg
    eGFR: 35 mL/min/1.73m2
    Potassium: 5.9 mmol/L
    Allergies: shellfish
    """
    m = parse_markers(text)
    assert m.hba1c == 65.0
    assert m.glucose_fasting == 9.1
    assert m.bp_systolic == 158
    assert m.bp_diastolic == 98
    assert m.egfr == 35.0
    assert m.potassium == 5.9
    assert "shellfish" in m.allergens
