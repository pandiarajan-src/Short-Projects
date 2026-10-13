from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Provenance:
    source:     str
    confidence: str
    timestamp:  str
    agent_role: str


@dataclass
class Finding:
    field_name: str
    value:      str
    provenance: Provenance
    finding_id: str = ""


def make_finding(
    field_name: str,
    value:      str,
    source:     str,
    confidence: str,
    agent_role: str,
    finding_id: str = ""
) -> Finding:
    ts = datetime.now(timezone.utc).isoformat()
    return Finding(
        field_name=field_name,
        value=value,
        provenance=Provenance(
            source=source,
            confidence=confidence,
            timestamp=ts,
            agent_role=agent_role
        ),
        finding_id=finding_id
    )


CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}

AUTHORITY_RANK = {
    "contract_specialist":  4,
    "legal_reviewer":       3,
    "generalist_extractor": 2,
    "fallback_extractor":   1,
}


def resolve_conflict(a: Finding, b: Finding) -> Finding:
    conf_a = CONFIDENCE_RANK.get(a.provenance.confidence, 0)
    conf_b = CONFIDENCE_RANK.get(b.provenance.confidence, 0)

    if conf_a != conf_b:
        winner = a if conf_a > conf_b else b
        print(f"  Resolved by confidence: {winner.provenance.confidence} wins")
        return winner

    auth_a = AUTHORITY_RANK.get(a.provenance.agent_role, 0)
    auth_b = AUTHORITY_RANK.get(b.provenance.agent_role, 0)

    if auth_a != auth_b:
        winner = a if auth_a > auth_b else b
        print(f"  Resolved by authority: {winner.provenance.agent_role} wins")
        return winner

    winner = a if a.provenance.timestamp > b.provenance.timestamp else b
    print(f"  Resolved by recency: most recent timestamp wins")
    return winner


def summarize_findings(findings: list[Finding]) -> str:
    lines = []
    for f in findings:
        p = f.provenance
        lines.append(
            f"Field: {f.field_name}\n"
            f"  Value:      {f.value}\n"
            f"  Confidence: {p.confidence}\n"
            f"  Source:     {p.source}\n"
            f"  Agent:      {p.agent_role}\n"
            f"  Timestamp:  {p.timestamp}"
        )
    return "\n\n".join(lines)


if __name__ == "__main__":
    print("=== Information Provenance Demo ===\n")

    finding_a = make_finding(
        field_name="clause_type",
        value="limitation_of_liability",
        source="contract_v2.pdf, clause 4.2",
        confidence="high",
        agent_role="generalist_extractor",
        finding_id="F-001"
    )

    finding_b = make_finding(
        field_name="clause_type",
        value="indemnification",
        source="contract_v2.pdf, clause 4.2",
        confidence="medium",
        agent_role="contract_specialist",
        finding_id="F-002"
    )

    print("Finding A:")
    print(f"  value={finding_a.value}, confidence={finding_a.provenance.confidence}, "
          f"agent={finding_a.provenance.agent_role}")

    print("\nFinding B:")
    print(f"  value={finding_b.value}, confidence={finding_b.provenance.confidence}, "
          f"agent={finding_b.provenance.agent_role}")

    print("\n=== Resolving conflict (confidence → authority → recency) ===")
    winner = resolve_conflict(finding_a, finding_b)
    print(f"  Winner: {winner.value} (from {winner.provenance.agent_role})")

    findings = [
        make_finding("clause_type",    "limitation_of_liability", "contract_v2.pdf §4.2",   "high",   "generalist_extractor"),
        make_finding("effective_date", "2024-09-01",              "contract_v2.pdf §1",      "high",   "contract_specialist"),
        make_finding("liability_cap",  "USD 500,000",             "contract_v2.pdf §4.2(b)", "medium", "legal_reviewer"),
    ]

    print("\n=== Findings Summary (for coordinator synthesis) ===")
    print(summarize_findings(findings))
