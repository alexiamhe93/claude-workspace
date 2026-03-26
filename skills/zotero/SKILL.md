---
name: zotero
description: Interface with Alex's Zotero library. Use when searching for references, browsing collections, adding papers after a literature search, or exporting BibTeX.
argument-hint: [search|collection|collections|item|add-paper|bibtex] [args]
allowed-tools:
  - Bash(python3:*)
---

Interface with Alex's Zotero library via: $ARGUMENTS

```bash
python3 ~/.claude/scripts/zotero.py search "query" [--limit N] [-v]
python3 ~/.claude/scripts/zotero.py collection <KEY> [-v]
python3 ~/.claude/scripts/zotero.py collections
python3 ~/.claude/scripts/zotero.py item <KEY>
python3 ~/.claude/scripts/zotero.py add-paper
python3 ~/.claude/scripts/zotero.py bibtex <KEY>
```

**Key collections:**

| Key | Name |
|-----|------|
| COLLECTION_KEY | Your collection name |

**When to add papers:** after a literature search; when Alex mentions a paper not in Zotero; consciousness/philosophy papers go in a new collection (ask Alex before creating one).

Config: `~/.claude/zotero_config.json` — never commit to git.
