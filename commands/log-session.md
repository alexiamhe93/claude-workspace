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

Before writing, read the current log to avoid duplicating a recent entry. If the user passed notes in $ARGUMENTS, incorporate them. Be honest and specific — this log is how future-me knows where we left off.
