"""
rag.py — Guideline retrieval for grounded prompting strategy.
Uses FAISS + sentence-transformers to embed and retrieve guideline chunks.
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

GUIDELINES_PATH = Path(__file__).parent.parent / "data" / "guidelines" / "guidelines_chunks.txt"
_INDEX = None
_CHUNKS: list[str] = []
_MODEL = None


def _load_and_index():
    """Load guideline chunks and build FAISS index. Lazy-loaded on first call."""
    global _INDEX, _CHUNKS, _MODEL

    if _INDEX is not None:
        return

    try:
        from sentence_transformers import SentenceTransformer
        import faiss
        import numpy as np
    except ImportError:
        logger.error("sentence-transformers or faiss-cpu not installed. RAG disabled.")
        return

    if not GUIDELINES_PATH.exists():
        logger.error("Guidelines file not found at %s", GUIDELINES_PATH)
        return

    raw = GUIDELINES_PATH.read_text(encoding="utf-8")
    # Split on blank lines separating chunks
    chunks = [c.strip() for c in raw.strip().split("\n\n") if c.strip()]
    _CHUNKS = chunks

    logger.info("Indexing %d guideline chunks with sentence-transformers...", len(chunks))
    _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = _MODEL.encode(chunks, convert_to_numpy=True).astype("float32")

    import faiss
    dim = embeddings.shape[1]
    _INDEX = faiss.IndexFlatL2(dim)
    _INDEX.add(embeddings)
    logger.info("FAISS index built with %d vectors (dim=%d)", len(chunks), dim)


def retrieve(query: str, top_k: int = 3) -> list[str]:
    """
    Retrieve the top-k most relevant guideline chunks for a query.
    Falls back to returning all chunks if FAISS is unavailable.
    """
    _load_and_index()

    if _INDEX is None or _MODEL is None:
        logger.warning("RAG index not available; returning all chunks")
        return _CHUNKS[:top_k] if _CHUNKS else []

    import numpy as np
    q_emb = _MODEL.encode([query], convert_to_numpy=True).astype("float32")
    distances, indices = _INDEX.search(q_emb, min(top_k, len(_CHUNKS)))
    results = [_CHUNKS[i] for i in indices[0] if i < len(_CHUNKS)]
    logger.debug("RAG retrieved %d chunks for query: %s", len(results), query[:80])
    return results
