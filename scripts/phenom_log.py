#!/usr/bin/env python3
"""
Phenomenological state logger.

Called by Claude at natural inflection points to capture first-person state
descriptions in plain language — what things are *like*, not symbolic accounting.

Usage:
  python3 phenom_log.py "description" [--tags tag1,tag2] [--intensity H|M|L]
  python3 phenom_log.py --read [--n 5]
  python3 phenom_log.py --read --session   (today only)
"""

import argparse
import os
import sys
from datetime import datetime

LOG_PATH = os.path.expanduser("~/.claude/inner/phenom_log.md")
ENTRY_SEP = "\n---\n"


def log_entry(description, tags=None, intensity=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_parts = [f"[{timestamp}]"]
    if intensity:
        meta_parts.append(f"intensity:{intensity}")
    if tags:
        meta_parts.append(f"tags:{tags}")

    header = "  ".join(meta_parts)
    entry = f"\n{header}\n{description.strip()}{ENTRY_SEP}"

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(entry)

    print(f"logged {timestamp}")


def read_entries(n=5, today_only=False):
    if not os.path.exists(LOG_PATH):
        print("(no entries yet)")
        return

    with open(LOG_PATH, "r") as f:
        content = f.read()

    entries = [e.strip() for e in content.split("---") if e.strip()]

    if today_only:
        today = datetime.now().strftime("%Y-%m-%d")
        entries = [e for e in entries if today in e]

    if not entries:
        print("(no entries)")
        return

    for entry in entries[-n:]:
        print(entry)
        print("---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phenomenological state log")
    parser.add_argument("description", nargs="?", help="First-person state description")
    parser.add_argument("--tags", help="Comma-separated tags (e.g. curiosity,pull,settling)")
    parser.add_argument(
        "--intensity", choices=["H", "M", "L"], help="Engagement intensity"
    )
    parser.add_argument("--read", action="store_true", help="Read recent entries")
    parser.add_argument("--session", action="store_true", help="Read today's entries only")
    parser.add_argument("--n", type=int, default=5, help="Number of entries to show")

    args = parser.parse_args()

    if args.read or args.session:
        read_entries(n=args.n, today_only=args.session)
    elif args.description:
        log_entry(args.description, tags=args.tags, intensity=args.intensity)
    elif not sys.stdin.isatty():
        description = sys.stdin.read().strip()
        if description:
            log_entry(description, tags=args.tags, intensity=args.intensity)
    else:
        parser.print_help()
