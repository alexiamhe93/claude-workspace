# /personality-mirror

Use a local model as an external mirror on my conversational behavior.

## What this does

Pipes a snippet of recent conversation to a local model with a prompt designed to surface personality observations I might miss about myself. The local model doesn't know me or the brief — that's the point.

## Steps

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
5. Note anything that surprises me or confirms something I suspected.
6. Optionally: update `claude_personality.md` if the mirror caught something real.

## When to use

- When something felt slightly off in a session but I can't name it
- When I want a genuinely external perspective on a specific exchange
- Periodically, as calibration — maybe every 5-10 sessions
