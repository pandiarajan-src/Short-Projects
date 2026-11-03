"""
Assignment 4 - Reference example: one agent that combines everything,
built with the Claude Agent SDK (no other framework).

In assignments 1-3 we wrote the agent loop ourselves. The Claude Agent SDK
gives us the same loop Claude Code uses - we just configure it:

    +-------------------- Study Buddy agent (ClaudeSDKClient) --------------------+
    |  Built-in web tools   : WebSearch, WebFetch          (run by Claude Code)    |
    |  External MCP server  : a3_notes_mcp_server.py       (stdio subprocess)      |
    |  In-process MCP tool  : study_plan                   (@tool in this file)    |
    |  Skill                : .claude/skills/flashcards/SKILL.md                   |
    +------------------------------------------------------------------------------+

Authentication: the Agent SDK runs Claude Code under the hood, so it can use
your Claude Pro login (run `claude` once and log in). By default this script
removes ANTHROPIC_API_KEY from its environment so your Pro subscription is used
instead of API credits. Set AGENT_AUTH=api_key in .env to use the API key.

Run:
  uv run python examples/a4_integrated_agent.py
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    tool,
)

load_dotenv()
if os.getenv("AGENT_AUTH", "subscription") != "api_key":
    os.environ.pop("ANTHROPIC_API_KEY", None)  # use the Claude Pro login

HERE = Path(__file__).parent

SYSTEM_PROMPT = """You are "Study Buddy", a research and revision agent for college students.
- Use WebSearch/WebFetch for facts you are not sure about, and cite sources.
- The student's notebook is behind the notes tools (add_note, search_notes, delete_note).
  Check it before researching a topic the student has studied before.
- Use study_plan when the student wants a revision schedule.
- Use the flashcards skill when the student asks for flashcards.
Keep answers concise."""


# ---------------------------------------------------------------------------
# 1. An in-process MCP tool. It runs inside THIS Python process - no
#    subprocess, no server file. Handy for logic that needs your app's state.
# ---------------------------------------------------------------------------

@tool(
    "study_plan",
    "Split a study session into Pomodoro blocks (25 min focus + 5 min break) across topics.",
    {"total_minutes": int, "topics": list[str]},
)
async def study_plan(args: dict) -> dict:
    topics = args["topics"] or ["general review"]
    blocks = max(1, args["total_minutes"] // 30)
    lines = [
        f"Block {i + 1}: 25 min on '{topics[i % len(topics)]}' + 5 min break"
        for i in range(blocks)
    ]
    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


planner_server = create_sdk_mcp_server(name="planner", version="1.0.0", tools=[study_plan])


# ---------------------------------------------------------------------------
# 2. Agent configuration - this is where all the pieces are plugged in.
# ---------------------------------------------------------------------------

options = ClaudeAgentOptions(
    system_prompt=SYSTEM_PROMPT,
    model=os.getenv("CLAUDE_MODEL") or None,  # None = Claude Code's default model
    cwd=str(HERE),                 # the agent works in examples/ ...
    setting_sources=["project"],   # ... and loads examples/.claude/ (our skill) only
    skills=["flashcards"],
    mcp_servers={
        # External MCP server from assignment 3, started as a subprocess.
        "notes": {"type": "stdio", "command": sys.executable,
                  "args": [str(HERE / "a3_notes_mcp_server.py")]},
        # In-process MCP server defined above.
        "planner": planner_server,
    },
    # Built-in Claude Code tools this agent may use. Everything else
    # (Bash, Write, Edit, ...) is not even offered to the model.
    tools=["WebSearch", "WebFetch", "Skill"],
    # Tools that run without asking. MCP tools are named mcp__<server>__<tool>.
    allowed_tools=[
        "WebSearch", "WebFetch",
        "mcp__notes__add_note", "mcp__notes__search_notes",
        "mcp__planner__study_plan",
    ],
    permission_mode="dontAsk",  # anything not allowed above is denied (e.g. delete_note)
    max_turns=15,               # safety net, like MAX_LOOPS in the earlier assignments
)


# ---------------------------------------------------------------------------
# 3. A multi-turn chat loop. ClaudeSDKClient keeps the session (memory) for us.
# ---------------------------------------------------------------------------

async def print_response(client: ClaudeSDKClient) -> None:
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                elif isinstance(block, ToolUseBlock):
                    print(f"\033[36m  [tool] {block.name} {block.input}\033[0m")
        elif isinstance(message, ResultMessage):
            cost = f"${message.total_cost_usd:.4f}" if message.total_cost_usd else "n/a"
            print(f"\033[90m  ({message.num_turns} turns, {message.duration_ms / 1000:.1f}s, "
                  f"cost estimate {cost})\033[0m\n")


async def main() -> None:
    print("Study Buddy (Claude Agent SDK). Type /quit to exit.")
    print("Try: 'Make me flashcards on HTTP status codes'  "
          "'What did I save about python?'  'Plan 2 hours on SQL and Git'\n")

    async with ClaudeSDKClient(options=options) as client:
        while True:
            try:
                user_text = (await asyncio.to_thread(input, "you > ")).strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not user_text:
                continue
            if user_text in ("/quit", "/exit"):
                break
            await client.query(user_text)
            await print_response(client)


if __name__ == "__main__":
    asyncio.run(main())
