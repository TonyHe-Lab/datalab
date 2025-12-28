"""PII detection and scrubbing utilities (initial implementation).

Provides regex-based detection and simple redaction utilities. This
is a conservative initial implementation that will be improved with
additional patterns and medical terminology support.
"""

import re
from typing import Tuple, List, Dict

# Simple PII regex patterns (examples). These are for synthetic tests only.
_EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+")
_PHONE_RE = re.compile(
    r"(?:(?<=\s)|^)(?:\+?\d{1,3}[\s\-]?)?(?:\(\d{2,4}\)|\d{2,4})[\s\-]?\d{3,4}[\s\-]?\d{3,4}(?=(?:\s|[\.;,]|$))"
)
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# Dates (ISO-like) and MRN (medical record number examples - synthetic)
_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_MRN_RE = re.compile(r"\bMRN[:\s]*\d{6,10}\b", re.IGNORECASE)

# Names (basic first last name pattern)
_NAME_RE = re.compile(
    r"\b(?!Patient\b|Name\b|Contact\b|SSN\b|DOB\b)[A-Z][a-z]+ (?!St\.?|Street|Rd\.?|Road|Ave\.?|Avenue|Lane|Blvd\.?|Way\b)[A-Z][a-z]+\b"
)

# Addresses (simple street address)
_ADDRESS_RE = re.compile(r"\b\d+\s+[A-Za-z]+\s+St\.?\b")

# Chinese names (common pattern)
_CHINESE_NAME_RE = re.compile(r"[\u4e00-\u9fff]{2,4}")

# IDs (synthetic ID pattern)
_ID_RE = re.compile(r"\b[A-Z]-\d{6}\b")

# Basic medical terms (to help scrub indirect identifiers in summaries)
MEDICAL_TERMS = {
    # Common symptoms and components that might combine with identifiers
    "fever",
    "cough",
    "diarrhea",
    "overheating",
    "pump",
    "bearing",
    "filter",
    "ventilator",
    "patient",
}


def detect_pii(text: str) -> Dict[str, List[str]]:
    """Return detected PII spans and counts.

    This returns a dict with keys for pattern types and list of matches.
    """
    emails = _EMAIL_RE.findall(text)
    phones = _PHONE_RE.findall(text)
    ssn = _SSN_RE.findall(text)
    dates = _DATE_RE.findall(text)
    mrn_raw = _MRN_RE.findall(text)
    # Normalize MRN to digits only to align with fixture expectations
    mrn = []
    for m in mrn_raw:
        digits = re.findall(r"\d{6,10}", m)
        mrn.extend(digits)
    names = _NAME_RE.findall(text)
    addresses = _ADDRESS_RE.findall(text)
    chinese_names = _CHINESE_NAME_RE.findall(text)
    ids = _ID_RE.findall(text)

    return {
        "emails": emails,
        "phones": phones,
        "ssn": ssn,
        "dates": dates,
        "mrn": mrn,
        "names": names,
        "addresses": addresses,
        "chinese_names": chinese_names,
        "ids": ids,
    }


def redact_pii(
    text: str, placeholder: str = "[REDACTED]"
) -> Tuple[str, Dict[str, List[str]]]:
    """Redact known PII patterns and return (redacted_text, details).

    details contains the same structure as detect_pii for test assertions.
    """
    details = detect_pii(text)
    redacted = _EMAIL_RE.sub(placeholder, text)
    redacted = _PHONE_RE.sub(placeholder, redacted)
    redacted = _SSN_RE.sub(placeholder, redacted)
    redacted = _DATE_RE.sub(placeholder, redacted)
    redacted = _MRN_RE.sub(placeholder, redacted)
    redacted = _NAME_RE.sub(placeholder, redacted)
    redacted = _ADDRESS_RE.sub(placeholder, redacted)
    redacted = _CHINESE_NAME_RE.sub(placeholder, redacted)
    redacted = _ID_RE.sub(placeholder, redacted)
    return redacted, details


def contains_medical_terms(text: str) -> bool:
    """Heuristic: detect presence of basic medical terms for downstream handling.

    Used to adjust prompts or caution when extracting data, without being PII itself.
    """
    lower = text.lower()
    return any(term in lower for term in MEDICAL_TERMS)
