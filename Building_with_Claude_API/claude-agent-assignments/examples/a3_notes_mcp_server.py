"""
Assignment 3 - Reference example (part 1 of 2): a minimal MCP SERVER.

MCP (Model Context Protocol) is a standard way to expose tools and data to
ANY AI app. Instead of hard-coding tools inside one agent (like assignment 2),
we put them in a separate server process. Any MCP client - our own client,
Claude Code, Claude Desktop, the Claude Agent SDK - can then use them.

An MCP server can offer three things:
  * Tools     - functions the model can call       (@mcp.tool)
  * Resources - read-only data the app can fetch   (@mcp.resource)
  * Prompts   - reusable prompt templates          (@mcp.prompt)

This server talks over STDIO (stdin/stdout), so the client starts it as a
subprocess. You normally do NOT run it by hand - a3_mcp_client.py launches it.
To poke at it interactively, use the MCP Inspector:
  uv run mcp dev examples/a3_notes_mcp_server.py

IMPORTANT: never print() to stdout in a stdio server - stdout carries the
protocol messages. Log to stderr instead.
"""

import json
from datetime import datetime
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

NOTES_FILE = Path(__file__).parent / "study_notes.json"

mcp = MCPServer("study-notes")


def _load() -> list[dict]:
    return json.loads(NOTES_FILE.read_text()) if NOTES_FILE.exists() else []


def _save(notes: list[dict]) -> None:
    NOTES_FILE.write_text(json.dumps(notes, indent=2))


# ----------------------------- Tools ---------------------------------------
# The function name becomes the tool name, the docstring becomes the
# description, and the type hints become the JSON input schema.

@mcp.tool()
def add_note(topic: str, content: str) -> str:
    """Save a study note under a topic (e.g. 'python', 'databases')."""
    notes = _load()
    new_id = max((n["id"] for n in notes), default=0) + 1
    notes.append({
        "id": new_id,
        "topic": topic.lower().strip(),
        "content": content,
        "created": datetime.now().isoformat(timespec="seconds"),
    })
    _save(notes)
    return f"Saved note #{new_id} under topic '{topic}'."


@mcp.tool()
def search_notes(keyword: str) -> str:
    """Find notes whose topic or content contains the keyword (case-insensitive)."""
    keyword = keyword.lower()
    hits = [n for n in _load() if keyword in n["topic"] or keyword in n["content"].lower()]
    return json.dumps(hits) if hits else f"No notes matching '{keyword}'."


@mcp.tool()
def delete_note(note_id: int) -> str:
    """Delete a note by its numeric id."""
    notes = _load()
    remaining = [n for n in notes if n["id"] != note_id]
    if len(remaining) == len(notes):
        # ToolError = an expected failure: Claude receives is_error=True plus this message.
        # Any other exception is treated as a crash and Claude only sees a generic error.
        raise ToolError(f"Note #{note_id} does not exist.")
    _save(remaining)
    return f"Deleted note #{note_id}."


# ----------------------------- Resources -----------------------------------
# Resources are addressed by URI. "{topic}" makes this a resource TEMPLATE.

@mcp.resource("notes://all", mime_type="application/json")
def all_notes() -> str:
    """Every saved note as JSON."""
    return json.dumps(_load(), indent=2)


@mcp.resource("notes://topic/{topic}", mime_type="application/json")
def notes_for_topic(topic: str) -> str:
    """All notes for a single topic."""
    return json.dumps([n for n in _load() if n["topic"] == topic.lower()], indent=2)


# ----------------------------- Prompts -------------------------------------

@mcp.prompt()
def quiz_me(topic: str) -> str:
    """Ask the assistant to quiz the student using their own notes."""
    return (
        f"Use the search_notes tool to find my notes about '{topic}'. "
        "Then ask me 3 short quiz questions, one at a time, based ONLY on those notes. "
        "Wait for my answer before asking the next question."
    )


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
