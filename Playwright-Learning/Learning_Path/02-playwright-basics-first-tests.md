# Module 02 — Playwright Basics & First Tests

**Maps to:** `Day-1/`

## Why this module

Get a green test running end-to-end before learning theory — confirms your environment works and builds a feel for the test runner.

## Objectives

- Install Playwright, scaffold a project, and run tests headless, headed, and in UI mode.
- Understand `test()`, `expect()`, locators, and the shape of `playwright.config.ts` (projects, browsers, baseURL, reporters).
- Write your first two specs against a real page.

## Key concepts

- **Locators**: Playwright's auto-waiting selector engine — closer to a live UI-tree query than a cached CSS selector. Prefer `getByRole`/`getByTestId` over brittle CSS/XPath.
- **Auto-waiting, retrying assertions**: `expect(locator).toBeVisible()` polls; you rarely need a manual `sleep()`.
- **Test runner projects**: `playwright.config.ts` can run the same suite across chromium/firefox/webkit as separate "projects."

## Hands-on (already completed in Day-1)

- `tests/example.spec.ts` — first smoke spec.
- `tests/todomvc.spec.ts` — interacting with a real small web app (TodoMVC): add/complete/delete items, assert list state.

## Checkpoint

Run `npx playwright test --ui` in `Day-1/` and narrate out loud what each step in the trace timeline is doing.

## Resources

- https://playwright.dev/docs/writing-tests
- https://playwright.dev/docs/locators
