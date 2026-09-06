# Module 03 — Page Object Model & Authentication

**Maps to:** `Day-2/`

## Why this module

Real suites don't repeat selectors in every spec. The Page Object Model (POM) wraps a page's elements and actions in a class — the same discipline as wrapping a legacy API in a service class.

## Objectives

- Design Page Object classes (`LoginPage`, `InventoryPage`, `LogoutPage`) that expose actions (`login()`, `addItemToCart()`) instead of raw locators.
- Use Playwright's **setup projects** to log in once and reuse an authenticated session via `storageState.json`, instead of logging in inside every test.

## Key concepts

- **POM**: one class per page/component; tests read like user stories (`await loginPage.login(user, pass)`), not selector soup.
- **Setup projects & storageState**: a `*.setup.ts` project runs once and saves cookies/localStorage to a JSON file; other projects declare it as a dependency and start already logged in.

## Hands-on (already completed in Day-2)

- `pages/LoginPage.ts`, `pages/InventoryPage.ts`, `pages/LogoutPage.ts`
- `tests/02-saucedemo.setup.ts` (auth setup) + `tests/02-saucedemo.spec.ts` (consumes `storageState.json`) against saucedemo.com

## Checkpoint

Explain why the setup-project pattern is faster and more reliable than calling a `login()` helper inside every test's `beforeEach`.

## Resources

- https://playwright.dev/docs/pom
- https://playwright.dev/docs/auth
