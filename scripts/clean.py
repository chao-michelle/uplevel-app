#!/usr/bin/env python3
"""Clean the raw registrant CSV export into normalized JSON, one record per attendee.

Usage:
    python scripts/clean.py --input data/form-response.csv --output data/attendees.json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import secrets
import sys
import unicodedata

# Maps the exact source column headers to internal field names. Only these
# columns are kept — admin/registration-platform columns (ticket type,
# checked in, refund/extra-ticket flags, waiver text, etc.) are dropped by
# omission.
KEEP_COLUMNS = {
    "Full Name": "full_name",
    "Email": "email",
    "Phone Number": "phone",
    "LinkedIn Profile": "linkedin",
    "Which best describes your primary role right now?": "primary_role",
    "If you picked Founder, what stage are you at?": "founder_stage",
    "What other role(s) do you associate with? (check all that apply)": "other_roles_raw",
    (
        "What’s one topic you’d love to see covered in a session "
        "that would genuinely level you up right now?"
    ): "topic",
    "Do you have any dietary restrictions?": "dietary_restrictions_raw",
}

MULTI_SELECT_DELIMITER = ";"

NEGATIVE_DIETARY_ANSWERS = {"none", "no", "na", "nope", "nil", "nonethanks"}


def slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "attendee"


def make_unique_slug(base: str, used_slugs: set) -> str:
    slug = base
    n = 2
    while slug in used_slugs:
        slug = f"{base}-{n}"
        n += 1
    used_slugs.add(slug)
    return slug


def load_existing_private_slugs(output_path: str) -> dict:
    """Private slugs must stay stable across pipeline re-runs — once a
    person's private link is sent, re-running clean.py (e.g. for a data
    correction) must not silently change it. Keyed by email since that's
    the one stable identity field across re-exports of the raw CSV."""
    try:
        with open(output_path, encoding="utf-8") as f:
            existing = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {
        a["email"]: a["private_slug"]
        for a in existing.values()
        if a.get("email") and a.get("private_slug")
    }


def make_private_slug(public_slug: str, email: str, existing_by_email: dict, used: set) -> str:
    """Unlike the public slug, this must not be derivable from the
    person's name — it's the only thing standing between the public
    profile page and the private page with their schedule/matches. Stable
    across re-runs (see load_existing_private_slugs); brand new people get
    a random suffix, not a guessable one."""
    existing = existing_by_email.get(email)
    if existing and existing not in used:
        used.add(existing)
        return existing

    while True:
        candidate = f"{public_slug}-{secrets.token_hex(4)}"
        if candidate not in used:
            used.add(candidate)
            return candidate


def clean_text(value: str) -> str | None:
    value = value.strip()
    return value or None


def clean_roles_list(value: str) -> list:
    if not value.strip():
        return []
    return [part.strip() for part in value.split(MULTI_SELECT_DELIMITER) if part.strip()]


def clean_dietary(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    normalized = re.sub(r"[^a-z]", "", value.lower())
    if normalized in NEGATIVE_DIETARY_ANSWERS:
        return None
    return value


def load_rows(input_path: str) -> list:
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [col for col in KEEP_COLUMNS if col not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"CSV is missing expected column(s): {missing}")
        return list(reader)


def clean_row(row: dict) -> dict | None:
    full_name = row["Full Name"].strip()
    email = row["Email"].strip()

    if not email:
        print(
            f"Skipping row with no email (not a real attendee record): {full_name!r}",
            file=sys.stderr,
        )
        return None

    return {
        "full_name": full_name,
        "email": email,
        "phone": clean_text(row["Phone Number"]),
        "linkedin": clean_text(row["LinkedIn Profile"]),
        "primary_role": clean_text(row["Which best describes your primary role right now?"]),
        "founder_stage": clean_text(row["If you picked Founder, what stage are you at?"]),
        "other_roles": clean_roles_list(
            row["What other role(s) do you associate with? (check all that apply)"]
        ),
        "topic": clean_text(
            row[
                "What’s one topic you’d love to see covered in a session "
                "that would genuinely level you up right now?"
            ]
        ),
        "dietary_restrictions": clean_dietary(row["Do you have any dietary restrictions?"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/form-response.csv", help="Path to raw registrant CSV")
    parser.add_argument("--output", default="data/attendees.json", help="Path to write cleaned attendees JSON")
    args = parser.parse_args()

    rows = load_rows(args.input)
    existing_private_slugs = load_existing_private_slugs(args.output)

    attendees = {}
    used_slugs = set()
    used_private_slugs = set()
    skipped = 0

    for row in rows:
        cleaned = clean_row(row)
        if cleaned is None:
            skipped += 1
            continue
        slug = make_unique_slug(slugify(cleaned["full_name"]), used_slugs)
        cleaned["slug"] = slug
        cleaned["private_slug"] = make_private_slug(
            slug, cleaned["email"], existing_private_slugs, used_private_slugs
        )
        attendees[slug] = cleaned

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(attendees, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {len(attendees)} attendees to {args.output} ({skipped} row(s) skipped)")


if __name__ == "__main__":
    main()
