# Module 01 — TypeScript Fundamentals for Playwright

## Why this module

Playwright's Node API is TypeScript-first. You already think in strongly-typed languages (C++, C#) — TypeScript's type system will feel familiar; the new part is JavaScript's runtime quirks (async/await, promises) wrapped in those types.

## Objectives

- Read and write basic TypeScript: types, interfaces, classes, generics — just enough to use Playwright's API and read its `.d.ts` definitions.
- Understand `async`/`await` and Promises — everything in Playwright is asynchronous.
- Understand ES module imports/exports as used in `playwright.config.ts` and spec files.

## Key concepts

- **Types & interfaces**: like a C++ struct or a C# interface — they describe shape, not behavior.
- **async/await**: like a C# `async Task` method — `await` pauses until the browser action (click, navigation, request) resolves.
- **Classes**: TypeScript classes look like C#/Java classes; used heavily for the Page Object Model (Module 03).

## Hands-on

1. Install Node 20+ and TypeScript; confirm `npx tsc --version` works.
2. Write a 10-line TypeScript script with a typed interface and an async function returning a `Promise`; run it with `tsx` or `ts-node`.
3. Read `Day-1/playwright.config.ts` and annotate, in comments, what each typed field does.

## Checkpoint

Explain, without looking it up: what `Promise<void>` means, why `await` is required before `page.click(...)`, and what a TypeScript interface buys you over a plain JS object.

## Resources

- https://www.typescriptlang.org/docs/handbook/intro.html
- https://playwright.dev/docs/intro
