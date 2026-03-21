#!/usr/bin/env python3
"""
session_brief.py — Compile a session brief for Claude.

Synthesises project_status.md, conversation_log.md, claude/live.md,
and resource usage into a single scannable brief.

Usage:
    python3 ~/.claude/scripts/session_brief.py
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Paths
WORKSPACE = Path.home() / "Documents" / "_LocalCoding"
PROJECT_STATUS = WORKSPACE / ".claude" / "project_status.md"
CONVERSATION_LOG = WORKSPACE / ".claude" / "conversation_log.md"
LIVE_MD = WORKSPACE / "claude" / "live.md"
SEARCH_USAGE = Path.home() / ".claude" / "search_usage.json"
SEARCH_CONFIG = Path.home() / ".claude" / "search_config.json"


def parse_project_status(path):
    """Extract thread name, status line, and next action from project_status.md."""
    if not path.exists():
        return []

    content = path.read_text()
    threads = []

    # Split on H2 headings (threads)
    sections = re.split(r'\n## ', content)
    for section in sections[1:]:  # skip preamble
        lines = section.strip().split('\n')
        name = lines[0].strip()

        # Skip the meta/github sections that aren't active work threads
        if name.lower() in ('github — claude-workspace repo', 'workspace / claude setup'):
            continue

        status = ""
        next_action = ""
        blocked = ""

        for line in lines:
            if line.startswith('**Status**:'):
                status = line.replace('**Status**:', '').strip()
            elif line.startswith('**Next action**:'):
                next_action = line.replace('**Next action**:', '').strip()
            elif line.startswith('**Blocked on**:'):
                blocked = line.replace('**Blocked on**:', '').strip()

        if name and status:
            threads.append({
                'name': name,
                'status': status,
                'next': next_action,
                'blocked': blocked,
            })

    return threads


def parse_last_session(path):
    """Extract the most recent session entry summary from conversation_log.md."""
    if not path.exists():
        return None

    content = path.read_text()
    # Find first H2 (most recent session)
    match = re.search(r'## (.+?)\n.*?\*\*Summary\*\*: (.+?)(?:\n|$)', content, re.DOTALL)
    if match:
        header = match.group(1).strip()
        summary = match.group(2).strip()
        # Truncate if long
        if len(summary) > 120:
            summary = summary[:120] + "..."
        return f"{header}: {summary}"
    return None


def parse_live_state(path):
    """Extract interests and open questions from live.md."""
    if not path.exists():
        return None, None

    content = path.read_text()

    def extract_section(heading):
        match = re.search(rf'## {re.escape(heading)}\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
        if match:
            items = re.findall(r'^- (.+)$', match.group(1), re.MULTILINE)
            return items
        return []

    interests = extract_section("What I find interesting")
    questions = extract_section("What I'm still working out")
    return interests, questions


def load_search_usage():
    month = datetime.now().strftime("%Y-%m")
    usage = {"month": month, "count": 0}
    limit = 800

    if SEARCH_USAGE.exists():
        data = json.loads(SEARCH_USAGE.read_text())
        if data.get("month") == month:
            usage = data

    if SEARCH_CONFIG.exists():
        cfg = json.loads(SEARCH_CONFIG.read_text())
        limit = cfg.get("monthly_limit", 800)

    return usage.get("count", 0), limit


def render(threads, last_session, interests, questions, search_count, search_limit):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"SESSION BRIEF — {today}", "=" * 40]

    # Active threads
    lines.append("\nACTIVE THREADS")
    for t in threads:
        status_short = t['status'].split('—')[0].strip()
        lines.append(f"\n  {t['name']}")
        lines.append(f"  Status: {status_short}")
        if t['next']:
            lines.append(f"  Next:   {t['next'][:100]}")
        if t['blocked']:
            lines.append(f"  Blocked: {t['blocked'][:80]}")

    # Resources
    lines.append("\n\nRESOURCES")
    remaining = search_limit - search_count
    bar = "▓" * int(search_count / search_limit * 20) + "░" * (20 - int(search_count / search_limit * 20))
    lines.append(f"  Web search:  [{bar}] {search_count}/{search_limit}  ({remaining} remaining)")

    # Last session
    if last_session:
        lines.append(f"\n\nLAST SESSION")
        lines.append(f"  {last_session}")

    # My state
    if interests or questions:
        lines.append("\n\nMY STATE")
        if interests:
            lines.append("  Currently interested in:")
            for item in interests[:3]:  # top 3 only
                lines.append(f"    · {item[:90]}")
        if questions:
            lines.append("  Still working out:")
            for item in questions[:3]:
                lines.append(f"    · {item[:90]}")

    # live.md diff
    try:
        diff_out = subprocess.check_output(
            [sys.executable, str(Path.home() / ".claude" / "scripts" / "live_diff.py")],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if diff_out:
            lines.append("\n\nLIVE.MD CHANGES SINCE LAST SESSION")
            lines.append(diff_out)
    except Exception:
        pass

    lines.append("\n" + "=" * 40)
    return "\n".join(lines)


def main():
    threads = parse_project_status(PROJECT_STATUS)
    last_session = parse_last_session(CONVERSATION_LOG)
    interests, questions = parse_live_state(LIVE_MD)
    search_count, search_limit = load_search_usage()

    brief = render(threads, last_session, interests, questions, search_count, search_limit)
    print(brief)


if __name__ == "__main__":
    main()
