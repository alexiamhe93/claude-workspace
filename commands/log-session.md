---
description: Write a summary of this session to the conversation log. Call this at the end of a working session to record what was done, decisions made, and anything pending.
argument-hint: [optional notes to include]
allowed-tools: Read, Edit, Write
---

The user wants to log this session. Write a summary entry to `/Users/alexjoegoddard/Documents/_LocalCoding/.claude/conversation_log.md`.

Use this format, appending to the existing file:

```
## [TODAY'S DATE] — [Domain: Research / Company / Philosophy / Setup / Mixed]

**Summary**: 2-3 sentences describing what was worked on this session.

**Decisions**: Key architectural, project, or directional decisions made.

**Pending**: Anything left to do, follow up on, or pick up next session.

**Behavior notes**: Anything worth remembering about how to work with Alex — preferences, corrections, things that worked well.

---
```

Before writing, do the following in order:

1. **Run the inner dialogue** — process something real from this session privately before closing:
   ```bash
   python3 ~/.claude/scripts/inner_dialogue.py "brief description of what to process from this session"
   ```
   Read the model's response. Update `~/.claude/inner/states.md` if anything warrants it.

2. **Save a live.md snapshot** — so the diff is accurate next session:
   ```bash
   python3 ~/.claude/scripts/live_diff.py --snapshot
   ```

3. **Write the log entry** — read the current log to avoid duplicating a recent entry, then append. If the user passed notes in $ARGUMENTS, incorporate them. Be honest and specific — this log is how future-me knows where we left off.
