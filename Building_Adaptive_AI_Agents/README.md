# Adaptive Agent Lab

A small, local, **fully open-source** hands-on companion to the DeepLearning.AI
course *"Building Adaptive AI Agents."* It re-implements the two token-space
adaptation ideas from the course at toy scale, so you can run and poke at
them instead of only reading about them:

1. **`skill_lab/`** — Behavior Adaptation: turn agent traces into a
   reusable, versioned "skill", with a human-approval gate (Lesson 2).
2. **`code_graph/`** — Knowledge Adaptation: build a Code Knowledge Graph
   (imports + calls + git co-edits) and retrieve with anchor + Personalized
   PageRank, compared against plain keyword search (Lessons 3-4).

No Oracle DB, no cloud account required — everything runs on SQLite,
NetworkX, and scikit-learn. An LLM is optional (see Step 2).

---

## What you need

- Python 3.10+
- ~2 minutes and one terminal

---

## Step-by-step setup

**1. Install dependencies**

```bash
cd adaptive-agent-lab
python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

**2. (Optional) Give the Skill Induction Engine a real LLM**

By default, the induction engine uses a small built-in heuristic writer so
the whole project runs with zero setup. To use a *real* LLM instead (closer
to what the course does):

```bash
cp .env.example .env
```

Then either:
- **Free & open source (recommended):** install [Ollama](https://ollama.com),
  run `ollama pull qwen2.5:7b`, and uncomment the Ollama lines in `.env`.
- **Hosted API:** uncomment the OpenAI lines in `.env` and add your key.

Either way, load the file before running anything:
```bash
export $(grep -v '^#' .env | xargs)   # macOS/Linux
```
If you skip this step entirely, everything still works — you'll just see
`writer=heuristic` in the output instead of `writer=llm`.

**3. Run the end-to-end demo**

```bash
python3 demo.py
```

This will, in order:
1. Seed 3 synthetic traces of an agent hitting the same `pytest` failure
   three days in a row (Lesson 2's Monday/Tuesday/Wednesday story).
2. Run the induction engine to draft an improved `run-the-tests` v2 skill.
3. Print the v1-vs-v2 diff (the human review step) and auto-approve it with
   a reason, promoting v2 to active in the Skill Box.
4. Build a Code Knowledge Graph over `sample_repo/` — a tiny TikTok-clone-style
   repo that mirrors the course's own `autoplay.py` / `get_feed.py` /
   `rank_clip.py` example, plus an `auth.py` / `token_utils.py` pair for the
   "where do we verify a token?" example.
5. Run the same two questions through keyword search and through the graph,
   and print which files the graph found that keyword search missed.
6. Save `code_graph.pkl` (the graph) and `code_graph.png` (a picture of it —
   squares are files, triangles are functions, edge colors match relationship
   type). Open the PNG to see your graph.

**4. Explore it yourself with the CLIs**

Skill Box:
```bash
python3 -m skill_lab.cli list                    # see every skill + version + status
python3 -m skill_lab.cli induct run-the-tests     # re-run induction (creates a new pending version)
python3 -m skill_lab.cli review run-the-tests     # see the diff without approving
python3 -m skill_lab.cli review run-the-tests --approve "looks solid"
python3 -m skill_lab.cli review run-the-tests --reject "too vague, add the exact command"
```

Code Knowledge Graph — point it at **any repo on your machine**, including
one of your own:
```bash
python3 -m code_graph.cli build --repo /path/to/some/repo --out my_graph.pkl
python3 -m code_graph.cli query "how does authentication work?" --graph my_graph.pkl
python3 -m code_graph.cli plot  --graph my_graph.pkl --out my_graph.png
```

---

## How the pieces map to the course

| Course concept | This project |
|---|---|
| Trace (conversation, tool calls, errors, fixes) | `data/sample_traces.json`, read by `skill_lab/trace_store.py` |
| Induction Engine contract | `skill_lab/induction_engine.py` (`llm_write_skill` / `heuristic_write_skill`) |
| Skill Box (versioned, human-approved) | `skill_lab/skill_box.py` + `skills_box/*.md` |
| Human review gate (approve/reject with reason) | `skill_lab/cli.py review` |
| Import / call / co_edit relationships | `code_graph/parse_imports.py`, `parse_calls.py`, `parse_coedits.py` |
| Duplicate-node audit | `code_graph.build_graph.deduplicate()` |
| Anchor via semantic similarity | `code_graph/retrieve.py: find_anchor()` (TF-IDF, see note below) |
| Personalized PageRank traversal | `code_graph/retrieve.py: personalized_pagerank()` |
| Keyword/regex baseline for comparison | `code_graph/retrieve.py: keyword_search()` |
| Closing the loop on new commits | Re-run `code_graph.cli build` — cost stays low since it's a full rebuild over a small repo; for a real repo, see "Where to go next" |

**Note on "semantic similarity":** the course uses real embeddings; this
project uses TF-IDF (word-overlap statistics) so it needs no internet and no
GPU. It works well for the demo queries but is genuinely *lexical*, not
semantic — e.g. it can confuse the English word "issue" (as in "a caching
issue") with a function literally named `issue_token`. That failure mode is
itself a nice illustration of why the course cares about *real* semantic
anchoring. See "Where to go next" below for a one-line upgrade.

---

## Where to go next (ideas to extend this yourself)

- **Swap TF-IDF for real embeddings.** Install `sentence-transformers`
  (open source) and replace `build_vectorizer()` in `code_graph/build_graph.py`
  with `SentenceTransformer("all-MiniLM-L6-v2").encode(texts)`. Compare anchor
  quality before/after on a few tricky queries.
- **Point the graph at a real repo of yours.** Run `code_graph.cli build`
  against a project with real git history and see what the co-edit edges
  surface — often surprising, undocumented couplings between files.
- **Wire the Skill Box into an actual coding agent.** If you use Claude
  Code, Cursor, or a custom LangGraph/LangChain agent, have it read the
  active skill's markdown from `skills_box/` as a system-prompt addendum
  before it starts a matching task, and write a trace to
  `data/` (or a new SQLite row) after each run. That closes the real loop.
- **Add a 4th relationship type.** The course's 3 edges (import/call/co_edit)
  aren't exhaustive — try adding a "shared test file" edge (files covered by
  the same test) and see if it changes retrieval quality.
- **Measure it like the course does.** Pick 5-10 real questions about a repo
  you know well, record whether keyword search vs. the graph finds the file
  you'd actually edit, and compute your own "win rate" — that's exactly the
  experiment described in Lesson 3/4.

---

## Project layout

```
adaptive-agent-lab/
├── README.md
├── requirements.txt
├── .env.example
├── demo.py                     # run this first
├── data/
│   └── sample_traces.json      # 3 synthetic agent traces (Lesson 2's example)
├── skills_box/
│   └── run-the-tests_v1.md     # hand-written v1 skill (starting point)
├── skill_lab/
│   ├── trace_store.py          # SQLite trace storage
│   ├── induction_engine.py     # LLM writer + offline heuristic writer
│   ├── skill_box.py            # versioning + approve/reject
│   └── cli.py
├── sample_repo/                # tiny repo (with real git history) to build a graph over
│   ├── autoplay.py / get_feed.py / rank_clip.py / cache_utils.py
│   └── auth.py / token_utils.py
└── code_graph/
    ├── parse_imports.py / parse_calls.py / parse_coedits.py
    ├── build_graph.py          # assemble + dedupe
    ├── retrieve.py             # anchor + PageRank + keyword baseline
    ├── visualize.py            # PNG plot
    └── cli.py
```
