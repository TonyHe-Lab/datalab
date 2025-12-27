#!/usr/bin/env python3
"""Generate synthetic PII samples as JSONL for tests/fixtures.

Usage:
  python tools/generate_pii_synthetic.py --count 1000 --out tests/fixtures/pii_synthetic_samples_large.jsonl

This script creates records with a variety of PII types: names, dates, phones, emails, SSNs, addresses.
"""

import argparse
import json
import random
from datetime import datetime


FIRST_NAMES = [
    "Alice",
    "Bob",
    "Carol",
    "David",
    "Emma",
    "Frank",
    "Grace",
    "Hiro",
    "Isabel",
    "José",
    "李",
    "王",
    "张",
    "Óscar",
    "Sofia",
    "Liu",
    "Chen",
    "Mikhail",
    "Fatima",
    "Aisha",
]
LAST_NAMES = [
    "Johnson",
    "Lee",
    "Garcia",
    "Martinez",
    "O'Neil",
    "Núñez",
    "Kumar",
    "Patel",
    "Zhang",
    "Wang",
]


def random_dob():
    year = random.randint(1940, 2005)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"


def random_phone():
    # international-ish
    country = random.choice(["+1", "+44", "+34", "+86", "+61"])
    return f"{country} {random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"


def random_email(first, last):
    domain = random.choice(["example.com", "example.org", "example.cn", "mail.test"])
    local = f"{first[0].lower()}{last.lower()}"
    return f"{local}@{domain}"


def random_ssn():
    return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"


def maybe(val, p=0.8):
    return val if random.random() < p else None


def make_record(i):
    # sometimes no PII
    if random.random() < 0.12:
        return {
            "id": f"gen-{i:06d}",
            "text": "Routine equipment check. No patient data.",
            "pii": [],
        }

    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}" if random.random() < 0.9 else f"{first}"
    dob = maybe(random_dob(), 0.9)
    phone = maybe(random_phone(), 0.9)
    email = maybe(random_email(first, last), 0.85)
    ssn = maybe(random_ssn(), 0.25)
    lines = [f"Patient: {name}"]
    if dob:
        lines.append(f"DOB: {dob}")
    if phone:
        lines.append(f"Contact: {phone}")
    if email:
        lines.append(f"Email: {email}")
    if ssn:
        lines.append(f"SSN: {ssn}")
    text = ", ".join(lines)
    pii = [v for v in [maybe(name, 0.99), dob, phone, email, ssn] if v]
    return {"id": f"gen-{i:06d}", "text": text, "pii": pii}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument(
        "--out", type=str, default="tests/fixtures/pii_synthetic_samples_large.jsonl"
    )
    args = parser.parse_args()

    random.seed(42)
    out_path = args.out
    with open(out_path, "w", encoding="utf-8") as f:
        for i in range(1, args.count + 1):
            rec = make_record(i)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {args.count} synthetic records to {out_path}")


if __name__ == "__main__":
    main()
