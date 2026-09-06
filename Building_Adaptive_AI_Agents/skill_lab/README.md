# Skill Lab

A toy but functionally complete implementation of **Behavior Adaptation**:
turning an agent's raw execution history into a versioned, human-approved
"skill" that future agent runs can follow. It is the code behind Lesson 2 of
the *Adaptive AI Agents* course, re-implemented at local/offline scale.

Companion module: [`skills_box/`](../skills_box/) (skill markdown files on
disk) and [`data/`](../data/) (sample trace input). See the
[project-level README](../README.md) for the end-to-end demo and how this
module relates to `code_graph/` (Knowledge Adaptation).

---

## 1. High-level overview

An agent that solves the same recurring task (e.g. "run the tests") tends to
rediscover the same fix every time, because nothing persists between runs.
Skill Lab closes that loop with a four-stage pipeline:

```
 traces (what happened)        skill_box (what's true now)
 ┌─────────────────┐   induct   ┌──────────────────┐   review   ┌──────────────────┐
 │  trace_store.py  │ ────────► │ induction_engine  │ ────────► │   skill_box.py    │
 │  (SQLite, one    │           │  (LLM or heuristic│           │ (SQLite + .md,    │
 │  row per episode)│           │   writer drafts   │           │  versioned,       │
 └─────────────────┘           │   a skill.md)     │           │  active/pending/  │
                                └──────────────────┘           │  rejected)         │
                                                                 └──────────────────┘
                                                                        ▲
                                                                        │ human approves
                                                                        │ or rejects with
                                                                        │ a reason
                                                                cli.py (entry point)
```

| File | Role |
|---|---|
| [`trace_store.py`](trace_store.py) | Persists agent traces (tool calls, reasoning notes, outcomes) as JSON blobs in SQLite, keyed by topic. |
| [`induction_engine.py`](induction_engine.py) | Reads all traces for one topic and drafts an improved `skill.md` body — either via a real LLM call or a deterministic offline heuristic. |
| [`skill_box.py`](skill_box.py) | The versioned skill store: proposes new pending versions, diffs active-vs-pending, and applies human approve/reject decisions. |
| [`cli.py`](cli.py) | Command-line entry point (`seed`, `induct`, `review`, `list`) tying the three modules together. |

The result: a skill starts as a hand-written v1 (`skills_box/run-the-tests_v1.md`),
gets challenged by real failure traces, and evolves into a v2 (or v3, …) only
after a human reviews the diff and approves it — never silently.

---

## 2. What it does

1. **Ingests traces.** `trace_store.load_sample_traces()` reads
   `data/sample_traces.json` — a list of episodes, each a `topic`, a `task`
   description, an ordered list of `steps` (tool calls with inputs/results, or
   free-text reasoning notes), an `outcome`, and a one-line `fix_summary`.
   These are stored as one SQLite row per trace (`agent_lab.db`, table
   `traces`), with the step list kept as a JSON blob so the schema doesn't
   need to anticipate every possible action shape.

2. **Seeds a starting skill.** `skill_box.seed_v1()` registers the
   hand-authored `skills_box/run-the-tests_v1.md` as the `active` version —
   the naive baseline: "run pytest, report pass/fail." Nothing adaptive yet.

3. **Induces an improved skill from evidence.** `cli induct <topic>` pulls
   every trace for that topic and calls `draft_skill()`, which:
   - Tries `llm_write_skill()` first — sends all traces to an OpenAI-compatible
     endpoint (real OpenAI, or a free local Ollama model) with a prompt that
     asks it to find the repeated failure pattern, the fix that worked, and
     write it up as `## Steps` / `## Tools` / `## Known errors & fixes`.
   - Falls back to `heuristic_write_skill()` if no LLM is configured or the
     call fails — a zero-dependency stand-in that counts which tool calls
     recur across traces, ranks them by frequency, and pattern-matches
     "error result → next tool call" pairs into an error→fix table. This
     keeps the whole project runnable with no API key and no internet.
   - Either way, the result is proposed into the Skill Box as a new
     `pending` version (`skill_box.propose()`), written both to SQLite and to
     a new `skills_box/<name>_v<n>.md` file with YAML-ish frontmatter.

4. **Gates the change on human review.** `cli review <topic>` shows
   `skill_box.diff_active_vs_pending()` — the current active body side-by-side
   with the proposed one. A human then runs the same command with
   `--approve "reason"` (promotes the pending version to active, demotes the
   old active to `superseded`, and records the reason) or `--reject "reason"`
   (marks it `rejected` and leaves the old version active). No proposal ever
   becomes active without an explicit, reasoned human action.

5. **Tracks full history.** `cli list` prints every skill/version/status/writer
   ever created, so you can see the whole lineage — active, pending,
   rejected, and superseded — not just the current state.

---

## 3. Why it does this

- **Traces are cheap, memory is not.** An agent re-solving "run the tests"
  from scratch every day wastes tokens and time rediscovering
  `PYTHONPATH=src` (see `data/sample_traces.json` — that exact scenario, plus
  a later trace that also needs `pip install -e '.[test]'` for missing
  fixtures). Recording *what actually happened* — including the dead ends —
  is the raw material for not repeating them.
- **Distillation, not accumulation.** Dumping every trace into a prompt
  forever doesn't scale. The Induction Engine's job is to compress N episodes
  into one short, generalized procedure — separating what's *reusable*
  (the fix) from what's *incidental* (the exact error text, timestamps).
- **A human gate exists because generalization can be wrong.** An LLM (or the
  heuristic) might overfit to 3 traces, miss a step that only showed up
  once, or hallucinate a plausible-sounding but false pattern. Requiring
  `--approve "reason"` / `--reject "reason"` keeps a person accountable for
  what actually enters the agent's operating procedure, and the recorded
  reason is itself evidence for later auditing ("why did we approve this?").
- **Two writers, on purpose.** `llm_write_skill` shows what the course
  actually intends (real semantic distillation of messy traces); the
  deterministic `heuristic_write_skill` exists so the whole repo runs with
  zero setup and zero cost — and, as a side effect, makes explicit exactly
  what "distillation" a *non*-LLM approach can and can't do (frequency
  counting and adjacent-step pattern matching, nothing more).
- **Versioning instead of overwriting.** Keeping `active` / `pending` /
  `rejected` / `superseded` rather than mutating one file in place preserves
  a paper trail: you can always see what v1 said, why v2 was rejected once
  before an eventual v3 was approved, and who (or what writer) proposed each.

---

## 4. How it does it

- **Storage:** plain SQLite (`agent_lab.db`) with two tables — `traces`
  (append-only-ish, keyed by trace id) and `skills` (keyed by
  `(name, version)`, primary key enforces no duplicate versions). No ORM, no
  migrations framework — schema is a single `CREATE TABLE IF NOT EXISTS`
  string executed on every connection, which is fine at this scale and keeps
  the whole module dependency-free beyond the standard library.
- **Skill files are the source of truth for *content*, SQLite for *state*.**
  Every proposed version is written to `skills_box/<name>_v<n>.md` with a
  small frontmatter block (`name`, `version`, `status`, `writer`) *and*
  mirrored into the `skills` table; `approve()` flips `status` in both places
  (string-replace in the file, `UPDATE` in the table) so the on-disk file and
  the DB never disagree about which version is active.
- **The induction prompt is a strict contract.** `PROMPT_TEMPLATE` in
  `induction_engine.py` fixes the output shape (`## Steps`, `## Tools`,
  `## Known errors & fixes`) so a downstream agent can parse or at least
  reliably skim the result regardless of which writer produced it.
- **Heuristic writer is intentionally simple and explainable.** It uses a
  `Counter` over `(tool, input)` pairs to rank steps by recurrence, and a
  linear scan pairing any step whose result contains `"error"` or
  `"notfound"` with the very next tool call as the "fix." This is a
  precision-over-recall design: it will miss subtler patterns, but it never
  fabricates a step that didn't literally appear in a trace.
- **The CLI is a thin adapter.** `cli.py` has no logic of its own beyond
  argument parsing and wiring `trace_store` → `induction_engine` → `skill_box`
  together — every function it calls is independently testable and usable
  from other Python code (e.g. a real agent's post-run hook).
- **Graceful LLM fallback.** `llm_write_skill()` returns `None` (not an
  exception) on missing config, missing `openai` package, or any request
  failure, logging a one-line notice; `draft_skill()` treats `None` as "use
  the heuristic," so a flaky network or an unset `.env` never breaks the
  pipeline — see [`.env.example`](../.env.example) for the Ollama/OpenAI
  setup.

---

## 5. How this could be improved for a real Skill Lab / Induction Engine

This project optimizes for "runs offline in 2 minutes with zero setup." A
production version would need to address what that trades away:

**Trace capture**
- **Automatic capture, not hand-written JSON.** Real traces should come from
  a logging hook inside the actual agent runtime (tool-call middleware,
  OpenTelemetry spans, etc.), not a static fixture file — capture every run,
  not just curated examples.
- **Richer step schema.** Today a step is `action` + free-text `input`/
  `result`. Real traces benefit from structured fields (exit codes, stdout/
  stderr separately, timing, cost/tokens used) so induction can reason about
  more than string matching.
- **PII/secret scrubbing before storage.** Traces of real work will contain
  credentials, file paths, customer data — redact or encrypt before
  persisting, and consider retention/expiry policies.

**Induction quality**
- **Replace the heuristic writer's string matching** (`"error" in result`)
  with structured success/failure signals (exit code, exception type) and a
  real clustering step (group traces by *root cause*, not just topic string)
  before drafting — today, two unrelated failures under the same topic get
  blended into one skill.
- **Multi-topic / cross-skill induction.** Right now induction is scoped to
  one exact `topic` string. A real engine should detect when traces tagged
  with different topics actually share a fix (e.g. "run-the-tests" and
  "run-the-linter" both need `PYTHONPATH=src`) and propose a shared
  sub-skill instead of duplicating it.
- **Confidence / evidence scoring.** Attach a confidence score to each
  proposed step based on how many independent traces support it, and surface
  that in the review diff — "supported by 5/5 traces" vs. "supported by 1/5"
  changes how a reviewer should treat it.
- **Regression testing a proposed skill before it's even shown to a human.**
  Replay it against held-out traces (or a sandboxed live run) and attach
  pass/fail evidence to the proposal, so review isn't purely a read of prose.

**Skill Box / review gate**
- **Concurrency and multi-writer safety.** SQLite with no locking discipline
  works for a single local user; a real deployment needs either a real
  database with transactions, or an explicit optimistic-locking / queueing
  scheme so two induction runs (or two reviewers) can't race.
- **Structured diffs, not text diffs.** `diff_active_vs_pending()` returns
  raw markdown side-by-side; a real UI should diff at the section level
  (Steps/Tools/Errors) and highlight exactly which step changed.
- **Richer review states.** Add "needs changes" / "request revision" (send
  back to the induction engine with reviewer notes) instead of only binary
  approve/reject, and support multiple reviewers / required approvals for
  higher-stakes skills.
- **Rollback and canary rollout.** Let an approved version be demoted back
  to `superseded` if it causes regressions in production, and support
  rolling a new version out to a subset of agent runs before full promotion.

**Closing the loop with a real agent**
- **Wire skill retrieval into the agent's system prompt.** Before a matching
  task starts, fetch `skill_box.get_active(topic)` and inject its body as a
  system-prompt addendum (the project README already flags this as the
  natural next step) — right now nothing actually *consumes* an active skill
  at run time.
- **Auto-detect topic from the task**, rather than requiring an exact
  string match — embedding-based topic clustering (same upgrade path as
  swapping TF-IDF for real embeddings in `code_graph/`) so traces from
  slightly differently-phrased tasks still count as evidence for the same
  skill.
- **Feed outcomes back automatically.** After an agent run that used an
  active skill, write a new trace recording whether the skill worked
  as-is — turning this into a continuously closing loop instead of a
  manually triggered `induct` command.
