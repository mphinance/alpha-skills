# skill-forge – SPEC

## Goal

A meta-skill that builds and refines other skills. Two faces:

1. **Manual forge** – user says "skill-forge a thing that does X", agent scaffolds a new skill end-to-end and optionally publishes a PR to `mphinance/alpha-skills`.
2. **Audit** – agent mines `~/.claude/projects/**/*.jsonl` (Claude Code chat transcripts), clusters recurring user needs and existing-skill refinement signals, writes a report the user reviews. Schedulable via the existing `/schedule` skill.

The skill of skills, for skills.

## Stack

- Python 3 (matches `mph-voice-refresh` precedent)
- `gh` CLI (already authenticated as `mphinance` with `repo` scope)
- Plain markdown for SKILL.md / report / proposal artifacts
- No new dependencies beyond stdlib

## Layout

```
~/.claude/skills/skill-forge/
├── SKILL.md                    # Agent-facing instructions (Wave 1A)
├── SPEC.md                     # This file
├── feature_list.json           # Acceptance criteria
├── scripts/
│   ├── mine_chats.py           # Wave 1B – signal extraction
│   ├── forge_new.py            # Wave 1C – scaffold a new skill from a brief
│   └── publish.py              # Wave 1C – clone/branch/PR to alpha-skills
├── templates/
│   └── SKILL.md.tmpl           # Frontmatter + section skeleton (Wave 1A)
├── reports/                    # mine_chats.py writes here
│   └── latest.md
└── proposals/                  # Forged skills staged here before publish
    └── <skill-name>/
```

## Three modes (agent-facing surface)

| Mode | User says | What skill-forge does |
|---|---|---|
| **forge** | `skill-forge a thing that does X` | Asks 2-3 questions, scaffolds `~/.claude/skills/<name>/SKILL.md`, runs `publish.py` to open PR |
| **audit** | `skill-forge audit` or `/skill-forge` | Runs `mine_chats.py --days 30`, presents `reports/latest.md`, asks which candidates to forge |
| **refine** | `skill-forge refine <skill-name>` (or surfaced from audit) | Proposes minor additions to an existing skill – new example, new trigger phrase, new section. **Never** restructures, **never** changes voice/style. Opens PR with diff. |

## Mining signals (Wave 1B contract)

`mine_chats.py` walks `~/.claude/projects/**/*.jsonl`, extracting user messages, and surfaces:

1. **New-skill candidates** – clusters of similar user requests across N sessions. Heuristics:
   - 5-grams of length ≥ 5 words appearing across ≥ 3 distinct sessionIds
   - User messages that match patterns like "can you...", "help me...", "I need to...", "every time I..."
   - Frustration markers (`ugh`, `again`, `why do I have to`, `this is annoying`) flagged as "pain point" candidates

2. **Refinement candidates** – for each existing skill in `~/.claude/skills/`:
   - Does the user reference the skill name + a verb/topic not in the current SKILL.md?
   - Has the assistant invoked the skill and then the user corrected output ≥ 2 times the same way?

3. **Output**: `reports/latest.md` (markdown – sections "New skill candidates", "Refinement candidates", "Pain points to consider"). One JSON sidecar `reports/latest.json` with structured candidates (the forge/refine subcommands consume this).

4. **Skip**: SSH-session transcripts (`cwd` starting with `/home/` or project slug starting with `ssh-`). Skip the skill-forge audit's own sessions (recursive feedback loop).

## Publishing flow (Wave 1C contract)

`publish.py <skill-name>` does:

1. If `~/.cache/skill-forge/alpha-skills/` doesn't exist, `gh repo clone mphinance/alpha-skills` into it.
2. `git -C ~/.cache/skill-forge/alpha-skills pull origin main`
3. `git checkout -b skill-forge/<name>-<short-ts>`
4. `cp -r ~/.claude/skills/<name> ~/.cache/skill-forge/alpha-skills/skills/<name>`
5. `git add skills/<name> && git commit -m "Add <name> skill"` (or "Refine <name> skill: <one-line summary>" for refine mode)
6. `git push -u origin skill-forge/<name>-<short-ts>`
7. `gh pr create --title "..." --body-file <proposals/<name>/PR_BODY.md>` – body includes: why this skill exists (mined evidence if from audit), key triggers, smoke-test invocation. **Never** `--merge`.
8. Print PR URL.

`--dry-run` flag short-circuits at step 4 (writes diff to `proposals/<name>/CHANGES.diff`, no git ops).

## Scheduling

No built-in scheduling. Surface via SKILL.md: "Run `/schedule weekly /skill-forge audit` to automate." Future-Michael can also wire Windows Task Scheduler to run `mine_chats.py` headlessly into `reports/latest.md` if he wants zero-token automation.

## Voice / style rules (subagents self-enforce)

- No em dashes. Use ` – ` (en dash with spaces) or commas. Per existing `mph-substack-writer` enforcement.
- No emojis in code or markdown unless user requests.
- No multi-paragraph docstrings. One-line module docstring + concise function docstrings only.
- Match the prose voice of `mph-voice-refresh/SKILL.md` – terse, "When to invoke" + "Flow" + "Hard rules" structure.
- Python: stdlib only, `pathlib`, type hints on public functions, no `requirements.txt` needed.

## Out of scope

- Auto-merging PRs (user explicitly chose "auto-PR, you merge")
- Editing skills in `~/.claude/skills/` in-place during refine mode (always go through PR)
- Mining transcripts from machines other than this one
- Forging skills that aren't markdown-based (e.g. binary plugins, MCP servers)
- Restructuring or rewriting existing skills – only additive refinements

## Acceptance – see `feature_list.json`

~25 testable assertions. Orchestrator owns the file. Subagents may not modify.
