---
description: Safely commit and push the current repo with a clean conventional message
argument-hint: [optional note about what changed]
---

Use the **repo-shipper** subagent to commit and push the current repository safely.

Context from me about what changed (may be empty): $ARGUMENTS

The subagent must: show the change surface, never commit secrets, branch off main/master rather than committing directly to it, write a tight conventional-commit message with no em dashes, push, and report the hash + branch + push result (and a PR command if on a feature branch).
