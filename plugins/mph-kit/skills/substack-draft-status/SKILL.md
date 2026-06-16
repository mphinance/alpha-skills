---
name: substack-draft-status
description: Show pending Substack drafts and reconcile them against local ~/.mph-substack-cache workspaces. Flags local-only drafts older than 3 days as stale (the "wait did I actually save this on substack" problem). Read-only — never publishes. Triggers on "did I save that draft", "is that saved on substack", "what drafts do I have", "show my substack drafts", "are my drafts pushed", "/substack-status", "/draft-status".
---

# Substack Draft Status

Reconciles two sources of "what drafts do I have":
- Local workspaces under `~/.mph-substack-cache/<slug>/` (rendered images + post.md)
- Server drafts at `https://mphinance.substack.com/api/v1/drafts`

The "did I save that yesterday" anxiety usually means: a local workspace exists but it never got pushed. This skill makes that visible in 5 seconds.

## When to invoke

- User asks "did I save that draft" / "is that on substack" / "what drafts do I have"
- User mentions a recent post by date or topic and wants to confirm its state
- Before forging a new substack post, sanity-check that an older one isn't sitting half-pushed

## Flow

1. Run the worker:
   ```
   python ~/.claude/skills/substack-draft-status/scripts/status.py
   ```
2. The script reads `SUBSTACK_SID` from `C:\Users\mphan\OneDrive\Documents\GitHub\mphinance\secrets.env` (or the `SUBSTACK_SID` env var) and hits `GET /api/v1/drafts?limit=20`.
3. It walks `~/.mph-substack-cache/` and matches each workspace against server drafts by date-prefix and title.
4. Output is grouped:
   - **Pushed** — local workspace AND matching server draft (shows edit URL)
   - **Server-only** — draft on substack with no local workspace (created via web)
   - **Local-only fresh** — workspace exists, no server match, post.md mtime within 3 days
   - **Local-only STALE** — workspace exists, no server match, post.md mtime older than 3 days. These are the "forgotten" drafts.
5. Surface the table verbatim to the user. If any STALE entries exist, offer to push them via `mph-substack-publish` (do not push automatically).

## Hard rules

- **Read-only.** Never call `POST /api/v1/drafts/.../publish`. Never modify local workspaces. Publishing is mph-substack-publish's job and requires explicit confirmation there.
- Reuse the existing `secrets.env` auth pattern from `create_draft_from_md.py`. Do not invent a new auth flow.
- Do not commit `~/.mph-substack-cache/` contents to git. Those workspaces are local-only by user policy.
- If `SUBSTACK_SID` is missing, print a clear error pointing at `secrets.env` and exit 2. Do not try to interactively prompt for credentials.
- Stale threshold = 3 days. If user wants a different threshold, pass `--stale-days N`.

## Out of scope

- Pushing, publishing, or editing drafts (use mph-substack-publish for the push)
- Listing published posts (the API endpoint is different and not interesting for the "did I save it" problem)
- Multi-publication support (only mphinance.substack.com)
- Anything that requires network calls beyond the single GET to /api/v1/drafts
