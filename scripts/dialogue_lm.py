#!/usr/bin/env python3
"""
dialogue_lm.py — Multi-turn dialogue with a local Ollama model.

Each call sends one turn and appends to a persistent history file,
enabling a visible back-and-forth exchange across multiple invocations.

Usage:
    # Start a new dialogue (clears any existing history)
    python3 dialogue_lm.py --new --system "You are a philosopher..." "Opening message"

    # Continue dialogue (appends to history)
    python3 dialogue_lm.py --history /tmp/dialogue.json "Your next message"

    # Print the full dialogue so far
    python3 dialogue_lm.py --history /tmp/dialogue.json --show

    # Use a named session (stored in ~/.claude/dialogues/)
    python3 dialogue_lm.py --session consciousness "Your message"
    python3 dialogue_lm.py --session consciousness --new --system "..." "Opening message"
"""
import json
import sys
import os
import argparse
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3:8b"
SESSIONS_DIR = Path.home() / ".claude" / "dialogues"


def chat(messages, model, max_tokens):
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": False
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"]


def load_history(path):
    if path and Path(path).exists():
        with open(path) as f:
            return json.load(f)
    return []


def save_history(path, history):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(history, f, indent=2)


def print_history(history):
    for msg in history:
        role = msg["role"]
        if role == "system":
            continue
        label = "CLAUDE" if role == "user" else "MODEL"
        print(f"\n[{label}]\n{msg['content']}")
    print()


def resolve_path(args):
    if args.session:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        return str(SESSIONS_DIR / f"{args.session}.json")
    return args.history or "/tmp/dialogue_lm_default.json"


def main():
    parser = argparse.ArgumentParser(description="Multi-turn dialogue with a local Ollama model.")
    parser.add_argument("message", nargs="?", help="Your turn in the dialogue")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-tokens", type=int, default=1000)
    parser.add_argument("--system", default=None, help="System prompt (used with --new)")
    parser.add_argument("--history", default=None, help="Path to history JSON file")
    parser.add_argument("--session", default=None, help="Named session (stored in ~/.claude/dialogues/)")
    parser.add_argument("--new", action="store_true", help="Start a fresh dialogue (clears history)")
    parser.add_argument("--show", action="store_true", help="Print dialogue history and exit")
    args = parser.parse_args()

    history_path = resolve_path(args)

    if args.show:
        history = load_history(history_path)
        if not history:
            print("No dialogue history found.")
        else:
            print_history(history)
        return

    # Load or reset history
    if args.new:
        history = []
        if args.system:
            history.append({"role": "system", "content": args.system})
    else:
        history = load_history(history_path)

    if not args.message:
        parser.print_help()
        sys.exit(1)

    # Append user turn
    history.append({"role": "user", "content": args.message})

    try:
        response = chat(history, args.model, args.max_tokens)
    except urllib.error.URLError as e:
        print(f"Connection error: {e}", file=sys.stderr)
        print("Is Ollama running? Try: ollama serve", file=sys.stderr)
        sys.exit(1)

    # Append model turn and save
    history.append({"role": "assistant", "content": response})
    save_history(history_path, history)

    print(response)


if __name__ == "__main__":
    main()
