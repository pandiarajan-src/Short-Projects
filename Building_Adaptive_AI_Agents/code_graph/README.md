# code_graph/ — Code Knowledge Graph

## What is this folder for?

This folder answers one question: **"How can an AI agent find the *right* files
in a codebase, instead of just the files that happen to contain matching
keywords?"**

It builds a **Code Knowledge Graph** — a map of a Python repository where:

- **Nodes** are files (shown as squares) and functions (shown as triangles)
- **Edges** are relationships between them:
  - `import` — file A imports file B
  - `call` — function A calls function B
  - `co_edit` — file A and file B are frequently changed together in git history
  - `contains` — a file "contains" its functions (structural, not one of the 3 course relationships)

Once that graph exists, an agent can start from a rough match ("this file's
text looks like the query") and then **walk the graph** to discover related
files it never would have found from keywords alone (e.g. the file that calls
the matched function, or the file usually edited alongside it).

This is the code implementation of **Lessons 3 & 4 ("Knowledge Adaptation")**
in the course this repo accompanies — everything here is a simplified, local,
free-to-run stand-in for the same ideas taught there.

## Why does this exist?

Keyword search (`grep`, Ctrl+F, simple text matching) is blind to
*relationships*. If a bug is in `player.py` but the fix actually belongs in
`auth.py` because `player.py` calls a function defined there, keyword search
on the word "player" will never surface `auth.py`. A knowledge graph can,
because it can follow the `call` edge from one to the other.

`demo.py` (at the repo root) runs both halves of the project side-by-side so
you can see the difference for yourself, e.g.:

```
--- Query: "Where do we verify a token?" ---
Keyword search finds:       ['auth/session.py']
Graph anchor:                auth/session.py::verify  (similarity 0.412)
Graph (PageRank) finds:      ['auth/session.py', 'auth/session.py::verify', 'api/routes.py']
-> Files the graph found that keyword search MISSED: ['api/routes.py']
```

## Frameworks / libraries used

All local, free, and open-source — no API keys or cloud services required:

| Library | Used for |
|---|---|
| [`networkx`](https://networkx.org/) | Building and traversing the graph itself (`MultiDiGraph`), running PageRank |
| [`scikit-learn`](https://scikit-learn.org/) | `TfidfVectorizer` + cosine similarity — a free, local stand-in for "embedding search" (the course uses a real embedding model; here it's TF-IDF so the demo needs no API key) |
| [`matplotlib`](https://matplotlib.org/) | Drawing the graph as a PNG picture |
| `ast` (Python stdlib) | Parsing Python source code to find `import` statements and function calls, without executing any code |
| `subprocess` + `git log` | Mining git history to find files that are edited together |
| `pickle` (Python stdlib) | Saving/loading the built graph to/from `code_graph.pkl` so you don't have to rebuild it every time |

## The files, in the order they run

```
parse_imports.py   ─┐
parse_calls.py      ├──►  build_graph.py  ──►  code_graph.pkl
parse_coedits.py    ┘            │
                                  ▼
                            visualize.py  ──►  code_graph.png
                                  │
                                  ▼
                             retrieve.py  ──►  search results
```

1. **`parse_imports.py`** — Reads every `.py` file with Python's built-in
   `ast` module (Abstract Syntax Tree — a way to read code as structured data
   instead of plain text) and records every `import` / `from ... import`
   statement as a `file -> file` edge.

2. **`parse_calls.py`** — Same technique, but finds every function
   definition (`def name(...):`) and every place one function calls another,
   producing function nodes and `function -> function` "call" edges. This is
   deliberately simple name-matching, so it can have false positives on
   common names like `run()` — documented in the file's own docstring as an
   intentional trade-off (a *hint* for the agent, not perfect ground truth).

3. **`parse_coedits.py`** — Runs `git log` on the target repo and counts
   which files keep showing up together in the same commit. Files edited
   together often enough (2+ times by default) get a `co_edit` edge. This
   captures a relationship the code itself can't show you: "these two files
   are related in practice, even though neither imports or calls the other."

4. **`build_graph.py`** — The assembler. Calls all three parsers above,
   combines everything into one `networkx.MultiDiGraph`, and adds two more
   things:
   - `deduplicate()` — uses TF-IDF + cosine similarity to detect
     near-duplicate files (e.g. two copies of the same file) and drops them
     before the graph is used for search.
   - `build_vectorizer()` — builds the TF-IDF search index over every
     node's text, used later by `retrieve.py` to find a starting point for a
     query.
   - `save_graph()` / `load_graph()` — persist the graph to a `.pkl` file so
     it can be reused without rebuilding.

5. **`visualize.py`** — Draws the graph to a PNG: files as blue squares,
   functions as orange triangles, and each edge type in a different color
   (see the legend in the image itself). Purely for humans to *see* what the
   agent sees.

6. **`retrieve.py`** — The actual search logic, in two flavors:
   - `keyword_search()` — a plain baseline: does the query's words appear in
     a node's name or text? This is "what most tools do today."
   - `graph_search()` — the graph-powered approach:
     1. **Anchor selection**: use TF-IDF cosine similarity to find the one
        node most similar to the query (best-effort local stand-in for a
        real embedding-based semantic search).
     2. **Personalized PageRank**: starting from that anchor node, walk the
        graph outward and rank every other node by how "important" it is
        *relative to the anchor* — so files/functions connected to the
        anchor via import/call/co-edit edges bubble up, even if their text
        doesn't match the query at all.

7. **`cli.py`** — A command-line wrapper so you can run any of this
   yourself, without writing Python:
   ```bash
   python -m code_graph.cli build --repo sample_repo --out code_graph.pkl
   python -m code_graph.cli query  "How do I improve autoplay?" --graph code_graph.pkl
   python -m code_graph.cli plot   --graph code_graph.pkl --out code_graph.png
   ```

8. **`__init__.py`** — Empty. It just marks this folder as a Python package
   so files can do `from code_graph.build_graph import build_graph`.

## How this relates to `demo.py`

`demo.py`, at the repo root, is the single entry point that ties the whole
project together (both this graph half and the `skill_lab/` behavior-adaptation
half). Its `part2_code_knowledge_graph()` function is a short script version
of the same workflow as `cli.py`:

1. `build_graph(repo)` over `sample_repo/` (the toy repo included in this
   project, used as example code to search over)
2. `deduplicate(graph)` to clean it up
3. `save_graph(...)` and `plot_graph(...)` to persist a `.pkl` and a `.png`
4. Runs two sample questions ("How do I improve the autoplay button for
   clips?" and "Where do we verify a token?") through both `keyword_search()`
   and `graph_search()`, and prints out which files the graph found that
   keyword search missed — the whole point of this folder, in a few lines of
   output.

Run it yourself with zero setup:

```bash
pip install -r requirements.txt
python demo.py
```

Then open the generated `code_graph.png` at the repo root to see the graph
that was built, and try your own question with:

```bash
python -m code_graph.cli query "your own question here" --graph code_graph.pkl
```

## Quick glossary (for beginners)

- **Graph**: a structure of *nodes* (things) connected by *edges*
  (relationships) — think of a subway map, but nodes are files/functions and
  edges are "imports", "calls", or "usually edited together".
- **AST (Abstract Syntax Tree)**: a way for Python to read source code as
  structured data (e.g. "this is a function definition named `foo`") instead
  of as plain text — this is how `parse_imports.py` and `parse_calls.py` find
  imports and calls without actually running the code.
- **TF-IDF (Term Frequency–Inverse Document Frequency)**: a classic,
  free/local way to turn text into numbers so you can measure how similar
  two pieces of text are. Used here as a stand-in for the "embeddings"
  the full course uses, so this demo needs no API key.
- **PageRank**: the original Google search algorithm — ranks nodes in a graph
  by importance based on how they're connected. "Personalized" PageRank
  starts the ranking from one specific node (the anchor) instead of ranking
  the whole graph equally.
- **Anchor node**: the single best-matching starting point for a query,
  found via TF-IDF similarity, before the graph walk begins.
