# Module 08 — Debugging, Tracing & Reporting

**Maps to:** `Day-4/` report and trace artifacts (applies to every prior module too)

## Objectives

- Read the HTML test report and the Trace Viewer to debug a failing test without adding print statements.
- Know the key flags: `--debug`, `--headed`, `--trace on`, `show-report`, `show-trace`.

## Key concepts

- **Trace Viewer**: a full recording (DOM snapshots, network, console, screenshots) of a test run — a flight recorder for a failed test, so you debug the recording instead of re-running a live, possibly-flaky test.
- **Reporters**: `playwright.config.ts` controls what gets generated (HTML report, JUnit XML for CI, list output).

## Hands-on (already completed in Day-4)

- `playwright-report/` and `test-results/*/trace.zip`, generated from the API suite — open with `npx playwright show-trace`

## Checkpoint

Deliberately break a locator, run the suite, and diagnose the failure using only the Trace Viewer (no re-running with `--headed`).

## Resources

- https://playwright.dev/docs/trace-viewer-intro
- https://playwright.dev/docs/test-reporters
