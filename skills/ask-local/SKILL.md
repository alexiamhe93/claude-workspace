---
name: ask-local
description: Query a local Ollama model. Use when the user wants to consult a local LLM, delegate a sub-task to a local model, or test local model responses.
argument-hint: [--model MODEL] [--max-tokens N] [--system SYS] <prompt>
allowed-tools:
  - Bash(python3:*)
  - Bash(ollama list:*)
  - Bash(ollama pull:*)
---

The user wants to query a local Ollama model with: $ARGUMENTS

Parse the arguments to extract any flags (--model, --max-tokens, --system) and the remaining text as the prompt. Then call:

```bash
python3 ~/.claude/scripts/query_lm.py [extracted flags] "prompt text"
```

Present the model's response clearly, including which model was used.

**Model roles:**
- `llama3:8b` — default, general use
- `llama3.1:8b` — research and analysis
- `qwen2.5-coder:7b` — code tasks

If the call fails with a connection error, tell the user to run `ollama serve` and check models are installed with `ollama list`.
