# ai-provider-integration Specification

## Purpose

Provides a pluggable LLM client abstraction that distills extracted newsletter content into markdown using any configured provider (Anthropic native or OpenAI-compatible), driven by externally supplied prompt files and environment-based credentials.

## Requirements

### Requirement: Provider selection via configuration, not silent default
The system SHALL require the user to explicitly select an AI provider (and, for OpenAI-compatible providers, an endpoint/model) via configuration, and SHALL NOT silently fall back to a default provider when none is specified.

#### Scenario: No provider configured
- **WHEN** the user runs the tool without specifying a provider
- **THEN** the system SHALL exit with a non-zero status and an error message instructing the user to configure a provider, without making any AI API request

### Requirement: Two-adapter provider abstraction
The system SHALL support at least two provider adapters: a native Anthropic Messages API adapter, and a generic OpenAI-compatible chat-completions adapter configurable with a base URL, model name, and API key, covering providers such as Ollama, DeepSeek, and Kimi/Moonshot without requiring a dedicated adapter per vendor.

#### Scenario: OpenAI-compatible provider configured
- **WHEN** the user configures the OpenAI-compatible adapter with a custom base URL and model name (e.g., pointing at a local Ollama instance or DeepSeek's API)
- **THEN** the system SHALL send requests to that base URL using the OpenAI-compatible chat-completions request format

### Requirement: Credentials from environment only
The system SHALL read API keys exclusively from environment variables (optionally loaded from a local `.env` file), and SHALL NOT accept an API key via a command-line flag.

#### Scenario: API key supplied via environment variable
- **WHEN** the required environment variable for the selected provider is set
- **THEN** the system SHALL use its value as the API key for outgoing requests

#### Scenario: Required API key missing
- **WHEN** the environment variable required by the selected provider is not set
- **THEN** the system SHALL exit with a non-zero status and an error naming the missing environment variable, without attempting any AI API call

### Requirement: Load and validate prompt files
The system SHALL load a system prompt and a user prompt from external text files whose paths are configurable, and SHALL validate that both files exist and contain non-empty content before making any AI API call.

#### Scenario: Prompt file missing
- **WHEN** the configured system-prompt or user-prompt file path does not exist
- **THEN** the system SHALL exit with a non-zero status and an error identifying the missing file path

#### Scenario: Prompt file empty
- **WHEN** the configured prompt file exists but contains only whitespace
- **THEN** the system SHALL exit with a non-zero status and an error identifying the empty prompt file

### Requirement: Build provider-agnostic distillation request
The system SHALL combine the loaded system prompt, user prompt, extracted article text, and candidate image metadata (alt text, surrounding context, placeholder ID) into a single request understood identically regardless of which provider adapter is used.

#### Scenario: Request built from extracted content and prompts
- **WHEN** extraction has produced article text and a set of candidate images with metadata
- **THEN** the system SHALL construct one distillation request containing the system prompt, user prompt, article text, and each candidate image's placeholder ID with its metadata

### Requirement: Attach image bytes only for vision-capable models
The system SHALL determine whether the configured provider/model is vision-capable, and SHALL attach raw candidate image bytes to the request only when it is; for text-only models, the request SHALL rely solely on image metadata (alt text, surrounding context) for any image-relevance judgment.

#### Scenario: Vision-capable model configured
- **WHEN** the configured model is known to support image inputs
- **THEN** the system SHALL include the downloaded image bytes for each candidate image in the request

#### Scenario: Text-only model configured
- **WHEN** the configured model does not support image inputs
- **THEN** the system SHALL omit raw image bytes from the request and rely on image metadata alone, without failing the run

### Requirement: Delegate ad-vs-concept judgment to the AI
The system SHALL NOT apply its own heuristic rules to classify a candidate image as an advertisement or a concept/explanatory image; that judgment SHALL be made by the AI provider based on the system/user prompts and the supplied image metadata (and bytes, when available).

#### Scenario: AI excludes a promotional image
- **WHEN** the AI response's markdown omits the placeholder ID of a candidate image it judged promotional
- **THEN** the system SHALL NOT reintroduce that image into the final output

### Requirement: Surface AI API errors clearly
The system SHALL catch authentication failures, rate limiting, and timeout errors from the configured provider and exit with a non-zero status and a clear, provider-attributed error message, without silently retrying indefinitely or producing a partial/corrupt output file.

#### Scenario: Authentication failure
- **WHEN** the provider rejects the request due to an invalid or expired API key
- **THEN** the system SHALL exit with a non-zero status and an error message indicating an authentication failure, without writing an output file

#### Scenario: Rate limit or timeout
- **WHEN** the provider returns a rate-limit error or the request times out
- **THEN** the system SHALL exit with a non-zero status and an error message describing the failure, without writing an output file
