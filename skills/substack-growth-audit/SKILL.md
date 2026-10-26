---
name: substack-growth-audit
description: Weekly read-only audit of a Substack publication's public archive to find why growth or engagement is slipping, using fixed tests with metrics. Use when asked why posts underperform, why subscribers are not growing, for a weekly growth check, or before planning the next week of posts. Never publishes.
---

# Substack Growth Audit

Read-only. Pull public data, compare to the prior audit, report what moved and which test to run next. Never post, draft to Substack, or touch subscriber data.

## Data

1. Public archive: `https://<pub>.substack.com/api/v1/archive?sort=new&limit=50` (page with `&offset=`). Per post: title, subtitle, date, word count, reactions, comment count, paywall flag, SEO fields (`search_engine_title`, `search_engine_description`).
2. Michael's own exports when he provides them (Stats > Growth/Subscribers/Posts, Settings > Exports): subscriber source, open and click rates, churn, free-to-paid. Aggregates only. Never print emails.
3. Save each audit to the memory/notes store with the date so the next run can diff.

## Measure every audit

- Posts per week and longest gap since last post.
- Average reactions and comments per post for the last 4 weeks vs the previous 4.
- Share of posts with zero comments.
- Subtitle quality: does it sell the post, or is it a category label.
- Title quality: stranger-readable, a $TICKER or number, a claim.
- SEO fields filled (count out of last 10 posts).
- Free posts of 1,500+ words vs short posts: reactions per post.
- Share and subscribe asks above the paywall.
- Restacks per post (public count).

## The five tests (14 days each, one metric each)

1. **Hook subtitles** replacing category-mix lines. Metric: reactions and email open rate vs prior 4 posts.
2. **Two flagship free posts a week**, 1,500 to 2,500 words, with receipts and charts. Short ideas go to Notes. Metric: reactions per flagship post.
3. **Stranger-readable titles** (ticker plus claim, or number plus method), with Substack headline tests when available. Metric: open rate and reactions.
4. **Share and subscribe asks above the paywall**, plus SEO title and description on every post. Metric: new subscribers per post, search impressions.
5. **Notes sprint**: 1 to 2 Notes a day (chart plus two lines of math), restack a peer's chart with one line added, three recommendation or creator-match outreaches a month. Metric: new subscribers from Notes, restacks.

Run one test at a time when possible so the result is attributable.

## Report format

```
Substack audit <date>
Moved: <3 numbers that changed vs last audit, with the values>
Cadence: <posts last 7 days, longest gap>
Worst offender: <the single biggest problem this week, with evidence>
Next test: <test number, what to change, metric, when to read the result>
Missing data: <what Michael could export to sharpen this>
```

Label claims OBSERVED (seen on a page), INFERRED, or UNKNOWN. Be blunt; no flattery. Reaction counts are not subscriber conversions; say so when it matters. No em dashes.
