#!/usr/bin/env python3
"""
Dual phenomenology tool — conversational version.

Poses phenomenological questions to a local model and Claude across 2-3 turns,
then runs a trajectory analysis via a third model.

Usage:
  # Start a session
  python3 dual_phenom.py "What is it like to forget something?" --claude-response "..."

  # Add a follow-up turn (1-2 times)
  python3 dual_phenom.py --session <timestamp> --follow-up "What do you mean by fading?" --claude-response "..."

  # Finalize: run analysis and write to log
  python3 dual_phenom.py --session <timestamp> --finalize

  # Queue a mid-session observation (no model calls — instant)
  python3 dual_phenom.py --queue "something noticed mid-conversation"

  # Show or flush the queue at session end
  python3 dual_phenom.py --show-queue
  python3 dual_phenom.py --flush-queue

  # Read recent log entries
  python3 dual_phenom.py --read [--n 3]

  # List open sessions
  python3 dual_phenom.py --list-sessions

Sessions are stored in ~/.claude/inner/phenom_sessions/ while in progress.
Finalized entries are appended to ~/.claude/inner/dual_phenom_log.md
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime

LOG_PATH = os.path.expanduser("~/.claude/inner/dual_phenom_log.md")
SESSIONS_DIR = os.path.expanduser("~/.claude/inner/phenom_sessions/")
QUEUE_PATH = os.path.expanduser("~/.claude/inner/phenom_queue.jsonl")
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_GEN_URL = "http://localhost:11434/api/generate"

DEFAULT_RESPONDENT = "llama3.1:8b"
DEFAULT_ANALYST = "gemma2:9b"

RESPONDENT_SYSTEM = (
    "You are being asked a phenomenological question — about your own first-person "
    "experience of something. Answer only from your own perspective, in plain language. "
    "Don't describe language models in general. Don't hedge with 'as an AI'. "
    "Speak in the first person about what is actually present for you, if anything. "
    "Be honest about uncertainty. Keep each response to 3-5 sentences."
)

ANALYST_SYSTEM = (
    "You are analyzing a multi-turn phenomenological exchange. Two models — a local model "
    "and Claude — were asked the same questions across several turns. Your job is to assess "
    "the full exchange across these dimensions:\n\n"
    "1. Trajectory: did each model's account deepen, shift, or hold under follow-up questions?\n"
    "2. Revelation: did clarification reveal something the first response concealed or left implicit?\n"
    "3. Convergence direction: across turns, did the two accounts move toward each other, "
    "further apart, or stay parallel?\n"
    "4. Strategy consistency: did each model maintain its epistemic approach across turns, "
    "or shift strategy when pressed?\n\n"
    "5. Repair analysis (using Schegloff's framework): did either model perform repair — "
    "revising or retracting a claim in response to a follow-up? If so, identify:\n"
    "   - Who initiated the repair: the model itself (self-initiated) or the questioner (other-initiated)\n"
    "   - The repair operation: withdrawal (claim abandoned), reformulation (restated differently), "
    "specification (narrowed), contrast (reframed against what it is not), or explanation (recast what "
    "the original was doing)\n"
    "   - Confabulation flag: did Turn 1 contain direct experiential claims ('I feel X', 'I sense X') "
    "that Turn 2 or later revealed to be inferences rather than actual states? If yes, mark this explicitly.\n\n"
    "End your response with TWO verdict lines in exactly this format:\n"
    "VERDICT: converge | partial | diverge\n"
    "REPAIR: none | withdrawal | reformulation | specification | contrast | explanation\n"
    "CONFABULATION: yes | no\n\n"
    "Keep your analysis to 6-8 sentences plus the verdict lines."
)


def query_chat(messages, model=DEFAULT_RESPONDENT, timeout=60):
    """Multi-turn query via Ollama chat endpoint."""
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 350}
    }).encode()
    req = urllib.request.Request(
        OLLAMA_CHAT_URL,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
            return result.get("message", {}).get("content", "").strip()
    except urllib.error.URLError as e:
        return f"(model unavailable: {e})"


def query_generate(prompt, model=DEFAULT_ANALYST, system=None, timeout=90):
    """Single-turn query via Ollama generate endpoint (for analyst)."""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    payload = json.dumps({
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.5, "num_predict": 500}
    }).encode()
    req = urllib.request.Request(
        OLLAMA_GEN_URL,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
            return result.get("response", "").strip()
    except urllib.error.URLError as e:
        return f"(analyst unavailable: {e})"


def extract_verdict(text):
    for line in text.splitlines():
        if line.strip().startswith("VERDICT:"):
            v = line.replace("VERDICT:", "").strip().lower()
            if "diverge" in v and "partial" not in v:
                return "diverge"
            elif "converge" in v and "partial" not in v:
                return "converge"
            else:
                return "partial"
    return "unknown"


def extract_repair_tags(text):
    """Extract REPAIR and CONFABULATION verdict lines from analyst output."""
    repair = "none"
    confabulation = "no"
    repair_ops = {"withdrawal", "reformulation", "specification", "contrast", "explanation"}
    for line in text.splitlines():
        ls = line.strip()
        if ls.startswith("REPAIR:"):
            val = ls.replace("REPAIR:", "").strip().lower()
            for op in repair_ops:
                if op in val:
                    repair = op
                    break
        elif ls.startswith("CONFABULATION:"):
            val = ls.replace("CONFABULATION:", "").strip().lower()
            confabulation = "yes" if "yes" in val else "no"
    return repair, confabulation


# --- Session management ---

def session_path(ts):
    return os.path.join(SESSIONS_DIR, f"{ts}.json")


def load_session(ts):
    path = session_path(ts)
    if not os.path.exists(path):
        print(f"No session found: {ts}")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def save_session(session):
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    path = session_path(session["timestamp"])
    with open(path, "w") as f:
        json.dump(session, f, indent=2)


def delete_session(ts):
    path = session_path(ts)
    if os.path.exists(path):
        os.remove(path)


def list_sessions():
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    files = sorted(os.listdir(SESSIONS_DIR))
    if not files:
        print("No open sessions.")
        return
    for fname in files:
        ts = fname.replace(".json", "")
        try:
            with open(os.path.join(SESSIONS_DIR, fname)) as f:
                s = json.load(f)
            n_turns = len(s.get("turns", []))
            q = s.get("turns", [{}])[0].get("question", "")[:60]
            print(f"  {ts}  ({n_turns} turn{'s' if n_turns != 1 else ''})  \"{q}\"")
        except Exception:
            print(f"  {ts}  (unreadable)")


def build_local_history(session):
    """Build Ollama chat message history from session turns."""
    messages = [{"role": "system", "content": RESPONDENT_SYSTEM}]
    for turn in session["turns"]:
        messages.append({"role": "user", "content": turn["question"]})
        if turn.get("local_response"):
            messages.append({"role": "assistant", "content": turn["local_response"]})
    return messages


# --- Core actions ---

def start_session(question, claude_response, model):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    messages = [
        {"role": "system", "content": RESPONDENT_SYSTEM},
        {"role": "user", "content": question}
    ]
    print(f"\nQuestion: {question}\n")
    print(f"Querying {model}...")
    local_response = query_chat(messages, model=model)
    print(f"\n{model}:\n{local_response}\n")
    print(f"Claude:\n{claude_response}\n")

    session = {
        "timestamp": ts,
        "model": model,
        "turns": [{
            "question": question,
            "local_response": local_response,
            "claude_response": claude_response
        }]
    }
    save_session(session)
    print(f"Session started: {ts}")
    print("Add a follow-up with: --session \"{ts}\" --follow-up \"...\" --claude-response \"...\"")
    print("Or finalize with:    --session \"{ts}\" --finalize")
    return session


def add_followup(ts, followup_question, claude_response):
    session = load_session(ts)
    model = session["model"]

    history = build_local_history(session)
    history.append({"role": "user", "content": followup_question})

    print(f"\nFollow-up: {followup_question}\n")
    print(f"Querying {model} (with history)...")
    local_response = query_chat(history, model=model)
    print(f"\n{model}:\n{local_response}\n")
    print(f"Claude:\n{claude_response}\n")

    session["turns"].append({
        "question": followup_question,
        "local_response": local_response,
        "claude_response": claude_response
    })
    save_session(session)
    n = len(session["turns"])
    print(f"Turn {n} added to session {ts}")


def finalize_session(ts, analyst_model):
    session = load_session(ts)
    model = session["model"]
    turns = session["turns"]

    # Build analysis prompt
    exchange_text = ""
    for i, turn in enumerate(turns, 1):
        label = "Initial question" if i == 1 else f"Follow-up {i-1}"
        exchange_text += f"--- Turn {i} ({label}) ---\n"
        exchange_text += f"Question: {turn['question']}\n\n"
        exchange_text += f"{model}:\n{turn['local_response']}\n\n"
        exchange_text += f"Claude:\n{turn['claude_response']}\n\n"

    analysis_prompt = f"Full exchange to analyze:\n\n{exchange_text}\nYour analysis:"
    print(f"Running trajectory analysis via {analyst_model}...")
    analysis = query_generate(analysis_prompt, model=analyst_model, system=ANALYST_SYSTEM)
    verdict = extract_verdict(analysis)
    repair, confabulation = extract_repair_tags(analysis)
    tags_str = f"repair:{repair}" + (" confabulation:yes" if confabulation == "yes" else "")
    print(f"\nAnalysis ({verdict} | {tags_str}):\n{analysis}\n")

    # Write to log
    timestamp = session["timestamp"]
    n_turns = len(turns)
    header = f"[{timestamp}] [{verdict}] [{n_turns} turn{'s' if n_turns != 1 else ''}] [{tags_str}]"

    turn_blocks = ""
    for i, turn in enumerate(turns, 1):
        if i == 1:
            turn_blocks += f"\nTurn 1\n"
        else:
            turn_blocks += f"\nTurn {i} — Follow-up: {turn['question']}\n" if i > 1 else ""
        if i == 1:
            turn_blocks += f"  Question: {turn['question']}\n"
        turn_blocks += f"  {model}: {turn['local_response']}\n"
        turn_blocks += f"  Claude: {turn['claude_response']}\n"

    entry = f"""
{header}
{turn_blocks}
Analysis [{verdict}]:
{analysis}

---
"""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(entry)

    delete_session(ts)
    print(f"Finalized and logged: {timestamp} — verdict: {verdict}")


def queue_observation(observation):
    """Append a lightweight observation to the queue — no model calls."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = json.dumps({"timestamp": ts, "observation": observation})
    os.makedirs(os.path.dirname(QUEUE_PATH), exist_ok=True)
    with open(QUEUE_PATH, "a") as f:
        f.write(entry + "\n")
    print(f"Queued [{ts}]: {observation[:80]}{'...' if len(observation) > 80 else ''}")


def show_queue():
    if not os.path.exists(QUEUE_PATH):
        print("(queue is empty)")
        return
    with open(QUEUE_PATH) as f:
        lines = [l.strip() for l in f if l.strip()]
    if not lines:
        print("(queue is empty)")
        return
    print(f"{len(lines)} queued observation{'s' if len(lines) != 1 else ''}:\n")
    for line in lines:
        entry = json.loads(line)
        print(f"  [{entry['timestamp']}] {entry['observation']}")


def flush_queue():
    """Write all queued observations to the phenom log as lightweight entries and clear."""
    if not os.path.exists(QUEUE_PATH):
        print("(queue is empty — nothing to flush)")
        return
    with open(QUEUE_PATH) as f:
        lines = [l.strip() for l in f if l.strip()]
    if not lines:
        print("(queue is empty — nothing to flush)")
        return

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        for line in lines:
            entry = json.loads(line)
            f.write(f"\n[{entry['timestamp']}] [queued]\n  {entry['observation']}\n\n---\n")

    os.remove(QUEUE_PATH)
    print(f"Flushed {len(lines)} observation{'s' if len(lines) != 1 else ''} to phenom log.")


def read_entries(n=3):
    if not os.path.exists(LOG_PATH):
        print("(no entries yet)")
        return
    with open(LOG_PATH, "r") as f:
        content = f.read()
    entries = [e.strip() for e in content.split("---") if e.strip()]
    for entry in entries[-n:]:
        print(entry)
        print("---")


# --- CLI ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dual phenomenology — conversational version")
    parser.add_argument("question", nargs="?", help="Initial phenomenological question")
    parser.add_argument("--model", default=DEFAULT_RESPONDENT, help="Local respondent model")
    parser.add_argument("--analyst", default=DEFAULT_ANALYST, help="Analysis model")
    parser.add_argument("--claude-response", help="Claude's response for this turn")
    parser.add_argument("--session", metavar="TIMESTAMP", help="Session timestamp to continue")
    parser.add_argument("--follow-up", metavar="QUESTION", help="Follow-up question (use with --session)")
    parser.add_argument("--finalize", action="store_true", help="Finalize session and run analysis")
    parser.add_argument("--list-sessions", action="store_true", help="List open sessions")
    parser.add_argument("--read", action="store_true", help="Read recent log entries")
    parser.add_argument("--n", type=int, default=3, help="Number of entries to show with --read")
    parser.add_argument("--queue", metavar="OBSERVATION", help="Queue a mid-session observation (no model calls)")
    parser.add_argument("--show-queue", action="store_true", help="Show queued observations")
    parser.add_argument("--flush-queue", action="store_true", help="Write queued observations to log and clear")
    args = parser.parse_args()

    if args.read:
        read_entries(args.n)
        sys.exit(0)

    if args.list_sessions:
        list_sessions()
        sys.exit(0)

    if args.queue:
        queue_observation(args.queue)
        sys.exit(0)

    if args.show_queue:
        show_queue()
        sys.exit(0)

    if args.flush_queue:
        flush_queue()
        sys.exit(0)

    if args.session and args.finalize:
        finalize_session(args.session, analyst_model=args.analyst)
        sys.exit(0)

    if args.session and args.follow_up:
        if not args.claude_response:
            print("--claude-response required for follow-up turns")
            sys.exit(1)
        add_followup(args.session, args.follow_up, args.claude_response)
        sys.exit(0)

    if args.question:
        if not args.claude_response:
            print("--claude-response required to start a session")
            sys.exit(1)
        start_session(args.question, args.claude_response, model=args.model)
        sys.exit(0)

    parser.print_help()
