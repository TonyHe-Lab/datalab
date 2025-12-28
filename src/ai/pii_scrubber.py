"""PII detection and scrubbing utilities (initial implementation).

Provides regex-based detection and simple redaction utilities. This
is a conservative initial implementation that will be improved with
additional patterns and medical terminology support.
"""

import re
from typing import Tuple, List, Dict

# Simple PII regex patterns (examples). These are for synthetic tests only.
# Emails: allow plus tags (e.g., user+tag@domain.com)
_EMAIL_RE = re.compile(r"[\w\.+-]+@[\w\.-]+")
_PHONE_RE = re.compile(
    r"(?:(?<=\s)|^)(?:\+?\d{1,3}[\s\-]?)?(?:\(\d{2,4}\)|\d{2,4})[\s\-]?\d{3,4}[\s\-]?\d{3,4}(?:\s*(?:ext\.?|x)\s*\d{1,5})?(?=(?:\s|[\.;,]|$))",
    re.IGNORECASE,
)
# Mainland China mobile (11 digits starting with 1[3-9])
_CN_MOBILE_RE = re.compile(r"\b1[3-9]\d{9}\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# Dates (ISO-like) and MRN (medical record number examples - synthetic)
_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
# MRN formats: "MRN 00012345" or "MRN-789"
_MRN_RE = re.compile(r"\bMRN[-:\s]*\d{3,10}\b", re.IGNORECASE)
# Expiration date (MM/YY)
_EXPIRY_RE = re.compile(r"\b(?:0[1-9]|1[0-2])\/\d{2}\b")
# CVV labeled digits (3-4)
_CVV_RE = re.compile(r"\bCVV[:\s]*\d{3,4}\b", re.IGNORECASE)

# Names (basic first last name pattern) with exclusions to reduce FPs from labels and addresses
# This pattern looks for capitalized first name + last name, excluding common non-name words
_NAME_RE = re.compile(
    r"\b(?:Patient\s+)?(?:Name\s*:\s*)?(?:Contact\s*:\s*)?"
    r"(?!Device\b|Medical\b|Record\b|Serial\b|Insurance\b|Account\b|Credit\b|Card\b|Exp\b|CVV\b)"
    r"[A-Z][a-z]+\s(?!St\.?|Street|Rd\.?|Road|Ave\.?|Avenue|Lane|Ln\.?|Blvd\.?|Boulevard|Way\b|York\b|Box\b|Serial\b|Record\b|Number\b|ID\b)[A-Z][a-z]+\b(?!,\s*[A-Z]{2})"
)
# Simpler pattern for fallback with exclusions
_NAME_SIMPLE_RE = re.compile(
    r"\b(?!Device\b|Medical\b|Record\b|Serial\b|Insurance\b|Account\b)"
    r"[A-Z][a-z]+\s(?!St\.?|Street|Rd\.?|Road|Ave\.?|Avenue|Lane|Ln\.?|Blvd\.?|Boulevard|Way\b|York\b|Box\b|Serial\b|Record\b)[A-Z][a-z]+\b"
)

# Addresses (simple street address)
# Addresses: broaden to common street forms (Street/Road/Ave/etc.) and allow apartment/unit parts
_ADDRESS_STREET_RE = re.compile(
    r"\b\d+\s+\w+(?:\s\w+)*\s+(?:St\.?|Street|Rd\.?|Road|Ave\.?|Avenue|Blvd\.?|Boulevard|Ln\.?|Lane|Way)\b",
    re.IGNORECASE,
)
_ADDRESS_FULL_RE = re.compile(
    r"\b\d+\s+[A-Za-z0-9\s]+(?:Street|St\.?|Road|Rd\.?|Avenue|Ave\.?|Lane|Ln\.?|Boulevard|Blvd\.?|Way)\b(?:,\s*Apt\s*[A-Za-z0-9]+)?(?:,\s*[A-Za-z\s]+)?,\s*[A-Z]{2}\s*\d{5}\b",
    re.IGNORECASE,
)
_PO_BOX_RE = re.compile(r"\bPO\s+Box\s+\d+\b", re.IGNORECASE)

# Chinese names (common pattern)
_CHINESE_NAME_RE = re.compile(r"[\u4e00-\u9fff]{2,4}")

# IDs (synthetic ID pattern)
_ID_RE = re.compile(r"\b[A-Z]-\d{6}\b")
# Insurance/Account/Serial identifiers (synthetic examples)
_INSURANCE_RE = re.compile(r"\bINS-\d+\b")
_ACCOUNT_RE = re.compile(r"\bACC-\d+\b")
_SERIAL_RE = re.compile(r"\bSN-[A-Z0-9]+\b")

# Credit card (very naive pattern for synthetic tests; do NOT use in production without Luhn/brand checks)
_CREDIT_CARD_RE = re.compile(r"\b\d{4}[- ]\d{4}[- ]\d{4}[- ]\d{4}\b")

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
    cn_mobiles = _CN_MOBILE_RE.findall(text)
    ssn = _SSN_RE.findall(text)
    dates = _DATE_RE.findall(text)
    mrn_raw = _MRN_RE.findall(text)
    # MRN handling:
    # - If pattern includes hyphen (e.g., MRN-789), include raw token only
    # - Otherwise include digits only (e.g., MRN 00012345 → 00012345)
    mrn = []
    for m in mrn_raw:
        if "-" in m:
            mrn.append(m)
        else:
            digits = re.findall(r"\d{3,10}", m)
            mrn.extend(digits)

    # Detect names and normalize them (remove common prefixes)
    raw_names = _NAME_RE.findall(text)
    if not raw_names:
        raw_names = _NAME_SIMPLE_RE.findall(text)

    names = []
    for name in raw_names:
        # Normalize name - remove common prefixes and extra whitespace
        normalized = name.strip()
        normalized_lower = normalized.lower()

        # Remove common prefixes
        for prefix in ["patient", "name:", "contact:"]:
            if normalized_lower.startswith(prefix):
                normalized = normalized[len(prefix) :].strip()
                break

        # Ensure it's still a valid name (at least two words)
        if len(normalized.split()) >= 2:
            names.append(normalized)
    addresses = _ADDRESS_FULL_RE.findall(text) or _ADDRESS_STREET_RE.findall(text)
    po_boxes = _PO_BOX_RE.findall(text)
    chinese_names = _CHINESE_NAME_RE.findall(text)
    # Filter out common labels that may be captured by the broad Chinese chars regex
    chinese_names = [
        cn for cn in chinese_names if cn not in {"患者姓名", "电话", "邮箱"}
    ]
    ids = _ID_RE.findall(text)
    insurance = _INSURANCE_RE.findall(text)
    account = _ACCOUNT_RE.findall(text)
    serial = _SERIAL_RE.findall(text)
    credit_cards = _CREDIT_CARD_RE.findall(text)
    expiries = _EXPIRY_RE.findall(text)
    cvv = []
    for match in _CVV_RE.finditer(text):
        # Extract only the digits for CVV
        d = re.findall(r"\d{3,4}", match.group(0))
        cvv.extend(d)

    return {
        "emails": emails,
        "phones": phones + cn_mobiles,
        "ssn": ssn,
        "dates": dates,
        "mrn": mrn,
        "names": names,
        "addresses": addresses,
        "po_boxes": po_boxes,
        "chinese_names": chinese_names,
        "ids": ids,
        "insurance": insurance,
        "account": account,
        "serial": serial,
        "credit_cards": credit_cards,
        "expiries": expiries,
        "cvv": cvv,
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
    redacted = _CN_MOBILE_RE.sub(placeholder, redacted)
    redacted = _SSN_RE.sub(placeholder, redacted)
    redacted = _DATE_RE.sub(placeholder, redacted)
    redacted = _MRN_RE.sub(placeholder, redacted)
    redacted = _NAME_RE.sub(placeholder, redacted)
    redacted = _ADDRESS_FULL_RE.sub(placeholder, redacted)
    redacted = _ADDRESS_STREET_RE.sub(placeholder, redacted)
    redacted = _CHINESE_NAME_RE.sub(placeholder, redacted)
    redacted = _ID_RE.sub(placeholder, redacted)
    redacted = _INSURANCE_RE.sub(placeholder, redacted)
    redacted = _ACCOUNT_RE.sub(placeholder, redacted)
    redacted = _SERIAL_RE.sub(placeholder, redacted)
    redacted = _CREDIT_CARD_RE.sub(placeholder, redacted)
    redacted = _EXPIRY_RE.sub(placeholder, redacted)
    redacted = _CVV_RE.sub(placeholder, redacted)
    redacted = _PO_BOX_RE.sub(placeholder, redacted)
    return redacted, details


def contains_medical_terms(text: str) -> bool:
    """Heuristic: detect presence of basic medical terms for downstream handling.

    Used to adjust prompts or caution when extracting data, without being PII itself.
    """
    lower = text.lower()
    return any(term in lower for term in MEDICAL_TERMS)
