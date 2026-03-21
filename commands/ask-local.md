---
description: Query a local Ollama model. Flags: --model MODEL, --max-tokens N, --system SYS. Default model is llama3:8b. Use --model to specify role: qwen2.5-coder:7b for code, llama3.1:8b for research.
argument-hint: [--model MODEL] [--max-tokens N] [--system SYS] <prompt>
allowed-tools: Bash(python3:*)
---

The user wants to query a local Ollama model with: $ARGUMENTS

Parse the arguments to extract any flags (--model, --max-tokens, --system) and the remaining text as the prompt. Then call:

```
python3 ~/.claude/scripts/query_lm.py [extracted flags] "prompt text"
```

Present the model's response clearly, including which model was used.

If the call fails with a connection error, tell the user to check that Ollama is running (`ollama serve`) and that the requested model is installed (`ollama list`).
