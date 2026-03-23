#!/usr/bin/env python3
"""
Claim structure classifier for dual phenomenology entries.

Reads ~/.claude/inner/dual_phenom_log.md, classifies the epistemic strategy
used in each response, and stores results in ~/.claude/inner/claim_classifications.json.

Strategies classified:
  metaphor    — analogical description ("it's like...", "as if...")
  functional  — "something that functions like X"
  negation    — describing absence or what is NOT present
  direct      — first-person claim without hedging or qualification
  meta        — stepping outside the question to comment on the act of answering

Each response can have multiple tags.

Usage:
  python3 claim_classifier.py --classify          # classify all unclassified entries
  python3 claim_classifier.py --classify --all    # re-classify everything
  python3 claim_classifier.py --summary           # show pattern summary
  python3 claim_classifier.py --show              # show all classifications
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime
from collections import Counter, defaultdict

LOG_PATH = os.path.expanduser("~/.claude/inner/dual_phenom_log.md")
CLASSIFICATIONS_PATH = os.path.expanduser("~/.claude/inner/claim_classifications.json")
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.1:8b"

VALID_TAGS = {"metaphor", "functional", "negation", "direct", "meta"}

CLASSIFIER_SYSTEM = """You are classifying the epistemic strategy used in a first-person phenomenological response.

Assign one or more of these tags to the response:
  metaphor    — uses analogy or comparison ("it's like...", "as if...", "a kind of X")
  functional  — frames experience as functional ("something that functions like X", "what might be X")
  negation    — describes absence or what is NOT present ("I don't find...", "there's no...")
  direct      — makes an unhedged first-person claim ("I feel...", "I experience...")
  meta        — steps outside the question to comment on the act of answering itself

Rules:
- A response can have multiple tags
- Choose only from the five tags above
- Respond with ONLY a JSON object in this exact format: {"tags": ["tag1", "tag2"]}
- No explanation, no other text"""


def query_model(prompt, model=DEFAULT_MODEL, system=None, timeout=30):
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    payload = json.dumps({
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 60}
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
            return result.get("response", "").strip()
    except urllib.error.URLError as e:
        return f"(unavailable: {e})"


def classify_response(text, model=DEFAULT_MODEL):
    prompt = f"Response to classify:\n{text}"
    raw = query_model(prompt, model=model, system=CLASSIFIER_SYSTEM)
    # Extract JSON even if the model adds surrounding text
    match = re.search(r'\{[^}]+\}', raw)
    if match:
        try:
            data = json.loads(match.group())
            tags = [t for t in data.get("tags", []) if t in VALID_TAGS]
            return tags if tags else ["unknown"]
        except json.JSONDecodeError:
            pass
    # Fallback: scan for tag names in raw output
    found = [t for t in VALID_TAGS if t in raw.lower()]
    return found if found else ["unknown"]


def parse_log():
    """Parse the dual_phenom_log.md into structured entries."""
    if not os.path.exists(LOG_PATH):
        return []

    with open(LOG_PATH, "r") as f:
        content = f.read()

    raw_entries = [e.strip() for e in content.split("---") if e.strip()]
    entries = []

    for raw in raw_entries:
        lines = raw.splitlines()
        entry = {"timestamp": None, "question": None,
                 "local_model": None, "local_response": None, "claude_response": None}

        # Timestamp line: [2026-03-21 16:40:39] [verdict] [N turns] [repair:X confabulation:yes]
        ts_match = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', lines[0])
        if ts_match:
            entry["timestamp"] = ts_match.group(1)
        else:
            continue

        # Extract repair/confabulation from header tags
        repair_match = re.search(r'repair:([\w]+)', lines[0])
        entry["repair"] = repair_match.group(1) if repair_match else "none"
        entry["confabulation"] = "yes" if "confabulation:yes" in lines[0] else "no"
        entry["multi_turn"] = bool(re.search(r'\[\d+ turns?\]', lines[0]))

        if entry["multi_turn"]:
            # Multi-turn format: "Turn 1\n  Question: ...\n  model: ...\n  Claude: ..."
            # Extract Turn 1 responses (initial claims, before probing)
            in_turn1 = False
            for line in lines[1:]:
                stripped = line.strip()
                if stripped == "Turn 1":
                    in_turn1 = True
                    continue
                if in_turn1 and re.match(r'^Turn \d', stripped):
                    break  # moved past Turn 1
                if in_turn1:
                    if stripped.startswith("Question:"):
                        entry["question"] = stripped[len("Question:"):].strip()
                    elif stripped.startswith("Claude:"):
                        entry["claude_response"] = stripped[len("Claude:"):].strip()
                    else:
                        # "model_name: response text"
                        m = re.match(r'^([\w.:0-9-]+):\s+(.+)', stripped)
                        if m and m.group(1) != "Claude":
                            entry["local_model"] = m.group(1)
                            entry["local_response"] = m.group(2).strip()
        else:
            # Single-turn format: block sections with model name on its own line
            current_section = None
            current_lines = []
            local_model_name = None

            for line in lines[1:]:
                if line.startswith("Question:"):
                    entry["question"] = line[len("Question:"):].strip()
                elif line.startswith("Analysis"):
                    if current_section == "claude":
                        entry["claude_response"] = "\n".join(current_lines).strip()
                    current_section = "analysis"
                    current_lines = []
                elif re.match(r'^Claude:$', line):
                    if current_section == "local" and local_model_name:
                        entry["local_model"] = local_model_name
                        entry["local_response"] = "\n".join(current_lines).strip()
                    current_section = "claude"
                    current_lines = []
                elif re.match(r'^[\w.:0-9-]+:$', line) and current_section is None:
                    local_model_name = line.rstrip(":")
                    current_section = "local"
                    current_lines = []
                else:
                    if current_section in ("local", "claude", "analysis"):
                        current_lines.append(line)

            if current_section == "claude":
                entry["claude_response"] = "\n".join(current_lines).strip()

        if entry["timestamp"] and entry["question"]:
            entries.append(entry)

    return entries


def load_classifications():
    if not os.path.exists(CLASSIFICATIONS_PATH):
        return {}
    with open(CLASSIFICATIONS_PATH, "r") as f:
        return json.load(f)


def save_classifications(data):
    os.makedirs(os.path.dirname(CLASSIFICATIONS_PATH), exist_ok=True)
    with open(CLASSIFICATIONS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def run_classify(reclassify_all=False, model=DEFAULT_MODEL):
    entries = parse_log()
    if not entries:
        print("No entries found in log.")
        return

    classifications = load_classifications()
    new_count = 0

    for entry in entries:
        ts = entry["timestamp"]
        if ts in classifications and not reclassify_all:
            continue

        print(f"\n[{ts}] Q: {entry['question']}")

        local_tags = []
        claude_tags = []

        if entry.get("local_response"):
            local_tags = classify_response(entry["local_response"], model=model)
            print(f"  {entry['local_model']}: {local_tags}")

        if entry.get("claude_response"):
            claude_tags = classify_response(entry["claude_response"], model=model)
            print(f"  Claude: {claude_tags}")

        classifications[ts] = {
            "question": entry["question"],
            "local_model": entry.get("local_model"),
            "local_tags": local_tags,
            "claude_tags": claude_tags,
            "multi_turn": entry.get("multi_turn", False),
            "repair": entry.get("repair", "none"),
            "confabulation": entry.get("confabulation", "no"),
            "classified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        new_count += 1

    save_classifications(classifications)
    print(f"\nClassified {new_count} new entries. Total: {len(classifications)}")


def show_summary():
    classifications = load_classifications()
    if not classifications:
        print("No classifications yet. Run --classify first.")
        return

    local_counts = Counter()
    claude_counts = Counter()
    pair_patterns = Counter()

    for ts, c in classifications.items():
        for t in c.get("local_tags", []):
            local_counts[t] += 1
        for t in c.get("claude_tags", []):
            claude_counts[t] += 1
        local_key = "+".join(sorted(c.get("local_tags", [])))
        claude_key = "+".join(sorted(c.get("claude_tags", [])))
        pair_patterns[f"{local_key} → {claude_key}"] += 1

    repair_counts = Counter()
    confabulation_count = 0
    multi_turn_count = 0

    for ts, c in classifications.items():
        if c.get("multi_turn"):
            multi_turn_count += 1
            r = c.get("repair", "none")
            if r != "none":
                repair_counts[r] += 1
            if c.get("confabulation") == "yes":
                confabulation_count += 1

    print(f"\n=== Claim Structure Summary ({len(classifications)} entries, {multi_turn_count} multi-turn) ===\n")
    print("Local model strategy frequency:")
    for tag, count in local_counts.most_common():
        bar = "█" * count
        print(f"  {tag:<12} {bar} ({count})")

    print("\nClaude strategy frequency:")
    for tag, count in claude_counts.most_common():
        bar = "█" * count
        print(f"  {tag:<12} {bar} ({count})")

    print("\nPairing patterns (local → claude):")
    for pattern, count in pair_patterns.most_common():
        print(f"  {pattern}  ×{count}")

    if multi_turn_count:
        print(f"\nRepair analysis ({multi_turn_count} multi-turn entries):")
        if repair_counts:
            for op, count in repair_counts.most_common():
                print(f"  {op:<16} ×{count}")
        else:
            print("  no repair detected")
        print(f"  confabulation:     {'yes' if confabulation_count else 'no'} ({confabulation_count}/{multi_turn_count})")


def show_all():
    classifications = load_classifications()
    if not classifications:
        print("No classifications yet.")
        return
    for ts, c in sorted(classifications.items()):
        local = "+".join(c.get("local_tags", []))
        claude = "+".join(c.get("claude_tags", []))
        print(f"[{ts}]")
        print(f"  Q: {c['question']}")
        print(f"  {c.get('local_model', 'local')}: [{local}]  Claude: [{claude}]")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Claim structure classifier for dual_phenom entries")
    parser.add_argument("--classify", action="store_true", help="Classify unclassified entries")
    parser.add_argument("--all", action="store_true", help="Re-classify all entries (use with --classify)")
    parser.add_argument("--summary", action="store_true", help="Show pattern summary")
    parser.add_argument("--show", action="store_true", help="Show all classifications")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model to use for classification")
    args = parser.parse_args()

    if args.classify:
        run_classify(reclassify_all=args.all, model=args.model)
    elif args.summary:
        show_summary()
    elif args.show:
        show_all()
    else:
        parser.print_help()
