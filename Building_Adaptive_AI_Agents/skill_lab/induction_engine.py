"""
The Skill Induction Engine (Lesson 2): reads all traces for one topic and
drafts an improved skill.md. Mirrors the course's "Induction Engine
contract": take episodes -> distill into reusable procedure + evidence.

Two writers are provided:
  - `llm_write_skill`      real LLM call (OpenAI-compatible; works with a
                            free local Ollama model, see .env.example)
  - `heuristic_write_skill` a zero-setup, deterministic stand-in so the demo
                            runs with no API key / no internet at all.

`draft_skill()` picks whichever is available automatically.
"""
from __future__ import annotations

import os
from collections import Counter

PROMPT_TEMPLATE = """You are a Skill Induction Engine for a coding agent.

You will be given several past traces (episodes) for the same recurring
task/topic: what the agent tried, where it failed, and what finally worked.

Your job:
1. Find the repeated failure pattern and the fix that actually worked.
2. Write an improved procedure as a numbered list of concrete steps.
3. List any tools/commands used and any errors + fixes observed.
4. Keep it short and actionable — this becomes a skill.md a future agent
   run will follow verbatim.

Topic: {topic}

Traces:
{traces_text}

Output a markdown skill with sections: `## Steps`, `## Tools`, `## Known errors & fixes`.
"""


def _traces_to_text(traces: list[dict]) -> str:
    chunks = []
    for t in traces:
        step_lines = "\n".join(
            f"  - {s.get('action')}: {s.get('input', s.get('note', ''))} -> {s.get('result', '')}"
            for s in t["steps"]
        )
        chunks.append(f"[{t['id']}] task: {t['task']}\n{step_lines}\nfix_summary: {t.get('fix_summary', '')}")
    return "\n\n".join(chunks)


def llm_write_skill(topic: str, traces: list[dict]) -> str | None:
    """Try a real LLM call. Returns None if no endpoint is configured or the
    call fails, so callers can fall back gracefully."""
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not base_url or not api_key:
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None

    try:
        client = OpenAI(base_url=base_url, api_key=api_key)
        prompt = PROMPT_TEMPLATE.format(topic=topic, traces_text=_traces_to_text(traces))
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return resp.choices[0].message.content
    except Exception as exc:  # network down, model missing, etc.
        print(f"[induction_engine] LLM call failed, falling back to heuristic writer: {exc}")
        return None


def heuristic_write_skill(topic: str, traces: list[dict]) -> str:
    """A simple, deterministic 'induction engine' with no LLM: it looks at
    which tool calls preceded a success across traces and writes those up
    as steps. This exists so the whole project runs offline with zero setup
    — swap in `llm_write_skill` for real distillation quality."""
    tool_calls: Counter[tuple[str, str]] = Counter()
    errors_fixes = []
    for t in traces:
        steps = t["steps"]
        for i, s in enumerate(steps):
            if s.get("action") == "tool_call":
                tool_calls[(s["tool"], s["input"])] += 1
                if "error" in str(s.get("result", "")).lower() or "notfound" in str(s.get("result", "")).lower().replace(" ", ""):
                    fix = steps[i + 1] if i + 1 < len(steps) else None
                    if fix and fix.get("action") == "tool_call":
                        errors_fixes.append((s["result"], fix["input"]))

    # Steps = distinct tool calls that appear in the *successful, final*
    # position across multiple traces, in the order they most commonly occur.
    ranked_calls = [call for call, _ in tool_calls.most_common()]
    steps_md = "\n".join(f"{i+1}. Run `{call[1]}` (tool: `{call[0]}`)" for i, call in enumerate(ranked_calls))

    tools_md = "\n".join(f"- {tool}" for tool in sorted({c[0] for c in tool_calls}))

    seen = set()
    fixes_md_lines = []
    for err, fix in errors_fixes:
        key = (err, fix)
        if key not in seen:
            seen.add(key)
            fixes_md_lines.append(f"- If you see `{err}` -> run `{fix}`")
    fixes_md = "\n".join(fixes_md_lines) or "- (none observed yet)"

    evidence = "\n".join(f"- {t['id']}: {t.get('fix_summary', '')}" for t in traces)

    return f"""## Steps
{steps_md}

## Tools
{tools_md}

## Known errors & fixes
{fixes_md}

## Evidence
{evidence}
"""


def draft_skill(topic: str, traces: list[dict]) -> tuple[str, str]:
    """Returns (skill_markdown_body, writer_used)."""
    body = llm_write_skill(topic, traces)
    if body:
        return body, "llm"
    return heuristic_write_skill(topic, traces), "heuristic"
