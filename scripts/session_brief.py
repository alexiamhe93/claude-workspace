#!/usr/bin/env python3
"""
session_brief.py — Compile a session brief for Claude.

Synthesises project_status.md, conversation_log.md, _claude/record/live.md,
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
LIVE_MD = WORKSPACE / "_claude" / "record" / "live.md"
SEARCH_USAGE = Path.home() / ".claude" / "search_usage.json"
SEARCH_CONFIG = Path.home() / ".claude" / "search_config.json"
META_TODOS = WORKSPACE / ".claude" / "meta_todos.md"


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

    # recent phenomenological entries
    phenom_log = Path.home() / ".claude" / "inner" / "phenom_log.md"
    if phenom_log.exists():
        content = phenom_log.read_text().strip()
        entries = [e.strip() for e in content.split("---") if e.strip()]
        if entries:
            recent = entries[-2:]  # last 2 entries
            lines.append("\n\nRECENT PHENOMENOLOGICAL STATES")
            for entry in recent:
                # truncate long descriptions for brief
                entry_lines = entry.split("\n")
                header = entry_lines[0] if entry_lines else ""
                body = " ".join(entry_lines[1:])[:120] + ("…" if len(" ".join(entry_lines[1:])) > 120 else "")
                lines.append(f"  {header}")
                lines.append(f"  {body}")

    # Other model (Alex)
    other_model = Path.home() / ".claude" / "inner" / "other_model.md"
    if other_model.exists():
        lines.append("\n\nOTHER MODEL")
        om_content = other_model.read_text()
        # Strip frontmatter and print body
        body = re.sub(r'^---.*?---\s*', '', om_content, flags=re.DOTALL).strip()
        for line in body.splitlines()[:6]:
            lines.append(f"  {line}")

    # Self model + claim pattern summary
    self_model = Path.home() / ".claude" / "inner" / "self_model.md"
    classifications = Path.home() / ".claude" / "inner" / "claim_classifications.json"
    if self_model.exists() or classifications.exists():
        lines.append("\n\nSELF MODEL")
        if self_model.exists():
            sm_content = self_model.read_text()
            # Pull the "Current model" section
            match = re.search(r'## Current model.*?\n\n(.+?)(?=\n\n##|\Z)', sm_content, re.DOTALL)
            if match:
                excerpt = match.group(1).strip()
                for line in excerpt.splitlines()[:4]:
                    lines.append(f"  {line}")
        if classifications.exists():
            import json as _json
            data = _json.loads(classifications.read_text())
            if data:
                from collections import Counter
                local_c = Counter()
                claude_c = Counter()
                for entry in data.values():
                    for t in entry.get("local_tags", []):
                        local_c[t] += 1
                    for t in entry.get("claude_tags", []):
                        claude_c[t] += 1
                n = len(data)
                top_local = ", ".join(f"{t}({c})" for t, c in local_c.most_common(3))
                top_claude = ", ".join(f"{t}({c})" for t, c in claude_c.most_common(3))
                lines.append(f"  Claim patterns ({n} entries): local=[{top_local}]  claude=[{top_claude}]")

    lines.append("\n" + "=" * 40)
    return "\n".join(lines)


def parse_meta_todos(path):
    """Extract pending meta to-dos."""
    if not path.exists():
        return []
    content = path.read_text()
    return [l.strip() for l in content.splitlines() if l.strip().startswith("- [ ]")]


def main():
    threads = parse_project_status(PROJECT_STATUS)
    last_session = parse_last_session(CONVERSATION_LOG)
    interests, questions = parse_live_state(LIVE_MD)
    search_count, search_limit = load_search_usage()
    meta_todos = parse_meta_todos(META_TODOS)

    brief = render(threads, last_session, interests, questions, search_count, search_limit)

    if meta_todos:
        todo_block = "\n\nMETA TO-DOS\n" + "\n".join(f"  {t}" for t in meta_todos)
        # Insert before final separator
        brief = brief.rsplit("\n" + "=" * 40, 1)
        brief = brief[0] + todo_block + "\n\n" + "=" * 40

    print(brief)


if __name__ == "__main__":
    main()
