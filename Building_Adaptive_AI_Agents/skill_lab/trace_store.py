"""SQLite-backed store for agent traces (Lesson 2's raw material: 'a complete
record of every event that occurred within an agent interaction')."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "agent_lab.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS traces (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    task TEXT,
    content_json TEXT NOT NULL,
    outcome TEXT,
    fix_summary TEXT
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA)
    return conn


def load_sample_traces(json_path: str | Path) -> int:
    """Seed the DB with the sample traces shipped in data/sample_traces.json."""
    traces = json.loads(Path(json_path).read_text())
    with _connect() as conn:
        for t in traces:
            conn.execute(
                "INSERT OR REPLACE INTO traces (id, topic, task, content_json, outcome, fix_summary) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (t["id"], t["topic"], t.get("task"), json.dumps(t["steps"]), t.get("outcome"), t.get("fix_summary")),
            )
    return len(traces)


def get_traces_by_topic(topic: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, topic, task, content_json, outcome, fix_summary FROM traces WHERE topic = ?",
            (topic,),
        ).fetchall()
    return [
        {
            "id": r[0],
            "topic": r[1],
            "task": r[2],
            "steps": json.loads(r[3]),
            "outcome": r[4],
            "fix_summary": r[5],
        }
        for r in rows
    ]


def list_topics() -> list[str]:
    with _connect() as conn:
        rows = conn.execute("SELECT DISTINCT topic FROM traces").fetchall()
    return [r[0] for r in rows]
