## Why

There is currently no automated way to turn a raw newsletter URL into a clean, distraction-free markdown digest containing only the substantive article text and its explanatory charts/diagrams. Doing this by hand is tedious, and generic readability tools don't distinguish concept/chart images from promotional ones, nor do they work across the mix of LLM backends (Anthropic, Ollama, DeepSeek, Kimi, etc.) already available for this kind of processing.

## What Changes

- New standalone Python CLI, `newsletter-distiller`, that takes a newsletter URL as input and produces a markdown digest as output.
- Fetches the URL over HTTP(S) (scheme-validated), and mechanically strips structural boilerplate (nav, footer, social-share icons, tracking pixels, unsubscribe blocks) from the HTML, extracting the main article text plus candidate images with alt-text, surrounding paragraph context, and reading-order position.
- Downloads bytes for candidate images and assigns each a stable placeholder ID for later reference.
- Loads a system prompt and a user prompt from external text files (paths configurable via CLI flags, with sensible defaults), validating both exist and are non-empty before use.
- Builds a provider-agnostic AI request combining the system prompt, user prompt, extracted article text, and per-image metadata/IDs — attaching raw image bytes only when the configured model is vision-capable — and delegates the ad-vs-concept-image judgment to the LLM (via the prompt files) rather than to brittle Python-side heuristics.
- Supports a provider abstraction with two adapters: a native Anthropic Messages API adapter, and a generic OpenAI-compatible chat-completions adapter (covers Ollama, DeepSeek, Kimi/Moonshot, and other compatible endpoints) configured via base URL, model name, and API key.
- Reads all credentials from environment variables, optionally loaded from a local `.env` file; secrets are never accepted as CLI flags.
- Resolves the LLM's markdown output (which references images only by placeholder ID) into a final markdown file with real local relative image paths, writing `output/<slug>/<slug>.md` and `output/<slug>/assets/*`.
- Applies guardrails throughout the pipeline: URL scheme allowlist, empty-extraction detection, required-env-var validation before any network call, prompt file validation, network timeouts, clear error messages with non-zero exit codes on failure, output-directory writability checks up front, and validation that every image placeholder ID the LLM references resolves to an actually-downloaded image.
- Project setup, dependency management, and running the tool/tests are done exclusively through `uv` — no `pip`, no manually-managed `venv`. Dependencies and their lockfile (`pyproject.toml` + `uv.lock`) are the single source of truth for reproducible environments.
- Every capability (content extraction, AI provider integration, output assembly, CLI orchestration) is covered by automated unit tests exercising its spec's requirements/scenarios, plus one end-to-end test running the full pipeline against a fixture newsletter with a mocked AI response — all run via `uv run pytest`.

## Capabilities

### New Capabilities
- `content-extraction`: Fetching a newsletter URL and extracting clean article text plus candidate concept images (with alt-text/context metadata), with structural boilerplate stripped mechanically.
- `ai-provider-integration`: Pluggable LLM client abstraction (Anthropic native adapter + OpenAI-compatible adapter), prompt file loading/validation, and environment-variable-based provider/credential configuration.
- `markdown-output-assembly`: Resolving LLM-referenced image placeholder IDs to local downloaded files and writing the final markdown digest plus its asset folder.
- `cli-orchestration`: The end-to-end command-line entry point that wires the extraction, AI, and output stages together, enforcing guardrail/validation ordering and user-facing error handling with appropriate exit codes.

### Modified Capabilities
None — this is a greenfield project with no existing specs.

## Impact

- New Python package with a CLI entry point (e.g. `newsletter-distiller <url> [options]`), managed end-to-end with `uv` (environment creation, dependency install/lock, running the CLI, and running tests all go through `uv`).
- New dependencies: an HTTP client and HTML parser for fetching/extraction, an Anthropic client (or direct REST calls), a `.env` loader for local credential files, and `pytest` as a dev dependency for the unit/end-to-end test suite.
- No existing code is affected (greenfield repository).
- Requires the user to supply an API key via environment variable for whichever provider they select; no provider is silently defaulted.
- New local filesystem writes under an `output/` directory (one subfolder per processed newsletter, containing the markdown file and its downloaded image assets).
