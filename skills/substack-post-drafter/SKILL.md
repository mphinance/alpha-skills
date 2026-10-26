---
name: substack-post-drafter
description: Pick a topic and write a private Substack draft in Michael's voice from live market data, recent repo work, and the weekly franchise schedule. Use when asked what to write about, to draft a post or Notes, or for the Sunday plan, Wednesday explainer, or Friday scorecard. Draft only, never publishes.
---

# Substack Post Drafter

Output is a draft file for Michael to read and edit. Never publish, schedule, or post a Note. Read the real voice guide first: `/home/mph/mphinance/SAM-VOICE.md` and Michael's `VOICE.md` (sign-off is exactly `~ Michael`, then `https://mphinance.com` on its own line; no last name, no dashes of any kind, no em or en dashes in public copy; PG-13; Sam is third person in Michael's prose; blunt about the market, modest about himself; banned phrases: "Here's the truth", "Real talk", "Everyone gets this wrong", "Buckle up", "Let me be honest").

## Pick the topic (when he has none)

Gather signals, then propose 3 candidates ranked, and draft the best:
1. **Market**: `get_market_health`, `get_macro_regime`, `get_sector_flow` (window 5d), `get_economic_calendar`. A good topic is a conflict between signals (index flat but rotation underneath, flow vs technicals disagreeing).
2. **Repos**: recent merged commits in his repos (TraderMatrix, alpha-skills, mphinance). A fix or feature that teaches something ("IV Rank is range position, not a percentile") is a receipt-style post.
3. **Calendar**: FOMC, CPI, GDP, opex week.
4. Positions only if Michael names them. Never use family or customer accounts or customer data.

## Franchises (sustainable weekly system)

- **Sunday**: Weekly Plan. 3 levels, 2 scenarios, 1 invalidation, GEX walls and flow with as-of times.
- **Wednesday**: one mechanics explainer with real numbers (free, the shareable one).
- **Friday after close**: scorecard of the Sunday plan. What hit, what failed, arithmetic, misses included.
- **Notes**: 1 to 2 a day: a chart plus two lines of math, a level with its invalidation, or a contrarian one-liner with a number.
- **Monthly**: one free primer or big thesis piece; keep a pinned "Start here" index.

## Title and subtitle

- Title a stranger can read: claim plus contrast, a $TICKER or number, or a method. Examples: "SPY Is Flat. The Money Isn't", "Why Call Walls Beat Max Pain: Last 20 Expirations".
- Subtitle is a hook line that sells the post, not a category mix. If Michael wants the category line, add it as a second line.
- Fill the SEO title and description. Put a share and subscribe ask above any paywall.

## Draft rules

- Lead with what price and data did, then the story. News follows price.
- Every number has its as-of time and source. If a number is stale or missing, say so or cut it.
- Show the arithmetic. Include misses in any scorecard.
- Free flagship posts: 1,500 to 2,500 words when the topic earns it; otherwise make it a Note.
- Compliance: impersonal and general. No performance claims or win-rate banners, no "buy this now", no answering someone's personal position. Third-party research stays labeled and credited.
- Do not promise outcomes. Premium selling is "get rich slowly", not a guarantee.

## Output

Write `draft_<yyyy-mm-dd>_<slug>.md` in the Substack drafts folder (or the path Michael gives) containing: the post, 3 to 4 companion Notes, and a "Notes for Michael (delete before posting)" block listing anything unverified, assumptions, and where the draft departs from VOICE.md. Run a final check for banned phrases and dashes.
