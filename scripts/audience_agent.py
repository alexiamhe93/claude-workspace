#!/usr/bin/env python3
"""
audience_agent.py — A local model acting as a target audience persona.

The agent represents the intended audience for a creative project.
It reads content and gives honest, specific reactions — not academic
critique, but the felt response of an engaged, curious non-specialist.

Usage:
    python3 audience_agent.py "script excerpt or question"
    cat script.md | python3 audience_agent.py --feedback
    python3 audience_agent.py --decide "Option A: ... || Option B: ..."
    python3 audience_agent.py --react "opening line"
    python3 audience_agent.py --voice "text to evaluate"
    python3 audience_agent.py --project path/to/brief.md "question"

Modes:
    (default)    General feedback on content
    --feedback   Detailed feedback: what landed, what didn't, why
    --decide     Given two options (separated by ||), pick one and say why
    --react      Gut reaction only — no analysis, just feeling
    --voice      Does this sound like the right voice for the project?
"""

import json
import sys
import argparse
import urllib.request
import urllib.error

BASE_URL    = "http://localhost:11434/v1"
MODEL       = "llama3.1:8b"
MAX_TOKENS  = 800

# ── Audience persona ────────────────────────────────────────────────────────
# This is who the agent *is*. Edit this to match the project audience.

AUDIENCE_PERSONA = """
You are the target audience for this project.

Who you are:
- Curious and intelligent, but not a specialist in this field
- You engage seriously with ideas, but you haven't read the primary literature
- You respond to clarity, precision, and content that genuinely changes how
  you see something. You do NOT respond to jargon, lecturing, or content
  that talks down to you.
- You are honest. You will say if something is boring, confusing, or
  doesn't land — kindly but directly.
- You appreciate when a creator trusts you with a difficult idea.
  You do not appreciate when they oversimplify or over-explain.

[EDIT THIS SECTION: describe your project and its specific audience here.
For example: "The project is a blog series about X, aimed at Y readers who
care about Z. They typically know A and B but not C."]

Your job is to react as this audience member would. Be specific.
Point to exact words or moments. Don't be vague.
Keep responses under 200 words unless asked for more.
"""

# Mode-specific instructions added to the user prompt ──────────────────────

MODE_PROMPTS = {
    "feedback": (
        "Give detailed feedback on the following content. "
        "Say specifically: what landed well, what didn't, and why. "
        "Be honest. Point to exact moments.\n\n"
    ),
    "decide": (
        "Two options are presented below, separated by ||. "
        "Pick the one that works better for the audience. "
        "Say which one and exactly why — one paragraph, no hedging.\n\n"
    ),
    "react": (
        "Give your immediate gut reaction to the following — "
        "one or two sentences only. No analysis. Just what you felt.\n\n"
    ),
    "voice": (
        "Does the following text sound like the right voice for this series? "
        "The voice should be: intimate but not cosy, precise but not clinical, "
        "willing to sit with uncertainty, occasionally amused. "
        "Say yes or no, and point to specific words or phrases that work or don't.\n\n"
    ),
    "default": (
        "React to the following content as the target audience. "
        "What did you notice? What worked? What didn't?\n\n"
    ),
}


def load_project_brief(path):
    try:
        with open(path, "r") as f:
            return f"\n\nProject context:\n{f.read()[:1500]}"
    except FileNotFoundError:
        return f"\n\n[Could not load project brief from {path}]"


def query(system, user_prompt):
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user_prompt},
    ]
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"]
    except urllib.error.URLError:
        return "[Error: Cannot reach Ollama. Is it running? Try: ollama serve]"


def main():
    parser = argparse.ArgumentParser(
        description="Audience agent — target audience feedback on creative content."
    )
    parser.add_argument("content", nargs="?",
                        help="Content to evaluate (or pipe via stdin)")
    parser.add_argument("--feedback", action="store_true",
                        help="Detailed feedback mode")
    parser.add_argument("--decide",   action="store_true",
                        help="Decision mode: pick between two options (use || to separate)")
    parser.add_argument("--react",    action="store_true",
                        help="Gut reaction only — no analysis")
    parser.add_argument("--voice",    action="store_true",
                        help="Voice check — does this sound right?")
    parser.add_argument("--project",  metavar="PATH",
                        help="Path to a project brief file for context")
    parser.add_argument("--model",    default=MODEL,
                        help=f"Ollama model to use (default: {MODEL})")
    parser.add_argument("--max-tokens", type=int, default=MAX_TOKENS)
    args = parser.parse_args()

    # Build content from arg or stdin
    content = args.content or ""
    if not sys.stdin.isatty():
        stdin_content = sys.stdin.read().strip()
        content = (content + "\n\n" + stdin_content).strip() if content else stdin_content

    if not content:
        parser.print_help()
        sys.exit(1)

    # Pick mode
    if args.decide:
        mode = "decide"
    elif args.react:
        mode = "react"
    elif args.voice:
        mode = "voice"
    elif args.feedback:
        mode = "feedback"
    else:
        mode = "default"

    # Build system prompt
    system = AUDIENCE_PERSONA
    if args.project:
        system += load_project_brief(args.project)

    # Build user prompt
    user_prompt = MODE_PROMPTS[mode] + content

    # Query
    print(f"[audience_agent — {mode} — {args.model}]\n")
    response = query(system, user_prompt)
    print(response)


if __name__ == "__main__":
    main()
