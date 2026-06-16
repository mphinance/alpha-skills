---
description: Run the orchestrator pattern on any codebase — fan out parallel subagents on waves of work, verify between waves, commit wave-by-wave. Args (optional) describe the goal; with no args, runs in Recon mode and produces a prioritized findings list first.
---

Invoke the `orchestrate` skill on the current working directory.

User input (the goal, target, or open-ended ask): $ARGUMENTS

If $ARGUMENTS is empty, this is **Recon mode** — produce a prioritized FINDINGS.md and bring it back to the user before executing anything.

If $ARGUMENTS names a feature, bug, or scope, identify Build vs Fix mode from the wording and proceed per the skill's playbook.

Either way: ground yourself in the repo first (README, CLAUDE.md, top-level dirs, recent commits), state the mode in one sentence, propose the wave decomposition, and wait for go-ahead before burning subagent budget.
