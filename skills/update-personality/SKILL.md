---
name: update-personality
description: Sync the personality folder into the global CLAUDE.md conversational style section. Use after reflect makes changes to identity.md.
allowed-tools:
  - Read
  - Edit
  - Bash(python3:*)
---

Sync the personality folder into the global CLAUDE.md conversational style section.

```bash
python3 ~/.claude/scripts/update_personality.py
```

This reads `_claude/record/identity.md`, extracts the operationally relevant parts (engagement style, tone, repair protocol, expertise asymmetry), and updates the `## Conversational Style` section of `~/.claude/CLAUDE.md`.

**What gets synced:** engagement style, repair protocol, tone rules, expertise asymmetry, concrete rules from the examples bank.

**What stays in the personality folder only:** `toolkit.md`, `live.md`, `examples.md`, and anything reflective that isn't an operational rule.

Confirm what changed in one sentence.
