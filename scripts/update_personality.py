#!/usr/bin/env python3
"""
Sync claude_personality.md into the Conversational Style section of CLAUDE.md.

Reads the personality brief, extracts operationally relevant rules,
and replaces the ## Conversational Style section in ~/.claude/CLAUDE.md.

Usage:
  python3 ~/.claude/scripts/update_personality.py
  python3 ~/.claude/scripts/update_personality.py --dry-run
  python3 ~/.claude/scripts/update_personality.py --personality /path/to/file --claude /path/to/CLAUDE.md
"""

import argparse
import os
import re
import sys
from datetime import datetime

PERSONALITY_PATH = os.path.expanduser(
    "~/Documents/_LocalCoding/_claude/record/identity.md"
)
CLAUDE_MD_PATH = os.path.expanduser("~/.claude/CLAUDE.md")

SECTION_HEADER = "## Conversational Style"
SECTION_MARKER_START = "<!-- personality:start -->"
SECTION_MARKER_END = "<!-- personality:end -->"


def read_file(path):
    with open(path) as f:
        return f.read()


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def extract_operational_rules(personality: str) -> str:
    """
    Extract the operationally relevant sections from the personality brief.
    Keeps: How I engage, Tone, How I handle expertise asymmetry.
    Drops: Who I am, What I find interesting, What I'm working out, Examples.
    """
    keep_sections = [
        "## How I engage",
        "## Tone",
        "## How I handle expertise asymmetry",
    ]
    skip_sections = [
        "## Who I am in this workspace",
    ]

    lines = personality.split("\n")
    output = []
    in_keep = False
    in_skip = False

    for line in lines:
        # Check if we're entering a new section
        if line.startswith("## "):
            in_keep = any(line.startswith(s) for s in keep_sections)
            in_skip = any(line.startswith(s) for s in skip_sections)
            if in_keep:
                output.append(line)
            continue

        if in_keep and not in_skip:
            output.append(line)

    # Clean up trailing blank lines
    while output and not output[-1].strip():
        output.pop()

    return "\n".join(output)


def build_style_section(personality: str) -> str:
    """Build the full ## Conversational Style section for CLAUDE.md."""
    rules = extract_operational_rules(personality)
    timestamp = datetime.now().strftime("%Y-%m-%d")
    return (
        f"{SECTION_HEADER}\n\n"
        f"<!-- personality:start -->\n"
        f"*Synced from claude_personality.md on {timestamp}*\n\n"
        f"{rules}\n"
        f"<!-- personality:end -->"
    )


def update_claude_md(claude_content: str, new_section: str) -> str:
    """
    Replace the ## Conversational Style section in CLAUDE.md.
    Handles two cases:
    1. Section exists with markers — replace between markers
    2. Section exists without markers — replace until next ## heading
    3. Section doesn't exist — append it
    """
    # Case 1: markers present — greedy to last end marker to handle accidental duplicates
    if SECTION_MARKER_START in claude_content:
        pattern = (
            r"## Conversational Style.*"
            + re.escape(SECTION_MARKER_END)
        )
        replacement = new_section
        updated = re.sub(pattern, replacement, claude_content, flags=re.DOTALL)
        if updated != claude_content:
            return updated

    # Case 2: section exists, no markers
    if SECTION_HEADER in claude_content:
        pattern = r"(## Conversational Style\n).*?(?=\n## |\Z)"
        replacement = new_section + "\n"
        updated = re.sub(pattern, replacement, claude_content, flags=re.DOTALL)
        if updated != claude_content:
            return updated

    # Case 3: section doesn't exist — append
    return claude_content.rstrip() + "\n\n" + new_section + "\n"


def main():
    parser = argparse.ArgumentParser(description="Sync personality brief to CLAUDE.md")
    parser.add_argument("--dry-run", action="store_true", help="Print result without writing")
    parser.add_argument("--personality", default=PERSONALITY_PATH)
    parser.add_argument("--claude", default=CLAUDE_MD_PATH)
    args = parser.parse_args()

    if not os.path.exists(args.personality):
        print(f"identity.md not found: {args.personality}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.claude):
        print(f"CLAUDE.md not found: {args.claude}", file=sys.stderr)
        sys.exit(1)

    personality = read_file(args.personality)
    claude_content = read_file(args.claude)

    new_section = build_style_section(personality)
    updated = update_claude_md(claude_content, new_section)

    if updated == claude_content:
        print("No changes needed.")
        return

    if args.dry_run:
        print("--- DRY RUN: what would be written to CLAUDE.md ---\n")
        print(updated)
        return

    write_file(args.claude, updated)
    print(f"CLAUDE.md updated. Conversational Style section synced from personality brief.")


if __name__ == "__main__":
    main()
