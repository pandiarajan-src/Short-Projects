import json
from dataclasses import dataclass


@dataclass
class HandoffPacket:
    goal:         str
    inputs:       dict
    constraints:  dict
    output_shape: dict


def build_financial_handoff(company: str, fiscal_year: int) -> HandoffPacket:
    return HandoffPacket(
        goal=(
            "Assess the financial health of the target company for acquisition due diligence. "
            "Focus on solvency, growth trajectory, and near-term debt obligations."
        ),
        inputs={"company_name": company, "fiscal_year": fiscal_year, "currency": "USD"},
        constraints={
            "time_range":   f"{fiscal_year - 2} to {fiscal_year}",
            "data_sources": ["financial_statements", "credit_ratings", "debt_schedule"],
            "depth":        "summary, no raw data dumps"
        },
        output_shape={
            "key_metrics": "dict — revenue, gross_margin, debt_to_equity, cash_position",
            "risk_flags":  "list[str] — any financial red flags identified",
            "data_gaps":   "list[str] — metrics that could not be retrieved and why",
            "sources":     "list[str] — data sources used and their type (verified/extracted)"
        }
    )


def packet_to_prompt(packet: HandoffPacket) -> str:
    return (
        f"Goal: {packet.goal}\n\n"
        f"Inputs:\n{json.dumps(packet.inputs, indent=2)}\n\n"
        f"Constraints:\n{json.dumps(packet.constraints, indent=2)}\n\n"
        f"Required output fields (return as JSON):\n{json.dumps(packet.output_shape, indent=2)}\n\n"
        "Return only the JSON object. Do not include commentary outside the JSON."
    )


def resolve_conflict(value_a: str, source_a: str, value_b: str, source_b: str) -> str:
    verified_types = {"SEC EDGAR filing", "Moody's API", "government registry"}
    a_is_verified  = any(t in source_a for t in verified_types)
    b_is_verified  = any(t in source_b for t in verified_types)

    if a_is_verified and not b_is_verified:
        return value_a
    if b_is_verified and not a_is_verified:
        return value_b
    return (f"CONFLICT: {value_a} ({source_a}) vs {value_b} ({source_b})"
            " — requires human review")


SAMPLE_FINANCIAL_RESULT = {
    "key_metrics": {"revenue_2025": "$142M", "gross_margin": "61%",
                    "debt_to_equity": "0.43", "cash_position": "$18M"},
    "risk_flags":  ["Debt maturity spike in Q3 2026: $24M due within 18 months"],
    "data_gaps":   ["Profitability breakdown by product line — requires premium data subscription"],
    "sources":     ["financial_statements: SEC EDGAR filing (verified)",
                    "credit_ratings: Moody's API (verified)",
                    "debt_schedule: Annual report PDF page 44 (extracted)"]
}


if __name__ == "__main__":
    packet = build_financial_handoff("Acme Corp", 2025)

    print("=== Handoff Packet Prompt ===")
    print(packet_to_prompt(packet))

    print("\n=== Sample Specialist Result (with provenance) ===")
    print(json.dumps(SAMPLE_FINANCIAL_RESULT, indent=2))

    print("\n=== Conflict Resolution: verified vs. extracted source ===")
    result = resolve_conflict("$142M", "SEC EDGAR filing",
                              "$130M", "Annual report PDF page 44 (extracted)")
    print(f"  Winner: {result}")

    print("\n=== Conflict Resolution: both extracted (escalate) ===")
    result = resolve_conflict("$142M", "Annual report PDF (extracted)",
                              "$130M", "Press release (extracted)")
    print(f"  Outcome: {result}")
