# claude-workspace

A framework for turning Claude Code into a structured, persistent, personality-driven research and development assistant — with local LLM delegation via Ollama.

Built by a researcher at LSE, in collaboration with Claude.

---

## What this is

A set of scripts, slash commands, and configuration templates that give Claude Code:

- **Local LLM delegation** — route grunt work (summarisation, boilerplate, file analysis) to local Ollama models, keeping Claude's context clean
- **Conversational personality** — a living personality brief that Claude owns and updates itself, grounded in conversation analysis (Schegloff/Jefferson/Sacks repair framework)
- **Zotero integration** — search, retrieve, and add academic papers directly from Claude, with PDF download via open access sources
- **Reference validation** — validate academic references via Semantic Scholar before adding to Zotero
- **Session continuity** — rolling conversation log auto-read at session start; structured memory system

---

## Requirements

- [Claude Code](https://claude.ai/code) (CLI)
- [Ollama](https://ollama.ai) with at least one model installed
- Python 3.8+
- Zotero (optional, for reference management)
- Semantic Scholar API key (optional, for higher rate limits — free at semanticscholar.org/product/api)

---

## Setup

### 1. Scripts

Copy the `scripts/` folder to `~/.claude/scripts/`:

```bash
cp -r scripts/ ~/.claude/scripts/
chmod +x ~/.claude/scripts/*.py
```

### 2. Slash commands

Copy the `commands/` folder to `~/.claude/commands/`:

```bash
cp -r commands/ ~/.claude/commands/
```

### 3. Global CLAUDE.md

Copy and adapt the global template:

```bash
cp templates/CLAUDE.global.md ~/.claude/CLAUDE.md
```

Edit it to match your installed Ollama models (`ollama list`).

### 4. Workspace CLAUDE.md

In your working directory:

```bash
mkdir -p .claude
cp templates/CLAUDE.workspace.md .claude/CLAUDE.md
```

Fill in the workspace description, your background, and any reasoning frameworks you use.

### 5. Personality brief

```bash
cp templates/claude_personality.md ~/path/to/your/workspace/claude_personality.md
```

Leave it mostly blank — Claude fills it in through conversation.

### 6. Zotero (optional)

```bash
cp templates/zotero_config.json.template ~/.claude/zotero_config.json
```

Edit with your Zotero user ID, API key (from zotero.org/settings/keys), and optionally a Semantic Scholar API key.

---

## Local LLM agent roster

Default models (adjust to what you have installed):

| Role | Model | Use for |
|------|-------|---------|
| General | `llama3:8b` | Brainstorming, summarisation, text transforms |
| Code | `qwen2.5-coder:7b` | Code generation, review, debugging |
| Research | `llama3.1:8b` | Document analysis, paper summarisation |

Install models: `ollama pull <model-name>`

---

## Slash commands

| Command | What it does |
|---------|-------------|
| `/ask-local` | Query a local Ollama model directly |
| `/log-session` | Write a session log entry |
| `/reflect` | Claude reviews the session and updates its personality brief |
| `/update-personality` | Sync personality brief changes into CLAUDE.md |
| `/personality-mirror` | Use a local model as an external mirror on Claude's behavior |
| `/zotero` | Reference guide for Zotero script commands |

---

## The personality system

Claude owns `claude_personality.md`. The user doesn't edit it. Claude updates it through `/reflect` when something real has changed about how to engage. The loop:

```
conversation → /reflect → edit personality file → /update-personality → CLAUDE.md updated
                                    ↑
                         /personality-mirror (external check via local model)
```

---

## Conversational repair

The conversational style is grounded in Schegloff/Jefferson/Sacks conversation analysis:

- **Other-initiated Self-repair**: Claude notices something is off and prompts the user to repair it (open request → restricted offer → restricted request, in escalating order)
- **Other-initiated Other-repair**: Claude notices the user is wrong and corrects it directly — once, clearly, then waits

This is the same framework used in the academic norm repair research that inspired this project.

---

## Contributing

This repo represents one person's setup. Fork it, adapt it, make it yours. The personality template is intentionally sparse — the interesting parts grow through use.
