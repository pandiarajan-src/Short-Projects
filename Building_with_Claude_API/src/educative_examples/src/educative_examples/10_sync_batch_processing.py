import anthropic
import json
import time
from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=anthropic_api_key)

SYSTEM = ("Extract invoice fields and return a JSON object with keys: "
          "vendor_name, invoice_total (number), issue_date (YYYY-MM-DD), "
          "due_date (YYYY-MM-DD), currency (USD/EUR/GBP/CAD/AUD). "
          "Return only the JSON object.")

SAMPLE_DOCUMENTS = [
    {"id": "inv-001",
     "text": "Vendor: Acme Ltd. Invoice Date: 2024-11-01. Due: 2024-11-30. Total: $257.50 USD."},
    {"id": "inv-002",
     "text": "Supplier: Beta Corp. Invoice Date: 2024-10-15. Due: 2024-11-14. Amount: €890.00 EUR."},
    {"id": "inv-003",
     "text": "From: Gamma Inc. Date: 2024-09-20. Payment due: 2024-10-20. Total: GBP 1,200.00."},
]


@dataclass
class ValidationResult:
    valid:  bool
    errors: list


def validate_invoice(raw_input: str, extracted: dict) -> ValidationResult:
    errors = []
    total = extracted.get("invoice_total")
    if total is not None and total < 0:
        errors.append(f"invoice_total is {total} — must be positive.")
    issue_date = extracted.get("issue_date", "")
    due_date   = extracted.get("due_date",   "")
    if issue_date and due_date and issue_date > due_date:
        errors.append(f"issue_date ({issue_date}) is after due_date ({due_date}).")
    vendor = extracted.get("vendor_name", "").strip()
    if not vendor:
        errors.append("vendor_name is empty.")
    currency = extracted.get("currency", "")
    if currency not in {"USD", "EUR", "GBP", "CAD", "AUD"}:
        errors.append(f"currency '{currency}' is not a recognized code.")
    return ValidationResult(valid=len(errors) == 0, errors=errors)


def submit_invoice_batch(documents: list[dict]) -> str:
    requests = []
    for doc in documents:
        requests.append(
            anthropic.types.message_create_params.MessageCreateParamsNonStreaming(
                custom_id=doc["id"],
                params={
                    "model":      "claude-opus-4-8",
                    "max_tokens": 512,
                    "system":     SYSTEM,
                    "messages":   [{"role": "user", "content": doc["text"]}]
                }
            )
        )
    batch = client.messages.batches.create(requests=requests)
    print(f"  Batch submitted: {batch.id} ({len(requests)} requests)")
    return batch.id


def retrieve_batch_results(batch_id: str) -> tuple[dict, dict]:
    print(f"  Polling batch {batch_id}...")
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        if batch.processing_status == "ended":
            break
        print(f"    Status: {batch.processing_status} — waiting 10s...")
        time.sleep(10)

    extracted = {}
    errors    = {}
    for result in client.messages.batches.results(batch_id):
        cid = result.custom_id
        if result.result.type == "succeeded":
            raw = result.result.message.content[0].text
            try:
                extracted[cid] = json.loads(raw)
            except json.JSONDecodeError:
                errors[cid] = "json_parse_error"
        elif result.result.type == "errored":
            errors[cid] = result.result.error.error.type
        else:
            errors[cid] = "expired"

    print(f"  Retrieved: {len(extracted)} succeeded, {len(errors)} failed")
    return extracted, errors


def batch_pipeline(documents: list[dict]) -> dict:
    print("\n--- Pass 1: full batch ---")
    batch_id              = submit_invoice_batch(documents)
    extracted, api_errors = retrieve_batch_results(batch_id)

    validation_errors = {}
    valid_results     = {}
    for doc_id, result in extracted.items():
        doc_text = next(d["text"] for d in documents if d["id"] == doc_id)
        vr = validate_invoice(doc_text, result)
        if vr.valid:
            valid_results[doc_id] = result
        else:
            validation_errors[doc_id] = vr.errors

    failed_ids = set(api_errors) | set(validation_errors)
    retry_docs = [d for d in documents if d["id"] in failed_ids]

    if retry_docs:
        print(f"\n--- Pass 2: retry batch ({len(retry_docs)} documents) ---")
        retry_batch_id             = submit_invoice_batch(retry_docs)
        retry_extracted, retry_err = retrieve_batch_results(retry_batch_id)
        for doc_id, result in retry_extracted.items():
            doc_text = next(d["text"] for d in documents if d["id"] == doc_id)
            vr = validate_invoice(doc_text, result)
            if vr.valid:
                valid_results[doc_id] = result
    else:
        print("\n  All documents passed on first pass — no retry needed.")

    return valid_results


if __name__ == "__main__":
    print("=== Batch Invoice Extraction Pipeline ===\n")
    print(f"Submitting {len(SAMPLE_DOCUMENTS)} documents...\n")

    results = batch_pipeline(SAMPLE_DOCUMENTS)

    print(f"\n=== Final results: {len(results)}/{len(SAMPLE_DOCUMENTS)} succeeded ===")
    for doc_id, fields in results.items():
        print(f"\n  {doc_id}:")
        for k, v in fields.items():
            print(f"    {k}: {v}")

    unresolved = [d["id"] for d in SAMPLE_DOCUMENTS if d["id"] not in results]
    if unresolved:
        print(f"\n  Unresolved after two passes: {unresolved}")
        print("  These documents should be flagged for human review.")
