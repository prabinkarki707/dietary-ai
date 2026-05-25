"""
ocr.py — FR-1: medical report image → raw text.
Supports JPG/PNG/PDF. Tries Google Cloud Vision first (accuracy), falls back to pytesseract.
"""

import os
import io
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _ocr_pytesseract(image_bytes: bytes, mime_type: str = "image/png") -> str:
    import pytesseract
    from PIL import Image
    img = Image.open(io.BytesIO(image_bytes))
    text = pytesseract.image_to_string(img, config="--psm 6")
    return text.strip()


def _ocr_pdf(pdf_bytes: bytes) -> str:
    from pdf2image import convert_from_bytes
    import pytesseract
    pages = convert_from_bytes(pdf_bytes, dpi=200)
    texts = [pytesseract.image_to_string(page, config="--psm 6") for page in pages]
    return "\n\n".join(texts).strip()


def extract_text(file_bytes: bytes, filename: str) -> dict:
    """
    Accept raw bytes + filename. Returns:
        {text: str, method: str, confidence: str}
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        try:
            text = _ocr_pdf(file_bytes)
            return {"text": text, "method": "pytesseract-pdf", "confidence": "medium"}
        except Exception as e:
            logger.error("PDF OCR failed: %s", e)
            return {"text": "", "method": "failed", "confidence": "low"}

    # Try Google Cloud Vision if key present
    gcp_key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get("GOOGLE_API_KEY")
    if gcp_key:
        try:
            text = _ocr_google_vision(file_bytes)
            if text:
                return {"text": text, "method": "google-vision", "confidence": "high"}
        except Exception as e:
            logger.warning("Google Vision OCR failed, falling back to pytesseract: %s", e)

    # Fallback: pytesseract
    try:
        text = _ocr_pytesseract(file_bytes)
        return {"text": text, "method": "pytesseract", "confidence": "medium"}
    except Exception as e:
        logger.error("pytesseract OCR failed: %s", e)
        return {"text": "", "method": "failed", "confidence": "low"}


def _ocr_google_vision(image_bytes: bytes) -> str:
    """Use Google Cloud Vision API for high-accuracy OCR."""
    import base64
    import requests
    key = os.environ.get("GOOGLE_API_KEY", "")
    url = f"https://vision.googleapis.com/v1/images:annotate?key={key}"
    payload = {
        "requests": [{
            "image": {"content": base64.b64encode(image_bytes).decode()},
            "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
        }]
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    annotations = resp.json().get("responses", [{}])[0]
    return annotations.get("fullTextAnnotation", {}).get("text", "")
