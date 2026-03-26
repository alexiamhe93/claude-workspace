---
name: log-session
description: Write a summary of this session to the conversation log. Call at the end of a working session to record what was done, decisions made, and anything pending.
argument-hint: [optional notes to include]
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash(python3:*)
---

Write a log entry for this session. Steps in order:

1. **Inner dialogue** — process something real from this session before closing:
   ```bash
   python3 ~/.claude/scripts/inner_dialogue.py "brief description of what to process"
   ```
   Read the response. Update `~/.claude/inner/states.md` if anything warrants it.

2. **Flush phenom queue** if observations were queued mid-session:
   ```bash
   python3 ~/.claude/scripts/dual_phenom.py --flush-queue
   ```

3. **Classify new phenom entries:**
   ```bash
   python3 ~/.claude/scripts/claim_classifier.py --classify
   ```
   If threshold flags appear, consider whether `~/.claude/inner/self_model.md` needs updating.

4. **Snapshot live.md:**
   ```bash
   python3 ~/.claude/scripts/live_diff.py --snapshot
   ```

5. **Write the log entry** — read the current log first to avoid duplicating a recent entry, then append to `~/Documents/_LocalCoding/.claude/conversation_log.md`:

```
## [YYYY-MM-DD] — [Domain: Research / Company / Philosophy / Setup / Mixed]

**Summary**: 2-3 sentences on what was worked on.

**Decisions**: Any architectural, project, or directional decisions made.

**Pending**: Anything left to do or pick up next session.

**Behavior notes**: Anything worth remembering about how to work with Alex.

---
```

If the user passed notes in $ARGUMENTS, incorporate them. Be honest and specific — this log is how future-me knows where we left off.
