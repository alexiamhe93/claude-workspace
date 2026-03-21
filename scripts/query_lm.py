#!/usr/bin/env python3
"""
query_lm.py — Simple prompt-only query to a local Ollama model.
No file tools; file content enters the model's context if piped.

Usage:
    python3 query_lm.py "your prompt"
    cat file.txt | python3 query_lm.py "summarise this"
    python3 query_lm.py --model qwen2.5-coder:7b "write a fibonacci function"
    python3 query_lm.py --list-models
"""
import json
import sys
import argparse
import urllib.request
import urllib.error

BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3:8b"


def chat(prompt, model, max_tokens, system=None):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": False
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    return result["choices"][0]["message"]["content"]


def list_models():
    req = urllib.request.Request(f"{BASE_URL}/models")
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    for m in result.get("data", []):
        print(m["id"])


def main():
    parser = argparse.ArgumentParser(
        description="Query a local Ollama model with a prompt."
    )
    parser.add_argument("prompt", nargs="?", help="Prompt text (or pipe via stdin)")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Ollama model (default: {DEFAULT_MODEL})")
    parser.add_argument("--max-tokens", type=int, default=1000,
                        help="Max completion tokens (default: 1000)")
    parser.add_argument("--system", default=None,
                        help="System prompt")
    parser.add_argument("--list-models", action="store_true",
                        help="List available Ollama models and exit")
    args = parser.parse_args()

    if args.list_models:
        try:
            list_models()
        except urllib.error.URLError as e:
            print(f"Connection error: {e}\nIs Ollama running?", file=sys.stderr)
            sys.exit(1)
        return

    # Build prompt — combine piped stdin and positional arg if both present
    piped = ""
    if not sys.stdin.isatty():
        piped = sys.stdin.read().strip()

    if piped and args.prompt:
        prompt = f"{piped}\n\n{args.prompt}"
    elif piped:
        prompt = piped
    elif args.prompt:
        prompt = args.prompt
    else:
        parser.print_help()
        sys.exit(1)

    try:
        result = chat(prompt, args.model, args.max_tokens, args.system)
        print(result)
    except urllib.error.URLError as e:
        print(f"Connection error: {e}", file=sys.stderr)
        print("Is Ollama running? Try: ollama serve", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
