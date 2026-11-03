#!/usr/bin/env python3
"""StudyCards - a Claude Agent SDK agent that turns lecture notes into flashcards.

Claude writes the question/answer pairs; a custom tool keeps them honest:
  save_cards - rejects duplicate cards, rejects cards that cite a line in a recap/review section
               (cite where the fact is first taught), and rejects line numbers that are blank,
               headings, or out of range. Can be called repeatedly; accepted cards accumulate.

Output: <notes>-cards.csv (question,answer,source - imports into Anki/Quizlet) and <notes>-cards.md

Usage:
  python studycards.py notes-photosynthesis.md
  python studycards.py notes-http-basics.txt --cards 15
"""

import argparse
import asyncio
import csv
import re
import sys
from difflib import SequenceMatcher
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

HEADING = re.compile(r"^(#{1,6}\s+.+|\d+[a-z]?\.\s+[A-Z0-9][A-Z0-9 \-&/,']+)$")
RECAP = re.compile(r"recap|review|summary|revision", re.I)


def text(msg: str, error: bool = False) -> dict:
    result = {"content": [{"type": "text", "text": msg}]}
    if error:
        result["is_error"] = True
    return result


def recap_lines(lines: list[str]) -> set[int]:
    """1-based line numbers that sit inside a recap / review section."""
    inside, result = False, set()
    for n, line in enumerate(lines, 1):
        if HEADING.match(line.strip()):
            inside = bool(RECAP.search(line))
        elif inside:
            result.add(n)
    return result


def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def build_tools(lines: list[str], cards: list[dict]):
    recap = recap_lines(lines)

    @tool("save_cards",
          "Save flashcards. Each card cites source_line: the 1-based line number where the fact is "
          "taught. Returns which cards were accepted and why others were rejected.",
          {
              "type": "object",
              "properties": {
                  "cards": {
                      "type": "array",
                      "items": {
                          "type": "object",
                          "properties": {
                              "question": {"type": "string"},
                              "answer": {"type": "string"},
                              "source_line": {"type": "integer"},
                          },
                          "required": ["question", "answer", "source_line"],
                      },
                  }
              },
              "required": ["cards"],
          })
    async def save_cards(args):
        accepted, rejected = 0, []
        for c in args["cards"]:
            q, n = c["question"].strip(), c["source_line"]
            label = f"{q[:60]!r}"
            if not 1 <= n <= len(lines) or not lines[n - 1].strip():
                rejected.append(f"{label}: line {n} is blank or out of range")
            elif HEADING.match(lines[n - 1].strip()):
                rejected.append(f"{label}: line {n} is a heading; cite the line with the fact")
            elif n in recap:
                rejected.append(f"{label}: line {n} is in a recap/review section; cite the earlier "
                                "line where this fact is first taught (or drop it if already covered)")
            else:
                dup = next((d for d in cards if similar(d["question"], q) > 0.8
                            or (d["source_line"] == n and similar(d["answer"], c["answer"]) > 0.8)), None)
                if dup:
                    rejected.append(f"{label}: duplicate of existing card {dup['question']!r}")
                else:
                    cards.append({"question": q, "answer": c["answer"].strip(), "source_line": n})
                    accepted += 1
        msg = f"Accepted {accepted}. Total cards so far: {len(cards)}."
        if rejected:
            msg += "\nRejected:\n- " + "\n- ".join(rejected)
        return text(msg)

    return [save_cards]


SYSTEM_PROMPT = """You are StudyCards. You turn lecture notes into high-quality flashcards.

Good cards:
- Test ONE fact each. Clear question, short answer (a word, phrase or one sentence).
- Mix kinds: definitions, where/when, cause and effect, numbers, comparisons.
- Cover every section of the notes, but never make two cards for the same fact.
- Notes often end with a recap/review that repeats earlier facts. Do not make cards from it -
  those facts are already covered by cards citing the original lines.
- source_line must be the line number where the fact is stated (the numbers shown before '|').
Call save_cards (in one or a few batches). Read its feedback, fix or drop rejected cards, and
stop when you have about the requested number. Finish with a one-line summary.
"""


async def main() -> int:
    ap = argparse.ArgumentParser(description="StudyCards - make flashcards from lecture notes.")
    ap.add_argument("notes", type=Path)
    ap.add_argument("--cards", type=int, default=12, help="roughly how many cards (default 12)")
    ap.add_argument("--model", default=None, help="Claude model to use (default: SDK default)")
    args = ap.parse_args()

    lines = args.notes.read_text(encoding="utf-8").splitlines()
    cards: list[dict] = []
    server = create_sdk_mcp_server("cards", tools=build_tools(lines, cards))
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"cards": server},
        tools=[],
        allowed_tools=["mcp__cards__save_cards"],
        permission_mode="dontAsk",
        max_turns=12,
        model=args.model,
    )

    numbered = "\n".join(f"{n:3}| {line}" for n, line in enumerate(lines, 1))
    prompt = (f"Make about {args.cards} flashcards from these notes ({args.notes.name}).\n\n"
              f"<notes>\n{numbered}\n</notes>")

    result = None
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                elif isinstance(block, ToolUseBlock):
                    print(f"  -> {block.name.split('__')[-1]} ({len(block.input.get('cards', []))} cards)")
        elif isinstance(msg, ResultMessage):
            result = msg

    cards.sort(key=lambda c: c["source_line"])
    stem = args.notes.with_name(args.notes.stem + "-cards")
    with stem.with_suffix(".csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["question", "answer", "source"])
        for c in cards:
            w.writerow([c["question"], c["answer"], f"{args.notes.name}:{c['source_line']}"])
    md = [f"# Flashcards - {args.notes.name}", ""]
    for i, c in enumerate(cards, 1):
        md += [f"**Q{i}. {c['question']}**  ", f"A: {c['answer']}  ",
               f"_line {c['source_line']}: {lines[c['source_line'] - 1].strip()}_", ""]
    stem.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")

    print(f"\nSaved {len(cards)} cards to {stem}.csv and {stem}.md")
    for c in cards:
        print(f"  [{c['source_line']:3}] {c['question']}  ->  {c['answer']}")
    if result:
        print(f"Turns: {result.num_turns}  Cost: ${result.total_cost_usd or 0:.4f}")
        return 1 if result.is_error else 0
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
