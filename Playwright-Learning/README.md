# Playwright Learning

A day-by-day journal of learning [Playwright](https://playwright.dev) for end-to-end and API testing — starting from basic specs and page objects, moving through data-driven tests, network mocking, and API testing, and finishing with AI-assisted testing using Playwright's **Test Agents** (Planner / Generator / Healer) and **Skills**, driven from Claude Code.

Each `Day-N` folder is a **standalone Playwright project** with its own `package.json`, `playwright.config.ts`, and dependencies — there is no shared root project.

## Repository layout

| Folder | Focus |
|---|---|
| [Day-1/](Day-1/) | Playwright basics — first specs (`tests/example.spec.ts`, `tests/todomvc.spec.ts`) |
| [Day-2/](Day-2/) | Page Object Model (`pages/LoginPage.ts`, `InventoryPage.ts`, `LogoutPage.ts`), auth setup projects, and reused storage state (`storageState.json`) against [saucedemo.com](https://www.saucedemo.com) |
| [Day-3/](Day-3/) | Advanced UI: browser interactions, iframes, file uploads, data-driven tests, and network mocking (`tests/network_mocking.spec.ts`) |
| [Day-4/](Day-4/) | API testing (`tests/api/users.spec.ts`) using Playwright's request context |
| [Day-8/](Day-8/) | Full Claude Code integration: Playwright **Test Agents** (planner/generator/healer), a `specs/` test-plan directory, a saucedemo checkout POM suite, and the Playwright MCP server config |

Each project's `test-results/`, `playwright-report/`, `.playwright-mcp/`, and `.playwright-cli/` folders are build/run artifacts (ignored by [.gitignore](.gitignore)) — safe to delete at any time.

## Prerequisites

- [Node.js](https://nodejs.org) 20 or newer
- npm (bundled with Node)
- [Claude Code](https://claude.com/claude-code) CLI, if you want to use the AI agents/skills described below

## Running a Day's tests

Every folder is set up the same way. From the repo root:

```bash
cd Day-8                       # or Day-1, Day-2, Day-3, Day-4
npm install                    # install @playwright/test and friends
npx playwright install         # download browser binaries (chromium/firefox/webkit)
```

Then run tests:

```bash
npx playwright test                        # run the whole suite headless
npx playwright test --ui                   # interactive UI mode
npx playwright test --headed               # watch the browser
npx playwright test tests/example.spec.ts  # run a single file
npx playwright show-report                 # open the HTML report from the last run
```

Day-4's suite is API-only (no browser needed), and Day-8 also ships `@playwright/cli` for ad-hoc, agent-driven browser automation (see below).

## Setting up Playwright Agents & Skills for Claude Code

This is what `Day-8/` has wired up, and what makes the AI-assisted workflow available inside Claude Code. Run these commands from inside the project folder you want to enable them in (e.g. `Day-8/`).

### 1. Test Agents — Planner, Generator, Healer

Requires Playwright v1.56+.

```bash
npx playwright init-agents --loop=claude
```

This scaffolds:
- `.claude/agents/playwright-test-planner.md` — explores the running app and writes a Markdown test plan
- `.claude/agents/playwright-test-generator.md` — turns a plan into real `*.spec.ts` files
- `.claude/agents/playwright-test-healer.md` — re-runs failing tests, inspects the live page, and fixes broken locators/assertions
- `.mcp.json` — points Claude Code at the Playwright Test MCP server (`npx playwright run-test-mcp-server`) that these agents drive to launch a browser, take accessibility snapshots, and interact with pages

Re-run this command whenever Playwright is upgraded, to pick up new tools/instructions.

### 2. Playwright CLI skills (playwright-cli, playwright-trace, playwright-component-testing)

```bash
npm install -g @playwright/cli@latest
playwright-cli install --skills
```

(or, without a global install: `npx @playwright/cli install --skills`)

This adds Claude Code **skills** under `.claude/skills/`:
- `playwright-cli` — browser automation and end-to-end test authoring from the terminal
- `playwright-trace` — inspect `.zip` trace files (actions, network requests, console, snapshots) without opening the Trace Viewer UI
- `playwright-component-testing` — scaffold React/Vue component tests via a story-gallery approach

### 3. Enable the MCP server in Claude Code

`init-agents` writes `.mcp.json` to the project root. Claude Code will prompt to enable it the first time you open the folder, or you can approve it up front in `.claude/settings.local.json` (see the `enabledMcpjsonServers` key already set up in [Day-8](Day-8/.mcp.json)).

## Using the agents once installed

From inside a Claude Code session opened in a folder with the agents installed (e.g. `Day-8/`):

1. **Plan** — ask Claude to use the `playwright-test-planner` agent against a running app (e.g. a local dev server or saucedemo) to produce a plan under `specs/` (see [Day-8/specs/README.md](Day-8/specs/README.md)).
2. **Generate** — ask the `playwright-test-generator` agent to turn a plan item into a `.spec.ts` file.
3. **Heal** — after code changes break tests, ask the `playwright-test-healer` agent to run the suite, debug failures, and patch the broken tests.

You can also drive the browser directly for exploratory automation via the `playwright-cli` skill, or inspect a saved trace with the `playwright-trace` skill (`npx playwright show-trace` equivalent, from the CLI).

## References

- [Playwright docs](https://playwright.dev/docs/intro)
- [Playwright Test Agents](https://playwright.dev/docs/test-agents)
- [Playwright Agent CLI](https://playwright.dev/agent-cli/installation)
- [Claude Code docs](https://docs.claude.com/en/docs/claude-code)
