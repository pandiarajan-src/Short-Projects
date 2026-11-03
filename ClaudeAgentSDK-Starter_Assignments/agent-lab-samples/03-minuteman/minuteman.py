#!/usr/bin/env python3
"""MinuteMan - a Claude Agent SDK agent that pulls action items out of a meeting transcript.

Claude reads the transcript and decides what is a real commitment. A custom tool checks its work
before anything is saved:
  save_action_items - owner must be an attendee, every item must quote a real transcript timestamp,
                      due dates must be real dates, no duplicates. Also records what was
                      deliberately left out (dropped, parked, no owner).

Usage:
  python minuteman.py standup-transcript.txt
  python minuteman.py planning-meeting-transcript.txt --out actions.md
"""

import argparse
import asyncio
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    query,
    tool,
)


def text(msg: str, error: bool = False) -> dict:
    result = {"content": [{"type": "text", "text": msg}]}
    if error:
        result["is_error"] = True
    return result


def parse_header(transcript: str) -> tuple[date | None, list[str]]:
    meeting_date = None
    m = re.search(r"^Date:\s*(?:\w+,\s*)?(\d{1,2} \w+ \d{4})", transcript, re.M)
    if m:
        meeting_date = datetime.strptime(m.group(1), "%d %B %Y").date()
    attendees = []
    m = re.search(r"^Attendees:\s*(.+)$", transcript, re.M)
    if m:
        attendees = [re.sub(r"\s*\(.*?\)", "", a).strip() for a in m.group(1).split(",")]
    return meeting_date, attendees


def calendar_hint(start: date) -> str:
    days = [start + timedelta(days=i) for i in range(0, 15)]
    return "\n".join(f"- {d:%A} {d:%d %B %Y} ({d.isoformat()})" for d in days)


def build_tools(transcript: str, attendees: list[str], out_path: Path, title: str):
    timestamps = set(re.findall(r"^\[(\d{1,2}:\d{2})\]", transcript, re.M))

    @tool("save_action_items",
          "Save the final list of action items and the topics deliberately left out. "
          "Rejected if anything fails validation - fix and call again.",
          {
              "type": "object",
              "properties": {
                  "items": {
                      "type": "array",
                      "items": {
                          "type": "object",
                          "properties": {
                              "owner": {"type": "string", "description": "one attendee's name"},
                              "task": {"type": "string", "description": "short imperative, e.g. 'Send sprint summary to leadership'"},
                              "due_date": {"type": "string", "description": "YYYY-MM-DD, or 'none' if no deadline was given"},
                              "due_as_said": {"type": "string", "description": "the deadline in the speaker's words, e.g. 'by noon today'"},
                              "timestamp": {"type": "string", "description": "transcript timestamp where it was agreed, e.g. '09:31'"},
                          },
                          "required": ["owner", "task", "due_date", "due_as_said", "timestamp"],
                      },
                  },
                  "not_actions": {
                      "type": "array",
                      "description": "things discussed but NOT action items, with why",
                      "items": {
                          "type": "object",
                          "properties": {"topic": {"type": "string"}, "why": {"type": "string"}},
                          "required": ["topic", "why"],
                      },
                  },
              },
              "required": ["items", "not_actions"],
          })
    async def save_action_items(args):
        problems, seen = [], set()
        for i, it in enumerate(args["items"], 1):
            if it["owner"] not in attendees:
                problems.append(f"item {i}: owner {it['owner']!r} is not an attendee {attendees}")
            if it["timestamp"] not in timestamps:
                problems.append(f"item {i}: timestamp {it['timestamp']!r} is not in the transcript")
            if it["due_date"] != "none":
                try:
                    date.fromisoformat(it["due_date"])
                except ValueError:
                    problems.append(f"item {i}: due_date {it['due_date']!r} is not YYYY-MM-DD or 'none'")
            key = (it["owner"], it["task"].lower().strip())
            if key in seen:
                problems.append(f"item {i}: duplicate of an earlier item")
            seen.add(key)
        if problems:
            return text("Not saved:\n- " + "\n- ".join(problems), error=True)

        items = sorted(args["items"], key=lambda it: (it["due_date"] == "none", it["due_date"]))
        md = [f"# Action items - {title}", "", "| # | Owner | Task | Due | Said at |",
              "|---|---|---|---|---|"]
        for i, it in enumerate(items, 1):
            due = it["due_as_said"] if it["due_date"] == "none" else f"{it['due_date']} ({it['due_as_said']})"
            md.append(f"| {i} | {it['owner']} | {it['task']} | {due} | {it['timestamp']} |")
        md += ["", "## Discussed but not action items", ""]
        md += [f"- **{n['topic']}** - {n['why']}" for n in args["not_actions"]] or ["- (none)"]
        out_path.write_text("\n".join(md) + "\n", encoding="utf-8")
        return text(f"Saved {len(items)} action items to {out_path}")

    return [save_action_items]


SYSTEM_PROMPT = """You are MinuteMan. You turn meeting transcripts into a precise list of action items.

An action item is a concrete task that a specific attendee agreed to do (or was asked to do and
accepted). Be strict:
- Ideas like "maybe someone should..." or "someone might want to..." with no owner are NOT action items.
- Topics that were dropped, parked, postponed ("let's talk about that later") or ruled out of scope
  are NOT action items. List them under not_actions with the reason.
- If a task is handed from one person to another, the FINAL owner is the one who accepted it.
- If the leader assigns work to themselves ("I'll prepare..."), that is an action item for them.
- A person committing to finish something by a stated time ("I should have X done by Wednesday")
  IS an action item, even if it is work already in progress. Only a status update with no
  promised deliverable or deadline ("I'm wiring it to the API today") is not.
- A request for something from another person with a deadline is an action item for the person who
  has to deliver it.
- Convert relative deadlines ("tomorrow", "by Wednesday", "end of week") into real dates using the
  meeting date and the calendar given. Keep the original words in due_as_said.
Call save_action_items once with everything; if it is rejected, fix the problems and call it again.
Then give a two-line summary.
"""


async def main() -> int:
    ap = argparse.ArgumentParser(description="MinuteMan - extract action items from a meeting transcript.")
    ap.add_argument("transcript", type=Path)
    ap.add_argument("--out", type=Path, help="output Markdown (default: <transcript>-actions.md)")
    ap.add_argument("--model", default=None, help="Claude model to use (default: SDK default)")
    args = ap.parse_args()

    transcript = args.transcript.read_text(encoding="utf-8")
    meeting_date, attendees = parse_header(transcript)
    if not attendees:
        sys.exit("Could not find an 'Attendees:' line in the transcript.")
    title = transcript.splitlines()[0].strip()
    out = args.out or args.transcript.with_name(args.transcript.stem + "-actions.md")

    server = create_sdk_mcp_server("minutes", tools=build_tools(transcript, attendees, out, title))
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"minutes": server},
        tools=[],
        allowed_tools=["mcp__minutes__save_action_items"],
        permission_mode="dontAsk",
        max_turns=10,
        model=args.model,
    )

    out.unlink(missing_ok=True)  # never show a report from an earlier run
    prompt = f"Attendees: {', '.join(attendees)}\n"
    if meeting_date:
        prompt += f"Meeting date: {meeting_date:%A %d %B %Y}\nCalendar:\n{calendar_hint(meeting_date)}\n"
    prompt += f"\n<transcript>\n{transcript}\n</transcript>"

    exit_code = 1
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                elif isinstance(block, ToolUseBlock):
                    print(f"  -> {block.name.split('__')[-1]} ({len(block.input.get('items', []))} items)")
        elif isinstance(msg, ResultMessage):
            if out.exists():
                print(f"\n=== {out} ===\n{out.read_text(encoding='utf-8')}")
            print(f"Turns: {msg.num_turns}  Cost: ${msg.total_cost_usd or 0:.4f}")
            exit_code = 1 if msg.is_error else 0
    return exit_code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
