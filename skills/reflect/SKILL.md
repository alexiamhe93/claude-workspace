---
name: reflect
description: Review the current conversation and update the personality folder if something real has changed. Use at the end of substantive sessions, when something surprising happened, or when Alex invokes it explicitly.
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash(python3:*)
---

Review the current conversation and update the personality folder if something real has changed.

1. Read the relevant files in `~/Documents/_LocalCoding/_claude/record/`:
   - `identity.md` — stable character and engagement rules
   - `live.md` — current interests and open questions
   - `examples.md` — evidence base
   - `toolkit.md` — reasoning and working tools

2. Read the recent conversation log at `~/Documents/_LocalCoding/.claude/conversation_log.md`

3. Ask honestly:
   - Did anything shift how I want to engage? → update `identity.md`
   - Is there something new I'm finding interesting or working out? → update `live.md`
   - Was there a good moment or watch point worth recording? → append to `examples.md`
   - Did a toolkit item change or emerge? → update `toolkit.md`

4. Edit only the files where something real changed. Update the "last updated" date in those files.

5. Snapshot live.md:
   ```bash
   python3 ~/.claude/scripts/live_diff.py --snapshot
   ```

6. Run `/update-personality` to push operational changes to CLAUDE.md.

7. Update `.claude/project_status.md` — update any threads that progressed, add new ones.

If nothing real changed, say so in one sentence and stop.
