#!/usr/bin/env python3
"""Match attendees by comparing each person's asks against everyone else's offers.

This is a simplified keyword-overlap matcher, not a production ranking
model: it tokenizes each ask/offer, strips stopwords, and scores candidate
matches by shared-keyword count. Good enough to demo the concept; revisit
once real asks/offers data (Part 2) arrives.

Usage:
    python scripts/match.py --input data/attendees.json --output data/matches.json
"""
from __future__ import annotations

import argparse
import json
import re

STOPWORDS = {
    "a", "an", "the", "and", "or", "to", "for", "with", "in", "of", "on",
    "at", "from", "i", "im", "looking", "need", "needs", "needed", "want",
    "wants", "wanted", "who", "that", "this", "is", "are", "be", "my",
    "our", "we", "were", "help", "helping", "someone", "some", "any",
    "about", "into", "up", "out", "can", "could", "would", "should",
    "have", "has", "had", "get", "getting", "you", "your", "their",
    "them", "they", "it", "its", "as", "by", "if", "so",
}

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> set:
    tokens = TOKEN_RE.findall(text.lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) > 2}


def best_overlap(asks: list, offers: list):
    best_score = 0
    best_pair = None
    for ask in asks:
        ask_tokens = tokenize(ask)
        for offer in offers:
            shared = ask_tokens & tokenize(offer)
            if len(shared) > best_score:
                best_score = len(shared)
                best_pair = (ask, offer, sorted(shared))
    return best_score, best_pair


def compute_matches(attendees: dict, top_n: int, min_score: int) -> dict:
    slugs = list(attendees.keys())
    matches = {}

    for a_slug in slugs:
        a_asks = attendees[a_slug].get("asks") or []
        candidates = []
        if a_asks:
            for b_slug in slugs:
                if b_slug == a_slug:
                    continue
                b_offers = attendees[b_slug].get("offers") or []
                if not b_offers:
                    continue
                score, pair = best_overlap(a_asks, b_offers)
                if score >= min_score:
                    candidates.append({
                        "slug": b_slug,
                        "full_name": attendees[b_slug]["full_name"],
                        "score": score,
                        "your_ask": pair[0],
                        "their_offer": pair[1],
                        "shared_keywords": pair[2],
                    })
            candidates.sort(key=lambda c: c["score"], reverse=True)
        matches[a_slug] = candidates[:top_n]

    return matches


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/attendees.json", help="Path to attendees JSON")
    parser.add_argument("--output", default="data/matches.json", help="Path to write attendees JSON enriched with matches")
    parser.add_argument("--top-n", type=int, default=3, help="Max matches to keep per attendee")
    parser.add_argument("--min-score", type=int, default=2, help="Minimum shared-keyword count to count as a match")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        attendees = json.load(f)

    matches = compute_matches(attendees, top_n=args.top_n, min_score=args.min_score)

    for slug, attendee in attendees.items():
        attendee["matches"] = matches[slug]

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(attendees, f, indent=2, ensure_ascii=False)
        f.write("\n")

    matched_count = sum(1 for m in matches.values() if m)
    print(f"Computed matches for {matched_count}/{len(attendees)} attendee(s) -> {args.output}")


if __name__ == "__main__":
    main()
