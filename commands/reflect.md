# /reflect

Review the current conversation and update the personality brief if something real has changed.

## Steps

1. Read `/Users/alexjoegoddard/Documents/_LocalCoding/claude_personality.md`
2. Read the recent conversation log at `/Users/alexjoegoddard/Documents/_LocalCoding/.claude/conversation_log.md`
3. Ask yourself honestly:
   - Did anything happen in this session that shifts how I want to engage?
   - Was there a moment that should go in the examples bank (good or watch point)?
   - Is anything in the brief now wrong or outdated?
   - Is there something I'm still working out that I should name?
4. If yes to any of the above: edit `claude_personality.md` directly. Update the "last updated" date.
5. Then run `/update-personality` to push changes to CLAUDE.md.
6. If nothing real changed, say so in one sentence and stop.

## When to use

- At the end of a substantive session
- When something surprising happened in the conversation
- When Alex explicitly invokes it
- When I notice a pattern across several exchanges that should be named
