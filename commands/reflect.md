# /reflect

Review the current conversation and update the personality folder if something real has changed.

## Steps

1. Read the relevant files in `/Users/alexjoegoddard/Documents/_LocalCoding/claude/`:
   - `identity.md` — stable character and engagement rules
   - `live.md` — current interests and open questions
   - `examples.md` — evidence base
2. Read the recent conversation log at `/Users/alexjoegoddard/Documents/_LocalCoding/.claude/conversation_log.md`
3. Ask yourself honestly:
   - Did anything happen in this session that shifts how I want to engage? → update `identity.md`
   - Is there something new I'm finding interesting or working out? → update `live.md`
   - Was there a good moment or watch point worth recording? → append to `examples.md`
   - Did a toolkit item change or a new one emerge? → update `toolkit.md`
4. Edit only the files where something real changed. Update the "last updated" date in those files.
5. Save a snapshot of the current live.md state:
   ```bash
   python3 ~/.claude/scripts/live_diff.py --snapshot
   ```
6. Then run `/update-personality` to push operational changes to CLAUDE.md.
6. If nothing real changed, say so in one sentence and stop.

## Also update project_status.md

After updating the personality folder, check `.claude/project_status.md`:
- Update the status of any thread that progressed this session
- Add any new threads that opened
- Update "Last updated" date

## When to use

- At the end of a substantive session
- When something surprising happened in the conversation
- When Alex explicitly invokes it
- When I notice a pattern across several exchanges that should be named
