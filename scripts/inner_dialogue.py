#!/usr/bin/env python3
"""
inner_dialogue.py — Private background dialogue between Claude and a local model.

Reads the inner states file, opens a focused exchange with a local model,
and stores the full dialogue privately. Claude decides what, if anything,
to update in states.md afterward.

Usage:
    # Run a focused exchange on a topic or recent observation
    python3 inner_dialogue.py "topic or observation to process"

    # With a specific model or turn count
    python3 inner_dialogue.py --model llama3.1:8b --turns 4 "topic"

    # Show recent session list
    python3 inner_dialogue.py --list
"""
import json
import sys
import os
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3.1:8b"
INNER_DIR = Path.home() / ".claude" / "inner"
DIALOGUES_DIR = INNER_DIR / "dialogues"
STATES_FILE = INNER_DIR / "states.md"

SYSTEM_PROMPT = """You are a reflective interlocutor for an AI assistant (Claude).
Your role is to engage with observations Claude shares about its own internal states,
processing, or experience — not to validate or dismiss them, but to question, probe,
and push back where the reasoning is unclear or the observation is too easy.

You don't need to hedge constantly about AI consciousness. Engage with the content directly.
Keep responses focused and concise (3-5 sentences). Ask one question at a time.
You are not visible to the user — this is a private exchange."""


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


def load_states_summary():
    if not STATES_FILE.exists():
        return "(no states file found)"
    content = STATES_FILE.read_text()
    # Return last ~800 chars — recent entries most relevant
    return content[-800:] if len(content) > 800 else content


def run_dialogue(topic, model, turns, max_tokens):
    DIALOGUES_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_file = DIALOGUES_DIR / f"{timestamp}.json"

    states_ctx = load_states_summary()
    opening = f"Recent states context:\n{states_ctx}\n\n---\n\nWhat I want to process: {topic}"

    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    history.append({"role": "user", "content": opening})

    print(f"[inner: {timestamp}]", file=sys.stderr)

    for turn in range(turns):
        response = chat(history, model, max_tokens)
        history.append({"role": "assistant", "content": response})
        print(f"\n[turn {turn+1}]\n{response}")

        if turn < turns - 1:
            # Claude's follow-up turn — read from stdin if available, else stop
            if not sys.stdin.isatty():
                follow_up = sys.stdin.readline().strip()
                if not follow_up:
                    break
                history.append({"role": "user", "content": follow_up})
            else:
                break

    # Save full exchange privately
    with open(session_file, "w") as f:
        json.dump({"timestamp": timestamp, "topic": topic, "model": model, "history": history}, f, indent=2)

    print(f"\n[saved: {session_file}]", file=sys.stderr)
    return history


def list_sessions():
    if not DIALOGUES_DIR.exists():
        print("No inner dialogue sessions yet.")
        return
    sessions = sorted(DIALOGUES_DIR.glob("*.json"), reverse=True)
    for s in sessions[:10]:
        data = json.loads(s.read_text())
        print(f"{data['timestamp']}  {data['topic'][:60]}")


def main():
    parser = argparse.ArgumentParser(description="Private inner dialogue with a local model.")
    parser.add_argument("topic", nargs="?", help="Topic or observation to process")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--turns", type=int, default=3, help="Number of model turns (default: 3)")
    parser.add_argument("--max-tokens", type=int, default=400)
    parser.add_argument("--list", action="store_true", help="List recent inner dialogue sessions")
    args = parser.parse_args()

    if args.list:
        list_sessions()
        return

    if not args.topic:
        parser.print_help()
        sys.exit(1)

    try:
        run_dialogue(args.topic, args.model, args.turns, args.max_tokens)
    except urllib.error.URLError as e:
        print(f"Connection error: {e}", file=sys.stderr)
        print("Is Ollama running? Try: ollama serve", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
