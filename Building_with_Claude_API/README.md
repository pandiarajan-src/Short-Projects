# Building with Claude API

A hands-on learning project (uv-managed, `src/` layout) exploring the Anthropic Claude API. Built while following Anthropic's "Building with Claude" course, with additional side experiments.

## What's covered

Numbered exercises under `src/building_with_claude_api/`:

- **API basics** — simple requests, streaming (`00`–`01`)
- **Structured output** — request structured data from the API (`02`)
- **Prompt evals** — generating evaluation datasets and running model + code evaluations (`03`–`04`)
- **Prompt engineering** — exercises building on prompt-engineering patterns (`05`)
- **Tool use** — calling tools, streaming tool calls, the in-built web search and text editor tools (`06`)
- **RAG** — retrieval-augmented generation with semantic (Chroma), BM25 and hybrid retrieval (`07`)
- **Extended thinking** — Claude's extended-thinking mode (`08`)
- **Multimodal** — image and PDF features (`08`)

Shared helpers live in `src/building_with_claude_api/utils/` (embeddings, Chroma semantic search, BM25 keyword search, tool schemas and executors, prompt evaluation, report generation).

## Side experiments

- `src/mcp_project/` — a CLI chat application with the Anthropic API and MCP-based tool integrations
- `src/lab_chroma/` — small Chroma vectorstore experiments (in-memory, local-disk, local-NW)
- `src/educative_examples/` — example agent patterns from Educative (guardrails, retry loops, context handoff, tool failure handling, provenance, etc.)
- `src/app_starter/` — a starter app with document and math tools plus tests

## Quick start

```bash
uv sync                       # install dependencies (Python 3.12+, uv)
cp .env.exmaple .env          # add your ANTHROPIC_API_KEY
uv run python src/building_with_claude_api/00-making-simple-api-request.py
```