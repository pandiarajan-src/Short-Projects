# Assignment 2: Give Your Agent Tools

**Reference code:** `examples/a2_tool_agent.py` · **Time:** about 3 hours · **Uses:** Claude API (`anthropic`)

## Goal

Turn the chatbot into a real **agent**: a model that decides *by itself* which actions to take, takes them, looks at the results, and keeps going until the job is done.

## Concepts you'll learn

### The agent loop (the most important idea in this course)

```
          ┌──────────────────────────────────────────────┐
          ▼                                              │
  send messages + tool list to Claude                    │
          │                                              │
   stop_reason == "tool_use"? ── yes ─▶ run the tools ───┤  append tool_result
          │                             on YOUR machine  │  in ONE user message
          no                                             │
          │                                              │
   stop_reason == "pause_turn"? ─ yes ─▶ send it back ───┘  (server tool still working)
          │
          no ──▶ done: print the final text
```

Claude never runs your code. It returns a `tool_use` block (*"please call `calculator` with `{"expression": "2+2"}`"*). Your loop runs the function and sends back a `tool_result` block with the same `tool_use_id`.

### Two kinds of tools

| | Local (client) tools | Server tools |
|---|---|---|
| Who runs it | **Your** Python code | Anthropic's servers |
| You provide | `name`, `description`, `input_schema`, and the implementation | Just the declaration, e.g. `{"type": "web_search_20260209", "name": "web_search"}` |
| Examples here | `calculator`, `get_current_datetime`, `save_note`, `list_notes` | `web_search` |
| Appears in the response as | `tool_use` block → you must answer it | `server_tool_use` + `web_search_tool_result` blocks, already finished |

### Tool design tips

- **The description is the prompt.** Claude picks tools based on the `description`. Say *what* the tool does and *when* to use it.
- **`strict: True`** plus `additionalProperties: False` guarantees that Claude's arguments match your schema.
- **Report errors, don't crash.** If a tool fails, return `{"type": "tool_result", ..., "is_error": True}` with a helpful message. Claude will often fix its input and try again.
- **Parallel calls.** Claude may ask for several tools at once. Return **all** results in **one** user message.
- **Safety cap.** Always limit loop iterations (`MAX_LOOPS`). Agents can get stuck.

## Step 0: Run the reference

```bash
uv run python examples/a2_tool_agent.py
```

Try these prompts and watch the cyan `[tool]` and magenta `[web]` lines:

```
you > What is 17.5% of 2340, plus 99?
you > Remember that my Data Structures exam is on 2026-12-12.
you > How many days until my exam?            ← uses get_current_datetime + list_notes + calculator
you > What's the latest stable version of Python? Cite your source.   ← web search
you > What's the square root of a banana?     ← watch the error handling
```

## Required tasks

Copy the example to `solutions/a2_<yourname>.py`, then:

1. **Add 3 new local tools** with good descriptions and `strict` schemas:
   - `unit_convert(value, from_unit, to_unit)`: at least km↔miles, kg↔lb, and °C↔°F
   - `delete_note(title)`: returns an `is_error` result if the note doesn't exist
   - one tool of **your own design** that's useful for a student (for example a GPA calculator, word counter, or random quiz picker)
2. **Tool-call trace:** log every tool call (name, input, output, duration in ms, success or error) to `tool_trace.jsonl`, one JSON object per line.
3. **Confirm risky actions:** before running `delete_note`, ask the human `Allow delete_note('X')? [y/N]`. If they say no, send back an `is_error` tool result saying *"User denied this action"*, and check that Claude responds sensibly. This is called *human-in-the-loop*.
4. **Restrict web search:** add a `/web <domains>` command that sets `allowed_domains` on the web search tool (for example `/web python.org,docs.python.org`). Show that results only come from those sites.
5. **Show citations:** after each answer that used web search, print a numbered list of source URLs. *Hint:* walk the response's `web_search_tool_result` blocks, or the `citations` on text blocks.

## Stretch goals (pick one)

- **Tool Runner comparison:** rewrite 2 of your tools using the SDK's `@beta_tool` decorator and `client.beta.messages.tool_runner(...)`. In `NOTES.md`, compare it with your hand-written loop. What does the helper hide from you?
- **Streaming agent:** convert the loop to `client.messages.stream(...)` so the final answer streams token by token while tools still work.
- **Web fetch:** add Claude's `web_fetch` server tool so the agent can read a full page from a URL the user pastes.

## Rubric (60 points for required tasks)

| Task | Points |
|------|--------|
| 3 new tools work, with clear descriptions and strict schemas | 15 |
| Trace file is valid JSONL with timing | 10 |
| Human approval works for both "yes" and "no" | 15 |
| `/web` domain restriction works | 10 |
| Citations printed for web answers | 10 |

## Self-check questions

1. What exactly is the difference between a *chatbot* and an *agent*?
2. Why do we append `response.content` (the whole list) to `messages`, and not just the text?
3. What happens if you forget to send back a `tool_result` for one of the `tool_use` blocks?
4. Your `calculator` uses `ast` instead of `eval()`. Why? (Think: who controls the input?)
