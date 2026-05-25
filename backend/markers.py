"""
markers.py — Parse raw OCR text into structured clinical markers.
Implements FR-2: regex + keyword rules with confidence logging.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

ALLERGEN_KEYWORDS = [
    "peanut", "tree nut", "shellfish", "fish", "gluten", "coeliac",
    "celiac", "milk", "egg", "soy", "soya", "wheat", "sesame",
    "sulphite", "sulphur", "lupin", "mollusc", "mustard",
]


@dataclass
class ClinicalMarkers:
    hba1c: Optional[float] = None           # mmol/mol
    glucose_fasting: Optional[float] = None  # mmol/L
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    egfr: Optional[float] = None            # mL/min/1.73m²
    potassium: Optional[float] = None       # mmol/L
    allergens: list[str] = field(default_factory=list)
    confidence: dict = field(default_factory=dict)
    raw_text: str = ""

    def to_dict(self) -> dict:
        return {
            "hba1c": self.hba1c,
            "glucose_fasting": self.glucose_fasting,
            "bp_systolic": self.bp_systolic,
            "bp_diastolic": self.bp_diastolic,
            "egfr": self.egfr,
            "potassium": self.potassium,
            "allergens": self.allergens,
            "confidence": self.confidence,
        }


def _extract_first_float(pattern: str, text: str) -> Optional[float]:
    """Return the first float-like number matched after the pattern."""
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(",", "."))
        except (ValueError, IndexError):
            return None
    return None


def _extract_first_int(pattern: str, text: str) -> Optional[int]:
    v = _extract_first_float(pattern, text)
    return int(round(v)) if v is not None else None


def parse_markers(raw_text: str) -> ClinicalMarkers:
    """
    Parse raw OCR text and return structured ClinicalMarkers.
    Confidence 1.0 = regex matched; 0.0 = not found.
    """
    m = ClinicalMarkers(raw_text=raw_text)
    text = raw_text

    # ── HbA1c ────────────────────────────────────────────────────────────────
    # Accept: "HbA1c 58 mmol/mol", "HbA1c: 7.5%", "A1c 8.2"
    hba1c_pct = _extract_first_float(
        r"(?:hba1c|a1c|haemoglobin\s+a1c)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*%", text
    )
    hba1c_mmol = _extract_first_float(
        r"(?:hba1c|a1c|haemoglobin\s+a1c)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*mmol", text
    )
    if hba1c_mmol is not None:
        m.hba1c = hba1c_mmol
        m.confidence["hba1c"] = 1.0
    elif hba1c_pct is not None:
        # Convert %NGSP to mmol/mol: (pct - 2.15) × 10.929
        m.hba1c = round((hba1c_pct - 2.15) * 10.929, 1)
        m.confidence["hba1c"] = 0.9
    else:
        m.confidence["hba1c"] = 0.0
        logger.debug("HbA1c not found in text")

    # ── Fasting glucose ───────────────────────────────────────────────────────
    glucose = _extract_first_float(
        r"(?:fasting\s+)?(?:blood\s+)?glucose[:\s]*([0-9]+(?:\.[0-9]+)?)\s*mmol", text
    )
    if glucose is None:
        glucose = _extract_first_float(
            r"fbg[:\s]*([0-9]+(?:\.[0-9]+)?)", text
        )
    m.glucose_fasting = glucose
    m.confidence["glucose_fasting"] = 1.0 if glucose is not None else 0.0

    # ── Blood pressure ────────────────────────────────────────────────────────
    bp = re.search(r"(?:blood\s+pressure|bp)[:\s]*([0-9]{2,3})\s*/\s*([0-9]{2,3})", text, re.IGNORECASE)
    if bp:
        m.bp_systolic = int(bp.group(1))
        m.bp_diastolic = int(bp.group(2))
        m.confidence["blood_pressure"] = 1.0
    else:
        m.confidence["blood_pressure"] = 0.0
        logger.debug("Blood pressure not found in text")

    # ── eGFR ─────────────────────────────────────────────────────────────────
    egfr = _extract_first_float(
        r"(?:egfr|gfr|estimated\s+gfr)[:\s]*([0-9]+(?:\.[0-9]+)?)", text
    )
    m.egfr = egfr
    m.confidence["egfr"] = 1.0 if egfr is not None else 0.0

    # ── Potassium ─────────────────────────────────────────────────────────────
    potassium = _extract_first_float(
        r"potassium[:\s]*([0-9]+(?:\.[0-9]+)?)\s*mmol", text
    )
    if potassium is None:
        potassium = _extract_first_float(r"\bk\+?[:\s]*([0-9]+(?:\.[0-9]+)?)\s*mmol", text)
    m.potassium = potassium
    m.confidence["potassium"] = 1.0 if potassium is not None else 0.0

    # ── Allergens ─────────────────────────────────────────────────────────────
    found_allergens = []
    lower_text = text.lower()
    for allergen in ALLERGEN_KEYWORDS:
        if allergen in lower_text:
            found_allergens.append(allergen)
    m.allergens = list(set(found_allergens))
    m.confidence["allergens"] = 1.0 if found_allergens else 0.0

    logger.info("Parsed markers: %s", m.to_dict())
    return m
