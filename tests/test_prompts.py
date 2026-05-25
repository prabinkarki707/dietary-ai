"""
test_prompts.py — pytest tests for FR-8: prompting strategies.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.prompts import build_prompt, zero_shot, structured_role, few_shot, rag_grounded

PAYLOAD = {
    "conditions": ["diabetes", "hypertension"],
    "allergens": [],
    "hba1c": 65,
    "blood_pressure": "158/96",
    "food": "french_fries",
    "question": "Is french fries suitable for me?",
}


def test_zero_shot_contains_food():
    p = zero_shot(PAYLOAD)
    assert "french_fries" in p or "french fries" in p.lower()
    assert "diabetes" in p


def test_structured_role_has_json_schema():
    p = structured_role(PAYLOAD)
    assert '"verdict"' in p
    assert '"reason"' in p
    assert "clinical dietitian" in p.lower()


def test_few_shot_has_examples():
    p = few_shot(PAYLOAD)
    assert "Example 1" in p
    assert "Example 2" in p
    assert "Example 3" in p


def test_rag_grounded_injects_chunks():
    chunks = ["[SOURCE: NICE NG28] Some guideline text here.", "[SOURCE: KDOQI] CKD guidance."]
    p = rag_grounded(PAYLOAD, chunks)
    assert "GUIDELINE EXCERPTS" in p
    assert "NICE NG28" in p


def test_rag_grounded_no_chunks():
    p = rag_grounded(PAYLOAD, [])
    assert "No specific guidelines" in p


def test_build_prompt_routes_correctly():
    for strategy in ["zero_shot", "structured_role", "few_shot"]:
        p = build_prompt(strategy, PAYLOAD)
        assert len(p) > 50


def test_build_prompt_rag():
    p = build_prompt("rag_grounded", PAYLOAD, ["Some guideline chunk."])
    assert "guideline" in p.lower()


def test_build_prompt_invalid_strategy():
    import pytest
    with pytest.raises(ValueError):
        build_prompt("made_up_strategy", PAYLOAD)


def test_disclaimer_in_module():
    from backend.prompts import MEDICAL_DISCLAIMER
    assert "disclaimer" in MEDICAL_DISCLAIMER.lower() or "not" in MEDICAL_DISCLAIMER.lower()
    assert len(MEDICAL_DISCLAIMER) > 30
