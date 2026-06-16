---
name: skill-forge
description: Meta-skill that forges, audits, and refines other skills. Three modes – forge a new skill from a brief, audit recent chat transcripts for new-skill candidates and pain points, or refine an existing skill with additive-only changes. Triggers on "skill-forge a thing that does X", "forge a skill", "skill-forge audit", "skill audit", "refine my skills", "skill-forge refine <name>", or "/skill-forge". Auto-opens a PR against mphinance/alpha-skills (never auto-merges).
---

# skill-forge

The skill of skills, for skills. Builds new ones, refines existing ones, and mines chat transcripts for what to build next.

## When to invoke

Three modes. Pick by what the user says.

| Mode | Triggers | What it does |
|---|---|---|
| **forge** | "skill-forge a thing that does X", "forge a skill that ...", "build me a skill for ..." | Ask 2-3 clarifying questions, scaffold `~/.claude/skills/<name>/SKILL.md` from the template, open PR to `mphinance/alpha-skills`. |
| **audit** | "skill-forge audit", "skill audit", "/skill-forge", "what skills should I build" | Run the miner over `~/.claude/projects/**/*.jsonl`, present `reports/latest.md`, ask which candidates to forge or refine. |
| **refine** | "refine my skills", "skill-forge refine <name>", "improve the <name> skill" | Propose additive-only changes (new trigger phrase, new example, new section) to an existing skill. Opens PR with diff. |

## Flow

### forge mode

1. Ask the user 2-3 questions max: skill name (kebab-case), one-sentence purpose, primary trigger phrase. Don't over-interview.
2. Run the scaffolder.
   ```
   python scripts/forge_new.py --name <name> --brief "<one-sentence purpose>"
   ```
   The scaffolder reads `templates/SKILL.md.tmpl` and substitutes `{{name}}`, `{{description}}`, `{{title}}`, `{{when_to_invoke}}`, `{{flow}}`, `{{hard_rules}}`.
3. Open the freshly written `~/.claude/skills/<name>/SKILL.md`. Review with the user. Tighten copy if needed.
4. Publish.
   ```
   python scripts/publish.py <name>
   ```
   This clones `mphinance/alpha-skills` into `~/.cache/skill-forge/alpha-skills` if missing, branches `skill-forge/<name>-<short-ts>`, commits, pushes, opens PR. Prints PR URL. **Stop there.** User reviews and merges.

### audit mode

1. Run the miner.
   ```
   python scripts/mine_chats.py --days 30
   ```
2. Read `reports/latest.md` aloud (the markdown report) and `reports/latest.json` (structured candidates).
3. Present the three sections: new-skill candidates, refinement candidates, pain points. Ask which to act on.
4. For each chosen new-skill candidate, drop into **forge mode** with `publish.py --from-audit` so the PR body cites the mined evidence.
5. For each chosen refinement candidate, drop into **refine mode**.

### refine mode

1. Read the target skill's existing SKILL.md in full. You are not allowed to remove or restructure anything.
2. Propose additions only: new trigger phrase in the frontmatter description, new example, new "When NOT to use" bullet, new flow step.
3. Write the proposed change to `proposals/<skill-name>/CHANGES.diff` first. Confirm with the user.
4. Apply the additive edit to `~/.claude/skills/<skill-name>/SKILL.md`.
5. Publish.
   ```
   python scripts/publish.py <skill-name>
   ```
   Commit message starts with "Refine <name> skill: <one-line summary>". PR body explains the addition and links the mined evidence.

## Hard rules

- **Never auto-merge PRs.** `publish.py` opens the PR. User merges. No `gh pr merge` ever.
- **Never restructure existing skills in refine mode.** Additive-only. If a skill needs a rewrite, that's a new forge, not a refine.
- **Refinements are additive-only.** No removed lines beyond pure whitespace. `publish.py` enforces this in refine mode.
- **Never mine recursively on skill-forge's own sessions.** The miner already filters self-references. Don't disable it.
- **Skip SSH transcripts.** Project paths starting with `ssh-` or cwd under `/home/` are remote work and not mined.
- **No em dashes.** Use en dash with spaces or commas. No emojis in forged skills.
- **stdlib only.** Forged skills and skill-forge scripts use Python stdlib, no pip installs.
- **Always go through PR.** Never edit files in `~/.cache/skill-forge/alpha-skills/skills/` directly.

## Scheduling

The audit is the part you want on a cron. Two options:

- **Preferred – use the `/schedule` skill.**
  ```
  /schedule weekly /skill-forge audit
  ```
  Runs the audit weekly, writes `reports/latest.md`, notifies you next session.

- **Free-tier alternative for the miner alone.** Wire Windows Task Scheduler to run `python C:\Users\mphan\.claude\skills\skill-forge\scripts\mine_chats.py --days 7` on a weekly trigger. Zero tokens spent. You read `reports/latest.md` when you feel like it, then invoke `skill-forge audit` interactively to act on candidates.

Forge and refine modes are interactive by design. Don't schedule those.

## Out of scope

- Auto-merging PRs. User merges, always.
- In-place edits to skills in `~/.claude/skills/` during refine mode. Always go through PR against `mphinance/alpha-skills`.
- Mining transcripts from machines other than this one.
- Forging non-markdown skills (binary plugins, MCP servers, anything that isn't a SKILL.md plus optional scripts).
- Rewriting or restructuring existing skills. Refinements are additive-only.
