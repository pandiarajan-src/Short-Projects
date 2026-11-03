# Running the six Claude Agent SDK assignments

Each agent is a single CLI script that sits next to its sample inputs in `agent-lab-samples/<nn>-<name>/`.

## Setup

```bash
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
# or: python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

The SDK drives the Claude Code CLI, so you need `claude` installed and logged in (or `ANTHROPIC_API_KEY` set).
Every script accepts `--model <id>`; if you leave it out, the SDK's default model is used. Every run prints its cost.

## Commands (run from inside each folder)

| # | Agent | Command | Output |
|---|---|---|---|
| 1 | TidyBot | `python tidybot.py sample-downloads.zip [--dry-run]` | files moved into category folders in `work/sample-downloads/` |
| 2 | SpendSense | `python spendsense.py statement-sample.csv [statement-sample-2.csv]` | `spendsense-report.md` |
| 3 | MinuteMan | `python minuteman.py standup-transcript.txt` | `standup-transcript-actions.md` |
| 4 | SnapNamer | `python snapnamer.py sample-images.zip [--dry-run]` | images renamed in `work/sample-images/` |
| 5 | DigestBot | `python digestbot.py "vertical farming"` or `--topics-file topics.txt [--all]` | `digests/digest-<topic>-<date>.md` |
| 6 | StudyCards | `python studycards.py notes-photosynthesis.md [--cards 15]` | `<notes>-cards.csv` (Anki/Quizlet) and `<notes>-cards.md` |

TidyBot and SnapNamer unzip a **fresh copy** into `work/` on every run, so the original zip is never changed.

## How they are built

Every script follows the same pattern: `query()` with a system prompt, plus a small in-process MCP server
(`@tool` + `create_sdk_mcp_server`). The custom tools are the only way the agent can act, and they enforce the rules:

| Agent | Built-in tools | Custom tools and what they enforce |
|---|---|---|
| TidyBot | none | `list_folder`, `peek_file` (checks magic bytes, e.g. a PDF with no extension), `move_file` (never overwrites, adds a ` (1)` suffix, handles `.tar.gz`), `skip_file` |
| SpendSense | none | `categorise` (credit vs debit categories, `Other` needs a reason); `summarise` / `compare_months` do the arithmetic in Python so totals are exact |
| MinuteMan | none | `save_action_items` (owner must be an attendee, timestamp must exist, ISO due dates, no duplicates, and it records what was left out) |
| SnapNamer | none | `view_image` sends the image to Claude; `rename_image` checks kebab-case, keeps the original extension (`.PNG`), and refuses non-images and name clashes |
| DigestBot | WebSearch, WebFetch | `check_link`; `save_digest` checks that every link loads and rejects duplicate stories and summaries that just repeat the headline |
| StudyCards | none | `save_cards` rejects duplicate cards, citations inside a recap/review section, and headings or blank lines as sources |

`permission_mode="dontAsk"` plus an explicit `allowed_tools` list means the agent cannot use anything else
(no Bash, no file writes outside the tools).
