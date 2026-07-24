#!/usr/bin/env python3
"""Match attendees to each other (or to content) based on cleaned survey data.

Usage:
    python scripts/match.py --input data/clean_survey.csv --output data/matches.csv
"""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to cleaned survey CSV")
    parser.add_argument("--output", required=True, help="Path to write matches CSV")
    args = parser.parse_args()

    raise NotImplementedError("matching logic not implemented yet")


if __name__ == "__main__":
    main()
