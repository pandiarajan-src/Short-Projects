# Module 05 — Data-Driven Testing & Fixtures

**Maps to:** `Day-3/` (part 2)

## Objectives

- Parameterize tests over datasets instead of copy-pasting near-identical specs.
- Use Playwright fixtures to share setup/teardown logic across tests.

## Key concepts

- **Data-driven tests**: loop over an array of test cases and call `test()` inside the loop — the same idea as parameterized tests (`[Theory]`/`[InlineData]` in xUnit, or pytest's `parametrize`).
- **Fixtures**: Playwright's dependency-injection mechanism for tests — declare what a test needs (`page`, a custom `loggedInPage`, test data) and Playwright wires it up.

## Hands-on (already completed in Day-3)

- `tests/common_ds.ts` — shared dataset used across specs
- `tests/data_driven.spec.ts` — loop-driven parameterized tests

## Checkpoint

Convert one hand-written repetitive test into a data-driven version using a `common_ds.ts`-style dataset.

## Resources

- https://playwright.dev/docs/test-parameterize
- https://playwright.dev/docs/test-fixtures
