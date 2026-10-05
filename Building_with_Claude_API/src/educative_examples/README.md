# Educative Examples

Small, self-contained Python scripts that show core patterns for building agents with the Claude API: the agent loop, picking between fixed workflows and adaptive agents, guardrails in code, context handoff between agents, and running specialists in parallel and combining their results.

Each script is numbered in learning order and runs on its own.

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
cd Building_with_Claude_API/src/educative_examples
uv sync
```

Create a `.env` file in this folder with your API key:

```env
ANTHROPIC_API_KEY=sk-ant-...
```

## Running a script

The filenames start with a digit, so run them as files rather than with `python -m`:

```bash
uv run python src/educative_examples/0_agent_loop_ex1.py
```

## Scripts

| # | Script | Pattern | Calls the API? |
|---|--------|---------|----------------|
| 0 | [0_agent_loop_ex1.py](src/educative_examples/0_agent_loop_ex1.py) | Agent loop with tool use | Yes |
| 1 | [1_fixed-wf_vs_adaptive_agent_ex.py](src/educative_examples/1_fixed-wf_vs_adaptive_agent_ex.py) | Fixed workflow vs. adaptive agent | Yes |
| 2 | [2_Guardralis_in_code.py](src/educative_examples/2_Guardralis_in_code.py) | Guardrails in code | No |
| 3 | [3_context_handoff.py](src/educative_examples/3_context_handoff.py) | Structured context handoff | No |
| 4 | [4_ParallelWorkAndReslutSynthesis.py](src/educative_examples/4_ParallelWorkAndReslutSynthesis.py) | Parallel specialists and result synthesis | Yes |

### 0. Agent loop

A customer support agent with two tools, `get_order_status` and `cancel_order`, backed by mock data. The `run_agent` loop:

- calls `client.messages.create` with the tools and the conversation so far
- branches on `stop_reason`: returns the text on `end_turn`, runs the requested tools and sends back `tool_result` blocks on `tool_use`, and raises an error on `max_tokens`
- logs each turn, tool call, and result

It runs two cases: cancelling order `#9999`, which succeeds, and order `#5678`, which fails because it has already shipped. The second case shows how the model handles an error returned by a tool.

### 1. Fixed workflow vs. adaptive agent

Two scenarios side by side:

- **Scenario A, fixed workflow:** an invoice extraction pipeline. Every invoice gets the same single call that extracts `vendor_name`, `invoice_date`, `line_items`, and `total_amount` as JSON. The script strips a JSON code fence if the model adds one.
- **Scenario B, adaptive agent:** tool definitions for a memory-leak investigation (`analyze_heap_dump`, `get_deployment_history`, `search_recent_changes`). Which tool comes next depends on what the previous one returned, so the path can't be fixed ahead of time. The script prints the tools; it doesn't run this agent.

Use it to see when a predictable pipeline is enough and when you need an agent.

### 2. Guardrails in code

Puts business rules in the tool dispatcher instead of the prompt. Uses mock data and makes no API calls.

- **Pre-execution check:** `apply_discount` refuses rates above 20% unless `user_role="manager"`, and returns a `POLICY_VIOLATION` message.
- **Post-execution redaction:** `get_employee_record` replaces `salary`, `tax_id`, and `bank_account_number` with `[REDACTED]` before the result reaches the model.
- **Confirmation flag:** `delete_campaign` returns `CONFIRMATION_REQUIRED` with a summary of the campaign until it's called again with `confirmed=True`.

### 3. Context handoff

Shows how a coordinator hands work to a specialist sub-agent. Makes no API calls.

- `HandoffPacket` is a dataclass with `goal`, `inputs`, `constraints`, and `output_shape`.
- `packet_to_prompt` turns a packet into a prompt that asks for JSON only.
- `SAMPLE_FINANCIAL_RESULT` shows a specialist result with `data_gaps` and `sources` that record where each value came from and whether it was verified or extracted.
- `resolve_conflict` uses the value from a verified source (SEC EDGAR, Moody's, government registry) over an extracted one, and sends the conflict to a human when neither source is verified.

### 4. Parallel work and result synthesis

A due-diligence coordinator that runs three specialists (financial, legal, news) at the same time with `ThreadPoolExecutor`, then combines their output.

- `dispatch_all_specialists` sends each specialist its own handoff packet and system prompt. An exception from one specialist becomes an error result with a `data_gaps` entry, so the other results aren't lost.
- `validate_results` checks that every expected specialist returned something.
- `synthesize_results` merges the findings, collects all data gaps, flags keys that came back with conflicting values, and sets `is_complete`.
- `_parse_json` gets JSON out of the response even when it's wrapped in a code fence or surrounded by other text.

The example target is `Stripe`, FY2025.

## Notes

- All tool backends are mocks, so nothing real is looked up, cancelled, or deleted.
- The scripts that call the API use the model `claude-opus-4-8`. Change the `model=` argument to try a different model.
