import json
import re
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


CLASSIFY_SYSTEM = """You are a support ticket classifier for Meridian Cloud.

Classify each ticket into exactly one of these categories:
  - billing_dispute: customer contests a charge or invoice total
  - billing_inquiry: customer asks about charges without disputing them
  - payment_failure: a payment attempt was declined or could not be processed
  - technical_error: a product or API is not working as expected
  - account_access: login, password, or permission issues
  - feature_request: customer asks for a capability that does not exist yet
  - other: does not fit the above categories

Return a JSON object with fields "category" and "confidence" (high/medium/low).

Examples:

Input: "I was charged $120 but my plan is $80/month. Please explain."
Output: {"category": "billing_dispute", "confidence": "high"}

Input: "When does my billing cycle reset each month?"
Output: {"category": "billing_inquiry", "confidence": "high"}

Input: "My card ending in 4421 was declined when I tried to upgrade."
Output: {"category": "payment_failure", "confidence": "high"}

Input: "The /v2/events endpoint has been returning 503 errors since yesterday."
Output: {"category": "technical_error", "confidence": "high"}

Input: "I need to add a team member but the invite button is greyed out."
Output: {"category": "account_access", "confidence": "medium"}

Return only the JSON object."""


def classify_ticket(message: str) -> dict:
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=128,
        system=CLASSIFY_SYSTEM,
        messages=[{"role": "user", "content": message}]
    )
    for block in response.content:
        if block.type == "text":
            return _parse_json(block.text)
    raise ValueError("No text block in response")


TRIAGE_SYSTEM = """You are a medical records triage assistant.

Given a patient intake form, assess urgency level (critical/urgent/routine) and
recommend the appropriate care pathway.

Think through the following before giving your answer:
1. Identify any symptoms that indicate a time-sensitive condition.
2. Check for contraindications with any listed medications.
3. Note any missing required fields that would affect the assessment.
Then state your urgency level and recommended pathway.

Return a JSON object with:
  - "reasoning": string (your step-by-step analysis, 2-4 sentences)
  - "urgency": string ("critical", "urgent", or "routine")
  - "pathway": string (one of: "emergency", "same-day", "scheduled", "telemedicine")

Example:
Input: "Patient reports chest pain (8/10) for 2 hours. Medications: metformin. No allergies."
Output: {
  "reasoning": "Chest pain at 8/10 severity for 2+ hours is a potential cardiac event. Metformin is not a contraindication. All required fields present.",
  "urgency": "critical",
  "pathway": "emergency"
}

Return only the JSON object."""


def triage_patient(intake_form: str) -> dict:
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=512,
        system=TRIAGE_SYSTEM,
        messages=[{"role": "user", "content": intake_form}]
    )
    for block in response.content:
        if block.type == "text":
            return _parse_json(block.text)
    raise ValueError("No text block in response")


if __name__ == "__main__":
    print("=== Few-shot ticket classifier ===\n")

    tickets = [
        "I was charged twice this month — two identical $99 charges on the 1st and 2nd.",
        "How do I export my invoice as a PDF?",
        "Our webhook endpoint stopped receiving events at 14:00 UTC today.",
        "Can you add bulk CSV import for contacts? We need it for our migration.",
        "I can't log in — it says my account is suspended but I received no email about it.",
    ]

    for ticket in tickets:
        result = classify_ticket(ticket)
        print(f"Ticket     : {ticket[:70]}{'...' if len(ticket) > 70 else ''}")
        print(f"Category   : {result.get('category')}")
        print(f"Confidence : {result.get('confidence')}")
        print()

    print("=== Chain-of-thought triage ===\n")

    intakes = [
        "Patient: 67F. Sudden severe headache (10/10) starting 20 min ago. No prior history. Medications: lisinopril. No allergies.",
        "Patient: 34M. Mild sore throat for 3 days, no fever. Medications: none. No allergies. Requesting same-day appointment.",
        "Patient: 52F. Chest tightness and shortness of breath for 45 min. Medications: aspirin, atorvastatin. No allergies.",
    ]

    for intake in intakes:
        result = triage_patient(intake)
        reasoning = result.get("reasoning", "")
        print(f"Intake     : {intake[:80]}{'...' if len(intake) > 80 else ''}")
        print(f"Urgency    : {result.get('urgency')}")
        print(f"Pathway    : {result.get('pathway')}")
        print(f"Reasoning  : {reasoning[:130]}{'...' if len(reasoning) > 130 else ''}")
        print()