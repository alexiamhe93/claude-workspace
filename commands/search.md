# /search

Run a web search via Tavily and return results with a summary.

## Usage

```bash
python3 ~/.claude/scripts/search.py "query"
python3 ~/.claude/scripts/search.py --depth advanced "detailed research query"
python3 ~/.claude/scripts/search.py --usage   # check monthly usage
```

## When to use

- Verifying facts or checking current state of a debate
- Finding papers or sources for the consciousness workbench or research projects
- Replacing the manual Perplexity/Gemini runs for literature searches
- Any time training data alone isn't sufficient

## Limits

- 800 searches/month hard limit (warns at 700)
- Use `--depth advanced` for research tasks; `basic` for quick factual checks
- Usage tracked in `~/.claude/search_usage.json`
