"""
prompts.py — FR-8 / Appendix B: four prompting strategies.
All strategies accept the same payload dict and return a string prompt.
"""

from typing import Optional

MEDICAL_DISCLAIMER = (
    "⚕️ DISCLAIMER: This advice is AI-generated and for informational purposes only. "
    "It does not constitute medical advice. Always consult a qualified healthcare professional "
    "before making changes to your diet, especially if you have a medical condition."
)


def _format_profile(payload: dict) -> str:
    conds = payload.get("conditions", [])
    allergens = payload.get("allergens", [])
    hba1c = payload.get("hba1c")
    bp = payload.get("blood_pressure")
    egfr = payload.get("egfr")
    potassium = payload.get("potassium")

    parts = []
    if conds:
        parts.append(f"Active conditions: {', '.join(conds)}")
    if allergens:
        parts.append(f"Known allergens: {', '.join(allergens)}")
    if hba1c:
        parts.append(f"HbA1c: {hba1c} mmol/mol")
    if bp:
        parts.append(f"Blood pressure: {bp}")
    if egfr:
        parts.append(f"eGFR: {egfr} mL/min/1.73m²")
    if potassium:
        parts.append(f"Potassium: {potassium} mmol/L")
    return "\n".join(parts) if parts else "No specific conditions recorded."


def zero_shot(payload: dict) -> str:
    """Zero-shot: direct question, no examples or persona."""
    food = payload.get("food", "")
    question = payload.get("question", f"Is {food} suitable for me?")
    profile = _format_profile(payload)

    return f"""Patient profile:
{profile}

Food item: {food}

Question: {question}

Please provide a dietary recommendation (recommend, limit, or avoid) for this food item given the patient profile, along with a brief reason. End with a JSON object: {{"verdict": "recommend|limit|avoid", "reason": "..."}}"""


def structured_role(payload: dict) -> str:
    """Structured role: clinical dietitian persona + strict JSON output schema."""
    food = payload.get("food", "")
    question = payload.get("question", f"Is {food} suitable for this patient?")
    profile = _format_profile(payload)

    return f"""You are an expert clinical dietitian with specialist knowledge of NICE guidelines (NG28 for diabetes, NG136 for hypertension), KDOQI 2020 CKD nutritional guidelines, and FSA allergen regulations. You give evidence-based dietary advice.

Patient profile:
{profile}

Food item: {food}

Task: {question}

You MUST respond ONLY with a valid JSON object in exactly this format — no additional text before or after:
{{
  "verdict": "recommend" | "limit" | "avoid",
  "reason": "one to two sentence evidence-based explanation citing the relevant guideline",
  "confidence": "high" | "medium" | "low"
}}"""


def few_shot(payload: dict) -> str:
    """Few-shot: 2–3 worked examples to calibrate the model."""
    food = payload.get("food", "")
    question = payload.get("question", f"Is {food} suitable for this patient?")
    profile = _format_profile(payload)

    examples = """Example 1:
Patient: Active conditions: diabetes, hypertension | HbA1c: 65 mmol/mol | Blood pressure: 158/96
Food: french_fries
Answer: {"verdict": "avoid", "reason": "French fries are deep-fried with a very high glycaemic index, causing rapid blood glucose spikes (NICE NG28), and are high in sodium which exacerbates hypertension (NICE NG136/AHA). Avoid entirely.", "confidence": "high"}

Example 2:
Patient: Active conditions: ckd | eGFR: 35 | Potassium: 5.8 mmol/L
Food: sashimi
Answer: {"verdict": "recommend", "reason": "Sashimi is raw fish with near-zero potassium and phosphate content. Lean, high-quality protein is preferred in CKD (KDOQI 2020) and it presents no significant risk at this eGFR level.", "confidence": "high"}

Example 3:
Patient: Active conditions: diabetes, hypertension | HbA1c: 55 mmol/mol | Blood pressure: 145/90
Food: greek_salad
Answer: {"verdict": "recommend", "reason": "Greek salad is low-GI, fibre-rich and supports glycaemic control (Diabetes UK). The potassium and healthy fats from olives benefit blood pressure (AHA/DASH). Feta adds moderate sodium — small portion advised.", "confidence": "high"}"""

    return f"""{examples}

Now answer for the following patient:
Patient: {profile}
Food: {food}
Question: {question}
Answer (JSON only): """


def rag_grounded(payload: dict, retrieved_chunks: list[str]) -> str:
    """Guideline-grounded (RAG): inject retrieved guideline chunks before asking."""
    food = payload.get("food", "")
    question = payload.get("question", f"Is {food} suitable for this patient?")
    profile = _format_profile(payload)

    chunks_text = "\n\n".join(retrieved_chunks) if retrieved_chunks else "No specific guidelines retrieved."

    return f"""You are a clinical dietitian. Use ONLY the guideline excerpts below to answer the dietary question. Do not use any knowledge outside these excerpts.

--- GUIDELINE EXCERPTS ---
{chunks_text}
--- END GUIDELINES ---

Patient profile:
{profile}

Food item: {food}

Question: {question}

Based strictly on the guidelines above, respond ONLY with a valid JSON object:
{{
  "verdict": "recommend" | "limit" | "avoid",
  "reason": "evidence-based explanation citing the specific guideline source",
  "confidence": "high" | "medium" | "low"
}}"""


def build_prompt(strategy: str, payload: dict, retrieved_chunks: Optional[list[str]] = None) -> str:
    """Route to the correct strategy."""
    if strategy == "zero_shot":
        return zero_shot(payload)
    elif strategy == "structured_role":
        return structured_role(payload)
    elif strategy == "few_shot":
        return few_shot(payload)
    elif strategy == "rag_grounded":
        return rag_grounded(payload, retrieved_chunks or [])
    else:
        raise ValueError(f"Unknown strategy: {strategy}. Choose from: zero_shot, structured_role, few_shot, rag_grounded")
