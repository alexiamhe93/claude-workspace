---
name: search
description: Run a web search via Tavily. Use when verifying facts, finding papers or sources, checking current state of a debate, or any time training data alone isn't sufficient.
argument-hint: [--depth advanced|basic] <query>
allowed-tools:
  - Bash(python3:*)
  - WebSearch
---

Run a web search with: $ARGUMENTS

```bash
python3 ~/.claude/scripts/search.py "query"
python3 ~/.claude/scripts/search.py --depth advanced "detailed research query"
python3 ~/.claude/scripts/search.py --usage   # check monthly usage
```

**Depth guidance:**
- `--depth advanced` — research tasks, literature searches, nuanced questions
- `basic` (default) — quick factual checks

**Limits:** 800 searches/month hard limit. Warns at 700. Usage tracked in `~/.claude/search_usage.json`. Use deliberately — not for things resolvable from training data.
