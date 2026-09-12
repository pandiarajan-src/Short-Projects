# Newsletter Distiller

A terminal tool that takes a newsletter URL and produces a clean, self-contained Markdown digest: the substantive article text plus the genuine concept/chart images, with ads, navigation, and other boilerplate stripped out. It works with whichever LLM backend you point it at — Anthropic, a local Ollama model, DeepSeek, Kimi/Moonshot, or any other OpenAI-compatible API.

> **Status:** Implemented and covered by an automated test suite (`uv run pytest`). The full requirements, technical design, and implementation checklist behind it live in [`openspec/changes/add-newsletter-distiller-cli/`](openspec/changes/add-newsletter-distiller-cli/).

## What it does

```
you run:  newsletter-distiller "<newsletter-url>"

               |
               v
   1. Fetch the page, strip nav/footer/social icons/tracking pixels
   2. Extract the article text and candidate images (with alt text + context)
   3. Send the text + prompts + image metadata to your chosen LLM
   4. The LLM decides which images are real charts/diagrams vs. ads,
      and writes the digest in Markdown
   5. Tool resolves image references to local files and writes the output

               |
               v
   output/<slug>/<slug>.md
   output/<slug>/assets/*.png
```

The tool never guesses which provider to use, never invents a missing prompt, and never leaves a broken image link in the output — every failure mode is reported clearly with a non-zero exit code rather than silently producing a bad result. See the [specs](openspec/changes/add-newsletter-distiller-cli/specs/) for the full list of guarantees.

## Requirements

- Python 3.12+ (see `pyproject.toml` for the exact minimum)
- [uv](https://docs.astral.sh/uv/) — this project uses `uv` exclusively for environment setup, dependency management, and running the CLI/tests. There is no `pip`/`requirements.txt` workflow.
- An API key for at least one supported provider (see [Configuration](#configuration))

## Installation

```bash
git clone <this-repo-url>
cd NewsLetter_Distiller
uv sync
```

`uv sync` creates a project-local virtual environment and installs exact versions from `uv.lock`. You never need to create or activate a `venv` by hand, and you never call `pip` directly.

## Configuration

The tool reads all secrets from environment variables (optionally via a local `.env` file at the repo root — copy [`.env.example`](.env.example) to `.env` and fill it in). **API keys are never passed as command-line flags**, so they never end up in your shell history or visible to other processes.

### 1. Choose a provider

| Setting | Purpose |
|---|---|
| `NEWSLETTER_DISTILLER_PROVIDER` | `anthropic` or `openai-compatible`. Required — there is no silent default. |
| `NEWSLETTER_DISTILLER_MODEL` | The model name to use with the chosen provider. |

### 2. Provider-specific settings

**Anthropic** (native API):

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key. |

**OpenAI-compatible** (covers Ollama, DeepSeek, Kimi/Moonshot, and other providers exposing an OpenAI-style `/chat/completions` endpoint):

| Variable | Purpose |
|---|---|
| `NEWSLETTER_DISTILLER_API_KEY` | API key for the endpoint (a local Ollama server may not require a real key, but the variable must still be set). |
| `NEWSLETTER_DISTILLER_BASE_URL` | Base URL of the endpoint, e.g. `http://localhost:11434/v1` for Ollama, `https://api.deepseek.com` for DeepSeek, `https://api.moonshot.cn/v1` for Kimi. |

### 3. Vision vs. text-only models

Whether the tool sends raw image bytes to the model (so it can visually double-check a chart vs. an ad) or relies only on alt-text/context depends on whether the configured model is known to support image input. If you're using a model the built-in list doesn't recognize, set:

| Variable | Purpose |
|---|---|
| `NEWSLETTER_DISTILLER_VISION` | `true` or `false` — overrides the automatic detection. |

### 4. Prompt files

The tool's behavior — including how it decides "concept image" vs. "ad" — is driven entirely by two plain-text prompt files you control:

| Setting | Default | Purpose |
|---|---|---|
| `--system-prompt` | `prompts/system_prompt.txt` | Sets the model's role/persona and general instructions. |
| `--user-prompt` | `prompts/user_prompt.txt` | Task-specific instructions: how to summarize, which images to keep, output format expectations. |

Both files must exist and be non-empty — the tool checks this before making any network call. Images are referenced by the LLM using placeholder IDs (`IMAGE_1`, `IMAGE_2`, ...) that your prompt should instruct it to use in `![alt text](IMAGE_n)` form; the tool resolves these to real local files afterward, so the LLM never needs to know (or guess) an actual file path or URL.

Starter versions of both files are included at [`prompts/system_prompt.txt`](prompts/system_prompt.txt) and [`prompts/user_prompt.txt`](prompts/user_prompt.txt) — edit them in place to change how the digest is written or how images are judged.

### 5. Output location

| Setting | Default | Purpose |
|---|---|---|
| `--output-dir` | `output/` | Where per-newsletter output folders are written. |
| `--overwrite` | off | Required to reuse an output folder name that already exists; otherwise the tool refuses to overwrite silently. |

## Usage

```bash
# Anthropic
export NEWSLETTER_DISTILLER_PROVIDER=anthropic
export NEWSLETTER_DISTILLER_MODEL=claude-sonnet-5
export ANTHROPIC_API_KEY=sk-ant-...
uv run newsletter-distiller "https://example.com/some-newsletter-issue"

# Local Ollama (OpenAI-compatible)
export NEWSLETTER_DISTILLER_PROVIDER=openai-compatible
export NEWSLETTER_DISTILLER_MODEL=llama3.2-vision
export NEWSLETTER_DISTILLER_BASE_URL=http://localhost:11434/v1
export NEWSLETTER_DISTILLER_API_KEY=ollama
uv run newsletter-distiller "https://example.com/some-newsletter-issue"
```

On success, the tool prints the path to the generated file and exits `0`:

```
output/some-newsletter-issue-title/some-newsletter-issue-title.md
```

On any failure (bad URL, missing prompt file, missing credentials, network error, provider error, unresolved image reference), it prints a message naming the failing stage and the reason, and exits non-zero without writing a partial output file.

Common flags:

| Flag | Purpose |
|---|---|
| `<url>` | Required. The newsletter URL to process. |
| `--provider` | Overrides `NEWSLETTER_DISTILLER_PROVIDER`. |
| `--model` | Overrides `NEWSLETTER_DISTILLER_MODEL`. |
| `--base-url` | Overrides `NEWSLETTER_DISTILLER_BASE_URL` (OpenAI-compatible only). |
| `--system-prompt` / `--user-prompt` | Override the default prompt file paths. |
| `--output-dir` | Override the default output directory. |
| `--overwrite` | Allow reusing an existing output folder. |

## Development

```bash
uv sync                # install all dependencies, including dev/test tools
uv run pytest          # run the full test suite
uv run newsletter-distiller --help
```

Every capability (content extraction, AI provider integration, output assembly, CLI orchestration) has unit tests exercising the guarantees in its spec, plus one end-to-end test that runs the full pipeline against a saved sample-newsletter fixture with a mocked AI response — no live network or API calls are required to run the suite.

## Project structure & design

This project follows a spec-driven workflow ([OpenSpec](openspec/)). For the authoritative detail behind everything summarized above:

- [`openspec/changes/add-newsletter-distiller-cli/proposal.md`](openspec/changes/add-newsletter-distiller-cli/proposal.md) — why this exists and what's changing
- [`openspec/changes/add-newsletter-distiller-cli/specs/`](openspec/changes/add-newsletter-distiller-cli/specs/) — the exact behavioral contract, one file per capability
- [`openspec/changes/add-newsletter-distiller-cli/design.md`](openspec/changes/add-newsletter-distiller-cli/design.md) — technical decisions and rationale (why `uv`, why two provider adapters, why images are referenced by ID, etc.)
- [`openspec/changes/add-newsletter-distiller-cli/tasks.md`](openspec/changes/add-newsletter-distiller-cli/tasks.md) — the implementation checklist
