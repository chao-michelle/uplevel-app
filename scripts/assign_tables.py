#!/usr/bin/env python3
"""Assign attendees to tables for the event.

Simplified stand-in for the eventual Phase 4 table-assignment logic:
groups attendees by primary role and deals them round-robin across N
tables, so each table gets a mix of roles rather than optimizing on
matches or industries. Replace with real Phase 4 logic once that's
designed.

Usage:
    python scripts/assign_tables.py --input data/matches.json --output data/tables.json --table-size 6
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict


def assign_tables(attendees: dict, table_size: int) -> dict:
    num_tables = max(1, math.ceil(len(attendees) / table_size))

    by_role = defaultdict(list)
    for slug, attendee in attendees.items():
        by_role[attendee.get("primary_role") or "Unspecified"].append(slug)

    table_assignment = {}
    next_table = 0
    for role in sorted(by_role):
        for slug in by_role[role]:
            table_assignment[slug] = next_table + 1  # 1-indexed for display
            next_table = (next_table + 1) % num_tables

    return table_assignment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/matches.json", help="Path to attendees JSON")
    parser.add_argument("--output", default="data/tables.json", help="Path to write attendees JSON enriched with table numbers")
    parser.add_argument("--table-size", type=int, default=6, help="Target number of people per table")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        attendees = json.load(f)

    table_assignment = assign_tables(attendees, args.table_size)

    for slug, attendee in attendees.items():
        attendee["table"] = table_assignment[slug]

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(attendees, f, indent=2, ensure_ascii=False)
        f.write("\n")

    num_tables = len(set(table_assignment.values()))
    print(f"Assigned {len(attendees)} attendee(s) to {num_tables} table(s) -> {args.output}")


if __name__ == "__main__":
    main()
