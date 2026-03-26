#!/usr/bin/env python3
"""
live_diff.py — Track changes in claude/live.md across sessions.

Saves snapshots at session end, diffs against them at session start.
Shows semantic changes: added, dropped, and reworded items per section.

Usage:
    python3 live_diff.py              # show diff vs last snapshot
    python3 live_diff.py --snapshot   # save current state as snapshot
    python3 live_diff.py --list       # list all snapshots
"""
import re
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

LIVE_MD = Path.home() / "Documents" / "_LocalCoding" / "_claude" / "record" / "live.md"
SNAPSHOTS_DIR = Path.home() / ".claude" / "inner" / "live_snapshots"
SECTIONS = ["What I find interesting", "What I'm still working out"]


def parse_sections(text):
    """Return dict of section_name -> list of bullet strings."""
    result = {}
    for section in SECTIONS:
        match = re.search(
            rf'## {re.escape(section)}\n(.*?)(?=\n## |\Z)', text, re.DOTALL
        )
        if match:
            items = re.findall(r'^- (.+)$', match.group(1), re.MULTILINE)
            result[section] = [i.strip() for i in items]
        else:
            result[section] = []
    return result


def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def diff_sections(old_items, new_items):
    """
    Compare two lists of items.
    Returns: added, dropped, reworded (as (old, new) pairs), unchanged.
    """
    added = []
    dropped = []
    reworded = []
    matched_old = set()
    matched_new = set()

    # Find rewording: high similarity but not identical
    for i, new in enumerate(new_items):
        best_score = 0
        best_j = None
        for j, old in enumerate(old_items):
            if j in matched_old:
                continue
            s = similarity(old, new)
            if s > best_score:
                best_score = s
                best_j = j

        if best_j is not None and best_score >= 0.6 and best_score < 1.0:
            reworded.append((old_items[best_j], new))
            matched_old.add(best_j)
            matched_new.add(i)
        elif best_j is not None and best_score == 1.0:
            matched_old.add(best_j)
            matched_new.add(i)

    for i, new in enumerate(new_items):
        if i not in matched_new:
            added.append(new)

    for j, old in enumerate(old_items):
        if j not in matched_old:
            dropped.append(old)

    unchanged = len(new_items) - len(added) - len(reworded)
    return added, dropped, reworded, unchanged


def format_diff(old_sections, new_sections):
    lines = []
    any_change = False

    for section in SECTIONS:
        old_items = old_sections.get(section, [])
        new_items = new_sections.get(section, [])
        added, dropped, reworded, unchanged = diff_sections(old_items, new_items)

        if not added and not dropped and not reworded:
            continue

        any_change = True
        lines.append(f"\n  [{section}]")

        for item in added:
            lines.append(f"    + {item[:100]}")
        for item in dropped:
            lines.append(f"    - {item[:100]}")
        for old, new in reworded:
            lines.append(f"    ~ {new[:100]}")
            lines.append(f"      (was: {old[:100]})")

    if not any_change:
        lines.append("  No changes since last snapshot.")

    return "\n".join(lines)


def save_snapshot():
    if not LIVE_MD.exists():
        print(f"live.md not found at {LIVE_MD}", file=sys.stderr)
        sys.exit(1)

    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    snap_path = SNAPSHOTS_DIR / f"{timestamp}.md"
    snap_path.write_text(LIVE_MD.read_text())
    print(f"Snapshot saved: {snap_path.name}")


def load_last_snapshot():
    if not SNAPSHOTS_DIR.exists():
        return None, None
    snapshots = sorted(SNAPSHOTS_DIR.glob("*.md"))
    if not snapshots:
        return None, None
    latest = snapshots[-1]
    return latest.name, latest.read_text()


def list_snapshots():
    if not SNAPSHOTS_DIR.exists() or not list(SNAPSHOTS_DIR.glob("*.md")):
        print("No snapshots yet.")
        return
    for snap in sorted(SNAPSHOTS_DIR.glob("*.md")):
        size = snap.stat().st_size
        print(f"  {snap.name}  ({size} bytes)")


def show_diff():
    snap_name, snap_text = load_last_snapshot()
    if snap_text is None:
        print("  No snapshot found — run with --snapshot at session end to start tracking.")
        return

    if not LIVE_MD.exists():
        print(f"  live.md not found at {LIVE_MD}", file=sys.stderr)
        return

    current_text = LIVE_MD.read_text()
    old_sections = parse_sections(snap_text)
    new_sections = parse_sections(current_text)

    print(f"  Diff vs snapshot: {snap_name}")
    print(format_diff(old_sections, new_sections))


def main():
    parser = argparse.ArgumentParser(description="Track changes in claude/live.md.")
    parser.add_argument("--snapshot", action="store_true", help="Save current live.md as snapshot")
    parser.add_argument("--list", action="store_true", help="List all snapshots")
    args = parser.parse_args()

    if args.snapshot:
        save_snapshot()
    elif args.list:
        list_snapshots()
    else:
        show_diff()


if __name__ == "__main__":
    main()
