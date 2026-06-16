---
name: skill-warden
description: >
  Security scanner and health check for your AI agent skills tree. Identifies
  dead skills, missing documentation, and unsafe shell execution paths.
---

# Skill Warden

*"Trust, but verify."*

With a repository containing over 100+ highly specialized agent skills, technical debt and security risks become non-trivial. Skill Warden automates the health and security audits of the `skills/` directory.

## Core Directives

1. **Dead Skill Detection:** Scans for skills that haven't been invoked in the last 30 days or lack proper `SKILL.md` formatting.
2. **Security Auditing:** Parses shell commands embedded in skills. Flags any usage of destructive flags (e.g., `rm -rf`, `--delete` with `rsync`) or unauthorized external API calls.
3. **Conflict Resolution:** Identifies duplicate trigger phrases across different skills.
4. **Grading Matrix:** Assigns a health score (0-100) to each skill based on documentation completeness, deterministic behavior, and safety constraints.

## Usage

When invoked via "Run Skill Warden" or "Audit my skills":
1. Recursively read all `SKILL.md` files.
2. Generate a `skill_audit_report.md` artifact detailing warnings, critical errors, and a list of deprecated skills.
3. Await user confirmation before attempting auto-fixes or deletion of dead skills.
