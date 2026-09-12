# cli-orchestration Specification

## Purpose

Provides the command-line entry point that wires content extraction, AI distillation, and output assembly into a single ordered run with predictable guardrails and error reporting.

## Requirements

### Requirement: Single URL argument entry point
The system SHALL accept exactly one newsletter URL as a required positional command-line argument, and SHALL print a usage error and exit non-zero if it is missing or if more than one is given.

#### Scenario: Missing URL argument
- **WHEN** the tool is invoked with no URL argument
- **THEN** the system SHALL exit with a non-zero status and print usage information

### Requirement: Configuration via flags/env, not hardcoded assumptions
The system SHALL accept provider, model, prompt-file paths, and output directory as configurable options (CLI flags and/or environment variables) with documented defaults, and SHALL NOT assume a provider, model, or prompt file silently when a required option is absent from both.

#### Scenario: All options at defaults
- **WHEN** the user supplies only the URL and has environment variables set for a provider's credentials
- **THEN** the system SHALL run using documented default prompt-file paths and output directory

#### Scenario: Required option absent from flags and environment
- **WHEN** a required configuration value (e.g., provider selection) is not supplied via flag or environment variable
- **THEN** the system SHALL exit with a non-zero status and an error naming the missing configuration, before performing any network I/O

### Requirement: Ordered validation before network/API calls
The system SHALL validate URL scheme, prompt file presence/non-emptiness, required provider credentials, and output directory writability before performing any network fetch or AI API call, so that configuration mistakes are reported immediately rather than after partial, wasted work.

#### Scenario: Multiple configuration problems present
- **WHEN** both the prompt file is missing and the provider API key is unset
- **THEN** the system SHALL report a validation error before attempting to fetch the URL or call the AI provider

### Requirement: Distinct, actionable exit codes and messages
The system SHALL report failures at each pipeline stage (fetch, extraction, AI request, output assembly) with a distinct, human-readable error message identifying the stage and cause, and SHALL exit with a non-zero status code on any failure and zero only on full success.

#### Scenario: Successful end-to-end run
- **WHEN** fetch, extraction, AI distillation, and output assembly all complete without error
- **THEN** the system SHALL print the path to the generated markdown file and exit with status code 0

#### Scenario: Failure at any stage
- **WHEN** any pipeline stage fails
- **THEN** the system SHALL print an error message identifying which stage failed and why, and exit with a non-zero status code
