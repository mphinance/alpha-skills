# mph-kit

Michael Hanko's portable Claude Code kit. One place, every machine the same.

This bundles the skills, slash commands, and subagents Michael actually uses into a
single installable plugin, so a fresh laptop or the `mph` server gets the identical
setup instead of three divergent `~/.claude/` folders.

## Install (per machine, once)

```
/plugin marketplace add mphinance/alpha-skills
/plugin install mph-kit
```

## Update later

```
/plugin update mph-kit
```

## What's inside

- **28 skills** — Substack pipeline (`mph-substack-writer`, `mph-substack-publish`,
  `mph-figure`, `mph-voice-refresh`, `substack-draft-status`, `draft-article`),
  trading research (`stock-deep-dive`, `stock-recap`, `value-complex`), design
  (`mph-synthwave-theme`, `frontend-design`, `design-an-interface`, `dashboard`,
  `critique`), and meta-tools (`orchestrate`, `skill-forge`, `skill-warden`,
  `diagnose`, `tdd`, `grill-me`, `mental-model-evaluator`, `portable-memory-core`).
- **6 commands** — `/ship`, `/save-all`, `/cockpit`, `/money`, `/orch-review`,
  `/orchestrate`.
- **3 subagents** — `repo-shipper`, `substack-editor`, `ticker-researcher`.

## Where things live

This plugin folder is the **canonical** copy of the kit. The repo's top-level
`skills/` directory is the broader archive/marketplace of every skill ever written
(community + experimental). When you add or edit a kit skill, do it here under
`plugins/mph-kit/skills/` and `/plugin update` picks it up everywhere.
