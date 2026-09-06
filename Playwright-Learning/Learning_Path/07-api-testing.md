# Module 07 — API Testing with Playwright

**Maps to:** `Day-4/`

## Objectives

- Use Playwright's `request` context to test REST APIs directly, with no browser involved.
- Understand when API-level tests are cheaper and faster than UI tests for the same coverage.

## Key concepts

- **APIRequestContext**: a lightweight HTTP client built into Playwright — the same `expect` assertion library works on API responses as on UI locators.
- **Test pyramid**: push coverage down to API tests where possible; reserve UI tests for user-journey-critical paths.

## Hands-on (already completed in Day-4)

- `tests/api/users.spec.ts` — create a user via API and verify it, using the `request` fixture

## Checkpoint

Write one new API test against a public test API (e.g. reqres.in or jsonplaceholder) from scratch, no reference.

## Resources

- https://playwright.dev/docs/api-testing
