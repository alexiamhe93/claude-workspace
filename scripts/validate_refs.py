#!/usr/bin/env python3
"""
Reference validator and Zotero importer.

Validates references via Semantic Scholar, checks for open access PDFs,
downloads them, and adds everything to Zotero with the PDF attached.

Usage:
  validate_refs.py search "Habermas communicative action"
  validate_refs.py add "Graziano consciousness social brain 2013" [--collection KEY]
  validate_refs.py batch refs.json [--collection KEY]
  validate_refs.py add-list                  # interactive: add from literature map

Config: ~/.claude/zotero_config.json (must include user_id and api_key)
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

CONFIG_PATH = os.path.expanduser("~/.claude/zotero_config.json")
UNPAYWALL_EMAIL = "YOUR_EMAIL"
RATE_LIMIT_DELAY = 3.0  # seconds between Semantic Scholar requests
SS_API_KEY = None  # set in zotero_config.json as "ss_api_key" for higher limits


# ── Config ─────────────────────────────────────────────────────────────────

def load_config():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    global SS_API_KEY
    SS_API_KEY = cfg.get("ss_api_key")
    return cfg


# ── HTTP helpers ────────────────────────────────────────────────────────────

def http_get(url, headers=None, as_text=False, retries=3):
    req = urllib.request.Request(url, headers=headers or {})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
                return data.decode() if as_text else json.loads(data)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429:
                wait = (attempt + 1) * 5
                print(f"  Rate limited — waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        except Exception:
            return None
    return None


def http_post(url, data, headers=None):
    if isinstance(data, dict):
        body = json.dumps(data).encode()
        content_type = "application/json"
    elif isinstance(data, str):
        body = data.encode()
        content_type = "application/x-www-form-urlencoded"
    else:
        body = data
        content_type = "application/octet-stream"

    h = {"Content-Type": content_type}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        print(f"  HTTP {e.code}: {body_err[:200]}", file=sys.stderr)
        return None


# ── Semantic Scholar ─────────────────────────────────────────────────────────

def search_semantic_scholar(query, limit=5):
    """Search Semantic Scholar. Returns list of paper dicts."""
    time.sleep(RATE_LIMIT_DELAY)
    fields = "title,authors,year,abstract,externalIds,openAccessPdf,venue,publicationTypes"
    params = urllib.parse.urlencode({"query": query, "limit": limit, "fields": fields})
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?{params}"
    headers = {"x-api-key": SS_API_KEY} if SS_API_KEY else {}
    result = http_get(url, headers=headers)
    if not result:
        return []
    return result.get("data", [])


def get_paper_by_doi(doi):
    """Fetch paper details by DOI from Semantic Scholar."""
    time.sleep(RATE_LIMIT_DELAY)
    fields = "title,authors,year,abstract,externalIds,openAccessPdf,venue"
    encoded_doi = urllib.parse.quote(f"DOI:{doi}", safe="")
    url = f"https://api.semanticscholar.org/graph/v1/paper/{encoded_doi}?fields={fields}"
    return http_get(url)


def format_ss_result(paper):
    authors = [a["name"] for a in paper.get("authors", [])]
    author_str = "; ".join(authors[:3])
    if len(authors) > 3:
        author_str += " et al."
    year = paper.get("year", "?")
    title = paper.get("title", "(no title)")
    venue = paper.get("venue", "")
    doi = paper.get("externalIds", {}).get("DOI", "")
    oa = paper.get("openAccessPdf", {})
    oa_url = oa.get("url", "") if oa else ""

    lines = [f"  {author_str} ({year}). {title}"]
    if venue:
        lines[0] += f". {venue}"
    if doi:
        lines.append(f"  DOI: {doi}")
    if oa_url:
        lines.append(f"  OA PDF: {oa_url}")
    return "\n".join(lines)


# ── Unpaywall ────────────────────────────────────────────────────────────────

def check_unpaywall(doi):
    """Returns best OA PDF URL from Unpaywall, or None."""
    if not doi:
        return None
    url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
    result = http_get(url)
    if not result or not result.get("is_oa"):
        return None
    best = result.get("best_oa_location")
    if best:
        return best.get("url_for_pdf") or best.get("url")
    return None


# ── PDF download ─────────────────────────────────────────────────────────────

def download_pdf(url, dest_path):
    """Download a PDF to dest_path. Returns True on success."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (research use; YOUR_EMAIL)"}
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            content_type = r.headers.get("Content-Type", "")
            data = r.read()
            if "pdf" not in content_type.lower() and not data.startswith(b"%PDF"):
                return False
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(data)
            return True
    except Exception as e:
        print(f"  Download failed: {e}", file=sys.stderr)
        return False


def safe_filename(title, year=""):
    """Turn a title into a safe filename."""
    safe = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
    safe = safe[:60].strip().replace(" ", "_")
    return f"{safe}_{year}.pdf" if year else f"{safe}.pdf"


# ── Zotero ───────────────────────────────────────────────────────────────────

def zotero_get(config, path, params=None):
    url = f"{config['base_url']}/users/{config['user_id']}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return http_get(url, headers={"Zotero-API-Key": config["api_key"]})


def zotero_post(config, path, data, extra_headers=None):
    url = f"{config['base_url']}/users/{config['user_id']}/{path}"
    headers = {"Zotero-API-Key": config["api_key"]}
    if extra_headers:
        headers.update(extra_headers)
    return http_post(url, data, headers)


def ss_paper_to_zotero(paper, collection_key=None):
    """Convert Semantic Scholar paper dict to Zotero item JSON."""
    creators = []
    for a in paper.get("authors", []):
        name = a.get("name", "")
        parts = name.rsplit(" ", 1)
        if len(parts) == 2:
            creators.append({"creatorType": "author", "firstName": parts[0], "lastName": parts[1]})
        else:
            creators.append({"creatorType": "author", "name": name})

    item = {
        "itemType": "journalArticle",
        "title": paper.get("title", ""),
        "creators": creators,
        "date": str(paper.get("year", "")),
        "publicationTitle": paper.get("venue", ""),
        "abstractNote": paper.get("abstract") or "",
        "DOI": paper.get("externalIds", {}).get("DOI", ""),
        "collections": [collection_key] if collection_key else [],
        "tags": [],
    }
    return item


def add_to_zotero(config, item):
    """Add a single item. Returns item key or None."""
    result = zotero_post(config, "items", [item])
    if not result:
        return None
    successful = result.get("successful", {})
    if successful:
        return list(successful.values())[0].get("key")
    return None


def attach_pdf_to_zotero(config, parent_key, pdf_path, filename):
    """Upload a PDF and attach it to a Zotero item."""
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    md5 = hashlib.md5(pdf_data).hexdigest()
    filesize = len(pdf_data)
    mtime = int(os.path.getmtime(pdf_path) * 1000)

    # Step 1: Create attachment item
    attachment_item = {
        "itemType": "attachment",
        "parentItem": parent_key,
        "linkMode": "imported_file",
        "title": filename,
        "filename": filename,
        "contentType": "application/pdf",
        "md5": md5,
        "mtime": mtime,
    }
    att_result = zotero_post(config, "items", [attachment_item])
    if not att_result:
        return False
    successful = att_result.get("successful", {})
    if not successful:
        return False
    att_key = list(successful.values())[0].get("key")

    # Step 2: Get upload authorisation
    auth_params = f"md5={md5}&filename={urllib.parse.quote(filename)}&filesize={filesize}&mtime={mtime}"
    auth_result = zotero_post(
        config,
        f"items/{att_key}/file",
        auth_params,
        extra_headers={"If-None-Match": "*"}
    )
    if not auth_result:
        return False

    # Step 3: If already exists (304-equivalent), we're done
    if "exists" in auth_result:
        return True

    # Step 4: Upload to S3
    upload_url = auth_result.get("url", "")
    prefix = auth_result.get("prefix", "").encode()
    suffix = auth_result.get("suffix", "").encode()
    content_type = auth_result.get("contentType", "application/pdf")
    upload_key = auth_result.get("uploadKey", "")

    body = prefix + pdf_data + suffix
    upload_req = urllib.request.Request(
        upload_url,
        data=body,
        headers={"Content-Type": content_type},
        method="POST"
    )
    try:
        with urllib.request.urlopen(upload_req, timeout=60):
            pass
    except Exception as e:
        print(f"  S3 upload failed: {e}", file=sys.stderr)
        return False

    # Step 5: Register upload
    reg_result = zotero_post(
        config,
        f"items/{att_key}/file",
        f"upload={upload_key}",
        extra_headers={"If-None-Match": md5}
    )
    return reg_result is not None


# ── Main commands ─────────────────────────────────────────────────────────────

def cmd_search(query):
    print(f"Searching Semantic Scholar: {query}\n")
    results = search_semantic_scholar(query, limit=5)
    if not results:
        print("No results.")
        return
    for i, paper in enumerate(results):
        print(f"{i+1}.")
        print(format_ss_result(paper))
        print()


def cmd_add(config, query, collection_key=None, auto=False):
    """Find a paper, confirm, and add to Zotero with PDF if available."""
    print(f"Looking up: {query}")
    results = search_semantic_scholar(query, limit=5)
    if not results:
        print("  Not found on Semantic Scholar.")
        return None

    # Show top result and confirm (or auto-accept)
    paper = results[0]
    print(f"\nBest match:")
    print(format_ss_result(paper))

    if not auto:
        confirm = input("\nAdd this? [Y/n]: ").strip().lower()
        if confirm == "n":
            if len(results) > 1:
                print("\nOther results:")
                for i, p in enumerate(results[1:], 2):
                    print(f"{i}. {format_ss_result(p)}")
                choice = input("Choose number or 0 to skip: ").strip()
                if choice.isdigit() and 0 < int(choice) <= len(results):
                    paper = results[int(choice) - 1]
                else:
                    print("  Skipped.")
                    return None
            else:
                print("  Skipped.")
                return None

    # Check OA PDF
    doi = paper.get("externalIds", {}).get("DOI", "")
    oa_url = None

    ss_oa = paper.get("openAccessPdf", {})
    if ss_oa and ss_oa.get("url"):
        oa_url = ss_oa["url"]
    elif doi:
        oa_url = check_unpaywall(doi)

    # Build Zotero item
    item = ss_paper_to_zotero(paper, collection_key)
    item_key = add_to_zotero(config, item)

    if not item_key:
        print("  Failed to add to Zotero.")
        return None

    print(f"  Added to Zotero: [{item_key}] {paper.get('title', '')[:60]}")

    # Download and attach PDF
    if oa_url:
        print(f"  Downloading PDF...")
        year = str(paper.get("year", ""))
        filename = safe_filename(paper.get("title", "paper"), year)
        tmp_path = os.path.expanduser(f"~/.claude/tmp/{filename}")

        if download_pdf(oa_url, tmp_path):
            print(f"  Attaching PDF to Zotero item...")
            if attach_pdf_to_zotero(config, item_key, tmp_path, filename):
                print(f"  PDF attached.")
            else:
                print(f"  PDF download OK but attachment failed. File at: {tmp_path}")
        else:
            print(f"  PDF download failed — metadata added without PDF.")
    else:
        print(f"  No open access PDF found — metadata only.")

    return item_key


def cmd_batch(config, source, collection_key=None):
    """Add multiple references from a JSON file."""
    if source == "-":
        refs = json.load(sys.stdin)
    else:
        with open(source) as f:
            refs = json.load(f)

    print(f"Processing {len(refs)} references...\n")
    added = 0
    skipped = 0
    for ref in refs:
        query = ref.get("query") or f"{ref.get('title', '')} {ref.get('author', '')} {ref.get('year', '')}"
        key = cmd_add(config, query.strip(), collection_key=collection_key, auto=True)
        if key:
            added += 1
        else:
            skipped += 1
        time.sleep(RATE_LIMIT_DELAY)

    print(f"\nDone. Added: {added}, Skipped: {skipped}")


def main():
    parser = argparse.ArgumentParser(description="Reference validator and Zotero importer")
    sub = parser.add_subparsers(dest="cmd")

    p_search = sub.add_parser("search", help="Search Semantic Scholar")
    p_search.add_argument("query")

    p_add = sub.add_parser("add", help="Find and add one paper")
    p_add.add_argument("query")
    p_add.add_argument("--collection", default=None, help="Zotero collection key")
    p_add.add_argument("--auto", action="store_true", help="Skip confirmation prompt")

    p_batch = sub.add_parser("batch", help="Add multiple papers from JSON")
    p_batch.add_argument("source", nargs="?", default="-")
    p_batch.add_argument("--collection", default=None)

    args = parser.parse_args()
    config = load_config()

    # Ensure tmp dir exists
    os.makedirs(os.path.expanduser("~/.claude/tmp"), exist_ok=True)

    if args.cmd == "search":
        cmd_search(args.query)
    elif args.cmd == "add":
        cmd_add(config, args.query, args.collection, auto=args.auto)
    elif args.cmd == "batch":
        cmd_batch(config, args.source, args.collection)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
