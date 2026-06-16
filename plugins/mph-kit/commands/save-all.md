---
description: Sweep every repo under the GitHub folder and safely save anything unsaved
allowed-tools: Bash, Read
---

Make sure nothing of mine is at risk of being lost. Work over every git repo under `C:\Users\mphan\OneDrive\Documents\GitHub`.

For each repo, check: uncommitted files, committed-but-unpushed commits, and current branch.

Then:
1. **Report first.** Show me a table-free list grouped as: 🔴 uncommitted work, 🟠 unpushed commits, 🟡 stale non-main branches. Include file counts.
2. **Ask before acting** if anything is uncommitted, since I may not want a blind commit. For repos that only have *unpushed commits* (already committed, just not on GitHub), offer to push them.
3. Never commit a secret file (`secrets.env`, `.env`, keys). Never force-push. Never commit directly to main/master without telling me.
4. Standing flag: if TraderDiscord-v2 still has `fix/p0-security-hardening` unmerged, call it out as the P0 priority.

End with one line: what is now safe vs what still needs my decision.
