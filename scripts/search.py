#!/usr/bin/env python3
"""
search.py — Web search via Tavily API with monthly usage tracking.

Usage:
    python3 search.py "your query"
    python3 search.py --depth advanced "detailed research query"
    python3 search.py --max-results 10 "broad query"
    python3 search.py --usage          # show usage for this month
    python3 search.py --reset-usage    # reset usage counter (e.g. new month)
"""
import json
import sys
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

CONFIG_PATH = Path.home() / ".claude" / "search_config.json"
USAGE_PATH = Path.home() / ".claude" / "search_usage.json"
TAVILY_URL = "https://api.tavily.com/search"


def load_config():
    if not CONFIG_PATH.exists():
        print("search_config.json not found.", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_usage():
    month = datetime.now().strftime("%Y-%m")
    if USAGE_PATH.exists():
        with open(USAGE_PATH) as f:
            data = json.load(f)
        if data.get("month") == month:
            return data
    return {"month": month, "count": 0, "queries": []}


def save_usage(usage):
    with open(USAGE_PATH, "w") as f:
        json.dump(usage, f, indent=2)


def check_limits(config, usage):
    limit = config.get("monthly_limit", 800)
    warn_at = config.get("warn_at", 700)
    count = usage["count"]

    if count >= limit:
        print(
            f"Monthly search limit reached ({count}/{limit}). "
            f"Use --reset-usage if a new month has started.",
            file=sys.stderr,
        )
        sys.exit(1)

    if count >= warn_at:
        print(
            f"Warning: {count}/{limit} searches used this month.",
            file=sys.stderr,
        )


def search(query, api_key, depth="basic", max_results=5, include_answer=True):
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": depth,
        "max_results": max_results,
        "include_answer": include_answer,
        "include_raw_content": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        TAVILY_URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def format_results(result):
    lines = []

    answer = result.get("answer")
    if answer:
        lines.append(f"Summary: {answer}\n")

    sources = result.get("results", [])
    if sources:
        lines.append(f"Sources ({len(sources)}):")
        for i, r in enumerate(sources, 1):
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            content = r.get("content", "").strip()
            score = r.get("score", 0)
            lines.append(f"\n[{i}] {title}")
            lines.append(f"    {url}  (relevance: {score:.2f})")
            if content:
                # Truncate long snippets
                snippet = content[:300] + "..." if len(content) > 300 else content
                lines.append(f"    {snippet}")

    return "\n".join(lines)


def show_usage(usage, config):
    limit = config.get("monthly_limit", 800)
    count = usage["count"]
    month = usage["month"]
    print(f"Month: {month}")
    print(f"Searches used: {count} / {limit}")
    remaining = limit - count
    print(f"Remaining: {remaining}")
    if usage.get("queries"):
        print(f"\nRecent queries:")
        for q in usage["queries"][-5:]:
            print(f"  [{q['time']}] {q['query']}")


def main():
    parser = argparse.ArgumentParser(description="Web search via Tavily.")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--depth", choices=["basic", "advanced"], default="basic",
                        help="Search depth (basic=faster, advanced=more thorough)")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--no-answer", action="store_true",
                        help="Skip Tavily's AI-generated answer summary")
    parser.add_argument("--usage", action="store_true", help="Show monthly usage and exit")
    parser.add_argument("--reset-usage", action="store_true", help="Reset usage counter")
    args = parser.parse_args()

    config = load_config()
    usage = load_usage()

    if args.reset_usage:
        save_usage({"month": datetime.now().strftime("%Y-%m"), "count": 0, "queries": []})
        print("Usage counter reset.")
        return

    if args.usage:
        show_usage(usage, config)
        return

    if not args.query:
        parser.print_help()
        sys.exit(1)

    check_limits(config, usage)

    try:
        result = search(
            args.query,
            config["tavily_api_key"],
            depth=args.depth,
            max_results=args.max_results,
            include_answer=not args.no_answer,
        )
    except urllib.error.HTTPError as e:
        print(f"API error {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e}", file=sys.stderr)
        sys.exit(1)

    # Update usage
    usage["count"] += 1
    usage.setdefault("queries", []).append({
        "time": datetime.now().strftime("%H:%M"),
        "query": args.query[:80],
    })
    save_usage(usage)

    print(format_results(result))
    print(f"\n[{usage['count']}/{config.get('monthly_limit', 800)} searches used this month]")


if __name__ == "__main__":
    main()
