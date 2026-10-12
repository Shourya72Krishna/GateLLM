import sqlite3
import time

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    model TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    latency_ms REAL,
    cost_usd REAL,
    status TEXT,
    error TEXT
)
"""


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(settings.db_path)


def init_db() -> None:
    with _conn() as c:
        c.execute(SCHEMA)


def log_request(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    cost_usd: float,
    status: str = "ok",
    error: str | None = None,
) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO requests (ts, model, prompt_tokens, completion_tokens, "
            "latency_ms, cost_usd, status, error) VALUES (?,?,?,?,?,?,?,?)",
            (time.time(), model, prompt_tokens, completion_tokens,
             latency_ms, cost_usd, status, error),
        )