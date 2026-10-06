import json
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=anthropic_api_key)


SYSTEM = """You are an order status classifier.

Classify the intent and urgency of each customer message. Use the customer's
own words to judge urgency; do not assume urgency from topic alone.

  - "intent" is one of: "status_check", "cancel", "modify_address", "other"
  - "urgency" is one of: "high", "normal", "low\""""


class OrderIntent(BaseModel):
    order_id: str | None
    intent: str
    urgency: str


def classify_order_intent(user_message: str) -> OrderIntent:
    response = client.messages.parse(
        model="claude-opus-4-8",
        max_tokens=256,
        system=SYSTEM,
        messages=[{"role": "user", "content": user_message}],
        output_format=OrderIntent
    )
    return response.parsed_output


EXTRACT_SYSTEM = """Extract invoice fields from the text.
Use the vendor's own wording for line items; do not summarize or abbreviate them."""


class Invoice(BaseModel):
    vendor_name: str
    invoice_date: str
    line_items: list[str]
    total_amount: str


def extract_invoice(text: str) -> Invoice:
    response = client.messages.parse(
        model="claude-opus-4-8",
        max_tokens=512,
        system=EXTRACT_SYSTEM,
        messages=[{"role": "user", "content": text}],
        output_format=Invoice
    )
    return response.parsed_output


FLIGHT_TOOL = {
    "name": "search_flights",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "destination": {"type": "string"},
            "date": {"type": "string", "format": "date"}
        },
        "required": ["destination", "date"],
        "additionalProperties": False
    }
}

TRIP_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "next_steps": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["summary", "next_steps"],
    "additionalProperties": False
}


def plan_trip(request: str) -> dict:
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=512,
        messages=[{"role": "user", "content": request}],
        output_config={"format": {"type": "json_schema", "schema": TRIP_SCHEMA}},
        tools=[FLIGHT_TOOL]
    )
    tool_call = next((b for b in response.content if b.type == "tool_use"), None)
    text_block = next((b for b in response.content if b.type == "text"), None)
    return {
        "tool_call": {"name": tool_call.name, "input": tool_call.input} if tool_call else None,
        "summary": json.loads(text_block.text) if text_block else None
    }


if __name__ == "__main__":
    print("=== classify_order_intent: JSON Outputs with a Pydantic model ===\n")

    classify_cases = [
        "I was charged $120 but my plan is only $80/month. Can you explain this?",
        "URGENT: Please cancel order ORD-4421 immediately, I ordered the wrong size.",
    ]
    for msg in classify_cases:
        result = classify_order_intent(msg)
        print(f"Input  : {msg[:70]}{'...' if len(msg) > 70 else ''}")
        print(f"Output : {result.model_dump_json()}")
        print()

    print("=== extract_invoice: JSON Outputs with a Pydantic model ===\n")

    invoice = (
        "INVOICE\n"
        "Vendor: Nexus Technology Partners\n"
        "Invoice Date: April 15, 2025\n"
        "Line Items:\n"
        "  Cloud hosting (monthly): $450.00\n"
        "  Managed backup service: $75.00\n"
        "Total Due: $525.00"
    )
    result = extract_invoice(invoice)
    print(result.model_dump_json(indent=2))
    print()

    print("=== plan_trip: JSON Outputs combined with strict tool use ===\n")
    result = plan_trip("Help me plan a trip to Paris departing May 15, 2026.")
    print(json.dumps(result, indent=2))
