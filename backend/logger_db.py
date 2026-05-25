"""
logger_db.py — FR-9: Persist queries + responses to SQLite for audit.
No secrets, no real PII.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "dietary_ai.db"


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS query_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            endpoint TEXT,
            model TEXT,
            strategy TEXT,
            profile_id TEXT,
            food TEXT,
            question TEXT,
            conditions TEXT,
            verdict TEXT,
            reason TEXT,
            latency_ms INTEGER,
            run INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialised at %s", DB_PATH)


def log_query(
    endpoint: str,
    model: str = "",
    strategy: str = "",
    profile_id: str = "",
    food: str = "",
    question: str = "",
    conditions: list = None,
    verdict: str = "",
    reason: str = "",
    latency_ms: int = 0,
    run: int = 1,
):
    try:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO query_log
               (timestamp, endpoint, model, strategy, profile_id, food, question,
                conditions, verdict, reason, latency_ms, run)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.utcnow().isoformat(),
                endpoint, model, strategy, profile_id, food, question,
                json.dumps(conditions or []),
                verdict, reason[:1000], latency_ms, run,
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("Failed to log query: %s", e)
