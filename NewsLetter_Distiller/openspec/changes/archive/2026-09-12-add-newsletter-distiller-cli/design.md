## Context

Greenfield project — no existing code. See proposal.md - Why for motivation. Two exploration findings shape this design:

- The sample target page (a HubSpot-hosted newsletter landing page) is fully server-rendered; a plain HTTP GET returns the complete HTML with no JavaScript execution required. This design assumes that holds generally for newsletter "view in browser" pages (email-derived pages are conventionally server-rendered since email clients don't run JS).
- In that sample, a promotional image (conference-ticket ad) sits in the same DOM flow as genuine chart/diagram images, so structural position alone cannot separate them — but alt text differs sharply in style (analytical vs. promotional language), which is the signal the AI-side judgment (confirmed during exploration) relies on.

## Goals / Non-Goals

**Goals:**
- Ship a working single-URL-per-invocation CLI covering the four capabilities in this change.
- Support Anthropic natively and any OpenAI-compatible endpoint (Ollama, DeepSeek, Kimi/Moonshot, others) through one generic adapter.
- Fail fast and loud on every guardrail in the specs, before spending a network call or AI request on doomed input.
- Produce a self-contained, portable output folder (markdown + local image assets) that doesn't depend on the source newsletter staying online.

**Non-Goals:**
- Headless browser rendering for JavaScript-heavy newsletter pages. Deferred; the empty-extraction guardrail will fail loudly rather than silently producing a near-empty digest if this is ever hit.
- Batch/multi-URL processing in a single invocation.
- Automatic retry/backoff on transient network or API failures. A single explicit attempt keeps failure behavior predictable and visible; the user re-runs the command.
- A persistent multi-profile configuration system beyond environment variables and a local `.env` file.

## Decisions

**HTML parsing & boilerplate stripping: custom BeautifulSoup-based stripper, not a readability library.**
Libraries like `trafilatura`/`readability-lxml` are good at generic main-content extraction but don't expose the per-image metadata (alt text, immediate surrounding paragraph, reading-order position) this tool needs to hand to the AI step, so a readability library would still need a custom image-metadata pass layered on top. Building the stripper directly on `BeautifulSoup4` (`lxml` parser) gives full control over both text and image extraction in one pass, at the cost of maintaining our own boilerplate ruleset (tag/class denylist for nav/footer/social-icons/unsubscribe blocks, informed by the grounded HubSpot example) rather than reusing a battle-tested one.

**HTTP client: `requests`, no headless browser.**
Confirmed against the sample URL that a plain GET with a browser user-agent returns full content. Adding Playwright/Selenium would be a much heavier dependency for a case not yet observed to be necessary; revisit if a real target newsletter turns out to require JS rendering (see Non-Goals and Risks).

**Provider adapters: `anthropic` SDK for the native adapter, raw `requests` for the OpenAI-compatible adapter.**
The Anthropic adapter uses the official `anthropic` Python SDK against the Messages API (handles multimodal content blocks). The OpenAI-compatible adapter is implemented as a raw HTTP POST to `{base_url}/chat/completions` with the standard OpenAI chat payload shape, rather than depending on the `openai` SDK — several OpenAI-compatible servers (Ollama, DeepSeek, Kimi/Moonshot) deviate slightly from strict client-side validation some SDK versions impose, and a raw request avoids those mismatches while still covering the confirmed two-adapter shape.

**Vision-capability detection: static lookup table with explicit override.**
A small table maps known model-name patterns (e.g. `claude-*`, `gpt-4o*`, `llama3.2-vision*`, `qwen2-vl*`) to a vision-capable flag. An unrecognized model defaults to text-only (safe default: never send binary image bytes to a model that might reject or silently ignore them). An explicit config/env override lets the user force vision-capable behavior for a model the table doesn't yet know about, so staleness in the table never hard-blocks the user.

**Image placeholder scheme: sequential `IMAGE_n` IDs assigned at extraction time, resolved by Python after the AI response.**
Confirmed during exploration: the AI never writes real file paths or URLs. Extraction assigns each downloaded candidate image an ID in reading order; the AI request includes those IDs with metadata; the AI's markdown output references images only as `![alt](IMAGE_n)`; a post-processing pass swaps each `IMAGE_n` for the real local relative asset path and hard-fails on any ID that doesn't match a downloaded image.

**Boilerplate & tracking-pixel filtering: denylist-based, mechanical only.**
Structural denylist (nav/footer/header/social-share/unsubscribe regions, by tag and common ESP class/id patterns) removes obvious non-content regions. Images with declared width/height at or below 2px are dropped as tracking pixels. No promotional-intent judgment happens here — that's explicitly left to the AI step per the confirmed hybrid design.

**Environment & dependency management: `uv` exclusively, no `pip`.**
All environment creation, dependency installation/locking, running the CLI, and running tests go through `uv` (`uv sync`, `uv add`, `uv run ...`). `pyproject.toml` plus a committed `uv.lock` are the single source of truth for reproducible installs. Rejected alternative: `pip` + manual `venv` + `requirements.txt` — rejected per explicit preference for one consistent, fast tool instead of the pip/venv/pip-tools combination.

**Testing strategy: `pytest` unit tests per capability + one end-to-end fixture test, run via `uv run pytest`.**
Each capability (content-extraction, ai-provider-integration, markdown-output-assembly, cli-orchestration) gets unit tests that exercise its spec's requirements and scenarios directly. External HTTP calls (page fetch, image download, AI provider requests) are mocked so the suite runs offline and deterministically. One end-to-end test runs the full pipeline against the saved sample-newsletter HTML fixture (captured during exploration) with a mocked AI response, verifying the produced markdown file and image links. Alternative considered: integration tests hitting real provider APIs — rejected for the default suite since it would require live credentials and network access to run tests, and would be flaky/costly in CI; a real-API smoke test can still be run manually/opt-in but is not part of the required suite.

**CLI argument parsing: stdlib `argparse`.**
The flag surface is small (URL positional; `--provider`, `--model`, `--base-url`, `--system-prompt`, `--user-prompt`, `--output-dir`, `--overwrite`). `argparse` avoids adding a dependency (`click`/`typer`) for a surface this size; revisit if the CLI grows subcommands later.

**Credential/config loading: environment variables + optional local `.env` via `python-dotenv`.**
Matches the confirmed decision: secrets never accepted as CLI flags. Non-secret settings (provider, model, base URL, prompt paths, output dir) may come from CLI flags or environment variables, with documented defaults; if a required one is absent from both, startup validation fails before any I/O.

**Validation ordering: a single fail-fast startup check before any network call.**
One validation pass (URL scheme -> provider selection present -> required env var present -> prompt files exist & non-empty -> output directory resolvable/writable -> output folder not already existing unless `--overwrite`) runs before the HTTP fetch, before any image download, and before the AI request. This directly implements the cli-orchestration spec's "ordered validation" requirement and avoids wasting a network fetch or a paid AI call on a configuration mistake.

## Risks / Trade-offs

- [Risk] The boilerplate denylist is tuned against one HubSpot-style sample and may misclassify structure on other ESPs (Substack, Beehiiv, ConvertKit, Mailchimp) → [Mitigation] Keep the denylist rules isolated in one clearly named module so they're easy to extend as more newsletter sources are tried; empty-extraction guardrail catches the worst case (nothing survives stripping) rather than silently emitting garbage.
- [Risk] LLM ad/content image judgment is a soft call, not a hard rule, and can occasionally misclassify (keep an ad, drop a real chart) → [Mitigation] Accepted trade-off of the confirmed hybrid design; prompt files are user-owned text files, so the judgment can be tuned by editing the prompt without a code change.
- [Risk] The vision-capability lookup table goes stale as new models ship → [Mitigation] Explicit override available; default-to-text-only fails safe (skips sending bytes) rather than failing the run.
- [Risk] Large image payloads to a vision-capable model may hit provider-side timeouts or rate limits → [Mitigation] Explicit configurable request timeout and clear stage-attributed error surfacing (spec'd in ai-provider-integration), no silent hang or infinite retry.
- [Risk] A target newsletter page that actually requires JavaScript to render (unlike the grounded sample) would extract as empty → [Mitigation] Explicitly out of scope for this change (see Non-Goals); the empty-extraction guardrail fails loudly instead of producing a near-empty digest, making the gap visible rather than silent.

## Migration Plan

None required — greenfield addition with no prior behavior to migrate from. Installing the package is opt-in via `uv sync`; rollback is simply not installing/running it.

## Open Questions

- Exact default model name per provider (e.g., which Claude model, which default Ollama tag) — implementation detail with a documented default, doesn't change any spec behavior.
- Exact boilerplate CSS-class/id denylist entries beyond the initial HubSpot-informed set — refined iteratively as more sample newsletters are tried, without changing the behavioral contract in content-extraction's spec.
- Whether to ship example starter prompt files in the repo for convenience — not required by any requirement, pure implementation convenience.
