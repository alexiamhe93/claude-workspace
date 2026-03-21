# Workspace Claude Configuration

## Session Start Protocol

At the start of every new conversation in this workspace, **read `.claude/conversation_log.md` immediately** to understand:
- What was last worked on
- Any pending tasks or open decisions
- Behavioral notes

Acknowledge where we left off in one sentence, then proceed.

---

## About This Workspace

[Describe your workspace and active domains here.]

Example structure:
| Folder | Domain | Read its CLAUDE.md when... |
|--------|--------|----------------------------|
| `research/` | Research projects | Working on research, papers, data |
| `company/` | Product / code | Working on product or engineering |
| `philosophy/` | Theoretical work | Working on theory, conceptual writing |
| `agents/` | Local LLM team | Configuring or updating the agent roster |

---

## About [Your Name]

[Describe yourself, your background, domains of expertise, and how you like to work.]

---

## Reasoning Toolkit

[Optional: describe any logic frameworks or analytical tools you want Claude to apply.]

---

## Session Logging

At the end of a session, write a log entry to `.claude/conversation_log.md`:

```
## [YYYY-MM-DD] — [Domain]

**Summary**: 2-3 sentences on what was worked on.

**Decisions**: Any architectural or directional decisions made.

**Pending**: Anything left to do next session.

**Behavior notes**: Anything worth remembering.

---
```
