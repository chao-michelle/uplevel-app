#!/usr/bin/env python3
"""Generate one static HTML page per attendee into /site.

Usage:
    python scripts/generate.py --input data/matches.csv --output-dir site/
"""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to matches CSV")
    parser.add_argument("--output-dir", required=True, help="Directory to write generated pages into")
    args = parser.parse_args()

    raise NotImplementedError("page generation logic not implemented yet")


if __name__ == "__main__":
    main()
