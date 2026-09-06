# LearnPlayWright — Course Plan

> Recreated 2026-09-06. The original 00-plan.md and 01-09 module files were accidentally deleted with no backup; this version was rebuilt from the project brief plus the actual work already completed in the sibling `playwright-learning` repo (Day-1 through Day-4, Day-8), so it reflects real progress rather than a blind guess. Commit this folder to git going forward so a future deletion is a `git checkout` away, not a rebuild.

## Who this is for

20+ years of software development (C++, C#, Python) on desktop applications, new to web development, TypeScript, and Playwright. Goal: get production-ready for a web automation project (API + UI end-to-end) as fast as possible, learning by building.

## How this works

Hands-on first. Each module below pairs a short concept brief with a real exercise in the `playwright-learning` repo. You already know software engineering — the modules lean on that and spend time only on what's actually new: the browser/web model, TypeScript's type system, and Playwright's APIs.

## Module map

| # | Module | Maps to | Status |
|---|---|---|---|
| 01 | TypeScript Fundamentals for Playwright | (prerequisite) | — |
| 02 | Playwright Basics & First Tests | Day-1 | done |
| 03 | Page Object Model & Authentication | Day-2 | done |
| 04 | Advanced UI Interactions | Day-3 (part 1) | done |
| 05 | Data-Driven Testing & Fixtures | Day-3 (part 2) | done |
| 06 | Network Mocking & Interception | Day-3 (part 3) | done |
| 07 | API Testing with Playwright | Day-4 | done |
| 08 | Debugging, Tracing & Reporting | Day-4 report/trace | done |
| 09 | AI-Assisted Testing: Agents, Skills & CI/CD | Day-8 | done (CI/CD step pending — see Module 09) |

Your actual work already covers modules 02-09 in some form. Use these files as the reference write-up for what you did and why, and as the syllabus if you want more reps before moving to real project work (e.g. deeper Day-5/6/7-style practice on any single module).

## Stack

TypeScript, `@playwright/test`, Node.js 20+, npm, Claude Code (agents/skills/MCP for Module 09).

## Working agreement

- Plans and course content always live in markdown files, stored locally, and get committed to git.
- Each project folder (Day-N) is a standalone Playwright project with its own `package.json`/`playwright.config.ts` — no shared root, per the existing convention.
