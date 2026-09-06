# Module 06 — Network Mocking & Interception

**Maps to:** `Day-3/` (part 3)

## Objectives

- Intercept and mock network requests/responses with `page.route()`.
- Understand when to mock (unreliable/slow/3rd-party backends) vs. hit the real API.

## Key concepts

- **Request interception**: `page.route(pattern, handler)` sits in front of the browser's network stack — like a local proxy you control from the test.
- **Mocking vs. hitting the real thing**: mocking a response lets you test UI states (error banners, empty states) that are hard to trigger against a real backend.

## Hands-on (already completed in Day-3)

- `tests/network_mocking.spec.ts` — intercepting and mocking API responses consumed by the UI

## Checkpoint

Mock a 500 error response for one API call and assert the UI shows the correct error state.

## Resources

- https://playwright.dev/docs/network
- https://playwright.dev/docs/mock
