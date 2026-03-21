#!/usr/bin/env python3
"""
agent_lm.py — Ollama file-reading agent loop.
The local model reads files itself via tool calls; content never enters Claude's context.

Usage:
    python3 agent_lm.py --dir /path/to/project "task description"
    python3 agent_lm.py --model qwen2.5-coder:7b "explain main.py"
"""
import json
import sys
import os
import argparse
import urllib.request
import urllib.error

BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3:8b"
MAX_FILE_CHARS = 12000

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the filesystem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative path to the file"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List the files and folders in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the directory"}
                },
                "required": ["path"]
            }
        }
    }
]


def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(MAX_FILE_CHARS)
        if len(content) == MAX_FILE_CHARS:
            content += "\n[... file truncated at 12000 chars ...]"
        return content
    except Exception as e:
        return f"Error reading file: {e}"


def list_dir(path):
    try:
        entries = sorted(os.listdir(path))
        return "\n".join(entries)
    except Exception as e:
        return f"Error listing directory: {e}"


def chat(messages, model, max_tokens):
    payload = {
        "model": model,
        "messages": messages,
        "tools": TOOLS,
        "max_tokens": max_tokens,
        "stream": False
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        if e.code == 400:
            raise RuntimeError(
                f"Model '{payload['model']}' rejected the tool-calling request (HTTP 400).\n"
                f"This model likely does not support tool calls. Try llama3.1:8b or qwen2.5-coder:7b.\n"
                f"Details: {body}"
            )
        raise


def run_agent(task, model, max_tokens, max_turns, work_dir):
    content = task
    if work_dir:
        content = f"Working directory: {work_dir}\n\n{task}"
    messages = [{"role": "user", "content": content}]

    for turn in range(max_turns):
        print(f"[turn {turn + 1}]", file=sys.stderr)
        response = chat(messages, model, max_tokens)
        choice = response["choices"][0]
        message = choice["message"]
        messages.append(message)

        tool_calls = message.get("tool_calls") or []
        if choice.get("finish_reason") == "tool_calls" or tool_calls:
            for tool_call in tool_calls:
                fn_name = tool_call["function"]["name"]
                try:
                    fn_args = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError:
                    fn_args = {}

                print(f"  → {fn_name}({fn_args})", file=sys.stderr)

                if fn_name == "read_file":
                    result = read_file(fn_args.get("path", ""))
                elif fn_name == "list_dir":
                    result = list_dir(fn_args.get("path", ""))
                else:
                    result = f"Unknown tool: {fn_name}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result
                })
        else:
            print(message.get("content", ""))
            return

    print("[max turns reached without final answer]", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Run a local Ollama model as a file-reading agent."
    )
    parser.add_argument("task", help="Task description for the agent")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Ollama model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--dir", default=None,
                        help="Working directory context to give the model")
    parser.add_argument("--max-tokens", type=int, default=2000,
                        help="Max completion tokens (default: 2000)")
    parser.add_argument("--max-turns", type=int, default=10,
                        help="Max agent loop turns (default: 10)")
    args = parser.parse_args()

    try:
        run_agent(args.task, args.model, args.max_tokens, args.max_turns, args.dir)
    except urllib.error.URLError as e:
        print(f"Connection error: {e}", file=sys.stderr)
        print("Is Ollama running? Try: ollama serve", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
