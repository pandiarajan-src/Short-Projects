import anthropic
import json
from dotenv import load_dotenv
import os

load_dotenv()

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=anthropic_api_key)

SYSTEM = "You are a customer support agent. Help customers with order inquiries and cancellations."

TOOLS = [
    {
        "name": "get_order_status",
        "description": (
            "Look up the current status of a customer order by its ID. "
            "Use this when the customer asks about an order, shipment, or delivery."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"]
        }
    },
    {
        "name": "cancel_order",
        "description": (
            "Cancel an order that has not yet shipped. "
            "Use this only when the customer explicitly requests cancellation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"]
        }
    }
]


def get_order_status(order_id: str) -> str:
    mock_orders = {"5678": "Shipped, expected delivery June 14.",
                   "9999": "Processing, not yet dispatched."}
    return mock_orders.get(order_id, f"Order {order_id} not found.")


def cancel_order(order_id: str) -> str:
    if order_id == "9999":
        return f"Order {order_id} has been successfully cancelled."
    if order_id == "5678":
        return (f"ERROR: Order {order_id} cannot be cancelled. "
                "It has already shipped. The customer may request a return after delivery.")
    return f"ERROR: Order {order_id} not found. Cannot cancel."


def dispatch_tool(name: str, input_args: dict) -> str:
    if name == "get_order_status":
        return get_order_status(**input_args)
    if name == "cancel_order":
        return cancel_order(**input_args)
    return f"Unknown tool: {name}"


def log(event: str, **kwargs) -> None:
    parts = [f"[{event}]"]
    for key, value in kwargs.items():
        if isinstance(value, (dict, list)):
            parts.append(f"{key}={json.dumps(value, default=str)[:120]}")
        else:
            parts.append(f"{key}={value}")
    print("  ".join(parts))


def dump_messages(messages: list) -> None:
    print(f"\n=== Messages array ({len(messages)} turns) ===")
    for i, msg in enumerate(messages):
        role    = msg["role"]
        content = msg["content"]
        if isinstance(content, str):
            print(f"  [{i}] {role}: {content[:100]}")
        elif isinstance(content, list):
            for block in content:
                btype = block.get("type") if isinstance(block, dict) else block.type
                if btype == "text":
                    text = block.get("text") if isinstance(block, dict) else block.text
                    print(f"  [{i}] {role}/text: {text[:100]}")
                elif btype == "tool_use":
                    name = block.get("name") if isinstance(block, dict) else block.name
                    print(f"  [{i}] {role}/tool_use: {name}")
                elif btype == "tool_result":
                    cv = block.get("content") if isinstance(block, dict) else block.content
                    print(f"  [{i}] {role}/tool_result: {str(cv)[:100]}")
    print("=== End ===\n")


def run_agent(task: str) -> str:
    messages = [{"role": "user", "content": task}]
    turn = 0

    while True:
        turn += 1
        log("api_call", turn=turn, messages=len(messages))

        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages
        )

        log("stop_reason", turn=turn, reason=response.stop_reason,
            response_id=response.id, output_tokens=response.usage.output_tokens)

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
                    log("tool_call", name=block.name, input=block.input)
                    result = dispatch_tool(block.name, block.input)
                    log("tool_result", name=block.name, result=result)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        if response.stop_reason == "max_tokens":
            log("error", reason="max_tokens", output_tokens=response.usage.output_tokens)
            raise RuntimeError(f"Response truncated after {response.usage.output_tokens} tokens.")

        if response.stop_reason == "stop_sequence":
            for block in response.content:
                if block.type == "text":
                    return block.text
            return ""


if __name__ == "__main__":
    print("=== Cancelling order #9999 (success path) ===")
    answer = run_agent("Please cancel my order #9999.")
    print(f"\nFinal answer: {answer}")

    print("\n=== Cancelling order #5678 (error path) ===")
    answer = run_agent("Please cancel my order #5678.")
    print(f"\nFinal answer: {answer}")
