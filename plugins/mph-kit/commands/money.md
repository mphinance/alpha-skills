---
description: Quick live money snapshot — Stripe revenue + brokerage
allowed-tools: Bash, Read
---

Give me a fast money snapshot (Central time). No em dashes.

**Stripe (handle the key safely):** read `STRIPE_SECRET_KEY` from `C:\Users\mphan\OneDrive\Documents\GitHub\mphinance\secrets.env` into a shell variable. NEVER print or echo the key. It is a LIVE key; use it only as curl basic-auth user (`curl -s https://api.stripe.com/v1/<ep> -u "$KEY:"`). Report:
- Balance: `/v1/balance` (available + pending, cents/100).
- Last 7 days net revenue: `/v1/charges?limit=100&created[gte]=<epoch 7d ago>`, sum paid and not-refunded amounts minus refunds; note if `has_more`.
- Active subs: `/v1/subscriptions?status=active&limit=100`, count + rough monthly recurring estimate.
If the key/file is missing, say so and continue.

**Brokerage:** use the connector — get_account_summary + get_account_positions. Net liq, % cash, unrealized P&L, best/worst mover.

Output a tight 8-12 line snapshot, Stripe first (that is the real revenue), brokerage second. Read-only. Never trade or move money.
