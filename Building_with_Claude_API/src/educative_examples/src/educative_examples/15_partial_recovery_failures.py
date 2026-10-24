from dataclasses import dataclass
from typing import Optional


@dataclass
class PartialResult:
    step:           str
    status:         str
    fields:         dict
    failure_type:   Optional[str] = None
    failure_detail: Optional[str] = None
    recovery_hint:  Optional[str] = None

    @property
    def is_complete(self) -> bool:
        return self.status == "complete"

    @property
    def is_recoverable(self) -> bool:
        return self.failure_type in ("empty_result", "partial_completion")


def extract_parties(document: str) -> list:
    return ["Party A: Acme Corp", "Party B: Beta Ltd"]


def extract_date(document: str) -> str:
    return "2024-09-01"


def extract_clauses(document: str, start_clause: int = 1) -> list:
    all_clauses = [
        "§1 Definitions", "§2 Term", "§3 Payment", "§4 Liability", "§5 Indemnification"
    ]
    return all_clauses[start_clause - 1:]


def extract_contract_fields(document: str, simulate_failure: str = "none") -> PartialResult:
    fields = {}

    try:
        if simulate_failure == "permission":
            raise PermissionError("Access denied: document vault requires elevated credentials.")
        fields["parties"]        = extract_parties(document)
        fields["effective_date"] = extract_date(document)
    except PermissionError as e:
        return PartialResult(
            step="party_and_date_extraction",
            status="failed",
            fields=fields,
            failure_type="access_failure",
            failure_detail=str(e),
            recovery_hint="Check tool permissions before retrying."
        )

    try:
        if simulate_failure == "empty":
            clause_results = []
        elif simulate_failure == "timeout":
            fields["clauses_partial"] = extract_clauses(document)[:2]
            raise TimeoutError("Clause extraction timed out after processing 2 of 5 clauses.")
        else:
            clause_results = extract_clauses(document)

        if not clause_results:
            fields["clauses"] = []
            return PartialResult(
                step="clause_extraction",
                status="partial",
                fields=fields,
                failure_type="empty_result",
                failure_detail="No clauses matched the extraction criteria.",
                recovery_hint="Treat clause absence as data; continue to validation."
            )
        fields["clauses"] = clause_results
    except TimeoutError as e:
        return PartialResult(
            step="clause_extraction",
            status="partial",
            fields=fields,
            failure_type="partial_completion",
            failure_detail=str(e),
            recovery_hint=(
                "Retry clause extraction only. "
                "Party and date fields in `fields` are valid."
            )
        )

    return PartialResult(step="full_extraction", status="complete", fields=fields)


def route_result(result: PartialResult) -> str:
    if result.is_complete:
        return "pass_to_validation"

    match result.failure_type:
        case "access_failure":
            return "escalate"
        case "empty_result":
            return "accept_as_data_gap"
        case "stale_data":
            return "escalate_or_refresh"
        case "partial_completion":
            return "retry_incomplete_steps"
        case _:
            return "escalate"


def coordinate(results: list[PartialResult]) -> list[dict]:
    routing = []
    for r in results:
        action = route_result(r)
        routing.append({
            "step":   r.step,
            "action": action,
            "fields": list(r.fields.keys()),
            "hint":   r.recovery_hint
        })
    return routing


SAMPLE_DOCUMENT = "SERVICE AGREEMENT between Acme Corp and Beta Ltd, effective 2024-09-01."

if __name__ == "__main__":
    scenarios = [
        ("none",       "Clean extraction (complete)"),
        ("permission", "Access failure during party extraction"),
        ("empty",      "Empty clause result"),
        ("timeout",    "Timeout during clause extraction (partial completion)"),
    ]

    results = []
    for failure_mode, label in scenarios:
        print(f"\n=== {label} ===")
        result = extract_contract_fields(SAMPLE_DOCUMENT, simulate_failure=failure_mode)
        results.append(result)
        print(f"  step:           {result.step}")
        print(f"  status:         {result.status}")
        print(f"  failure_type:   {result.failure_type}")
        print(f"  is_complete:    {result.is_complete}")
        print(f"  is_recoverable: {result.is_recoverable}")
        if result.recovery_hint:
            print(f"  recovery_hint:  {result.recovery_hint}")
        print(f"  fields extracted: {list(result.fields.keys())}")

    print("\n=== Coordinator Routing ===")
    routing = coordinate(results)
    for entry in routing:
        print(f"\n  step: {entry['step']}")
        print(f"    action: {entry['action']}")
        print(f"    fields: {entry['fields']}")
        if entry["hint"]:
            print(f"    hint:   {entry['hint']}")
