import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=anthropic_api_key)

SYSTEM = """You are a contract review agent. Review clauses and extract structured information.
When you encounter conflicting evidence, a policy gap, low confidence after retries,
or an irreversible action requiring approval, use the escalate_for_review tool."""

ESCALATE_TOOL = {
    "name": "escalate_for_review",
    "description": (
        "Halt the current workflow and surface an approval packet to a human reviewer. "
        "Use this tool when the action ahead is irreversible, when the situation is "
        "outside the defined policy boundaries, when evidence conflicts and cannot be "
        "resolved, or when confidence is below the required threshold. "
        "Do not use this tool for routine errors or retryable failures."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "case_reference":    {"type": "string"},
            "escalation_reason": {"type": "string"},
            "evidence_summary":  {"type": "string"},
            "decision_required": {"type": "string"},
            "next_step":         {"type": "string"}
        },
        "required": [
            "case_reference",
            "escalation_reason",
            "decision_required",
            "next_step"
        ]
    }
}

GET_CLAUSE_TOOL = {
    "name": "get_clause_text",
    "description": "Retrieve the full text of a specific clause from the contract by clause number.",
    "input_schema": {
        "type": "object",
        "properties": {
            "clause_number": {"type": "string", "description": "e.g. '4.2'"}
        },
        "required": ["clause_number"]
    }
}

CLAUSES = {
    "4.2": (
        "Party A shall indemnify and hold harmless Party B from and against any claims, "
        "damages, losses, and expenses. Notwithstanding the foregoing, in no event shall "
        "either party's aggregate liability exceed the amounts paid in the preceding twelve months."
    )
}


def format_escalation_packet(tool_input: dict) -> str:
    return (
        "=== ESCALATION PACKET ===\n"
        f"CASE REFERENCE\n  {tool_input['case_reference']}\n\n"
        f"ESCALATION REASON\n  {tool_input['escalation_reason']}\n\n"
        f"EVIDENCE\n  {tool_input.get('evidence_summary', 'None provided')}\n\n"
        f"DECISION REQUIRED\n  {tool_input['decision_required']}\n\n"
        f"NEXT STEP\n  {tool_input['next_step']}\n"
        "=== END PACKET ==="
    )


def handle_escalation(tool_input: dict) -> str:
    packet = format_escalation_packet(tool_input)
    print("\n" + packet + "\n")
    reviewer_decision = (
        "classify as (c) mixed — clause contains both indemnification "
        "and limitation of liability elements"
    )
    print(f"[Simulated reviewer decision]: {reviewer_decision}\n")
    return reviewer_decision


def dispatch_tool(name: str, tool_input: dict) -> str:
    if name == "get_clause_text":
        return CLAUSES.get(tool_input["clause_number"], "Clause not found.")
    if name == "escalate_for_review":
        return handle_escalation(tool_input)
    return f"Unknown tool: {name}"


def run_review_agent(task: str) -> str:
    messages = [{"role": "user", "content": task}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=4096,
            system=SYSTEM,
            tools=[GET_CLAUSE_TOOL, ESCALATE_TOOL],
            messages=messages
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    return block.text
            return ""

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [tool_call] {block.name}({json.dumps(block.input)})")
                    result = dispatch_tool(block.name, block.input)
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     result
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        if response.stop_reason == "max_tokens":
            raise RuntimeError("Response truncated.")

        return ""


if __name__ == "__main__":
    task = (
        "Review clause 4.2 of contract CLM-2024-4471 (policy POL-2024-0091-B, "
        "claimant Torres, Alejandra). "
        "Two prior passes produced conflicting classifications: "
        "Pass 1 called it an indemnification clause; Pass 2 called it a limitation of liability. "
        "Classify the clause and escalate if the conflict cannot be resolved."
    )

    print("=== Contract Review Agent — Escalation Demo ===\n")
    print(f"Task: {task}\n")
    final = run_review_agent(task)
    print(f"Final agent response:\n{final}")
