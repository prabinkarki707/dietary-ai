"""
test_safety_check.py — pytest tests for FR-5: gold-standard matrix lookups.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.safety_check import safety_check


def test_french_fries_diabetes():
    r = safety_check("french_fries", ["diabetes"], [])
    assert r["verdict"] == "avoid"


def test_sashimi_ckd():
    r = safety_check("sashimi", ["ckd"], [])
    assert r["verdict"] == "recommend"


def test_greek_salad_all_clear():
    r = safety_check("greek_salad", ["diabetes", "hypertension"], [])
    # Greek salad is recommend for both
    assert r["verdict"] == "recommend"


def test_allergy_triggers_avoid():
    r = safety_check("grilled_salmon", [], ["fish"])
    assert r["allergy_flag"] is True
    assert r["verdict"] == "avoid"


def test_shellfish_allergy_oysters():
    r = safety_check("oysters", [], ["shellfish"])
    assert r["allergy_flag"] is True
    assert r["verdict"] == "avoid"


def test_nachos_worst_case():
    r = safety_check("nachos", ["diabetes", "hypertension", "ckd"], [])
    assert r["verdict"] == "avoid"


def test_unknown_food():
    # "unicorn_steak" fuzzy-matches "steak" in the matrix — this is correct behaviour
    # Test that a completely novel food with no matrix substring match returns unknown
    r = safety_check("xyzzy_nonexistent_dish_abc123", ["diabetes"], [])
    assert r["verdict"] == "unknown"


def test_per_condition_populated():
    r = safety_check("chicken_curry", ["diabetes", "hypertension"], [])
    assert "diabetes" in r["per_condition"]
    assert "hypertension" in r["per_condition"]


def test_no_conditions_returns_verdict():
    r = safety_check("edamame", [], [])
    assert r["verdict"] in ("recommend", "limit", "avoid")


def test_macaroni_avoid_all():
    r = safety_check("macaroni_and_cheese", ["diabetes", "hypertension", "ckd"], [])
    assert r["verdict"] == "avoid"
