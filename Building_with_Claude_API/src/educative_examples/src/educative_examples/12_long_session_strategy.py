import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=anthropic_api_key)

SUMMARIZE_AT = 2_00   # trigger summarization at this many input tokens
DELEGATE_AT  = 3_00   # trigger sub-session delegation at this many input tokens

SYSTEM = """You are a claim investigation assistant working through a multi-step insurance claim review.
After each step, update the scratchpad provided in the user message.

When the conversation exceeds 30 turns or 2,00 input tokens, produce a structured
summary of completed steps before continuing. The summary must include:
- All case facts verbatim (do not abbreviate IDs, amounts, or dates)
- A numbered list of completed steps with their outcomes
- All active constraints that still apply
- All unresolved findings and open questions

After the summary, continue with the current step as if the summary were the complete
prior context."""

INITIAL_SCRATCHPAD = """=== SESSION SCRATCHPAD (updated after each action) ===

## Anchored facts
Case ID:    CLM-2024-4471
Policy ref: POL-2024-0091-B
Claimant:   Torres, Alejandra

## Progress
Step 1 (pending): Retrieve policy terms

## Current finding
None yet.

## Open questions
- Does coverage apply to the reported incident type?
=== END SCRATCHPAD ==="""


def run_turn(messages: list, system: str) -> tuple[str, int]:
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        system=system,
        messages=messages
    )
    input_tokens = response.usage.input_tokens
    text = response.content[0].text
    return text, input_tokens


def summarize_session(messages: list, system: str) -> list:
    compress_request = (
        "The session is approaching its context limit. "
        "Produce a structured summary of everything completed so far, "
        "preserving all case facts verbatim, all decisions, all active constraints, "
        "and all open questions. Then continue from where we left off."
    )
    messages_with_request = messages + [{"role": "user", "content": compress_request}]
    summary_text, _ = run_turn(messages_with_request, system)
    return [{"role": "user", "content": summary_text}]


def build_handoff_packet(
    case_facts:         dict,
    completed_steps:    list,
    active_constraints: list,
    open_questions:     list,
    current_step:       str
) -> str:
    facts_block       = "\n".join(f"{k}: {v}" for k, v in case_facts.items())
    steps_block       = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(completed_steps))
    constraints_block = "\n".join(f"  - {c}" for c in active_constraints)
    questions_block   = "\n".join(f"  - {q}" for q in open_questions)

    return (
        "=== HANDOFF PACKET ===\n"
        f"CASE FACTS (verbatim):\n{facts_block}\n\n"
        f"COMPLETED STEPS:\n{steps_block}\n\n"
        f"ACTIVE CONSTRAINTS:\n{constraints_block}\n\n"
        f"OPEN QUESTIONS:\n{questions_block}\n\n"
        f"CURRENT STEP: {current_step}\n"
        "=== END HANDOFF PACKET ==="
    )


def delegate_to_sub_session(last_reply: str, messages: list) -> None:
    print("\n[DELEGATION] Remaining work handed off to a fresh sub-session.")
    print("  The sub-session would receive a handoff packet containing:")
    print("  - All anchored case facts (verbatim)")
    print("  - Completed steps and their outcomes")
    print("  - Active constraints")
    print("  - Open questions")
    print("  - The current step to resume from")


def session_loop(task: str, system: str) -> None:
    messages = [{"role": "user", "content": task}]

    while True:
        reply, used = run_turn(messages, system)
        messages.append({"role": "assistant", "content": reply})
        print(f"  [turn complete] input_tokens={used}")
        print(f"  Reply excerpt: {reply[:120]}...\n")

        if used >= DELEGATE_AT:
            print(f"[{used} tokens] Threshold reached — delegating remaining work to sub-session.")
            delegate_to_sub_session(reply, messages)
            break

        if used >= SUMMARIZE_AT:
            print(f"[{used} tokens] Threshold reached — summarizing completed work.")
            messages = summarize_session(messages, system)

        next_input = input("Next instruction (or 'done'): ").strip()
        if next_input.lower() == "done":
            print("Session complete.")
            break
        messages.append({"role": "user", "content": next_input})


if __name__ == "__main__":
    print("=== Long Session Health Demo ===\n")
    print(f"  SUMMARIZE_AT = {SUMMARIZE_AT:,} tokens")
    print(f"  DELEGATE_AT  = {DELEGATE_AT:,} tokens\n")

    print("=== Handoff Packet Example ===")
    packet = build_handoff_packet(
        case_facts={
            "Case ID":    "CLM-2024-4471",
            "Policy ref": "POL-2024-0091-B",
            "Claimant":   "Torres, Alejandra"
        },
        completed_steps=[
            "Retrieved policy terms — coverage confirmed for incident type",
            "Requested adjuster notes — received and attached"
        ],
        active_constraints=[
            "Exclusion EXCL-48B must be checked before approving payout",
            "Pre-approval required for repair costs over $5,000"
        ],
        open_questions=[
            "Were repair costs pre-approved by the insurer?"
        ],
        current_step="Step 3: Review adjuster notes for documented exclusion flags"
    )
    print(packet)

    print("\n\nTo run the interactive session loop, uncomment the line below:")
    print("# session_loop(INITIAL_SCRATCHPAD, SYSTEM)")
