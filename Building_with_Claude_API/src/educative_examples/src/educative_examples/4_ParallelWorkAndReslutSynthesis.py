import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=anthropic_api_key)

def _parse_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r'```(?:json)?\s*\n?([\s\S]+?)\n?\s*```', text)
    if m:
        text = m.group(1).strip()
    start, end = text.find('{'), text.rfind('}') + 1
    if start != -1 and end > start:
        text = text[start:end]
    return json.loads(text)


@dataclass
class HandoffPacket:
    context: str
    task:    str


def build_financial_handoff(company: str, fiscal_year: int) -> HandoffPacket:
    return HandoffPacket(
        context=f"Due diligence for {company}, FY{fiscal_year}",
        task=(
            f"Summarize the financial profile of {company} for FY{fiscal_year} based on "
            "publicly available information. Return a JSON object with these keys: "
            "revenue_estimate (string or null), growth_signal ('positive'/'neutral'/'negative'), "
            "risk_flags (list of strings), data_gaps (list of strings), sources (list of strings). "
            "Return only the JSON object."
        ),
    )


def build_legal_handoff(company: str) -> HandoffPacket:
    return HandoffPacket(
        context=f"Legal compliance review for {company}",
        task=(
            f"Assess the regulatory and legal standing of {company} based on publicly available "
            "information. Return a JSON object with these keys: "
            "compliance_signal ('clean'/'caution'/'unknown'), notes (list of strings), "
            "data_gaps (list of strings), sources (list of strings). "
            "Do not invent specific case numbers. Return only the JSON object."
        ),
    )


def build_news_handoff(company: str, days: int = 90) -> HandoffPacket:
    return HandoffPacket(
        context=f"News sentiment for {company}, last {days} days",
        task=(
            f"Summarize public news sentiment for {company} over the past {days} days. "
            "Return a JSON object with these keys: "
            "sentiment ('positive'/'neutral'/'negative'), highlights (list of up to 3 strings), "
            "data_gaps (list of strings), sources (list of strings). "
            "Return only the JSON object."
        ),
    )


def packet_to_prompt(packet: HandoffPacket) -> str:
    return f"Context: {packet.context}\n\nTask: {packet.task}"


SPECIALIST_SYSTEMS = {
    "financial": "You are a financial due diligence specialist. Return structured JSON only.",
    "legal":     "You are a legal compliance specialist. Return structured JSON only.",
    "news":      "You are a news and sentiment analyst. Return structured JSON only.",
}


def run_specialist(system: str, prompt: str) -> dict:
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )
    for block in response.content:
        if block.type == "text":
            return _parse_json(block.text)
    return {"error": "no_text_block", "data_gaps": ["specialist returned no content"]}


def dispatch_all_specialists(company: str, fiscal_year: int) -> dict:
    handoffs = {
        "financial": build_financial_handoff(company, fiscal_year),
        "legal":     build_legal_handoff(company),
        "news":      build_news_handoff(company, days=90),
    }

    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(
                run_specialist,
                SPECIALIST_SYSTEMS[name],
                packet_to_prompt(packet)
            ): name
            for name, packet in handoffs.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as exc:
                results[name] = {
                    "error":     "specialist_exception",
                    "message":   str(exc),
                    "data_gaps": [f"All {name} data unavailable, specialist raised an exception"]
                }
    return results


EXPECTED_SPECIALISTS = {"financial", "legal", "news"}


def validate_results(results: dict) -> tuple[dict, list[str]]:
    gaps      = []
    validated = {}
    for name in EXPECTED_SPECIALISTS:
        if name not in results:
            gaps.append(f"{name} specialist: no result received")
            validated[name] = None
            continue
        result = results[name]
        if "error" in result:
            gaps.append(f"{name} specialist: {result.get('message', 'unknown error')}")
        validated[name] = result
    return validated, gaps


def synthesize_results(validated: dict, report_gaps: list[str]) -> dict:
    merged_findings = {}
    aggregated_gaps = list(report_gaps)
    conflict_flags  = []

    for name, result in validated.items():
        if result is None:
            aggregated_gaps.append(f"{name}: no data received")
            continue
        for key, value in result.items():
            if key == "data_gaps":
                aggregated_gaps.extend(value)
            elif key in ("error", "message"):
                pass
            else:
                if key in merged_findings:
                    conflict_flags.append(
                        f"Conflicting values for '{key}': "
                        f"{merged_findings[key]!r} vs {value!r} (from {name})"
                    )
                else:
                    merged_findings[key] = value

    return {
        "findings":    merged_findings,
        "gaps":        aggregated_gaps,
        "conflicts":   conflict_flags,
        "is_complete": len(aggregated_gaps) == 0 and len(conflict_flags) == 0,
    }


if __name__ == "__main__":
    COMPANY     = "Stripe"
    FISCAL_YEAR = 2025

    print(f"=== Parallel specialist dispatch: {COMPANY} FY{FISCAL_YEAR} ===\n")
    print("Dispatching all three specialists simultaneously...\n")

    raw = dispatch_all_specialists(COMPANY, FISCAL_YEAR)

    print("All specialists returned:\n")
    for name, result in raw.items():
        status = "error" if "error" in result else "ok"
        keys   = [k for k in result if k not in ("data_gaps", "sources", "error", "message")]
        print(f"  {name:<12} [{status}]  finding keys: {keys}")

    print("\n=== Validation ===\n")
    validated, gaps = validate_results(raw)
    print(f"Validation gaps : {gaps or 'none'}")

    print("\n=== Synthesis ===\n")
    report = synthesize_results(validated, gaps)

    print("Merged findings:")
    for key, value in report["findings"].items():
        display = str(value)
        if len(display) > 80:
            display = display[:80] + "..."
        print(f"  {key:<22} : {display}")

    print(f"\nAggregated gaps : {report['gaps'] or 'none'}")
    print(f"Conflicts       : {report['conflicts'] or 'none'}")
    print(f"is_complete     : {report['is_complete']}")
