---
description: On-demand cockpit view — today's calendar, money snapshot, and at-risk code
allowed-tools: Bash, Read
---

Give me my cockpit right now (Central time). Same spirit as my morning brief, on demand. No em dashes. Keep it under ~25 lines.

1. **📅 Today + tomorrow** — use the Google Calendar connector, time-ordered, flag anything I organize or need to prep.
2. **💰 Money** — use the brokerage connector (get_account_summary, get_account_positions): net liq, % cash (flag >50% as idle drag), unrealized P&L, best/worst mover. If you can read `C:\Users\mphan\OneDrive\Documents\GitHub\mphinance\secrets.env` for STRIPE_SECRET_KEY, also pull live Stripe balance + last-7-day net revenue (read-only, never print the key). Skip Stripe gracefully if the key is missing.
3. **🧑‍💻 Code** — scan repos under the GitHub folder; list only those with uncommitted or unpushed work, and the P0 branch flag if still open.
4. **⚡ One thing** — the single highest-leverage action for me right now, one sentence.

Never trade or move money. Read-only reporting.
