import json


# ─── Mock billing infrastructure (no real API needed) ─────────────────────────

class BillingAPIUnavailable(Exception):
    pass


class _BillingAPI:
    ACCOUNTS = {
        "ACC-00100": [
            {"date": "2025-03-01", "amount": 99.00,  "description": "Pro plan — monthly"},
            {"date": "2025-04-01", "amount": 99.00,  "description": "Pro plan — monthly"},
        ],
        "ACC-00200": [],          # exists but no charges
        # ACC-00300 triggers a simulated API outage — see fetch()
    }

    def fetch(self, account_id: str) -> list[dict]:
        if account_id == "ACC-00300":
            raise BillingAPIUnavailable("connection to billing service timed out after 10s")
        return self.ACCOUNTS.get(account_id, [])


billing_api = _BillingAPI()


# ─── Tool function: four structured failure categories ─────────────────────────

def get_billing_history(account_id: str, caller_role: str = "agent") -> str:
    if not account_id.startswith("ACC-"):
        return (
            "VALIDATION_ERROR: account_id must begin with 'ACC-' (received: "
            f"'{account_id}'). Example of a valid value: 'ACC-00123'."
        )

    if caller_role not in ("billing_admin", "support_tier2"):
        return (
            "PERMISSION_DENIED: Billing history requires billing_admin or support_tier2 "
            f"role. Caller role '{caller_role}' is not authorized. "
            "Escalate to a billing team member to retrieve this information."
        )

    try:
        records = billing_api.fetch(account_id)
    except BillingAPIUnavailable as exc:
        return (
            f"ACCESS_FAILURE: Billing API is unreachable ({exc}). "
            "The lookup was attempted but could not complete. "
            "Treat this billing history as unknown, not as empty."
        )

    if not records:
        return (
            f"RESULT: Billing history for account {account_id} is empty. "
            "The account exists and the API is accessible: there are no charges on record."
        )

    return json.dumps({"account_id": account_id, "records": records})


# ─── Specialist wrapper: data_gaps propagation ────────────────────────────────

def run_billing_specialist(account_id: str) -> dict:
    # Specialists run with billing_admin access via their authorization context.
    result = get_billing_history(account_id, caller_role="billing_admin")

    if result.startswith("ACCESS_FAILURE"):
        return {
            "billing_records": None,
            "data_gaps":       [f"billing history: {result}"],
            "status":          "access_failure",
        }

    if result.startswith("PERMISSION_DENIED"):
        return {
            "billing_records": None,
            "data_gaps":       [f"billing history: {result}"],
            "status":          "permission_denied",
        }

    if result.startswith("RESULT"):
        return {
            "billing_records": [],
            "data_gaps":       [],
            "status":          "empty",
        }

    records = json.loads(result)
    return {
        "billing_records": records["records"],
        "data_gaps":       [],
        "status":          "found",
    }


if __name__ == "__main__":
    print("=== Four failure categories in get_billing_history ===\n")

    cases = [
        ("12345",     "billing_admin",  "validation error — bad account_id format"),
        ("ACC-00100", "support_tier1",  "permission denied — unauthorized role"),
        ("ACC-00300", "billing_admin",  "access failure — API unreachable"),
        ("ACC-00200", "billing_admin",  "empty result — account exists, no charges"),
        ("ACC-00100", "billing_admin",  "success — account with two charge records"),
    ]

    for account_id, caller_role, label in cases:
        result = get_billing_history(account_id, caller_role)
        prefix = result.split(":")[0].strip()
        print(f"[{label}]")
        print(f"  prefix  : {prefix}")
        print(f"  content : {result[:110]}{'...' if len(result) > 110 else ''}")
        print()

    print("=== data_gaps propagation through run_billing_specialist ===\n")

    specialist_cases = [
        ("ACC-00100", "success — records found"),
        ("ACC-00200", "empty — no charges on record"),
        ("ACC-00300", "access failure — propagated to data_gaps"),
    ]

    for account_id, label in specialist_cases:
        r = run_billing_specialist(account_id)
        print(f"[{label}]")
        print(f"  billing_records : {r['billing_records']}")
        print(f"  data_gaps       : {r['data_gaps']}")
        print(f"  status          : {r['status']}")
        print()

    print("Key distinctions:")
    print("  None  in billing_records → access failure (unknown — could not check)")
    print("  []    in billing_records → empty result  (checked — found nothing)")
    print("  [...] in billing_records → success       (checked — records returned)")
