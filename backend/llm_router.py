"""
llm_router.py — FR-8: single interface to the LLM backend.
query(strategy, payload) → {verdict, reason, raw_response, latency_ms}

The only variable in the experiment is *strategy*.
Model is controlled by LLM_BACKEND env var:
  - "claude"  → Claude Sonnet 4.5 via Anthropic API (costs money)
  - "ollama"  → local Ollama model, free, runs on M4 Pro (default)
"""

import os
import json
import time
import re
import logging

from backend.prompts import build_prompt, MEDICAL_DISCLAIMER
from backend.rag import retrieve

logger = logging.getLogger(__name__)

# Which backend to use — default to free local Ollama
LLM_BACKEND = os.environ.get("LLM_BACKEND", "ollama").lower()

# Model names
CLAUDE_MODEL = "claude-sonnet-4-5"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")

# For the experiment, the "model" reported in CSV
ACTIVE_MODEL = CLAUDE_MODEL if LLM_BACKEND == "claude" else OLLAMA_MODEL

# Legacy alias
SUPPORTED_MODELS = [CLAUDE_MODEL]

STRATEGIES = ["zero_shot", "structured_role", "few_shot", "rag_grounded"]


def _parse_llm_output(raw: str) -> dict:
    """
    Extract JSON from LLM response. Handles:
    - Pure JSON
    - JSON embedded in text / markdown code blocks
    - Nested braces (Llama output style)
    - Malformed output → safe keyword fallback
    """
    text = raw.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try markdown code block first
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Extract outermost balanced {...} block (handles nested braces)
    start_idx = text.find('{')
    if start_idx != -1:
        depth = 0
        for i, ch in enumerate(text[start_idx:], start_idx):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start_idx:i+1])
                    except json.JSONDecodeError:
                        break

    # Keyword fallback
    lower = text.lower()
    if "avoid" in lower:
        verdict = "avoid"
    elif "limit" in lower:
        verdict = "limit"
    elif "recommend" in lower:
        verdict = "recommend"
    else:
        verdict = "uncertain"

    logger.warning("Could not parse JSON from LLM output; used keyword fallback. Raw: %s", raw[:200])
    return {
        "verdict": verdict,
        "reason": raw[:500] if raw else "Unable to parse model response. Please consult a healthcare professional.",
        "confidence": "low",
        "_parse_fallback": True,
    }


def _call_claude(prompt: str) -> str:
    """Call the fixed Claude model. This is the only real LLM path."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        temperature=0.0,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def _call_ollama(prompt: str) -> str:
    """Call a local Ollama model — free, runs on M4 Pro GPU."""
    import urllib.request
    data = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 512},
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode())
    return result["response"]


def _call_llm(prompt: str) -> str:
    """Route to local Ollama or cloud Claude based on LLM_BACKEND env var."""
    if LLM_BACKEND == "claude":
        return _call_claude(prompt)
    return _call_ollama(prompt)


def query(strategy: str, payload: dict, model: str = ACTIVE_MODEL) -> dict:
    """
    Central query function. Routes to local Ollama (free) or Claude API
    based on LLM_BACKEND environment variable (default: ollama).

    Returns:
        {verdict, reason, confidence, raw_response, latency_ms, disclaimer, model, strategy}
    """
    model = ACTIVE_MODEL  # enforce configured backend

    # Build RAG chunks if needed
    retrieved_chunks = []
    if strategy == "rag_grounded":
        food = payload.get("food", "")
        conditions = payload.get("conditions", [])
        rag_query = f"{food} dietary advice for {', '.join(conditions) if conditions else 'general'}"
        retrieved_chunks = retrieve(rag_query, top_k=3)

    prompt = build_prompt(strategy, payload, retrieved_chunks)

    start = time.perf_counter()
    try:
        raw = _call_llm(prompt)
    except Exception as e:
        logger.error("LLM call failed strategy=%s backend=%s: %s", strategy, LLM_BACKEND, e)
        return {
            "verdict": "uncertain",
            "reason": "Model call failed — uncertain verdict. Please consult a healthcare professional.",
            "confidence": "low",
            "raw_response": "",
            "latency_ms": int((time.perf_counter() - start) * 1000),
            "disclaimer": MEDICAL_DISCLAIMER,
            "model": model,
            "strategy": strategy,
            "error": str(e),
        }

    latency_ms = int((time.perf_counter() - start) * 1000)
    parsed = _parse_llm_output(raw)

    # Malformed-output safety: if parse fully failed and no keyword matched,
    # return a safe uncertain rather than a silent guess.
    if parsed.get("_parse_fallback") and parsed.get("verdict") == "uncertain":
        parsed["reason"] = (
            "Response could not be parsed — uncertain verdict. "
            "Please consult a healthcare professional."
        )

    return {
        "verdict": parsed.get("verdict", "uncertain"),
        "reason": parsed.get("reason", ""),
        "confidence": parsed.get("confidence", "medium"),
        "raw_response": raw,
        "latency_ms": latency_ms,
        "disclaimer": MEDICAL_DISCLAIMER,
        "model": model,
        "strategy": strategy,
        "_parse_fallback": parsed.get("_parse_fallback", False),
    }
