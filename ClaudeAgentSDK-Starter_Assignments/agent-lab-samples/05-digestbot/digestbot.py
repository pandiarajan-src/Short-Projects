#!/usr/bin/env python3
"""DigestBot - a Claude Agent SDK agent that searches the live web and writes a short news digest.

Built-in tools: WebSearch, WebFetch (read-only web access).
Custom tools:
  check_link   - confirm a URL actually loads before using it
  save_digest  - validates the digest (working links, no duplicate stories, summaries not copied
                 from headlines) and writes it to Markdown

Every run prints its cost (ResultMessage.total_cost_usd).

Usage:
  python digestbot.py "vertical farming"
  python digestbot.py --topics-file topics.txt            # first topic in the file
  python digestbot.py --topics-file topics.txt --all      # every topic, one digest each
"""

import argparse
import asyncio
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlsplit

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

USER_AGENT = "Mozilla/5.0 (DigestBot link checker)"


def text(msg: str, error: bool = False) -> dict:
    result = {"content": [{"type": "text", "text": msg}]}
    if error:
        result["is_error"] = True
    return result


def http_status(url: str) -> int | str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:  # DNS failure, timeout, TLS error ...
        return f"unreachable ({type(e).__name__})"


def link_ok(status: int | str) -> bool:
    # 401/403/429 usually mean the site blocks scripts, not that the page is gone
    return isinstance(status, int) and (status < 400 or status in (401, 403, 429))


def normalise_url(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.netloc.lower().removeprefix('www.')}{parts.path.rstrip('/')}"


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def build_tools(topic: str, out_path: Path, min_stories: int, max_stories: int):
    @tool("check_link", "Check that a URL loads. Returns the HTTP status.", {"url": str})
    async def check_link(args):
        status = await asyncio.to_thread(http_status, args["url"])
        return text(f"{args['url']} -> {status} ({'OK' if link_ok(status) else 'BROKEN'})")

    @tool("save_digest",
          f"Save the digest: {min_stories}-{max_stories} distinct stories. Rejected if links are broken, "
          "stories duplicate each other, or summaries just repeat the headline.",
          {
              "type": "object",
              "properties": {
                  "intro": {"type": "string", "description": "1-2 sentence overview of the topic right now"},
                  "stories": {
                      "type": "array",
                      "items": {
                          "type": "object",
                          "properties": {
                              "headline": {"type": "string"},
                              "source": {"type": "string", "description": "publication name"},
                              "published": {"type": "string", "description": "date if known, else 'unknown'"},
                              "url": {"type": "string"},
                              "summary": {"type": "string", "description": "2-3 sentences in your own words"},
                          },
                          "required": ["headline", "source", "published", "url", "summary"],
                      },
                  },
              },
              "required": ["intro", "stories"],
          })
    async def save_digest(args):
        stories, problems = args["stories"], []
        if not min_stories <= len(stories) <= max_stories:
            problems.append(f"need {min_stories}-{max_stories} stories, got {len(stories)}")
        for i, s in enumerate(stories):
            for j in range(i):
                if normalise_url(s["url"]) == normalise_url(stories[j]["url"]):
                    problems.append(f"story {i + 1} has the same link as story {j + 1}")
                elif SequenceMatcher(None, s["headline"].lower(), stories[j]["headline"].lower()).ratio() > 0.75:
                    problems.append(f"story {i + 1} looks like the same story as {j + 1}")
            if SequenceMatcher(None, s["summary"].lower(), s["headline"].lower()).ratio() > 0.8:
                problems.append(f"story {i + 1}: summary just repeats the headline")
            if len(s["summary"].split()) < 15:
                problems.append(f"story {i + 1}: summary is too short to be useful")
        statuses = await asyncio.gather(*(asyncio.to_thread(http_status, s["url"]) for s in stories))
        for i, (s, st) in enumerate(zip(stories, statuses), 1):
            if not link_ok(st):
                problems.append(f"story {i}: link {s['url']} is broken ({st}) - replace it")
        if problems:
            return text("Not saved:\n- " + "\n- ".join(problems), error=True)

        md = [f"# {topic.title()} - news digest", f"_{date.today():%d %B %Y}_", "", args["intro"], ""]
        for i, s in enumerate(stories, 1):
            md += [f"## {i}. {s['headline']}", f"*{s['source']}, {s['published']}*", "",
                   s["summary"], "", f"[Read more]({s['url']})", ""]
        out_path.write_text("\n".join(md), encoding="utf-8")
        return text(f"Digest saved to {out_path}")

    return [check_link, save_digest]


SYSTEM_PROMPT = """You are DigestBot. You write a short, trustworthy news digest on one topic.

Steps:
1. Use WebSearch to find recent, reputable coverage (prefer the last few months). Try 2-3 searches
   with different wording if the topic is broad or narrow.
2. Pick distinct stories - not the same announcement reported by several outlets.
3. Use WebFetch on a story when the search snippet is not enough to summarise it accurately.
4. check_link any URL you are unsure about. Only use URLs you actually found - never guess one.
5. Write every summary in your own words (no copying sentences from the article), saying what
   happened and why it matters.
6. save_digest. If it is rejected, fix the listed problems and call it again.
Finish with one line saying how many stories you saved.
"""


async def run_topic(topic: str, out_dir: Path, args) -> float:
    out = out_dir / f"digest-{slugify(topic)}-{date.today().isoformat()}.md"
    server = create_sdk_mcp_server("digest", tools=build_tools(topic, out, args.min, args.max))
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"digest": server},
        tools=["WebSearch", "WebFetch"],
        allowed_tools=["WebSearch", "WebFetch", "mcp__digest__check_link", "mcp__digest__save_digest"],
        permission_mode="dontAsk",
        max_turns=40,
        max_budget_usd=args.budget,
        model=args.model,
    )

    out.unlink(missing_ok=True)  # never show a report from an earlier run
    print(f"\n##### DigestBot: {topic} #####")
    cost = 0.0
    async for msg in query(prompt=f"Topic: {topic}", options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                elif isinstance(block, ToolUseBlock):
                    shown = {k: v for k, v in block.input.items() if k not in ("stories", "intro", "prompt")}
                    print(f"  -> {block.name.split('__')[-1]} {shown}")
        elif isinstance(msg, ResultMessage):
            cost = msg.total_cost_usd or 0.0
            if out.exists():
                print(f"\n=== {out} ===\n{out.read_text(encoding='utf-8')}")
            else:
                print(f"No digest saved ({msg.subtype}).")
            print(f"Turns: {msg.num_turns}  Cost: ${cost:.4f}")
    return cost


def read_topics(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.lstrip().startswith("#")]


async def main() -> int:
    ap = argparse.ArgumentParser(description="DigestBot - a web news digest on any topic.")
    ap.add_argument("topic", nargs="?", help="topic to cover")
    ap.add_argument("--topics-file", type=Path, help="file with one topic per line ('#' = comment)")
    ap.add_argument("--all", action="store_true", help="with --topics-file: run every topic")
    ap.add_argument("--min", type=int, default=3, help="minimum stories (default 3)")
    ap.add_argument("--max", type=int, default=5, help="maximum stories (default 5)")
    ap.add_argument("--budget", type=float, default=1.0, help="max spend per topic in USD (default 1.0)")
    ap.add_argument("--out-dir", type=Path, default=Path(__file__).parent / "digests")
    ap.add_argument("--model", default=None, help="Claude model to use (default: SDK default)")
    args = ap.parse_args()

    if args.topic:
        topics = [args.topic]
    elif args.topics_file:
        topics = read_topics(args.topics_file)
        topics = topics if args.all else topics[:1]
    else:
        ap.error("give a topic or --topics-file")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    total = 0.0
    for topic in topics:
        total += await run_topic(topic, args.out_dir, args)
    if len(topics) > 1:
        print(f"\nTotal cost for {len(topics)} topics: ${total:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
