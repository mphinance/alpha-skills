# Per-broker caveats

Status: `documented` = stated in broker docs when written; `unverified` = not confirmed against current docs or a live test. Re-check before relying on any row.

| Broker | Client order id | Limit | Duplicate-id behaviour | Lookup by client id | Environment read-back | Status |
|---|---|---|---|---|---|---|
| Webull | yes | max 32, alphanumeric | unverified | unverified | unverified | limit documented; rest unverified |
| Alpaca | `client_order_id` | max 128 chars | rejects duplicate id (unverified exact error) | `GET orders:by_client_order_id` (unverified) | paper/live is distinct base URL and keys; no session-capability call confirmed | limit documented; rest unverified |
| Tradier | no equivalent | n/a | no broker-side idempotency: your layer must prevent duplicates | reconcile by listing orders and matching symbol/side/qty/time | unverified | no-equivalent documented; rest unverified |

Consequence for Tradier: with no client id, a blind retry can create a second live order. Reconcile by listing orders before any resend, and keep your own local id and terms-hash as the source of truth.

Generate ids that satisfy the strictest limit you target (32 alphanumeric) if you want portability.
