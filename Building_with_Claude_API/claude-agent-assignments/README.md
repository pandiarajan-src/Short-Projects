# Building AI Agents with Claude: 4 Hands-on Assignments

A short, practical course for new graduates. Over four assignments you'll build one agent, **Study Buddy**, and make it more capable at every step:

| # | Assignment | You learn | Built with |
|---|------------|-----------|------------|
| 1 | [Chat Agent](assignments/assignment-1-chat-agent.md) | Messages API, system prompts, conversation memory, streaming, tokens | `anthropic` |
| 2 | [Tool-Using Agent](assignments/assignment-2-tool-agent.md) | The agent loop, local tools, Claude's web search tool, tool errors | `anthropic` |
| 3 | [MCP Server + Client](assignments/assignment-3-mcp.md) | Model Context Protocol: tools, resources, prompts, writing a client | `anthropic`, `mcp` |
| 4 | [Integrated Agent](assignments/assignment-4-integrated-agent.md) | Claude Agent SDK, built-in web tools, MCP servers, Skills, permissions | `claude-agent-sdk` |

**Rules for the whole course:** pure Python only. No LangChain, LangGraph, CrewAI, or any other agent framework. You may only use the Claude API (`anthropic`), the Claude Agent SDK (`claude-agent-sdk`), the official `mcp` package, and the Python standard library. The point is to see how agents actually work, not to hide that behind a framework.

Each assignment has:
- a **brief** (`assignments/*.md`): concepts, required tasks, stretch goals, and a rubric
- a **working reference example** (`examples/*.py`): run it first, read it, then extend it

---

## Setup (do this once)

### 1. Install tools

- **Python 3.12+**
- **uv** (fast Python package manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Claude Code** (needed by the Agent SDK in assignment 4): `npm install -g @anthropic-ai/claude-code`, or see https://code.claude.com

### 2. Install dependencies

```bash
cd claude-agent-assignments
uv sync
```

### 3. Set up authentication

There are two kinds of credentials, and it matters which one each assignment uses.

| Assignment | Uses | How to set it up |
|------------|------|------------------|
| 1, 2, 3 | **Claude API key** | Create a key at https://platform.claude.com → *API Keys*, then `cp .env.example .env` and paste the key in. |
| 4 | **Your Claude Pro login** | Run `claude` once in a terminal and log in with your Claude account. |

> ⚠️ **A Claude Pro subscription does not include Claude API credits.** The API (assignments 1–3) is billed separately through the Claude Console. Ask your instructor about API credits. These assignments are cheap: set `CLAUDE_MODEL=claude-haiku-5-5` in `.env` and the whole course should cost well under $1. The Agent SDK (assignment 4) runs on top of Claude Code, so it can use your Pro subscription instead.

### 4. Check that it works

```bash
uv run python examples/a1_chat_agent.py
```

---

## Project layout

```
claude-agent-assignments/
├── README.md                     ← you are here
├── pyproject.toml                ← dependencies
├── .env.example                  ← copy to .env and add your key
├── assignments/
│   ├── assignment-1-chat-agent.md
│   ├── assignment-2-tool-agent.md
│   ├── assignment-3-mcp.md
│   └── assignment-4-integrated-agent.md
└── examples/
    ├── a1_chat_agent.py           ← Assignment 1 reference
    ├── a2_tool_agent.py           ← Assignment 2 reference
    ├── a3_notes_mcp_server.py     ← Assignment 3 reference (MCP server)
    ├── a3_mcp_client.py           ← Assignment 3 reference (MCP client)
    ├── a4_integrated_agent.py     ← Assignment 4 reference
    └── .claude/skills/flashcards/SKILL.md   ← Assignment 4 skill (hidden folder!)
```

> On macOS/Linux, `.claude/` is a hidden folder. Use `ls -a examples` to see it.

---

## How to work through the course

1. Read the assignment brief.
2. **Run** the reference example and try the suggested prompts.
3. **Read** the example code. Every file is commented to explain the *why*.
4. Copy the example to `solutions/aN_<yourname>.py` and complete the **Required tasks**.
5. Attempt at least one **Stretch goal**.
6. Submit (see below).

Suggested pace: one assignment per day, about 2–3 hours each.

## What to submit

For each assignment, a zip or Git repo containing:
- your solution `.py` file(s)
- a `NOTES.md` with: (a) a pasted terminal transcript showing each required feature working, and (b) 3–5 sentences on what surprised you or what broke and how you fixed it
- **never your `.env` file or API key**

## Grading (per assignment, 100 points)

| Area | Points |
|------|--------|
| Required tasks work as described | 60 |
| Code quality: readable, small functions, errors handled, no secrets in code | 15 |
| `NOTES.md` transcript and reflection | 15 |
| Stretch goal | 10 |

## Useful documentation

- Claude API: https://platform.claude.com/docs
- Tool use: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- Web search tool: https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool
- Model Context Protocol: https://modelcontextprotocol.io and the Python SDK https://github.com/modelcontextprotocol/python-sdk
- Claude Agent SDK: https://code.claude.com/docs/en/agent-sdk/overview
- Agent Skills: https://code.claude.com/docs/en/skills

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `AuthenticationError` | Check `ANTHROPIC_API_KEY` in `.env`. It must start with `sk-ant-`. |
| `credit balance is too low` | Your API account has no credits. This is separate from Claude Pro. |
| Assignment 4: `CLINotFoundError` or a login error | Install Claude Code and run `claude` once to log in. |
| `No module named 'mcp.server.fastmcp'` | You found an old tutorial. In `mcp` 2.x, `FastMCP` was renamed to `MCPServer` (`from mcp.server.mcpserver import MCPServer`). |
| Web search errors on Haiku | The example picks the right web-search tool version for you. If you hard-code one, Haiku needs `web_search_20250305`. |
