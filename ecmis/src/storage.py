"""Saves each alert's status and note in a small SQLite file, so they survive app restarts."""
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

STATUSES = ["New", "Under Review", "Closed"]
DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "ecmis.db"


def _connect(db_path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path or DEFAULT_DB))
    conn.execute("""CREATE TABLE IF NOT EXISTS alert_review (
        alert_id TEXT PRIMARY KEY, status TEXT NOT NULL, note TEXT NOT NULL, updated_at TEXT NOT NULL)""")
    return conn


def load_reviews(db_path=None) -> dict[str, dict]:
    """All saved reviews as {alert_id: {"status": ..., "note": ...}}."""
    with closing(_connect(db_path)) as conn:
        rows = conn.execute("SELECT alert_id, status, note FROM alert_review").fetchall()
    return {alert_id: {"status": status, "note": note} for alert_id, status, note in rows}


def save_review(alert_id: str, status: str, note: str, db_path=None) -> None:
    if status not in STATUSES:
        raise ValueError(f"Status must be one of {STATUSES}")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with closing(_connect(db_path)) as conn, conn:  # "with conn" commits the change
        conn.execute(
            "INSERT INTO alert_review (alert_id, status, note, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(alert_id) DO UPDATE SET status=excluded.status, note=excluded.note, "
            "updated_at=excluded.updated_at",
            (alert_id, status, note.strip(), now))
