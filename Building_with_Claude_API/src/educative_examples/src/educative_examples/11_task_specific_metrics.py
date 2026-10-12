import random
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class FieldResult:
    correct: int = 0
    total:   int = 0

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total > 0 else 0.0


@dataclass
class MetricsCollector:
    by_doc_type: dict = field(default_factory=lambda: defaultdict(FieldResult))
    by_field:    dict = field(default_factory=lambda: defaultdict(FieldResult))


def record(collector, doc_type, field_name, extracted, ground_truth):
    is_correct = extracted.strip().lower() == ground_truth.strip().lower()
    collector.by_doc_type[doc_type].total   += 1
    collector.by_doc_type[doc_type].correct += int(is_correct)
    collector.by_field[field_name].total   += 1
    collector.by_field[field_name].correct += int(is_correct)


def print_doc_type_report(collector):
    print("Document-type accuracy (sorted worst first):")
    for doc_type, result in sorted(collector.by_doc_type.items(), key=lambda kv: kv[1].accuracy):
        bar = "#" * int(result.accuracy * 20)
        print(f"  {doc_type:<25} {result.accuracy*100:>5.1f}%  [{bar:<20}]  n={result.total}")


def print_field_report(collector):
    print("Field-level accuracy (sorted worst first):")
    for field_name, result in sorted(collector.by_field.items(), key=lambda kv: kv[1].accuracy):
        bar = "#" * int(result.accuracy * 20)
        print(f"  {field_name:<20} {result.accuracy*100:>5.1f}%  [{bar:<20}]  n={result.total}")


@dataclass
class ConfidenceBucket:
    correct: int = 0
    total:   int = 0

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total > 0 else 0.0


@dataclass
class CalibrationTracker:
    buckets: dict = field(default_factory=lambda: defaultdict(ConfidenceBucket))


def record_confidence(tracker, confidence, is_correct):
    tracker.buckets[confidence].total   += 1
    tracker.buckets[confidence].correct += int(is_correct)


def calibration_report(tracker):
    print("Confidence calibration (well-calibrated: high > medium > low):")
    for level in ["high", "medium", "low"]:
        b = tracker.buckets.get(level)
        if b and b.total > 0:
            bar = "#" * int(b.accuracy * 20)
            print(f"  {level:<8}  acc={b.accuracy*100:.1f}%  n={b.total}  [{bar:<20}]")


@dataclass
class PipelineMetrics:
    total:         int = 0
    first_pass_ok: int = 0
    retried:       int = 0
    retry_ok:      int = 0
    escalated:     int = 0

    @property
    def first_pass_rate(self)  -> float: return self.first_pass_ok / self.total if self.total else 0.0
    @property
    def retry_rate(self)       -> float: return self.retried / self.total if self.total else 0.0
    @property
    def second_pass_rate(self) -> float: return self.retry_ok / self.retried if self.retried else 0.0
    @property
    def escalation_rate(self)  -> float: return self.escalated / self.total if self.total else 0.0


def print_pipeline_report(m):
    print("Pipeline stage metrics:")
    print(f"  total documents  : {m.total}")
    print(f"  first-pass rate  : {m.first_pass_rate*100:.1f}%  ({m.first_pass_ok}/{m.total})")
    print(f"  retry rate       : {m.retry_rate*100:.1f}%  ({m.retried}/{m.total})")
    print(f"  second-pass rate : {m.second_pass_rate*100:.1f}%  ({m.retry_ok}/{m.retried or 0})")
    print(f"  escalation rate  : {m.escalation_rate*100:.1f}%  ({m.escalated}/{m.total})")


if __name__ == "__main__":
    random.seed(42)

    ACCURACY_PROFILE = {
        ("digital_invoice",    "vendor_name"):  0.97,
        ("digital_invoice",    "invoice_date"): 0.98,
        ("digital_invoice",    "line_items"):   0.91,
        ("digital_invoice",    "total_amount"): 0.99,
        ("scanned_invoice",    "vendor_name"):  0.78,
        ("scanned_invoice",    "invoice_date"): 0.80,
        ("scanned_invoice",    "line_items"):   0.62,
        ("scanned_invoice",    "total_amount"): 0.75,
        ("handwritten_receipt","vendor_name"):  0.55,
        ("handwritten_receipt","invoice_date"): 0.48,
        ("handwritten_receipt","line_items"):   0.30,
        ("handwritten_receipt","total_amount"): 0.52,
    }
    VOLUMES    = {"digital_invoice": 160, "scanned_invoice": 30, "handwritten_receipt": 10}
    FIELDS     = ["vendor_name", "invoice_date", "line_items", "total_amount"]
    RETRY_RATE = {"digital_invoice": 0.85, "scanned_invoice": 0.70, "handwritten_receipt": 0.35}

    collector   = MetricsCollector()
    calibration = CalibrationTracker()
    pipeline    = PipelineMetrics()

    for doc_type, count in VOLUMES.items():
        for _ in range(count):
            pipeline.total += 1
            doc_passed_first = True
            for f in FIELDS:
                acc        = ACCURACY_PROFILE[(doc_type, f)]
                is_correct = random.random() < acc
                record(collector, doc_type, f, "correct_value" if is_correct else "wrong_value", "correct_value")
                confidence = {"digital_invoice": "high", "scanned_invoice": "medium",
                              "handwritten_receipt": "low"}[doc_type]
                if doc_type == "scanned_invoice" and random.random() < 0.30:
                    confidence = "high"
                record_confidence(calibration, confidence, is_correct)
                if not is_correct:
                    doc_passed_first = False
            if doc_passed_first:
                pipeline.first_pass_ok += 1
            else:
                pipeline.retried += 1
                if random.random() < RETRY_RATE[doc_type]:
                    pipeline.retry_ok += 1
                else:
                    pipeline.escalated += 1

    print("=== Document-type accuracy ===\n")
    print_doc_type_report(collector)
    print("\n=== Field-level accuracy ===\n")
    print_field_report(collector)
    print("\n=== Confidence calibration ===\n")
    calibration_report(calibration)
    print("\n=== Pipeline stage metrics ===\n")
    print_pipeline_report(pipeline)

    total_correct = sum(r.correct for r in collector.by_doc_type.values())
    total_items   = sum(r.total   for r in collector.by_doc_type.values())
    print(f"\nKey insight: aggregate accuracy = {total_correct/total_items*100:.1f}%")
    hw = collector.by_doc_type["handwritten_receipt"]
    print(f"  handwritten_receipt accuracy = {hw.accuracy*100:.1f}% — hidden inside the aggregate.")