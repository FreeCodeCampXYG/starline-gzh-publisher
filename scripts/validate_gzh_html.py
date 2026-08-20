#!/usr/bin/env python3
"""Minimal publisher-side guard for generated WeChat HTML."""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

FORBIDDEN = [
    (r"<style\b|<script\b|</?div\b|<svg\b|</svg>|foreignObject", "forbidden tag"),
    (r"\b(?:class|id)\s*=", "class/id attribute"),
    (r"javascript:|vbscript:|data:image/svg\+xml", "unsafe resource protocol"),
    (r"(?:width|flex-basis)\s*:\s*50%", "half-width layout"),
]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path)
    args = parser.parse_args()
    text = args.html.read_text(encoding="utf-8")
    errors = []
    for pattern, label in FORBIDDEN:
        if re.search(pattern, text, re.I):
            errors.append(label)
    if not re.search(r"<section\b", text, re.I):
        errors.append("missing section root")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: publisher HTML passed minimal safety checks")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
