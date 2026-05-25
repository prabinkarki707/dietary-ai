"""
food_recognition.py — FR-4: food image → top-1/top-3 labels from Food-101 model.
Uses a ViT fine-tuned on Food-101 from Hugging Face.
Model is cached in memory after first load (NFR-5).
"""

import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

MODEL_ID = "nateraw/food"   # ViT-base fine-tuned on Food-101
_PIPELINE = None


def _load_pipeline():
    global _PIPELINE
    if _PIPELINE is not None:
        return _PIPELINE
    try:
        from transformers import pipeline
        logger.info("Loading food recognition model: %s ...", MODEL_ID)
        _PIPELINE = pipeline(
            "image-classification",
            model=MODEL_ID,
            top_k=3,
        )
        logger.info("Food recognition model loaded.")
    except Exception as e:
        logger.error("Failed to load food recognition model: %s", e)
        _PIPELINE = None
    return _PIPELINE


def recognise_food(image_bytes: bytes) -> dict:
    """
    Returns:
        {
          top1: str,
          top3: [{label, score}, ...],
          error: str | None
        }
    """
    pipe = _load_pipeline()
    if pipe is None:
        return {"top1": "unknown", "top3": [], "error": "Model not available"}

    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        results = pipe(img)
        top3 = [{"label": r["label"].lower().replace(" ", "_"), "score": round(r["score"], 4)} for r in results]
        return {"top1": top3[0]["label"] if top3 else "unknown", "top3": top3, "error": None}
    except Exception as e:
        logger.error("Food recognition inference failed: %s", e)
        return {"top1": "unknown", "top3": [], "error": str(e)}
