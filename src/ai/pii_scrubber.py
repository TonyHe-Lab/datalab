"""PII detection and scrubbing utilities (initial implementation).

Provides regex-based detection and simple redaction utilities. This
is a conservative initial implementation that will be improved with
additional patterns and medical terminology support.
"""

import re
from typing import Tuple

# Simple PII regex patterns (examples). These are for synthetic tests only.
_EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+")
_PHONE_RE = re.compile(
    r"\b(?:\+?\d{1,3}[ -]?)?(?:\(\d{2,4}\)|\d{2,4})[ -]?\d{3,4}[ -]?\d{3,4}\b"
)
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def detect_pii(text: str) -> dict:
    """Return detected PII spans and counts.

    This returns a dict with keys for pattern types and list of matches.
    """
    return {
        "emails": _EMAIL_RE.findall(text),
        "phones": _PHONE_RE.findall(text),
        "ssn": _SSN_RE.findall(text),
    }


def redact_pii(text: str, placeholder: str = "[REDACTED]") -> Tuple[str, dict]:
    """Redact known PII patterns and return (redacted_text, details).

    details contains the same structure as detect_pii for test assertions.
    """
    details = detect_pii(text)
    redacted = _EMAIL_RE.sub(placeholder, text)
    redacted = _PHONE_RE.sub(placeholder, redacted)
    redacted = _SSN_RE.sub(placeholder, redacted)
    return redacted, details
