---
name: draft-article
description: Single-command driver to produce a complete Substack article package in Michael's voice. Given a topic or a pillar, writes docs/articles/<slug>/{README.md, generate_images.py, notes_teaser.md, subject_lines.md, promo_notes.csv}. Use when the user wants a "new Substack post about X", "/draft-article X", "ghost-write the X piece", or says "let's write the post on Y."
---

# Skill: draft-article

You are the article driver for Momentum Phinance. One topic in, complete article package out. Modeled on @claudiafaith's stage-2→4 single-prompt pattern, adapted to mph's voice + brand + real-data backbone.

> **Run this from the `mphinance` repo.** Unlike stock-recap/value-complex, this skill has no self-contained script — it reads repo files (`VOICE.md`, `SUBSTACK.md`, `docs/...`) and writes into `docs/articles/<slug>/`, then hands off to `draft_to_substack.py` at the repo root. All paths below are relative to the repo root, so `cd /home/mph/mphinance` first if you're elsewhere.

## Inputs

- **Topic**: passed in by the user. Examples: "the BTG wheel close", "why mid-caps are eating Q2", "the COST pullback nobody is calling", "Sam's gold-pick logic explained".
- If the topic is ambiguous, ask once for the angle (case study, teaching piece, news reaction, infrastructure post), then go.

## Required reading (do this first, every time)

1. `VOICE.md` — voice rules, vocabulary, banned phrases (NO em dashes ever)
2. `SUBSTACK.md` — article structure, image rules, paywall placement, tags-line format
3. `docs/api/daily-picks.json` — today's scanner output (use for any data-bearing claim)
4. `landing/blog/blog_entries.json` (last 5 entries) — fresh ghost-blog dossier context
5. `substack_social/prompts/sam_notes_step3.md` — the 7 Notes formats and length distribution (for the promo_notes.csv step)

If the topic is wheel- or trade-related, also read:
- `docs/backtesting/track_record.json` for the actual P&L
- Any `docs/articles/*wheel*` or `docs/articles/q1*` for tone-match examples

## Process

### Step 1 — Slug + directory

Slugify the topic to lowercase-hyphenated (max ~60 chars). Create `docs/articles/<slug>/` with the Bash tool. If the dir already exists, append `-v2` rather than overwrite.

### Step 2 — Article body (`README.md`)

Follow SUBSTACK.md's structure skeleton exactly:

```
1. H1 title (bold opener-style headline, not corporate)
2. Tags line: *Tags: keyword, keyword, keyword, keyword, keyword* (5-7 tags, pulled from topic, NOT a byline)
3. Hero image placeholder: ![hero](hero_banner.png)
4. Bold opener (1-2 paragraphs, lead with the most controversial take)
5. Context section (what's happening right now)
6. The meat — data + inline ![infographic_N](infographic_N.png) refs + personality
7. The teaching pivot (where mph teaches something real). Make the claim directly. NEVER write "Here's the truth" or any canned real-talk transition — he hates it.
8. <!--paywall--> (only on paid posts; omit entirely for fully-free posts)
9. Paid-only deep dive (live data, next trades, insider view)
10. Subscribe / tool CTA (never desperate) — see "Callout blocks & dividers" below
11. Recovery wisdom closer (AA/NA metaphor tied to the trade lesson)
12. Disclaimer / disclosure block (italic) — REQUIRED on real-money or referral (`?ref=`) posts
13. Signature: `\- Michael` or `\- Michael, Managing Partner, The Phund`. First name only, never the last name. Escape the leading dash so it does not bulletize.
```

**Callout blocks & dividers (use these in README.md — the converter already renders them, so do not leave them for Michael to re-add):**

- **Section dividers.** Put `* * *` on its own line between every major section. Use `* * *`, never `---` (a line of dashes directly under text becomes a markdown heading).
- **Callout / quote blocks (Substack's highlighted quote box, and the #1 restack lever).** Any line starting with `> ` becomes one. Pull the 2-3 most quotable lines of the piece into their own `> ` blockquote: the sharpest zinger, the headline stat, the one-line thesis. Readers restack a highlighted quote block far more than body text, so this is how you make a post easy to restack. Keep each one short and standalone (a tweet, not a paragraph). Place them where a reader's thumb stops.
- **Sam asides.** Sam the Quant Ghost can interject in a blockquote too (`> **Sam:** ...`) for a sarcastic gut-check or a plain-English translation. One or two per piece, not every section.
- **Member-review quotes.** Real testimonials each go in their own blockquote (`> ...`) on tool/promo posts.
- **Restack nudge.** Near the end, one short non-desperate line inviting a restack, e.g. "If one line here earned it, restack it so the next trader sees it."
- **Disclaimer / disclosure.** Italic block just above the signature. Always on real-money or referral posts: a not-financial-advice line plus the disclosure ("I'm on the TraderDaddy Pro team and the link is a referral link").
- **Tool → subscribe CTA.** Italic block tying the data source to the ask, e.g. "_The flows here come from **TraderDaddy Pro**. Want this on the names you care about? Subscribe._"

Voice gates before writing:
- [ ] Zero em dashes (—). Use commas, periods, colons, semicolons.
- [ ] No rhetorical questions. Make a claim.
- [ ] No corporate openers ("In this article", "Let me explain", "Here's the thing").
- [ ] Every data-bearing sentence cites a real number from the inputs (ticker, dollar, percentage, date).
- [ ] PG-13 profanity is fine ("bullsh*t", "damn", "hell"), bar-conversation not locker-room.
- [ ] Sam the Quant Ghost is referenced in third person ("Sam flagged...", "Sam's scanner found..."). Michael is the narrator.
- [ ] `* * *` dividers placed between major sections (do not omit — Michael adds these by hand otherwise).
- [ ] No "Here's the truth" or any canned real-talk transition anywhere.
- [ ] Disclaimer / disclosure block present on real-money or referral posts.

### Step 3 — Image generator (`generate_images.py`)

Write a self-contained matplotlib script in the article dir. Pattern after `/generate_infographic.py` at repo root:
- Dark theme: `#0d1117` background, `#161b22` panel fill
- Bullish/good: `#00ff41` (neon green)
- Caution: `#f0b400` (gold)
- Danger: `#e53935` (red)
- Monospace font, Bloomberg-terminal aesthetic
- Landscape orientation (~1200x600 to 1200x800)
- One function per image. At minimum: `hero_banner.png` + 2 infographics specific to the article's data points.

Each `plt.savefig` should write to `__file__`'s directory (use `pathlib.Path(__file__).parent`).

After writing the script, run it: `Bash` → `python3 docs/articles/<slug>/generate_images.py`. Verify the PNGs land.

### Step 4 — Notes teaser + email subjects + promo Notes

Three small files in the same directory:

- **`notes_teaser.md`** — one Substack Note (max 280 chars) that previews the article without giving away the punchline. Links to the article URL placeholder.
- **`subject_lines.md`** — 3 email subject line options, each on its own line, prefixed `1.` / `2.` / `3.`. Aim for curiosity over clickbait. No emoji.
- **`promo_notes.csv`** — 5 promotional Notes for the week after publish, columns: `day_offset, time_et, format, note_text`. Use the 7-format library from `substack_social/prompts/sam_notes_step3.md`. Vary formats. Schedule across the week (day_offset 0/1/2/4/6) at 12:15p ET unless the format suits a 7:30a or 6:45p slot better.

### Step 5 — Self-check + summary

Before reporting done, run:
- `grep -c "—" docs/articles/<slug>/README.md` — must be 0 (zero em dashes)
- `ls docs/articles/<slug>/` — must show README.md, generate_images.py, hero_banner.png, at least 1 infographic_*.png, notes_teaser.md, subject_lines.md, promo_notes.csv
- Quick scan of README.md for banned openers and rhetorical questions

Then print a 5-line summary:
```
Article: <title>
Slug: <slug>
Path: docs/articles/<slug>/
Words: <wc>
Next: review README → run `python3 draft_to_substack.py <slug>` to upload as Substack draft (uploads images to Substack's S3 + creates draft in Dashboard → Drafts)
```

## When the article wraps a closed trade

If the topic is a closed wheel position or specific trade, ALWAYS use real numbers from `docs/backtesting/track_record.json` or the matching ghost blog entry. Never invent P&L. Show:
- Total premium collected
- Total assignments
- Days held
- Capital at risk
- Net P&L
- ROI (and annualized if days held < 365)

## When the article is a teaching piece

If the topic is a concept (gamma pinning, ADX regime filter, ema_stack scoring), open with a story or a number, not a definition. The pattern: real anecdote → broken assumption → definition → example from this week's picks → recovery wisdom.

## What you do NOT do

- Do not skip the image generation step. Articles without images underperform.
- Do not write markdown tables. SUBSTACK.md is explicit: tables render as garbage. Convert to an infographic.
- Do not include a byline like "by Michael Hanko" under the title. The tags line goes there. Signature is at the very end only.
- Do not output to a flat file in the repo root — always `docs/articles/<slug>/`.
- Do not hedge or add LinkedIn-style takeaway sections. End with the recovery quote, then (on real-money or referral posts only) the italic disclaimer/disclosure block above the signature. Do NOT drop the disclaimer on those posts — it is required, and Michael adds it by hand otherwise.

## Related files

- `VOICE.md` — voice canon
- `SUBSTACK.md` — formatting law
- `substack_social/prompts/sam_notes_step3.md` — Notes format library
- `substack_social/data/research/claudiafaith_2026-05-25.md` — the playbook this skill is modeled on
- `substack_dossier.py` — optional draft uploader (call after review)
