# Assignment 1: Your First Chat Agent

**Reference code:** `examples/a1_chat_agent.py` · **Time:** about 2 hours · **Uses:** Claude API (`anthropic`)

## Goal

Build a command-line chat agent called **Study Buddy** that remembers the conversation, streams its replies, and reports how many tokens it has used.

## Concepts you'll learn

| Concept | What it means |
|---------|---------------|
| **Messages API** | Every request is `client.messages.create(model=..., messages=[...])`. One endpoint, one request, one response. |
| **The API is stateless** | Claude does not remember earlier requests. *You* store the history in a list and send it all every time. That list *is* the agent's short-term memory. |
| **Roles** | `messages` alternates `user` and `assistant` turns. The `system` prompt sits outside the list and sets the agent's persona and rules. |
| **Content blocks** | A response's `content` is a **list** of blocks (`text`, `thinking`, `tool_use`, ...). Always check `block.type` before reading `block.text`. |
| **Streaming** | `client.messages.stream(...)` yields text as it's generated, so users aren't left waiting. `stream.get_final_message()` gives you the full message at the end. |
| **Tokens and stop reasons** | `response.usage` tells you input and output tokens (that's your cost). `stop_reason` tells you *why* Claude stopped: `end_turn`, `max_tokens`, `tool_use`, `refusal`, and so on. |
| **Effort** | `output_config={"effort": "low"}` asks for a quick, cheap answer. `high` means think harder. |

## Step 0: Run the reference

```bash
uv run python examples/a1_chat_agent.py
```

Try this conversation:

```
you > My name is Priya and I'm learning SQL.
you > What's a JOIN? Explain with an example.
you > What's my name and what am I learning?      ← memory works
you > /usage
you > /reset
you > What's my name?                              ← memory is gone
```

Read the code and find the exact line where memory is stored. Then answer this question in `NOTES.md`: *what would happen if you deleted that line?*

## Required tasks

Copy `examples/a1_chat_agent.py` to `solutions/a1_<yourname>.py` and add these features:

1. **Persona switcher:** a `/persona <name>` command that switches between at least 3 system prompts (for example `tutor`, `interviewer` for mock technical interviews, `eli5`). Show the active persona in the input prompt: `you [tutor] > `.
2. **Save and load conversations:** `/save <file>` writes `agent.messages` to a JSON file, and `/load <file>` restores it, so you can quit, restart, and keep chatting. *Hint:* `final.content` is a list of SDK objects. Store plain text with `{"role": "assistant", "content": text}`, or convert blocks with `block.model_dump()`.
3. **Cost meter:** after every reply, print one grey line such as `[in: 412 tok | out: 96 tok | session ≈ $0.0011]`. Keep the prices in a dict, and read the model's per-token prices from https://platform.claude.com/docs/en/about-claude/pricing.
4. **Context guard:** if the conversation goes over 20 messages, automatically drop the *oldest* user/assistant **pair** before sending. Print a notice when you do. *Question for `NOTES.md`:* why must you drop a pair and not a single message?
5. **Robustness:** the program must never crash with a Python traceback. Handle empty input, Ctrl+C, network errors, and a bad API key (test this by putting a wrong key in `.env`).

## Stretch goals (pick one)

- **Summarize instead of drop:** when the history gets long, ask Claude to summarize the oldest 10 messages into one short message and replace them with it.
- **Model comparison:** add `/model <id>` and compare `claude-haiku-5-5` with `claude-opus-5-5` on the same 3 questions. Record the speed, tokens, and quality in `NOTES.md`.
- **Structured output:** add `/quiz <topic>`, which returns exactly 3 multiple-choice questions as JSON (use `output_config={"format": ...}` with a JSON schema). Render them nicely and score the user's answers.

## Rubric (60 points for required tasks)

| Task | Points |
|------|--------|
| Persona switcher works and is shown in the prompt | 12 |
| Save and load round-trips a real conversation | 12 |
| Cost meter is correct for the model you used | 12 |
| Context guard drops pairs and the conversation still works | 12 |
| No tracebacks under the 4 failure cases | 12 |

## Self-check questions

1. Why is it called a "chat *agent*" if it can't take any actions yet? (Hint: it isn't really an agent yet. That's assignment 2.)
2. Where does the system prompt go: inside `messages` or outside?
3. What does `stop_reason == "max_tokens"` mean, and what should your program do about it?
