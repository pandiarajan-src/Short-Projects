"""
Assignment 2 - Reference example: an agent that uses tools.

Two kinds of tools are used here:

  1. LOCAL (client) tools - plain Python functions that run on YOUR machine.
     Claude only *asks* for them (stop_reason == "tool_use"); our loop runs
     them and sends back a tool_result.
       - calculator          : safe arithmetic
       - get_current_datetime: today's date / time
       - save_note / list_notes : a tiny JSON "database" on disk

  2. SERVER tools - run on Anthropic's side. We only declare them.
       - web_search          : Claude searches the web and cites sources

The heart of every agent is the loop at the bottom of this file:

    while True:
        response = call Claude
        if Claude wants local tools  -> run them, append results, loop again
        if Claude paused a long turn -> send it back, loop again
        otherwise                    -> done, print the answer

Run:
  uv run python examples/a2_tool_agent.py
"""

import ast
import json
import operator
import os
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
NOTES_FILE = Path(__file__).parent / "notes.json"
MAX_LOOPS = 10  # safety net so a confused agent can't loop forever

SYSTEM_PROMPT = """You are "Study Buddy", a tutor agent with tools.
- Use the calculator for ANY arithmetic, never do math in your head.
- Use web_search for recent facts or anything you are unsure about, and cite sources.
- When the student asks you to remember something, save it with save_note.
Keep final answers short and clear."""


# ---------------------------------------------------------------------------
# 1. Local tool implementations (plain Python)
# ---------------------------------------------------------------------------

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def calculator(expression: str) -> str:
    """Evaluate arithmetic safely (no eval!) by walking the syntax tree."""

    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported expression element: {ast.dump(node)}")

    return str(_eval(ast.parse(expression, mode="eval").body))


def get_current_datetime() -> str:
    return datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")


def _load_notes() -> list[dict]:
    if NOTES_FILE.exists():
        return json.loads(NOTES_FILE.read_text())
    return []


def save_note(title: str, content: str) -> str:
    notes = _load_notes()
    notes.append({"title": title, "content": content, "saved_at": get_current_datetime()})
    NOTES_FILE.write_text(json.dumps(notes, indent=2))
    return f"Saved note '{title}'. You now have {len(notes)} note(s)."


def list_notes() -> str:
    notes = _load_notes()
    return json.dumps(notes) if notes else "No notes saved yet."


# Map tool name -> Python function. The loop uses this to dispatch calls.
LOCAL_TOOLS = {
    "calculator": calculator,
    "get_current_datetime": get_current_datetime,
    "save_note": save_note,
    "list_notes": list_notes,
}


# ---------------------------------------------------------------------------
# 2. Tool definitions Claude sees (name + description + JSON schema)
#    Good descriptions matter: they are how Claude decides WHEN to use a tool.
# ---------------------------------------------------------------------------

def _schema(properties: dict) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


LOCAL_TOOL_DEFINITIONS = [
    {
        "name": "calculator",
        "description": "Evaluate an arithmetic expression such as '(12.5 * 4) / 3' or '2 ** 10'. "
                       "Supports + - * / ** % and parentheses. Use for every calculation.",
        "input_schema": _schema({"expression": {"type": "string", "description": "The expression to evaluate."}}),
        "strict": True,  # Claude's arguments are guaranteed to match the schema
    },
    {
        "name": "get_current_datetime",
        "description": "Return the current local date and time. Use when the user mentions today, "
                       "deadlines, or how many days until something.",
        "input_schema": _schema({}),
        "strict": True,
    },
    {
        "name": "save_note",
        "description": "Save a study note to the student's notebook on disk.",
        "input_schema": _schema({
            "title": {"type": "string", "description": "Short title for the note."},
            "content": {"type": "string", "description": "The note text."},
        }),
        "strict": True,
    },
    {
        "name": "list_notes",
        "description": "List every note in the student's notebook.",
        "input_schema": _schema({}),
        "strict": True,
    },
]


def web_search_tool(model: str) -> dict:
    """Claude's built-in web search (runs on Anthropic's servers).
    Newer models use the dynamic-filtering version; Haiku uses the basic one."""
    version = "web_search_20250305" if "haiku" in model else "web_search_20260209"
    return {"type": version, "name": "web_search", "max_uses": 3}


# ---------------------------------------------------------------------------
# 3. The agent loop
# ---------------------------------------------------------------------------

def run_local_tools(response) -> list[dict]:
    """Run every tool_use block in the response and build tool_result blocks.
    ALL results go back in ONE user message (that keeps parallel tool use working)."""
    results = []
    for block in response.content:
        if block.type != "tool_use":
            continue
        print(f"\033[36m  [tool] {block.name}({json.dumps(block.input)})\033[0m")
        try:
            output = LOCAL_TOOLS[block.name](**block.input)
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
        except Exception as exc:  # report failures to Claude instead of crashing
            results.append({
                "type": "tool_result", "tool_use_id": block.id,
                "content": f"Error: {exc}", "is_error": True,
            })
        print(f"\033[90m         -> {results[-1]['content'][:120]}\033[0m")
    return results


def log_server_tools(response) -> None:
    for block in response.content:
        if block.type == "server_tool_use":
            print(f"\033[35m  [web] {block.name}({json.dumps(block.input)})\033[0m")


def run_agent(client: anthropic.Anthropic, messages: list[dict]) -> str:
    tools = LOCAL_TOOL_DEFINITIONS + [web_search_tool(MODEL)]

    for _ in range(MAX_LOOPS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )
        log_server_tools(response)
        # Always keep the full assistant content (text, tool_use, thinking, search results).
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "tool_use":
            messages.append({"role": "user", "content": run_local_tools(response)})
            continue
        if response.stop_reason == "pause_turn":
            continue  # a long server-tool turn paused; send it back to let Claude resume
        if response.stop_reason == "refusal":
            return "[Claude declined this request]"

        return "".join(b.text for b in response.content if b.type == "text")

    return "[stopped: too many tool loops]"


def main() -> None:
    client = anthropic.Anthropic()
    messages: list[dict] = []
    print(f"Study Buddy + tools ({MODEL}). Type /quit to exit.")
    print("Try: 'What is 17.5% of 2340?'  'Remember that my exam is on Dec 12'  "
          "'How many days until my exam?'  'What is the latest Python release?'\n")

    while True:
        try:
            user_text = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_text:
            continue
        if user_text in ("/quit", "/exit"):
            break

        messages.append({"role": "user", "content": user_text})
        answer = run_agent(client, messages)
        print(f"buddy > {answer}\n")


if __name__ == "__main__":
    main()
