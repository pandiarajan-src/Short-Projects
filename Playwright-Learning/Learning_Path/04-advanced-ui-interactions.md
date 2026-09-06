# Module 04 — Advanced UI Interactions

**Maps to:** `Day-3/` (part 1)

## Objectives

- Handle interactions beyond click/fill: hover, drag, keyboard, mouse events.
- Work with iframes as isolated frame contexts.
- Automate file uploads.

## Key concepts

- **Frames**: an `<iframe>` is a nested browsing context — `frameLocator()` reaches inside it, similar to scoping a query to a child window handle in desktop UI automation.
- **File chooser**: Playwright intercepts the native file-picker dialog via `page.setInputFiles()` — no OS-level dialog automation needed.

## Hands-on (already completed in Day-3)

- `tests/browser_interactions.spec.ts` — mouse/keyboard interactions
- `tests/fixtures/iframe-parent.html` + `iframe-child.html` — cross-frame locator practice
- `tests/fixtures/sample-upload.txt` — file upload flow

## Checkpoint

Given a page with a nested iframe, write a locator chain to click a button inside it without looking at the reference solution first.

## Resources

- https://playwright.dev/docs/frames
- https://playwright.dev/docs/input#upload-files
