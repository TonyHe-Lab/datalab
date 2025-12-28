import pytest
from src.ai.pii_scrubber import detect_pii, redact_pii
import json


def test_detect_pii_basic():
    text = "Contact john.doe@example.com or +1 555-123-4567. SSN 123-45-6789"
    d = detect_pii(text)
    assert "john.doe@example.com" in d["emails"]
    assert any("555" in p or "123" in p for p in d["phones"])
    assert "123-45-6789" in d["ssn"]


def test_redact_pii_replaces():
    text = "Call 555-123-4567 or email alice@company.org"
    redacted, details = redact_pii(text)
    assert "[REDACTED]" in redacted
    assert details["emails"] and details["phones"]


def test_pii_detection_on_synthetic_data():
    with open("tests/fixtures/pii_synthetic_samples.jsonl", "r") as f:
        for line in f:
            sample = json.loads(line)
            text = sample["text"]
            expected_pii = set(sample["pii"])
            redacted, _ = redact_pii(text)
            for pii in expected_pii:
                assert pii not in redacted, f"PII not redacted: {pii} in {redacted}"
