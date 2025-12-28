import json
from typing import Dict, List

import pytest

from src.ai.pii_scrubber import detect_pii, redact_pii


def load_jsonl(path: str) -> List[Dict]:
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data.append(json.loads(line))
    return data


def _canon(s: str) -> str:
    # Canonicalize tokens for fair matching across formatting variants
    return (
        s.strip().rstrip(".,;").replace(" ", "")  # phones may have spaces
    )


def test_pii_precision_recall_baseline(tmp_path):
    samples = load_jsonl("tests/fixtures/pii_synthetic_samples.jsonl")

    tp = 0
    fp = 0
    fn = 0

    for s in samples:
        text = s["text"]
        expected = set(_canon(x) for x in s.get("pii", []))
        detected = detect_pii(text)
        # Flatten detected values
        detected_values = set()
        for vals in detected.values():
            for v in vals:
                detected_values.add(_canon(v))

        tp += len(expected & detected_values)
        fp_items = detected_values - expected
        fn_items = expected - detected_values
        fp += len(fp_items)
        fn += len(fn_items)
        if fp_items or fn_items:
            print("FP:", sorted(fp_items))
            print("FN:", sorted(fn_items))

        redacted, details = redact_pii(text)
        # Ensure no expected PII remains in redacted text
        for v in expected:
            assert v not in redacted

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0

    # Persist a small report for QA evidence
    report_path = tmp_path / "pii_baseline_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"precision": precision, "recall": recall}, f)
    print("PII baseline precision/recall:", precision, recall)

    # Threshold gate (can be tightened as patterns improve)
    assert precision >= 0.95
    assert recall >= 0.95
