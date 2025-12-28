import pytest
from src.ai.pii_scrubber import detect_pii, redact_pii


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
