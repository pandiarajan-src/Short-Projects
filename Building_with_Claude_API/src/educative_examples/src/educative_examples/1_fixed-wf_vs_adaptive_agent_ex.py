import json
import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=anthropic_api_key)


# ─── Scenario A: Fixed workflow — invoice extraction pipeline ──────────────────

def extract_invoice_fields(invoice_text: str) -> dict:
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=500,
        system=(
            "You are an invoice parser. Extract the following fields from the invoice text "
            "and return them as JSON: vendor_name, invoice_date, line_items (list of strings), total_amount. "
            "Return only the JSON object, no other text."
        ),
        messages=[{"role": "user", "content": invoice_text}]
    )
    for block in response.content:
        if block.type == "text":
            text = block.text.strip()
            # The model sometimes wraps the JSON in a ```json ... ``` fence
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(text)
    return {}


def run_pipeline(invoices: list[str]) -> list[dict]:
    results = []
    for invoice in invoices:
        fields = extract_invoice_fields(invoice)
        results.append(fields)
    return results


# ─── Scenario B: Adaptive agent — memory leak investigation ───────────────────

TOOLS = [
    {
        "name": "analyze_heap_dump",
        "description": (
            "Analyze a heap dump snapshot for a given service and time window. "
            "Use this first to identify which object types or allocations are growing abnormally."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "service":    {"type": "string"},
                "start_time": {"type": "string"},
                "end_time":   {"type": "string"}
            },
            "required": ["service", "start_time", "end_time"]
        }
    },
    {
        "name": "get_deployment_history",
        "description": (
            "Retrieve deployment events for a service in a time window. "
            "Use when the heap analysis points to a growth pattern that started at a specific time."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "service":    {"type": "string"},
                "start_time": {"type": "string"},
                "end_time":   {"type": "string"}
            },
            "required": ["service", "start_time", "end_time"]
        }
    },
    {
        "name": "search_recent_changes",
        "description": (
            "Search code changes merged around a specific deployment. "
            "Use when a deployment correlates with the onset of the memory spike."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "deployment_id": {"type": "string"},
                "keyword":       {"type": "string"}
            },
            "required": ["deployment_id"]
        }
    }
]


if __name__ == "__main__":
    sample_invoices = [
        (
            "INVOICE\n"
            "Vendor: Acme Corp\n"
            "Date: 2025-03-15\n"
            "Items:\n"
            "  Widget x10: $200.00\n"
            "  Shipping: $15.00\n"
            "Total: $215.00"
        ),
        (
            "INVOICE\n"
            "Vendor: Globex Industries\n"
            "Date: 2025-03-22\n"
            "Items:\n"
            "  Server license: $1,200.00\n"
            "  Support plan: $300.00\n"
            "Total: $1,500.00"
        ),
    ]

    print("=== Scenario A: Fixed workflow (invoice extraction pipeline) ===\n")
    print(f"Processing {len(sample_invoices)} invoices...\n")

    results = run_pipeline(sample_invoices)
    for i, result in enumerate(results, 1):
        print(f"Invoice {i}:")
        print(f"  vendor_name  : {result.get('vendor_name')}")
        print(f"  invoice_date : {result.get('invoice_date')}")
        print(f"  line_items   : {result.get('line_items')}")
        print(f"  total_amount : {result.get('total_amount')}")
        print()

    print("=== Scenario B: Adaptive agent (memory leak investigation) ===\n")
    print(f"{len(TOOLS)} tools registered for the investigation agent:\n")
    for tool in TOOLS:
        first_sentence = tool["description"].split(".")[0] + "."
        print(f"  {tool['name']}")
        print(f"    {first_sentence}")
        print()
    print("Contrast: For this task, the next tool call cannot be determined before")
    print("the previous result arrives; the path is decided at runtime.")
    print("The fixed pipeline above runs the same step for every invoice, every time.")