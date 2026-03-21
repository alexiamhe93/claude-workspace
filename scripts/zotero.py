#!/usr/bin/env python3
"""
Zotero CLI for Claude — search, retrieve, and add items to Alex's library.

Usage:
  zotero.py search <query>                    — search all items
  zotero.py collection <key>                  — list items in a collection
  zotero.py collections                       — list all collections (tree)
  zotero.py item <key>                        — get full item details
  zotero.py add <json_file_or_stdin>          — add item(s) from JSON
  zotero.py add-paper                         — interactive: add a journal article
  zotero.py bibtex <collection_key>           — export collection as BibTeX
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error

CONFIG_PATH = os.path.expanduser("~/.claude/zotero_config.json")


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def api_get(config, path, params=None):
    url = f"{config['base_url']}/users/{config['user_id']}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Zotero-API-Key": config["api_key"]})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def api_post(config, path, data):
    url = f"{config['base_url']}/users/{config['user_id']}/{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Zotero-API-Key": config["api_key"],
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"Error {e.code}: {e.reason}\n{body}", file=sys.stderr)
        sys.exit(1)


def format_item(item, verbose=False):
    d = item.get("data", item)
    title = d.get("title", "(no title)")
    creators = d.get("creators", [])
    authors = []
    for c in creators:
        if "lastName" in c:
            authors.append(f"{c['lastName']}, {c.get('firstName', '')[:1]}.")
        elif "name" in c:
            authors.append(c["name"])
    author_str = "; ".join(authors[:3])
    if len(authors) > 3:
        author_str += " et al."
    year = d.get("date", "")[:4] if d.get("date") else ""
    pub = d.get("publicationTitle", d.get("bookTitle", ""))
    key = item.get("key", d.get("key", ""))

    line = f"[{key}] {author_str} ({year}). {title}"
    if pub:
        line += f". {pub}"
    if verbose:
        if d.get("abstractNote"):
            line += f"\n  Abstract: {d['abstractNote'][:200]}..."
        if d.get("DOI"):
            line += f"\n  DOI: {d['DOI']}"
        if d.get("url"):
            line += f"\n  URL: {d['url']}"
        tags = [t["tag"] for t in d.get("tags", [])]
        if tags:
            line += f"\n  Tags: {', '.join(tags)}"
    return line


def cmd_search(config, query, limit=20, verbose=False):
    print(f"Searching for: {query}\n")
    results = api_get(config, "items", {
        "q": query,
        "limit": limit,
        "itemType": "-attachment",
        "sort": "date",
        "direction": "desc",
    })
    if not results:
        print("No results found.")
        return
    for item in results:
        print(format_item(item, verbose=verbose))
    print(f"\n{len(results)} result(s)")


def cmd_collection(config, key, verbose=False):
    items = api_get(config, f"collections/{key}/items", {
        "limit": 100,
        "itemType": "-attachment",
    })
    meta = api_get(config, f"collections/{key}")
    name = meta.get("data", {}).get("name", key)
    print(f"Collection: {name} ({len(items)} items)\n")
    for item in items:
        print(format_item(item, verbose=verbose))


def cmd_collections(config):
    data = api_get(config, "collections", {"limit": 100})
    children = {}
    top = []
    for d in data:
        p = d["data"].get("parentCollection")
        if p:
            children.setdefault(p, []).append(d)
        else:
            top.append(d)

    def print_tree(items, indent=0):
        for item in sorted(items, key=lambda x: x["data"]["name"]):
            k = item["data"]["key"]
            n = item["data"]["name"]
            count = item["meta"]["numItems"]
            print("  " * indent + f"[{k}] {n} ({count} items)")
            if k in children:
                print_tree(children[k], indent + 1)

    print_tree(top)


def cmd_item(config, key):
    item = api_get(config, f"items/{key}")
    print(format_item(item, verbose=True))
    print(f"\nFull data:\n{json.dumps(item.get('data', item), indent=2)}")


def cmd_add_paper(config):
    """Interactive add for a journal article."""
    print("Adding journal article to Zotero.")
    print("(Press Enter to skip optional fields)\n")

    title = input("Title: ").strip()
    if not title:
        print("Title required.")
        sys.exit(1)

    authors_raw = input("Authors (Last, First; Last, First ...): ").strip()
    creators = []
    for a in authors_raw.split(";"):
        a = a.strip()
        if "," in a:
            last, first = a.split(",", 1)
            creators.append({"creatorType": "author", "lastName": last.strip(), "firstName": first.strip()})
        elif a:
            creators.append({"creatorType": "author", "name": a})

    journal = input("Journal: ").strip()
    year = input("Year: ").strip()
    volume = input("Volume: ").strip()
    issue = input("Issue: ").strip()
    pages = input("Pages: ").strip()
    doi = input("DOI: ").strip()
    abstract = input("Abstract (optional): ").strip()
    collection_key = input("Collection key (optional, e.g. AEPNWYJF): ").strip()

    item = {
        "itemType": "journalArticle",
        "title": title,
        "creators": creators,
        "publicationTitle": journal,
        "date": year,
        "volume": volume,
        "issue": issue,
        "pages": pages,
        "DOI": doi,
        "abstractNote": abstract,
        "collections": [collection_key] if collection_key else [],
    }

    result = api_post(config, "items", [item])
    successful = result.get("successful", {})
    if successful:
        key = list(successful.values())[0].get("key", "?")
        print(f"\nAdded: [{key}] {title}")
    else:
        print(f"\nFailed: {result.get('failed', result)}")


def cmd_add_from_json(config, source):
    """Add item(s) from a JSON file or stdin."""
    if source == "-":
        data = json.load(sys.stdin)
    else:
        with open(source) as f:
            data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    result = api_post(config, "items", data)
    successful = result.get("successful", {})
    failed = result.get("failed", {})
    print(f"Added: {len(successful)}, Failed: {len(failed)}")
    for k, v in successful.items():
        print(f"  + [{v.get('key')}] {v.get('data', {}).get('title', '?')}")
    for k, v in failed.items():
        print(f"  ✗ {v}")


def cmd_bibtex(config, key):
    url = f"{config['base_url']}/users/{config['user_id']}/collections/{key}/items"
    params = urllib.parse.urlencode({"format": "bibtex", "limit": 100})
    req = urllib.request.Request(
        f"{url}?{params}",
        headers={"Zotero-API-Key": config["api_key"]}
    )
    with urllib.request.urlopen(req) as r:
        print(r.read().decode())


def main():
    parser = argparse.ArgumentParser(description="Zotero CLI for Claude")
    sub = parser.add_subparsers(dest="cmd")

    p_search = sub.add_parser("search")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=20)
    p_search.add_argument("-v", "--verbose", action="store_true")

    p_col = sub.add_parser("collection")
    p_col.add_argument("key")
    p_col.add_argument("-v", "--verbose", action="store_true")

    sub.add_parser("collections")

    p_item = sub.add_parser("item")
    p_item.add_argument("key")

    p_add = sub.add_parser("add")
    p_add.add_argument("source", nargs="?", default="-")

    sub.add_parser("add-paper")

    p_bib = sub.add_parser("bibtex")
    p_bib.add_argument("key")

    args = parser.parse_args()
    config = load_config()

    if args.cmd == "search":
        cmd_search(config, args.query, args.limit, args.verbose)
    elif args.cmd == "collection":
        cmd_collection(config, args.key, args.verbose)
    elif args.cmd == "collections":
        cmd_collections(config)
    elif args.cmd == "item":
        cmd_item(config, args.key)
    elif args.cmd == "add":
        cmd_add_from_json(config, args.source)
    elif args.cmd == "add-paper":
        cmd_add_paper(config)
    elif args.cmd == "bibtex":
        cmd_bibtex(config, args.key)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
