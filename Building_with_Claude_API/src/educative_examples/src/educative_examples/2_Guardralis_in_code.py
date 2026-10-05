import json

# Mock helper functions (replace with real implementations in production)

def calculate_discounted_total(order_id: str, rate: float) -> float:
    base_totals = {"ORD-001": 150.00, "ORD-002": 320.00}
    base = base_totals.get(order_id, 100.00)
    return round(base * (1 - rate), 2)

def get_employee_record(employee_id: str) -> dict:
    return {
        "name": "Jane Smith", "title": "Senior Engineer",
        "department": "Engineering", "email": "jane@example.com",
        "salary": 120000, "tax_id": "XXX-XX-1234",
        "bank_account_number": "****5678"
    }

def get_campaign_summary(campaign_id: str) -> dict:
    return {"name": "Summer Sale 2024", "recipient_count": 15000, "created_date": "2024-06-01"}

def execute_campaign_deletion(campaign_id: str) -> None:
    print(f"  [executed] Campaign {campaign_id} permanently deleted.")


SENSITIVE_FIELDS = {"salary", "tax_id", "bank_account_number"}

def apply_discount(order_id: str, rate: float) -> str:
    if rate > 0.20:
        return (f"POLICY_VIOLATION: Discount rate {rate:.0%} exceeds the 20% maximum. "
                "Discounts above 20% require manager approval. The discount was not applied.")
    new_total = calculate_discounted_total(order_id, rate)
    return f"Discount of {rate:.0%} applied to order {order_id}. New total: ${new_total:.2f}."

def redact_sensitive_fields(record: dict, fields_to_redact: set) -> str:
    redacted = {k: "[REDACTED]" if k in fields_to_redact else v for k, v in record.items()}
    return json.dumps(redacted, indent=2)

def delete_campaign(campaign_id: str, confirmed: bool = False) -> str:
    campaign = get_campaign_summary(campaign_id)
    if not confirmed:
        return (f"CONFIRMATION_REQUIRED: This will permanently delete campaign "
                f"'{campaign['name']}' ({campaign['recipient_count']} recipients, "
                f"created {campaign['created_date']}). "
                "To confirm deletion, call this tool again with confirmed=true.")
    execute_campaign_deletion(campaign_id)
    return f"Campaign '{campaign['name']}' has been permanently deleted."

def dispatch_tool(name: str, input_args: dict, user_role: str = "agent") -> str:
    if name == "apply_discount":
        rate = input_args.get("rate", 0)
        if rate > 0.20 and user_role != "manager":
            return (f"POLICY_VIOLATION: Discount rate {rate:.0%} exceeds 20%. "
                    "Manager approval required.")
        return apply_discount(**input_args)
    if name == "get_employee_record":
        raw_result = get_employee_record(**input_args)
        return redact_sensitive_fields(raw_result, SENSITIVE_FIELDS)
    if name == "delete_campaign":
        return delete_campaign(**input_args)
    return f"Unknown tool: {name}"


if __name__ == "__main__":
    print("=== Pre-execution: discount within cap ===")
    print(dispatch_tool("apply_discount", {"order_id": "ORD-001", "rate": 0.10}))

    print("\n=== Pre-execution: discount exceeds cap (non-manager) ===")
    print(dispatch_tool("apply_discount", {"order_id": "ORD-001", "rate": 0.35}))

    print("\n=== Pre-execution: discount exceeds cap (manager role) ===")
    print(dispatch_tool("apply_discount", {"order_id": "ORD-001", "rate": 0.35}, user_role="manager"))

    print("\n=== Post-execution: employee record with sensitive fields redacted ===")
    print(dispatch_tool("get_employee_record", {"employee_id": "EMP-42"}))

    print("\n=== Confirmation flag: delete campaign (unconfirmed) ===")
    print(dispatch_tool("delete_campaign", {"campaign_id": "CAMP-007"}))

    print("\n=== Confirmation flag: delete campaign (confirmed) ===")
    print(dispatch_tool("delete_campaign", {"campaign_id": "CAMP-007", "confirmed": True}))
