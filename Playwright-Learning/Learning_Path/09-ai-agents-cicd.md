# Module 09 — AI-Assisted Testing: Agents, Skills & CI/CD

**Maps to:** `Day-8/`

## Objectives

- Use Playwright's Test Agents (Planner, Generator, Healer) driven from Claude Code to go from a running app to a full spec suite.
- Install and use the `playwright-cli`, `playwright-trace`, and `playwright-component-testing` skills.
- Wire the Playwright MCP server into Claude Code for exploratory, agent-driven browser automation.
- (Next step, not yet done) wire the suite into CI so it runs on every push.

## Key concepts

- **Planner -> Generator -> Healer loop**: Planner explores the live app and writes a markdown test plan (`specs/*.md`); Generator turns plan items into real `.spec.ts` files; Healer re-runs failures, inspects the live page, and patches broken locators/assertions. This is the biggest leverage point for someone new to Playwright — you review generated code instead of writing every locator by hand.
- **MCP server**: `npx playwright run-test-mcp-server` exposes browser control (navigate, snapshot, interact) as tools the agents can call.

## Hands-on (already completed in Day-8)

- `npx playwright init-agents --loop=claude` -> `.claude/agents/playwright-test-{planner,generator,healer}.md`, `.mcp.json`
- `specs/saucedemo-sort-cart-checkout.plan.md` — a full Planner-authored test plan for saucedemo sorting/cart/checkout
- `tests/pom/*.ts` — generated Page Object classes (BasePage, CartPage, CheckoutStepOne/TwoPage, CheckoutCompletePage, InventoryPage, ItemListPage, LoginPage)
- `tests/tests/{cart,checkout,sorting}/*.spec.ts` — around 25 generated specs covering sorting, cart management, and checkout, all traceable back to the plan

## Checkpoint / next steps

1. Pick a small app you don't already have tests for; run the Planner agent against it and review the plan it writes before generating any code.
2. Add a CI workflow (e.g. GitHub Actions) that runs `npx playwright test` on push and uploads the HTML report as an artifact — the one piece of the original brief ("automation work" on a real project) not yet exercised.
3. Practice the Healer loop: intentionally change a `data-test` attribute in a mocked page and have the Healer agent fix the resulting broken spec.

## Resources

- https://playwright.dev/docs/test-agents
- https://playwright.dev/agent-cli/installation
- https://docs.claude.com/en/docs/claude-code
