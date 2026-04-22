#!/usr/bin/env python3
"""Scan for unresolved placeholders before shipping a paper / model card.

Greps target files for common "fill me in" sentinels: XX, XXX, ???, TODO,
FIXME, FILL_ME, PLACEHOLDER. Exits non-zero on any hit — suitable as a
pre-submit hook or the final check before compiling a paper or uploading
a model card.

Usage:
    python check_placeholders.py [paths...] [--extra PATTERN ...]

Defaults to scanning: paper/, README.md, MODEL_CARD.md, docs/
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_PATTERNS = [
    r"\bXX+\b",           # XX, XXX, XXXX ...
    r"\?\?\?",             # ???
    r"\bTODO\b",
    r"\bFIXME\b",
    r"\bFILL_ME\b",
    r"\bPLACEHOLDER\b",
    r"<<[^>]+>>",          # <<something>> templating
]

DEFAULT_TARGETS = ["paper", "README.md", "MODEL_CARD.md", "docs"]

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".ipynb_checkpoints",
             "wandb", "mlruns", "runs", "results", "data"}
SKIP_EXT = {".bin", ".safetensors", ".pt", ".ckpt", ".pdf", ".png", ".jpg",
            ".jpeg", ".gif", ".pyc", ".lock"}


def scan(path: Path, patterns: list[re.Pattern[str]]) -> list[tuple[Path, int, str]]:
    hits: list[tuple[Path, int, str]] = []
    try:
        text = path.read_text(errors="ignore")
    except (OSError, UnicodeDecodeError):
        return hits
    for i, line in enumerate(text.splitlines(), 1):
        for pat in patterns:
            if pat.search(line):
                hits.append((path, i, line.rstrip()))
                break
    return hits


def walk(root: Path):
    if root.is_file():
        yield root
        return
    if not root.exists():
        return
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in SKIP_EXT:
            continue
        yield p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", default=DEFAULT_TARGETS)
    ap.add_argument("--extra", action="append", default=[],
                    help="Extra regex patterns to flag.")
    ap.add_argument("--allow", action="append", default=[],
                    help="Regex patterns whose matches should be ignored (e.g. allowlist a known TODO).")
    args = ap.parse_args()

    patterns = [re.compile(p) for p in DEFAULT_PATTERNS + args.extra]
    allow = [re.compile(p) for p in args.allow]

    all_hits: list[tuple[Path, int, str]] = []
    for raw in args.paths:
        for f in walk(Path(raw)):
            for hit in scan(f, patterns):
                if any(a.search(hit[2]) for a in allow):
                    continue
                all_hits.append(hit)

    if not all_hits:
        print("No unresolved placeholders.")
        return 0

    print(f"Found {len(all_hits)} unresolved placeholder(s):")
    for path, line_no, line in all_hits:
        print(f"  {path}:{line_no}: {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
