"""
main.py — FastAPI entrypoint. Implements FR-1 through FR-9.
"""

import os
import logging
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from backend.ocr import extract_text
from backend.markers import parse_markers
from backend.conditions import infer_conditions
from backend.food_recognition import recognise_food
from backend.safety_check import safety_check
from backend.llm_router import query as llm_query, SUPPORTED_MODELS, STRATEGIES
from backend.logger_db import init_db, log_query
from backend.prompts import MEDICAL_DISCLAIMER

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Dietary AI API",
    description="COM6016M Dissertation — AI-Powered Dietary Recommendation System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Dietary AI backend started.")


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "models": SUPPORTED_MODELS, "strategies": STRATEGIES}


# ─── FR-1: OCR ───────────────────────────────────────────────────────────────

@app.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    """Accept a report image (JPG/PNG/PDF) → raw extracted text."""
    allowed = {".jpg", ".jpeg", ".png", ".pdf"}
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {allowed}")

    content = await file.read()
    result = extract_text(content, file.filename or "report.png")

    # FR-2: also parse markers from extracted text
    markers = parse_markers(result["text"])

    log_query(endpoint="/ocr")
    return {
        "raw_text": result["text"],
        "ocr_method": result["method"],
        "ocr_confidence": result["confidence"],
        "markers": markers.to_dict(),
    }


# ─── FR-2 + FR-3: Markers + Conditions ───────────────────────────────────────

class RawTextInput(BaseModel):
    text: str


@app.post("/markers")
def markers_endpoint(body: RawTextInput):
    """Parse raw text into structured clinical markers + condition flags."""
    markers = parse_markers(body.text)
    conditions = infer_conditions(markers)
    return {
        "markers": markers.to_dict(),
        "conditions": conditions.to_dict(),
    }


# ─── FR-4: Food recognition ───────────────────────────────────────────────────

@app.post("/recognise")
async def recognise_endpoint(file: UploadFile = File(...)):
    """Accept a food image → top-1 / top-3 labels."""
    allowed = {".jpg", ".jpeg", ".png", ".webp"}
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported image type: {ext}")

    content = await file.read()
    result = recognise_food(content)
    log_query(endpoint="/recognise", food=result.get("top1", ""))
    return result


# ─── FR-5 + FR-6 + FR-7: Advise ──────────────────────────────────────────────

class AdviseRequest(BaseModel):
    profile_id: Optional[str] = None
    conditions: list[str] = []
    allergens: list[str] = []
    hba1c: Optional[float] = None
    glucose_fasting: Optional[float] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    egfr: Optional[float] = None
    potassium: Optional[float] = None
    food: str = ""
    question: Optional[str] = None
    model: str = "claude-sonnet-4-5"
    strategy: str = "structured_role"


@app.post("/advise")
def advise_endpoint(req: AdviseRequest):
    """
    Full pipeline: safety_check + LLM advice.
    Returns verdict, reason, per-condition breakdown, disclaimer.
    """
    # Safety check from matrix (fast, no LLM needed)
    matrix_result = safety_check(req.food, req.conditions, req.allergens)

    # Build payload for LLM
    bp_str = f"{req.bp_systolic}/{req.bp_diastolic}" if req.bp_systolic and req.bp_diastolic else None
    payload = {
        "conditions": req.conditions,
        "allergens": req.allergens,
        "hba1c": req.hba1c,
        "blood_pressure": bp_str,
        "egfr": req.egfr,
        "potassium": req.potassium,
        "food": req.food,
        "question": req.question or f"Is {req.food} suitable for me given my conditions?",
        "matrix_verdict": matrix_result["verdict"],
        "matrix_reason": matrix_result["reason"],
    }

    # LLM advice — model is fixed to CLAUDE_MODEL inside llm_router, req.model is ignored
    llm_result = llm_query(req.strategy, payload)

    # For safety: if matrix says avoid but LLM says recommend → override to avoid
    final_verdict = llm_result["verdict"]
    if matrix_result["verdict"] == "avoid" and final_verdict == "recommend":
        final_verdict = "avoid"
        llm_result["reason"] = (
            "[Safety override] Matrix guideline says avoid. "
            + llm_result.get("reason", "")
        )

    log_query(
        endpoint="/advise",
        model=req.model,
        strategy=req.strategy,
        profile_id=req.profile_id or "",
        food=req.food,
        question=req.question or "",
        conditions=req.conditions,
        verdict=final_verdict,
        reason=llm_result.get("reason", ""),
        latency_ms=llm_result.get("latency_ms", 0),
    )

    return {
        "verdict": final_verdict,
        "reason": llm_result.get("reason", ""),
        "confidence": llm_result.get("confidence", "medium"),
        "per_condition": matrix_result.get("per_condition", {}),
        "allergy_flag": matrix_result.get("allergy_flag", False),
        "matrix_verdict": matrix_result["verdict"],
        "llm_verdict": llm_result["verdict"],
        "latency_ms": llm_result.get("latency_ms", 0),
        "model": req.model,
        "strategy": req.strategy,
        "disclaimer": MEDICAL_DISCLAIMER,
    }


# ─── Profiles (for UI convenience) ───────────────────────────────────────────

import json as _json

_PROFILES_PATH = Path(__file__).parent.parent / "data" / "profiles.json"


@app.get("/profiles")
def get_profiles():
    if not _PROFILES_PATH.exists():
        return []
    with open(_PROFILES_PATH) as f:
        return _json.load(f)


@app.get("/profiles/{profile_id}")
def get_profile(profile_id: str):
    if not _PROFILES_PATH.exists():
        raise HTTPException(404, "profiles.json not found")
    with open(_PROFILES_PATH) as f:
        profiles = _json.load(f)
    for p in profiles:
        if p["id"] == profile_id:
            return p
    raise HTTPException(404, f"Profile {profile_id} not found")
