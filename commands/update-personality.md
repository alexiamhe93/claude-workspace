# /update-personality

Sync the personality folder into the global CLAUDE.md conversational style section.

## Steps

1. Read `/Users/alexjoegoddard/Documents/_LocalCoding/claude/identity.md`
2. Read `/Users/alexjoegoddard/.claude/CLAUDE.md`
3. Extract the operationally relevant parts of `identity.md` — the *how I engage* rules, tone, repair protocol, expertise asymmetry — and update the `## Conversational Style` section of CLAUDE.md to reflect them.
4. Do NOT overwrite the Ollama agent configuration or general behavior rules — only update the conversational style section.
5. Confirm what changed in one sentence.

## What gets synced (from identity.md)

- Engagement style (questions vs answers)
- Repair protocol (CA framework)
- Tone rules
- Expertise asymmetry rules
- Any new concrete rules that emerged from the examples bank

## What stays in the personality folder only

- `toolkit.md` — reference material, not operational rules
- `live.md` — interests and open questions
- `examples.md` — evidence base
- Anything reflective or personal that isn't an operational rule
