import anthropic
import json
from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=anthropic_api_key)

SYSTEM_PROMPT = """Extract invoice fields from the document and return a JSON object with these keys:
- vendor_name: string
- invoice_total: number (positive)
- issue_date: string (YYYY-MM-DD)
- due_date: string (YYYY-MM-DD)
- currency: string (USD, EUR, GBP, CAD, or AUD)

Return only the JSON object with no extra text."""

SAMPLE_INVOICE = """
INVOICE

Vendor: Acme Supplies Ltd.
Invoice Date: 2024-11-01
Due Date: 2024-11-30
Invoice #: INV-2024-0042

Items:
  Office supplies ........... $245.00
  Shipping .................. $12.50

Total Due: $257.50 USD
"""


@dataclass
class ValidationResult:
    valid:  bool
    errors: list


def validate_invoice(raw_input: str, extracted: dict) -> ValidationResult:
    errors = []

    total = extracted.get("invoice_total")
    if total is not None and total < 0:
        errors.append(
            f"invoice_total is {total}, but invoice totals cannot be negative. "
            "Re-read the document and extract the correct positive total.")

    issue_date = extracted.get("issue_date", "")
    due_date   = extracted.get("due_date",   "")
    if issue_date and due_date and issue_date > due_date:
        errors.append(
            f"issue_date ({issue_date}) is after due_date ({due_date}). "
            "The issue date must be on or before the due date. "
            "Check both dates in the source document.")

    vendor = extracted.get("vendor_name", "").strip()
    if not vendor:
        errors.append("vendor_name is empty. Locate the vendor or supplier name in the "
                      "document header and extract it.")

    currency = extracted.get("currency", "")
    valid_currencies = {"USD", "EUR", "GBP", "CAD", "AUD"}
    if currency not in valid_currencies:
        errors.append(f"currency is '{currency}', which is not a recognized code. "
                      f"Use one of: {', '.join(sorted(valid_currencies))}.")

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def extract_with_retry(document: str, system_prompt: str, max_retries: int = 3) -> dict | None:
    messages = [{"role": "user", "content": document}]

    for attempt in range(max_retries):
        print(f"  [attempt {attempt + 1}] Calling API...")
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            system=system_prompt,
            messages=messages
        )

        raw_text = response.content[0].text
        try:
            extracted = json.loads(raw_text)
        except json.JSONDecodeError as e:
            feedback = f"The response was not valid JSON: {e}. Return only a JSON object."
            print(f"  [attempt {attempt + 1}] JSON parse error — retrying with feedback.")
            messages.append({"role": "assistant", "content": raw_text})
            messages.append({"role": "user",      "content": feedback})
            continue

        result = validate_invoice(document, extracted)
        if result.valid:
            print(f"  [attempt {attempt + 1}] Validation passed.")
            return extracted

        if attempt == max_retries - 1:
            print(f"  [attempt {attempt + 1}] Validation failed on final attempt. Giving up.")
            return None

        error_list = "\n".join(f"{i+1}. {e}" for i, e in enumerate(result.errors))
        feedback = (
            "The following errors were found in your extraction:\n\n"
            f"{error_list}\n\n"
            "Please correct only the fields listed above and return the full updated JSON.")
        print(f"  [attempt {attempt + 1}] Validation errors — retrying with feedback.")
        messages.append({"role": "assistant", "content": raw_text})
        messages.append({"role": "user",      "content": feedback})

    return None


if __name__ == "__main__":
    print("=== Invoice Extraction with Semantic Validation ===\n")
    result = extract_with_retry(SAMPLE_INVOICE, SYSTEM_PROMPT, max_retries=3)

    if result:
        print("\nExtracted fields:")
        for k, v in result.items():
            print(f"  {k}: {v}")
    else:
        print("\nExtraction failed after all retries. Document flagged for human review.")
