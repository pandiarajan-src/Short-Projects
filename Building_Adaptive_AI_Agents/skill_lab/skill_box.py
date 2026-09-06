"""
The Skill Box (Lesson 2): a managed, versioned collection of skills.

Each skill lives as a markdown file in skills_box/<name>_v<version>.md.
A tiny SQLite table tracks status (active / pending / rejected) so the
human-in-the-loop review gate has something to approve or reject, exactly
like the course's notebook.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from skill_lab.trace_store import DB_PATH

BOX_DIR = Path(__file__).resolve().parent.parent / "skills_box"

SCHEMA = """
CREATE TABLE IF NOT EXISTS skills (
    name TEXT NOT NULL,
    version INTEGER NOT NULL,
    status TEXT NOT NULL,           -- active | pending | rejected
    body TEXT NOT NULL,
    writer TEXT,
    review_reason TEXT,
    PRIMARY KEY (name, version)
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA)
    return conn


def _skill_path(name: str, version: int) -> Path:
    return BOX_DIR / f"{name}_v{version}.md"


def seed_v1(name: str, body: str) -> None:
    """Register the hand-written v1 skill (already in skills_box/) as active."""
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO skills (name, version, status, body, writer) VALUES (?, 1, 'active', ?, 'human')",
            (name, body),
        )


def get_active(name: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT name, version, status, body, writer FROM skills WHERE name = ? AND status = 'active'",
            (name,),
        ).fetchone()
    if not row:
        return None
    return {"name": row[0], "version": row[1], "status": row[2], "body": row[3], "writer": row[4]}


def latest_version(name: str) -> int:
    with _connect() as conn:
        row = conn.execute("SELECT MAX(version) FROM skills WHERE name = ?", (name,)).fetchone()
    return row[0] or 0


def propose(name: str, body: str, writer: str) -> int:
    """Store a new pending version proposed by the induction engine."""
    version = latest_version(name) + 1
    with _connect() as conn:
        conn.execute(
            "INSERT INTO skills (name, version, status, body, writer) VALUES (?, ?, 'pending', ?, ?)",
            (name, version, body, writer),
        )
    _skill_path(name, version).write_text(
        f"---\nname: {name}\nversion: {version}\nstatus: pending\nwriter: {writer}\n---\n\n{body}"
    )
    return version


def get_pending(name: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT name, version, status, body, writer FROM skills WHERE name = ? AND status = 'pending' "
            "ORDER BY version DESC LIMIT 1",
            (name,),
        ).fetchone()
    if not row:
        return None
    return {"name": row[0], "version": row[1], "status": row[2], "body": row[3], "writer": row[4]}


def diff_active_vs_pending(name: str) -> str:
    active = get_active(name)
    pending = get_pending(name)
    if not pending:
        return "No pending proposal for this skill."
    active_body = active["body"] if active else "(no active version yet)"
    lines = ["--- active (v%d) ---" % (active["version"] if active else 0), active_body,
              "", "+++ proposed (v%d, writer=%s) +++" % (pending["version"], pending["writer"]), pending["body"]]
    return "\n".join(lines)


def approve(name: str, reason: str) -> int:
    """Human approves the latest pending proposal -> it becomes active,
    demoting the previous active version."""
    pending = get_pending(name)
    if not pending:
        raise ValueError(f"No pending proposal for '{name}'")
    with _connect() as conn:
        conn.execute("UPDATE skills SET status = 'active' WHERE name = ? AND status = 'active'", (name,))
        conn.execute(
            "UPDATE skills SET status = 'active', review_reason = ? WHERE name = ? AND version = ?",
            (reason, name, pending["version"]),
        )
        conn.execute(
            "UPDATE skills SET status = 'superseded' WHERE name = ? AND version != ? AND status = 'active'",
            (name, pending["version"]),
        )
    path = _skill_path(name, pending["version"])
    text = path.read_text().replace("status: pending", "status: active")
    path.write_text(text)
    return pending["version"]


def reject(name: str, reason: str) -> int:
    pending = get_pending(name)
    if not pending:
        raise ValueError(f"No pending proposal for '{name}'")
    with _connect() as conn:
        conn.execute(
            "UPDATE skills SET status = 'rejected', review_reason = ? WHERE name = ? AND version = ?",
            (reason, name, pending["version"]),
        )
    return pending["version"]


def list_skill_box() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT name, version, status, writer FROM skills ORDER BY name, version").fetchall()
    return [{"name": r[0], "version": r[1], "status": r[2], "writer": r[3]} for r in rows]
