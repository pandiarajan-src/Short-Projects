# sample_repo/

This folder is **not part of the adaptive-agent-lab application**. It's a
tiny, fake codebase that exists purely so the rest of the project — the
Code Knowledge Graph in `code_graph/` — has something realistic to analyze.
Think of it as a "practice patient" for the graph-building tool: small
enough to read in five minutes, but shaped like a real app so imports,
function calls, and git history all look genuine.

It pretends to be two features of a short-video app (something like
TikTok's autoplay-next-clip button) plus a login/auth system:

```
sample_repo/
├── auth.py          feature: log a user in, check their token
├── token_utils.py   helper: issue and verify fake tokens
├── autoplay.py      feature: "what clip plays next?" button
├── get_feed.py      helper: fetch candidate clips for a user
├── rank_clip.py      helper: score and sort clips
└── cache_utils.py   helper: cache clip scores so we don't recompute them
```

There is **no framework** here on purpose — no Flask, Django, FastAPI,
React, database, or real cryptography. It's plain Python standard library
(`time`, dicts, lists). Keeping it framework-free means:

- it's easy for a beginner to read top to bottom in one sitting,
- it has no dependencies of its own to install,
- the Code Knowledge Graph tool can parse its imports/calls without
  worrying about framework "magic" (decorators, dependency injection,
  ORMs) that would complicate the demo.

## The two features, script by script

### Auth: "log in, then prove who you are"

```
auth.py            ──imports──▶  token_utils.py
  login()                          issue_token()
  require_auth()                   verify_token()
```

- **`token_utils.py`** — the only place that knows about tokens. It hands
  out a fake token string like `tok_42_1734000000` and remembers which
  tokens are valid in an in-memory dict (`_FAKE_VALID_TOKENS`). This
  stands in for what a real app would do with JWTs or a session store.
- **`auth.py`** — the two entry points a web framework would call:
  - `login(user_id, password)` — rejects an empty password, otherwise
    asks `token_utils` to issue a token.
  - `require_auth(token)` — asks `token_utils` to verify a token; raises
    `PermissionError` if it's missing/expired, otherwise returns the
    `user_id`. This is the function a route would call to guard a
    protected endpoint.

### Autoplay: "what clip should play next?"

```
autoplay.py  ──imports──▶  get_feed.py  ──imports──▶  rank_clip.py ──imports──▶  cache_utils.py
                                                          (also used
                                                     directly by autoplay.py)
```

- **`cache_utils.py`** — a dead-simple in-memory cache (`_CACHE` dict) so a
  clip's score isn't recomputed every time it's looked at.
- **`rank_clip.py`** — `score_clip()` gives each clip a placeholder score
  (checking the cache first, falling back to a fake formula); `rank_clips()`
  sorts a list of clip ids by that score, best first.
- **`get_feed.py`** — `fetch_candidate_clips()` pretends to hit a database
  and returns 20 clip ids for a user; `get_feed()` runs those candidates
  through `rank_clips()` to produce the final ordered feed.
- **`autoplay.py`** — the button handler: `press_autoplay(user_id,
  current_clip_id)` gets the user's feed, finds the clip after the one
  currently playing, and returns the next clip's id.

**Auth and autoplay never call each other.** They're deliberately two
separate, unconnected feature areas — that separation is what lets the demo
show a graph with two distinct clusters instead of one blob.

## Why this folder has its own `.git` history

Unlike the rest of the project, `sample_repo/` is a real (nested) git
repository with its own commit history — `git log` inside this folder shows
commits like "Add clip ranking with score cache" and "Tune autoplay ranking
behavior." That history is what `code_graph/parse_coedits.py` reads: it
looks at which files were committed together and draws a "co-edit" edge
between them (e.g. `autoplay.py`, `get_feed.py`, and `rank_clip.py` were all
touched in the same commit). This is one of the three relationship types
the knowledge graph models — the other two being `import` (which module
imports which) and `call` (which function calls which).

## How this relates to `demo.py`

`demo.py` at the project root is the single script that ties everything
together — run `python demo.py` and it does two things in sequence. **Part
2 of that script is entirely about this folder:**

```python
repo = ROOT / "sample_repo"
graph = build_graph(repo)              # parse imports/calls/co-edits into a graph
graph, dropped = deduplicate(graph)    # drop near-duplicate files, if any
...
questions = [
    "How do I improve the autoplay button for clips?",
    "Where do we verify a token?",
]
```

For each question, `demo.py` runs two searches over the graph built from
this folder and compares them:

1. **Keyword search** (`code_graph/retrieve.py: keyword_search`) — a plain
   substring match against file names and contents. It's fast but "blind":
   it only finds files that literally contain the query's words.
2. **Graph search** (`code_graph/retrieve.py: graph_search`) — finds the
   file most *semantically* related to the question (the "anchor"), then
   walks outward through the import/call/co-edit edges using Personalized
   PageRank to surface related files — including ones that don't share any
   keywords with the question at all.

The point of the demo: for "Where do we verify a token?", keyword search
can find `token_utils.py` (it literally contains `verify_token`), but graph
search can *also* surface `auth.py` — the file that actually calls
`verify_token()` — because of the `import`/`call` edge between them, not
because of shared words. That's the concrete, beginner-friendly proof that
**relationships between files can find things keyword matching misses.**

## Workflow summary

```
you run:  python demo.py
              │
              ▼
   demo.py Part 2 (code_graph)
              │
              ├─ build_graph(sample_repo/)   ← reads every .py file in this folder
              │     ├─ parse_imports.py      (auth.py -> token_utils.py, etc.)
              │     ├─ parse_calls.py        (require_auth() -> verify_token(), etc.)
              │     └─ parse_coedits.py      (reads THIS folder's git log)
              │
              ├─ keyword_search(graph, question)   ← naive text match
              ├─ graph_search(graph, question)     ← anchor + PageRank
              │
              └─ saves code_graph.pkl + code_graph.png (a picture of the graph)
```

You never need to run anything inside `sample_repo/` directly — it's pure
input data. To explore it yourself instead of via `demo.py`, see the root
[README.md](../README.md) for the `code_graph.cli` commands, e.g.:

```bash
python3 -m code_graph.cli query "how does authentication work?" --graph code_graph.pkl
```

## Quick reference

| Question | Answer |
|---|---|
| Is this real production code? | No — every score, cache, and token is a fake placeholder. |
| Does it use any frameworks? | No — plain Python standard library only. |
| Why does it exist? | To give `code_graph/` a small, realistic repo to build a knowledge graph over. |
| Do `auth.py` and `autoplay.py` interact? | No — they're intentionally separate feature clusters. |
| Where is it used? | `demo.py`'s `part2_code_knowledge_graph()` function. |
| Should I edit these files? | Only if you want to see how the graph/diff changes — see "Where to go next" in the root README. |
