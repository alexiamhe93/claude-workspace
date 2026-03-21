# /zotero

Interface with Alex's Zotero library.

## Commands

```bash
# Search
python3 ~/.claude/scripts/zotero.py search "query" [--limit N] [-v]

# Browse a collection
python3 ~/.claude/scripts/zotero.py collection <KEY> [-v]

# List all collections
python3 ~/.claude/scripts/zotero.py collections

# Get full item details
python3 ~/.claude/scripts/zotero.py item <KEY>

# Add a paper interactively
python3 ~/.claude/scripts/zotero.py add-paper

# Export collection as BibTeX
python3 ~/.claude/scripts/zotero.py bibtex <KEY>
```

## Key collections (frequently used)

| Key | Name |
|-----|------|
| AEPNWYJF | _Paper4_RedditModeration (NormRepair paper) |
| 37V97L7I | Paper3_OnlineRepairs |
| A3TLCYTB | Intersubjectivity |
| 4EAZNPNM | Deliberation |
| CB3V893S | NLP - LLMs |
| F6G9TJBF | ___TO READ |
| ASLHUFDI | __ThesisPapers (root) |

## When I should add papers

- After a literature search, add newly identified relevant papers to the appropriate collection
- When Alex mentions a paper that isn't in Zotero, offer to add it
- Consciousness/philosophy papers should go in a new collection (none exists yet — ask Alex before creating)

## Config

Credentials stored at `~/.claude/zotero_config.json` — never commit this file to git.
