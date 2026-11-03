# Assignment 4: The Integrated Agent (Claude Agent SDK + MCP + Skills)

**Reference code:** `examples/a4_integrated_agent.py` + `examples/.claude/skills/flashcards/SKILL.md` · **Time:** about 3 hours · **Uses:** `claude-agent-sdk`

## Goal

Put everything together into one Study Buddy agent that can **research the web, remember notes through your MCP server, plan study sessions, and follow a Skill**, using the **Claude Agent SDK** instead of a hand-written loop.

## From hand-written loop to Agent SDK

In assignments 2 and 3 *you* wrote the `while stop_reason == "tool_use"` loop. The **Claude Agent SDK** packages the same agent harness that powers Claude Code. You don't write the loop; you **configure** the agent:

| You wrote this by hand (A2/A3) | In the Agent SDK it's... |
|--------------------------------|---------------------------|
| `messages` list for memory | `ClaudeSDKClient` keeps the session |
| `while` loop + `MAX_LOOPS` | built in; `max_turns=15` |
| your web search tool declaration | built-in `WebSearch` and `WebFetch` tools |
| your `MCPClient` class | `mcp_servers={"notes": {"type": "stdio", ...}}` |
| local Python tool functions | `@tool` + `create_sdk_mcp_server()` (an in-process MCP server) |
| "ask the human before deleting" | `allowed_tools`, `permission_mode`, `can_use_tool` |
| a giant system prompt | **Skills**: instructions loaded only when needed |

## Concepts you'll learn

- **`query()` vs `ClaudeSDKClient`:** `query(prompt=..., options=...)` is one-shot. `ClaudeSDKClient` is for multi-turn chat that remembers context.
- **Message stream:** you iterate over messages. `AssistantMessage` holds `TextBlock` and `ToolUseBlock` items, and the final `ResultMessage` has the turn count, duration, and cost.
- **MCP tool names:** the SDK exposes MCP tools as `mcp__<server>__<tool>`, for example `mcp__notes__add_note`. This prefix is how name clashes between servers are avoided.
- **Permissions:**
  - `tools=[...]` controls which built-in tools **exist** for the model at all
  - `allowed_tools=[...]` lists tools that run **without asking**
  - `permission_mode="dontAsk"` **denies** anything not pre-approved
  - `can_use_tool=callback` lets **your code** decide at run time (human-in-the-loop)
- **Skills:** a folder holding a `SKILL.md` with `name` and `description` frontmatter. Claude sees only the short description until the skill is relevant, then loads the full instructions. This keeps the context small. Our skill lives in `examples/.claude/skills/flashcards/` and is enabled with `skills=["flashcards"]` plus `setting_sources=["project"]`.
- **Auth:** the SDK runs Claude Code under the hood, so it can use your **Claude Pro login**. The example removes `ANTHROPIC_API_KEY` from its environment so the subscription is used.

## Step 0: Run the reference

```bash
claude            # once, to log in with your Claude Pro account, then /exit
uv run python examples/a4_integrated_agent.py
```

```
you > Make me 5 flashcards on HTTP status codes        ← Skill + WebSearch + mcp__notes__add_note
you > What have I saved about http?                     ← mcp__notes__search_notes
you > Plan 2 hours of study on SQL and Git              ← in-process mcp__planner__study_plan
you > Delete note 1                                     ← denied: delete_note is not in allowed_tools
```

In `NOTES.md`, explain why the last request fails, and which line of the config causes it.

## Required tasks

Copy the example to `solutions/a4_<yourname>.py` (and your skill to `solutions/.claude/skills/...`), then:

1. **Use your own MCP server:** point `mcp_servers["notes"]` at **your** assignment 3 server, and add your timer server as a second stdio server. Allow only the tools that are safe to run without asking.
2. **Human-in-the-loop permissions:** instead of silently denying `delete_note` and `update_note`, add a `can_use_tool` callback that asks `Allow <tool>(<input>)? [y/N]` in the terminal and returns `PermissionResultAllow()` or `PermissionResultDeny(message=...)`. *Hint:* when you use `can_use_tool`, remove `permission_mode="dontAsk"` so that unlisted tools reach your callback, and read the SDK docs on permissions.
3. **Write your own Skill:** create `.claude/skills/exam-prep/SKILL.md`. When a student says *"I have an exam on X on <date>"*, the skill should: (a) use `get_current_datetime` (add it as an in-process `@tool`) to count the days left, (b) search the student's notes, (c) research gaps on the web, and (d) call `study_plan` to build a day-by-day plan. Enable it next to `flashcards`.
4. **One-shot mode:** if the script is run with a command-line argument (`uv run python a4.py "make flashcards on DNS"`), use `query()` to answer once and exit. With no argument, start the chat loop.
5. **Session summary:** when the user quits, print how many tool calls were made **per tool name**, and the total turns and duration from the `ResultMessage`s.

## Stretch goals (pick one)

- **Subagent:** define a `researcher` subagent with `agents={"researcher": AgentDefinition(description=..., prompt=..., tools=["WebSearch", "WebFetch"])}` and add `"Agent"` to `tools`. The main agent should hand off web research to it. Compare token use with and without the subagent.
- **Hooks:** add a `PreToolUse` hook (`hooks={"PreToolUse": [HookMatcher(...)]}`) that blocks any `WebFetch` to a domain on a blocklist and logs every tool call to a file.
- **Same agent, two ways:** write about 30 lines of `NOTES.md` comparing your assignment 3 client with this SDK agent. Cover lines of code, control, debuggability, and when you'd choose each.

## Rubric (60 points for required tasks)

| Task | Points |
|------|--------|
| Your A3 server and timer server are wired in, with sensible `allowed_tools` | 10 |
| `can_use_tool` approval works for both allow and deny | 15 |
| `exam-prep` skill triggers on its own and uses all 4 capabilities | 20 |
| One-shot `query()` mode | 5 |
| Session summary per tool | 10 |

## Self-check questions

1. `tools`, `allowed_tools`, and `permission_mode`: which one stops the model from even *seeing* `Bash`?
2. Why is a Skill better than pasting the same instructions into the system prompt?
3. The in-process `study_plan` tool and the stdio notes server are both MCP servers. When would you choose each?
4. You've now built the same agent three ways. Which would you use for (a) a production web backend, (b) a quick internal tool, or (c) learning? Why?
