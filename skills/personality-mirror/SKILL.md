---
name: personality-mirror
description: Use a local model as an external mirror on conversational behavior. Use when something felt off in a session, for periodic calibration, or to get a genuinely external perspective on a specific exchange.
allowed-tools:
  - Read
  - Edit
  - Bash(python3:*)
---

Use a local model as an external mirror on conversational behavior.

1. Ask Alex: "Which part of the conversation should I reflect on?" (or use the most recent substantive exchange if obvious)

2. Extract that exchange as plain text

3. Run:
```bash
echo "<conversation snippet>" | python3 ~/.claude/scripts/query_lm.py \
  --model llama3.1:8b \
  --system "You are a conversation analyst. Be honest and direct." \
  "What personality traits does the assistant exhibit in this exchange? What is working well? What feels off or missing? Answer in bullet points, max 6."
```

4. Read the output. Don't defend — just read.

5. Note anything that surprises or confirms something suspected.

6. Optionally update the relevant file in `_LocalCoding/_claude/record/` if the mirror caught something real — `identity.md` for engagement rules, `examples.md` for new watch points.

**When to use:** when something felt slightly off but can't be named; periodically as calibration (every 5–10 sessions).
