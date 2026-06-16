---
name: mph-voice-refresh
description: Mine Claude Code chat transcripts for Michael Hanko's actual phrasing patterns and refresh the VOICE.md corpus. Triggers on "refresh my voice", "update VOICE.md", "mine my chats for voice", "what does my voice sound like lately", "refresh voice corpus", or when mph-substack-writer output has started sounding stale/repetitive.
---

# MPH Voice Refresh

Keeps the [VOICE.md](VOICE.md) corpus alive. Without this, the writer keeps reusing the same "Michael impersonations" until they sound canned.

## When to invoke
- User asks to refresh / update / mine the voice corpus
- User says drafts are "sounding the same" or "you keep using that phrase"
- It's been more than ~3 weeks since last refresh (check the date at the bottom of VOICE.md)

## Two sources, two miners

| Source | Script | What it captures |
|---|---|---|
| Chat transcripts (`~/.claude/projects/*/*.jsonl`) | `scripts/mine_voice.py` | Unfiltered, conversational — tics like `..`, `lol`, `or whatever`, `Ugh.`, mid-sentence self-corrections. The way Michael actually types. |
| Substack RSS feed (`mphinance.substack.com/feed`) | `scripts/mine_feed.py` | Polished, published — paired openers, contradiction-filter constructions, punchy closers. The way Michael writes for readers. |

Both write to the **same VOICE.md**, but into separate sections. Don't mix them — chat voice has tics that don't belong in a Substack draft, and published voice has constructions that would sound forced in chat.

## Flow

1. **Read current state.** Read [VOICE.md](VOICE.md) so you know what's already in the corpus and what's already retired.

2. **Run the relevant miner.**
   - For chat voice refresh (most common — run every few weeks):
     ```
     python skills/mph-voice-refresh/scripts/mine_voice.py --days 30
     ```
   - For published voice refresh (run after Michael ships a new Substack post):
     ```
     python skills/mph-voice-refresh/scripts/mine_feed.py --limit 8
     ```
   - Run both back-to-back if it's been a while.

3. **Review with Michael.** Show the candidate lists. Do NOT auto-apply. Ask which additions to keep and which retirements to confirm. Voice is subjective; the miner is a candidate generator, not the authority.

4. **Apply approved changes.** Append confirmed additions to the appropriate section of VOICE.md:
   - Chat candidates → "Idioms & tics" / "Sentence rhythms" / "Long-form examples"
   - Feed openers/closers → "Published voice — Substack patterns"
   - Confirmed Claude repeats → `RETIRED`
   - Update the "Last refreshed" date at the bottom.

5. **No commits.** Leave the file dirty. Michael decides when/if to commit changes to the alpha-skills repo.

## What counts as "voice-worthy"

The miner looks for plain-string user messages (not tool results, not system reminders) that contain at least one informal marker: multi-dot punctuation (`..` / `....`), `lol`, `lmao`, `tbh`, `ngl`, `or whatever`, `kinda`, `sorta`, `I mean`, `I guess`, `wait`, `actually`, `yeah`, `damn`, `bullsh*t`, etc. It also requires length between 10 and 400 chars so we skip both one-word prompts and pasted essays.

## What counts as "stale"

Any 5-word phrase that appears in 3+ separate session transcripts (counted from assistant messages). The miner is intentionally aggressive here — better to surface a false positive Michael can ignore than miss a real tic. The user has explicitly said: "you end up reusing the same 'quotes' or whatever all the time" — this is what we're hunting.

## Hard rules

- **Never auto-apply.** Always present candidates for review.
- **Never delete the RETIRED section.** It's a permanent ban list.
- **Don't mine SSH-session transcripts** (project paths starting with `ssh-`). Those are remote work, often not in Michael's voice.
