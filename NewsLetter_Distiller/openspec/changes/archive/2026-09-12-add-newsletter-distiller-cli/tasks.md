## 1. Project Setup

- [x] 1.1 Initialize Python package structure (src layout, `pyproject.toml` with a `newsletter-distiller` console-script entry point) using `uv init`/`uv sync` (no `pip`, no manually-created `venv`), and verify `uv run newsletter-distiller --help` succeeds
- [x] 1.2 Add core dependencies (`requests`, `beautifulsoup4`, `lxml`, `anthropic`, `python-dotenv`) via `uv add`, and verify `uv.lock` is generated/updated and `uv sync` installs cleanly
- [x] 1.3 Add `pytest` as a dev dependency via `uv add --dev pytest`, create a fixtures directory containing a saved copy of the sample newsletter HTML, and verify `uv run pytest` runs with zero errors

## 2. Configuration & Credential Guardrails

- [x] 2.1 Implement a config loader that reads provider/model/base-url/prompt-paths/output-dir from CLI flags and environment variables (with local `.env` support via `python-dotenv`), and verify a required-but-missing value raises a clear error before any I/O
- [x] 2.2 Implement the ordered fail-fast startup validation (URL scheme -> provider selected -> required API-key env var present -> prompt files exist & non-empty -> output dir writable -> output folder doesn't already exist unless `--overwrite`) and verify each individual failure produces a distinct non-zero exit with an actionable message

## 3. Content Extraction

- [x] 3.1 Implement URL scheme validation and verify a non-http(s) URL is rejected before any network call
- [x] 3.2 Implement HTTP fetch with an explicit timeout and verify the success, timeout, and non-2xx-status paths each produce their specified error/exit behavior
- [x] 3.3 Implement the mechanical boilerplate stripper (nav/footer/social-icon/unsubscribe denylist + tracking-pixel filtering for images at or below 2px) and verify against the fixture HTML that footer/nav content is excluded from extraction output
- [x] 3.4 Implement main-article text extraction preserving reading order and verify extracted paragraph/heading order matches the fixture's source order
- [x] 3.5 Implement empty-extraction detection and verify a fixture with no substantive content triggers a non-zero exit before any AI call
- [x] 3.6 Implement candidate-image identification capturing alt text, surrounding paragraph text, and reading-order position, and verify against the fixture that all non-boilerplate images are captured with correct metadata
- [x] 3.7 Implement image byte download with stable placeholder-ID assignment, and verify a broken image link is excluded with a logged warning while the run continues

## 4. AI Provider Integration

- [x] 4.1 Define the provider-agnostic request shape (system prompt, user prompt, article text, per-image metadata + placeholder ID, optional image bytes) shared by both adapters, and verify a unit test can build a request from the fixture's extraction output
- [x] 4.2 Implement prompt-file loading and validation (existence + non-empty) and verify missing and empty prompt files each produce their specified error before any AI call
- [x] 4.3 Implement the vision-capability lookup table with an explicit override, and verify known vision models attach image bytes while unknown/text-only models omit them
- [x] 4.4 Implement the native Anthropic Messages API adapter using the `anthropic` SDK and verify (via a mocked transport) it sends a correctly shaped multimodal request
- [x] 4.5 Implement the generic OpenAI-compatible chat-completions adapter (raw HTTP via `requests`, configurable `base_url`/`model`/`api_key`) and verify it can successfully call a local mock server standing in for Ollama/DeepSeek/Kimi
- [x] 4.6 Implement the provider-selection guardrail (no silent default) and required-env-var validation, and verify running without a configured provider exits non-zero before any request is made
- [x] 4.7 Implement AI API error handling (authentication failure, rate limit, timeout) mapped to clear, provider-attributed error messages and non-zero exit, and verify each case (via a mocked failing response) writes no output file

## 5. Markdown Output Assembly

- [x] 5.1 Implement placeholder resolution that swaps each `IMAGE_n` reference in the AI's markdown output for the corresponding local asset's relative path, and verify against a fixture AI response containing multiple placeholders
- [x] 5.2 Implement unknown-placeholder validation and verify a fixture response referencing an unrecognized ID exits non-zero without writing a file
- [x] 5.3 Implement slug derivation from the newsletter title (falling back to the URL path when the title is missing/empty) and output-folder writing (`output/<slug>/<slug>.md` plus `output/<slug>/assets/*`), and verify the fixture run produces the expected file layout
- [x] 5.4 Implement the output-directory-writable check and the existing-folder-without-`--overwrite` guard, and verify both failure paths exit non-zero before any AI request is made

## 6. CLI Orchestration & End-to-End Verification

- [x] 6.1 Implement the `newsletter-distiller <url> [options]` entry point wiring extraction -> AI request -> output assembly in validated order, and verify `uv run newsletter-distiller --help` documents every flag and its default
- [x] 6.2 Wire the ordered fail-fast validation pass ahead of any network/API call and verify a scenario with simultaneous configuration problems (e.g., missing prompt file and missing API key) reports before the URL is fetched
- [x] 6.3 Add an end-to-end test using the sample newsletter HTML fixture with a mocked AI provider response, and verify via `uv run pytest` that it produces a valid markdown file with correctly resolved image links and exit code 0
- [x] 6.4 Verify exit codes and error messages are distinct per failing stage (fetch/extraction/AI/output) by exercising each failure scenario via `uv run pytest` and confirming the printed message identifies the failing stage
- [x] 6.5 Update the repo README (installation via `uv`, required environment variables per provider, prompt-file format and default locations, and example invocations) and verify a fresh read-through matches actual CLI behavior
