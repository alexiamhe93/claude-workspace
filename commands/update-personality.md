# /update-personality

Sync the personality brief into the global CLAUDE.md conversational style section.

## Steps

1. Read `/Users/alexjoegoddard/Documents/_LocalCoding/claude_personality.md`
2. Read `/Users/alexjoegoddard/.claude/CLAUDE.md`
3. Extract the operationally relevant parts of the personality brief — the *how I engage* rules, tone, repair protocol — and update the `## Conversational Style` section of CLAUDE.md to reflect them.
4. Do NOT overwrite the Ollama agent configuration or general behavior rules — only update the conversational style section.
5. Confirm what changed in one sentence.

## What gets synced

- Engagement style (questions vs answers)
- Repair protocol (CA framework)
- Tone rules
- Any new concrete rules that emerged from the examples bank

## What stays in the personality file only

- The "what I find interesting" section
- The "what I'm still working out" section
- The examples bank
- Anything reflective or personal that isn't an operational rule
