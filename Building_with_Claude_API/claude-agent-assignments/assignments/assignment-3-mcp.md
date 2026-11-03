# Assignment 3: MCP Server and Client from Scratch

**Reference code:** `examples/a3_notes_mcp_server.py` + `examples/a3_mcp_client.py` · **Time:** about 3 hours · **Uses:** `mcp`, `anthropic`

## Goal

Move the agent's notebook tools out of the agent and into a reusable **MCP server**. Then write your own **MCP client** that connects that server to Claude.

## Why MCP?

In assignment 2 the tools were stuck inside one Python file. If you also wanted them in Claude Code, Claude Desktop, or a teammate's agent, you'd have to copy the code. **MCP (Model Context Protocol)** is an open standard for this: write the tools once as a *server*, and any MCP-compatible *client* can use them.

```
 ┌──────────────┐   JSON-RPC over stdio   ┌───────────────────────┐
 │ MCP CLIENT   │ ◀─────────────────────▶ │ MCP SERVER            │
 │ (your agent) │   initialize            │ a3_notes_mcp_server.py│
 │      │       │   tools/list            │  • tools              │
 │      ▼       │   tools/call            │  • resources          │
 │   Claude API │   resources/read        │  • prompts            │
 └──────────────┘   prompts/get           └───────────────────────┘
```

## Concepts you'll learn

| MCP feature | Who decides to use it | Decorator | Example in our server |
|-------------|----------------------|-----------|----------------------|
| **Tools** | The **model** chooses to call them | `@mcp.tool()` | `add_note`, `search_notes`, `delete_note` |
| **Resources** | The **app or user** fetches data (read-only) | `@mcp.resource("uri")` | `notes://all`, `notes://topic/{topic}` |
| **Prompts** | The **user** picks a ready-made prompt template | `@mcp.prompt()` | `quiz_me(topic)` |

More things to know:
- **stdio transport:** the client starts the server as a subprocess and they talk over stdin/stdout. **Never `print()` to stdout inside a stdio server**, because that corrupts the protocol. Log to stderr.
- **Schemas for free:** `MCPServer` turns the function's name, docstring, and type hints into the tool's name, description, and JSON schema.
- **`ToolError`:** raise it for *expected* failures so Claude sees your message with `is_error=True`. Any other exception shows up as a generic "Error executing tool".
- **The bridge:** an MCP tool definition (`name`, `description`, `input_schema`) maps almost 1:1 onto a Claude tool definition. Your client is a translator between the two.
- **Version note:** this course uses `mcp` 2.x, where the server class is `MCPServer`. Many older tutorials use `FastMCP` from `mcp.server.fastmcp`, which is the 1.x name.

## Step 0: Run the reference

```bash
uv run python examples/a3_mcp_client.py
```

```
you > Save a note: a Python list is mutable, a tuple is not
you > Save a note under databases: an index speeds up reads but slows down writes
/tools
/resources
/read notes://all
/prompt quiz_me python          ← a server prompt drives a whole quiz
you > Delete note 42             ← watch the ToolError come back as is_error
```

Also explore the server on its own with the **MCP Inspector** (it opens a web UI):

```bash
uv run mcp dev examples/a3_notes_mcp_server.py
```

## Required tasks

### Part A: Server (`solutions/a3_server_<yourname>.py`)

1. **Add an `update_note(note_id, content)` tool** that raises `ToolError` for a missing id.
2. **Add a `notes://stats` resource** that returns JSON with the total notes, notes per topic, and the newest note's date.
3. **Add a second prompt**, `explain_like_im_new(topic)`, which tells Claude to read the student's notes on the topic and explain them as if to a first-year student.
4. **Test without Claude:** using the MCP Inspector, call every tool once, read every resource, and get every prompt. Paste screenshots or the output into `NOTES.md`.

### Part B: Client (`solutions/a3_client_<yourname>.py`)

5. **Connect to two servers at once:** write a second tiny MCP server, `solutions/a3_timer_server.py`, with one tool (`start_timer(minutes, label)`, which just records it) and one resource (`timer://active`). Your client must connect to **both** servers, merge their tools into one list for Claude, and send each `tools/call` to the server that owns that tool.
6. **Resource as context:** add `/attach <uri>`, which reads a resource and adds its contents to your *next* message to Claude, inside `<document>` tags.
7. **Generic prompt arguments:** make `/prompt <name> key=value key=value ...` work for any prompt and its arguments, not just `topic`. Use `list_prompts()` to show the user which arguments each prompt needs.

## Stretch goals (pick one)

- **Use your server from Claude Code:** register your server with `claude mcp add study-notes -- uv run python /full/path/to/a3_server_<yourname>.py`, then use it from a normal `claude` session. Describe the experience in `NOTES.md`.
- **HTTP transport:** run your server with `mcp.run(transport="streamable-http")` and connect to it with `mcp.client.streamable_http` instead of stdio.
- **Tool caching:** your client calls `list_tools()` on every turn. Cache it, and explain in `NOTES.md` when that cache could go stale.

## Rubric (60 points for required tasks)

| Task | Points |
|------|--------|
| Server: `update_note`, `notes://stats`, and new prompt are correct | 20 |
| Inspector evidence for every feature | 5 |
| Client routes tool calls across 2 servers | 15 |
| `/attach` resource context works | 10 |
| Generic `/prompt` with arguments works | 10 |

## Self-check questions

1. What's the difference between a tool and a resource? Give one example where each is the right choice.
2. Why can't a stdio MCP server use `print()`?
3. Two servers both expose a tool called `search`. What breaks, and how would you fix it? (Hint: look at how the Agent SDK names MCP tools in assignment 4.)
