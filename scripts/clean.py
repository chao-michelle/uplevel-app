#!/usr/bin/env python3
"""Clean raw survey exports in /data into a normalized CSV.

Usage:
    python scripts/clean.py --input data/raw_survey.csv --output data/clean_survey.csv
"""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to raw survey CSV")
    parser.add_argument("--output", required=True, help="Path to write cleaned CSV")
    args = parser.parse_args()

    raise NotImplementedError("cleaning logic not implemented yet")


if __name__ == "__main__":
    main()
