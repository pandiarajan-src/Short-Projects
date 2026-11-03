#!/usr/bin/env python3
"""SpendSense - a Claude Agent SDK agent that categorises a bank statement and writes a spending report.

Claude does the judgement (which category is each transaction?). Python does the arithmetic,
so the totals in the report are always exact. Custom tools:
  read_statement   - rows of a statement CSV (date, description, amount)
  categorise       - assign categories to rows (validated: credits vs debits, 'Other' needs a reason)
  summarise        - exact totals per category, income, refunds, largest debit
  compare_months   - category-by-category change between two statements (stretch goal)
  save_report      - write the final Markdown report

Usage:
  python spendsense.py statement-sample.csv
  python spendsense.py statement-sample.csv statement-sample-2.csv   # month-on-month comparison
"""

import argparse
import asyncio
import csv
import sys
from collections import defaultdict
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

SPEND_CATEGORIES = [
    "Rent", "Food & Dining", "Groceries", "Transport", "Shopping", "Bills & Utilities",
    "Entertainment", "Health", "Travel", "Other",
]
CREDIT_CATEGORIES = ["Income", "Refund", "Other Credit"]
ALL_CATEGORIES = SPEND_CATEGORIES + CREDIT_CATEGORIES


def text(msg: str, error: bool = False) -> dict:
    result = {"content": [{"type": "text", "text": msg}]}
    if error:
        result["is_error"] = True
    return result


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return [
            {"id": i, "date": r["date"], "description": r["description"].strip(), "amount": float(r["amount"])}
            for i, r in enumerate(csv.DictReader(f), start=1)
        ]


def rupees(x: float) -> str:
    return f"Rs {x:,.0f}"


def build_tools(statements: dict[str, list[dict]], out_path: Path):
    # labels[file][row_id] = (category, reason)
    labels: dict[str, dict[int, tuple[str, str]]] = {name: {} for name in statements}

    def unknown(name: str):
        return text(f"Unknown statement {name!r}. Available: {list(statements)}", error=True)

    def compute(name: str) -> dict:
        rows = statements[name]
        spend, credits = defaultdict(float), defaultdict(float)
        for r in rows:
            cat = labels[name].get(r["id"], ("UNCATEGORISED", ""))[0]
            (spend if r["amount"] < 0 else credits)[cat] += abs(r["amount"])
        debits = [r for r in rows if r["amount"] < 0]
        largest = max(debits, key=lambda r: -r["amount"]) if debits else None
        return {"spend": dict(spend), "credits": dict(credits), "largest": largest,
                "missing": [r["id"] for r in rows if r["id"] not in labels[name]]}

    @tool("read_statement", "Read every row of one statement. Negative amount = money spent, "
          "positive = money received.", {"statement": str})
    async def read_statement(args):
        name = args["statement"]
        if name not in statements:
            return unknown(name)
        lines = [f"{r['id']}|{r['date']}|{r['description']}|{r['amount']:+.0f}" for r in statements[name]]
        return text("id|date|description|amount\n" + "\n".join(lines))

    @tool("categorise",
          f"Assign categories to rows. Debit categories: {SPEND_CATEGORIES}. Credit categories: "
          f"{CREDIT_CATEGORIES}. 'Other' needs a reason. Can be called several times.",
          {
              "type": "object",
              "properties": {
                  "statement": {"type": "string"},
                  "items": {
                      "type": "array",
                      "items": {
                          "type": "object",
                          "properties": {
                              "id": {"type": "integer"},
                              "category": {"type": "string", "enum": ALL_CATEGORIES},
                              "reason": {"type": "string"},
                          },
                          "required": ["id", "category"],
                      },
                  },
              },
              "required": ["statement", "items"],
          })
    async def categorise(args):
        name = args["statement"]
        if name not in statements:
            return unknown(name)
        by_id = {r["id"]: r for r in statements[name]}
        problems, ok = [], 0
        for item in args["items"]:
            row, cat, reason = by_id.get(item["id"]), item["category"], item.get("reason", "").strip()
            if row is None:
                problems.append(f"row {item['id']}: no such row")
            elif row["amount"] > 0 and cat not in CREDIT_CATEGORIES:
                problems.append(f"row {row['id']} ({row['description']}): money received, use one of {CREDIT_CATEGORIES}")
            elif row["amount"] < 0 and cat not in SPEND_CATEGORIES:
                problems.append(f"row {row['id']} ({row['description']}): money spent, use one of {SPEND_CATEGORIES}")
            elif cat in ("Other", "Other Credit") and not reason:
                problems.append(f"row {row['id']} ({row['description']}): 'Other' needs a reason")
            else:
                labels[name][row["id"]] = (cat, reason)
                ok += 1
        missing = [r["id"] for r in statements[name] if r["id"] not in labels[name]]
        msg = f"Saved {ok} labels. {len(missing)} rows still uncategorised"
        msg += f": {missing}" if missing else "."
        if problems:
            msg += "\nRejected:\n- " + "\n- ".join(problems)
        return text(msg, error=bool(problems))

    @tool("summarise", "Exact totals for one statement. Spending only counts debits; refunds and "
          "income are reported separately.", {"statement": str})
    async def summarise(args):
        name = args["statement"]
        if name not in statements:
            return unknown(name)
        s = compute(name)
        if s["missing"]:
            return text(f"Categorise these rows first: {s['missing']}", error=True)
        total_spend = sum(s["spend"].values())
        lines = [f"Statement: {name}", f"Total spent: {rupees(total_spend)}",
                 f"Total received: {rupees(sum(s['credits'].values()))}", "Spending by category:"]
        for cat, amt in sorted(s["spend"].items(), key=lambda kv: -kv[1]):
            lines.append(f"- {cat}: {rupees(amt)} ({amt / total_spend:.1%})")
        lines.append("Money received by category:")
        lines += [f"- {cat}: {rupees(amt)}" for cat, amt in s["credits"].items()]
        if s["largest"]:
            r = s["largest"]
            lines.append(f"Largest single debit: {r['description']} on {r['date']}, {rupees(-r['amount'])}")
        others = [(r, labels[name][r["id"]][1]) for r in statements[name]
                  if labels[name][r["id"]][0] in ("Other", "Other Credit")]
        lines.append("Rows in Other:")
        lines += [f"- {r['date']} {r['description']} {rupees(r['amount'])}: {why}" for r, why in others]
        return text("\n".join(lines))

    @tool("compare_months", "Category-by-category spending change from statement a to statement b.",
          {"a": str, "b": str})
    async def compare_months(args):
        if args["a"] not in statements or args["b"] not in statements:
            return unknown(f"{args['a']} / {args['b']}")
        sa, sb = compute(args["a"]), compute(args["b"])
        if sa["missing"] or sb["missing"]:
            return text("Categorise both statements fully first.", error=True)
        lines = [f"Category | {args['a']} | {args['b']} | change"]
        for cat in sorted(set(sa["spend"]) | set(sb["spend"])):
            x, y = sa["spend"].get(cat, 0), sb["spend"].get(cat, 0)
            lines.append(f"{cat} | {rupees(x)} | {rupees(y)} | {y - x:+,.0f}")
        tx, ty = sum(sa["spend"].values()), sum(sb["spend"].values())
        lines.append(f"TOTAL | {rupees(tx)} | {rupees(ty)} | {ty - tx:+,.0f}")
        return text("\n".join(lines))

    @tool("save_report", "Save the final Markdown report. Use only numbers returned by summarise / "
          "compare_months.", {"markdown": str})
    async def save_report(args):
        out_path.write_text(args["markdown"], encoding="utf-8")
        return text(f"Report saved to {out_path}")

    return [read_statement, categorise, summarise, compare_months, save_report]


SYSTEM_PROMPT = """You are SpendSense, a careful personal-finance assistant for Indian bank statements.
Amounts are in Indian rupees. Negative = money spent, positive = money received.

Steps:
1. read_statement for each statement.
2. categorise EVERY row. Be honest about uncertainty: if a description does not tell you what the
   money was for (a UPI payment to a person, a bare POS terminal code, a NEFT reference, an ATM
   cash withdrawal) put it in 'Other' with a short reason - do not guess.
   Refunds are credits ('Refund'), never negative spending. Salary is 'Income'.
3. summarise each statement (and compare_months if there are two, oldest first).
4. save_report with a short, friendly Markdown report: headline totals, a category table,
   the largest expense, the 'Other' rows with reasons, refunds/income shown separately,
   and 2-3 practical observations. Every number must come from the tool output.
"""


async def main() -> int:
    ap = argparse.ArgumentParser(description="SpendSense - categorise a bank statement with Claude.")
    ap.add_argument("csv", nargs="+", type=Path, help="one statement CSV, or two to compare months")
    ap.add_argument("--out", type=Path, help="report path (default: spendsense-report.md next to the first CSV)")
    ap.add_argument("--model", default=None, help="Claude model to use (default: SDK default)")
    args = ap.parse_args()

    statements = {p.name: load_csv(p) for p in args.csv}
    out = args.out or args.csv[0].with_name("spendsense-report.md")
    server = create_sdk_mcp_server("spend", tools=build_tools(statements, out))
    names = ("read_statement", "categorise", "summarise", "compare_months", "save_report")
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"spend": server},
        tools=[],
        allowed_tools=[f"mcp__spend__{n}" for n in names],
        permission_mode="dontAsk",
        max_turns=40,
        model=args.model,
    )

    out.unlink(missing_ok=True)  # never show a report from an earlier run
    prompt = f"Analyse these statements: {', '.join(statements)}."
    exit_code = 1
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                elif isinstance(block, ToolUseBlock):
                    shown = {k: v for k, v in block.input.items() if k not in ("items", "markdown")}
                    print(f"  -> {block.name.split('__')[-1]} {shown}")
        elif isinstance(msg, ResultMessage):
            if out.exists():
                print(f"\n=== {out} ===\n{out.read_text(encoding='utf-8')}")
            print(f"Turns: {msg.num_turns}  Cost: ${msg.total_cost_usd or 0:.4f}")
            exit_code = 1 if msg.is_error else 0
    return exit_code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
