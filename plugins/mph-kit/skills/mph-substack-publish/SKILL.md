---
name: mph-substack-publish
description: End-to-end Substack pipeline. Take a subject, produce a draft (or publish it) at mphinance.substack.com. Chains mph-substack-writer (voice) + mph-figure (images) + the local create_draft_from_md.py pusher. Triggers on "write a Substack about X", "draft a post on Y", "publish to Substack", "/dispatch a Substack" or similar.
---

# MPH Substack Publish

End-to-end pipeline. Subject in → draft in mphinance.substack.com out (or published post if asked explicitly).

## Inputs

- **Subject** (required) — what the post is about. One line is fine; longer briefs are better.
- **Mode** (default: `draft`) — `draft` creates a draft only. `publish` calls `/api/v1/drafts/{id}/publish` after the draft lands. **Always confirm explicitly with Michael before `publish` mode** — that triggers the subscriber email blast and is not reversible.
- **Post category** (inferred from subject, or asked once if ambiguous):
  - `builder` — build-in-public, tool launches, code drops. No NFA needed. **Default.**
  - `trade` — specific positions / picks / "I bought X". NFA disclaimer required.
  - `paid_tease` — free post with a paywalled follow-up; include the "what's behind the paywall" section.
  - `recovery` — personal / sappy / non-finance reflection. No NFA.

## Pipeline

1. **Read the voice corpus.** Read `~/.claude/skills/mph-substack-writer/SKILL.md` and `~/.claude/skills/mph-voice-refresh/VOICE.md`. The hard rules and RETIRED phrases there supersede anything else.

2. **Pick a slug + workspace.**
   - Slug: `YYYY-MM-DD_kebab-case-title`
   - Workspace: `~/.mph-substack-cache/<slug>/` (create if missing). All intermediate files live here, not in the project repo. NEVER write Substack drafts to `docs/substack/drafts/` anymore — Michael does not want post markdown checked into git.

3. **Draft the post** following the mph-substack-writer skeleton:
   - H1 title (Title Case, terse)
   - One-line italic subtitle (the "dek")
   - Optional `![hero](hero.png)` reference
   - Bold opener (1-2 short paragraphs)
   - Context section
   - The meat (data + figures + voice)
   - "Here's the truth..." pivot
   - Optional paywall tease (for `paid_tease` category)
   - **Standardized footer** (see template below — do NOT improvise this)

4. **Render any figures.** For tables, comparison cards, stat blocks — write HTML in the workspace folder, render via mph-figure:
   ```
   node ~/.claude/skills/mph-figure/scripts/render.mjs --in <workspace>/foo.html --out <workspace>/foo.png --html
   ```
   Reference in markdown as `![alt](foo.png)`. Substack will receive these as uploaded S3 images.

5. **Push to Substack** via the script (handles image upload + ProseMirror conversion + cover image). The pusher lives in the mphinance repo, but the repo path differs per machine, so resolve it for wherever you're running:
   - Windows workstation: `C:/Users/mphan/OneDrive/Documents/GitHub/mphinance/substack_social/create_draft_from_md.py`
   - Coolify/Linux box (user `mph`): `~/mphinance/substack_social/create_draft_from_md.py`
   - Otherwise: find it with `git rev-parse --show-toplevel` from inside the mphinance checkout, or `find ~ -path '*substack_social/create_draft_from_md.py'`.

   ```
   python <pusher> <workspace>/post.md
   ```
   It prints the edit URL. Surface that URL to Michael.

6. **If mode is `publish`** (only with Michael's explicit confirmation):
   - Run `python <pusher> <workspace>/post.md --publish` (same `<pusher>` resolved in step 5)
   - Surface the live post URL.

## Standardized footer template

Use one of these three at the end of EVERY post. Replace the `---` separator with markdown horizontal rule (Substack handles it). Do not improvise alternative sign-offs or CTAs; consistency matters more than novelty here.

### `builder` (default) — no NFA

```
— Michael

---

*If this helped, subscribe so the next one lands in your inbox.*
```

### `trade` — with NFA

```
— Michael

---

*Not financial advice. Do your own research. Don't trade on someone else's conviction.*

*If this helped, subscribe so the next one lands in your inbox.*
```

### `paid_tease` — with paywall section above the footer

```
## What's behind the paywall

[one-paragraph tease of the paid follow-up — what it covers, when it drops, why it's worth paying for]

— Michael

---

*If this helped, subscribe so the next one lands in your inbox. Paid subs get the deep version on [day].*
```

## Path note (works from any CWD)

The pusher script `create_draft_from_md.py` lives in the mphinance repo. The absolute path above means this skill works whether Claude is invoked from the mphinance repo, a different repo, or anywhere else. If Michael moves the repo, update the path in this SKILL.md.

The script reads `secrets.env` from the mphinance repo automatically (resolved relative to the script's parent dir), so SUBSTACK_SID lookup works regardless of CWD.

## Hard rules (enforced)

- **Sign-off is exactly `— Michael`.** No last name. No `MPH` initials. No title. No "Managing Partner." No "The Phund." Just the em-dash + first name. (Yes, this is the one place an em-dash is allowed — it's the conventional dash for a signature, not narrative prose.) The `MPH` handle is fine as a brand/handle in body text ("@mphinance", "the mphinance newsletter") but never as a sign-off — that's the same as using the last name.
- **No NFA in `builder` posts.** Adding "not financial advice" to a post about building a Python tool reads like a lawyer wrote it. The top-engagement posts in Michael's network (Stephane Derosiaux, Pawel Jozefiak, Jenny Ouyang, even Compounding Quality who literally posts his trades) have ZERO NFA in the body.
- **Subscribe CTA goes at the bottom, after the signature.** Not at the top. Not mid-post (Substack auto-inserts those). One CTA, end of post, italicized.
- **The Substack-published draft is the source of truth.** The local markdown in `~/.mph-substack-cache/` is ephemeral. Don't commit it to git. Don't write to `docs/substack/drafts/`.

## Examples

### Example invocation: "write a Substack about why I dropped the institutional brokerage flow"
- Category: `builder` (it's a build-in-public post about a stack change)
- Mode: `draft`
- Footer: builder variant
- Expected output: draft URL like `https://mphinance.substack.com/publish/post/199012345`

### Example invocation: "draft a post on my new options.wheel position in GOLD"
- Category: `trade` (specific position)
- Mode: `draft`
- Footer: trade variant (NFA included)
- Expected output: draft URL, with NFA in footer

### Example invocation: "publish the pulse-style network analysis post"
- This is two questions: which post, and is `publish` mode confirmed? Ask: "Confirm you want this published live, not drafted? That'll send the email blast to all subscribers."
- Only proceed with `--publish` flag after explicit yes.

## Failure modes to watch for

- **Image upload returns 400** — usually means the image is too large or the format is unsupported. PNGs under 2MB are reliable.
- **Draft created but editor crashes opening it** — body included an unsupported ProseMirror node type. See the memory entry [[reference-substack-prosemirror-schema]] for valid types. The current pipeline avoids this by routing markdown through proper PM nodes, never `rawHtml`.
- **SUBSTACK_SID expired** — sign out + back in at substack.com to rotate, then update `secrets.env`.
