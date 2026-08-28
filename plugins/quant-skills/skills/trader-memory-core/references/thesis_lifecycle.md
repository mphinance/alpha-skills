# Thesis Lifecycle

## Status States

| Status | Description | Typical Trigger |
|--------|-------------|-----------------|
| `IDEA` | Screened candidate, not yet validated for entry | Ingest from screener output |
| `ENTRY_READY` | Validated, entry conditions defined, waiting for price | Manual review / deep-dive analysis |
| `ACTIVE` | Position opened (actual_price and actual_date filled) | Entry execution confirmed |
| `CLOSED` | Position exited, outcome recorded | Exit execution confirmed |
| `INVALIDATED` | Thesis killed before or during holding | Kill criteria triggered |

## Valid Transitions

```
IDEA ──────► ENTRY_READY ──────► ACTIVE ──────► CLOSED
  │               │                 │
  └───────────────┴─────────────────┴──────────► INVALIDATED
```

### Forward-Only Rule

Transitions must move forward in the lifecycle. Reverse transitions are not allowed:

- `ACTIVE → IDEA` — **blocked** (ValueError)
- `CLOSED → ACTIVE` — **blocked** (ValueError)
- `INVALIDATED → *` — **blocked** (terminal state)

### Any → INVALIDATED

Any non-terminal status can transition to `INVALIDATED`:
- `IDEA → INVALIDATED` (screener output invalidated before review)
- `ENTRY_READY → INVALIDATED` (kill criteria triggered before entry)
- `ACTIVE → INVALIDATED` (kill criteria triggered during holding)

## Status-Dependent Operations

| Operation | Required Status | Effect |
|-----------|----------------|--------|
| `register()` | — | Creates thesis with `IDEA` status (idempotent via fingerprint) |
| `transition()` | Any non-terminal (IDEA → ENTRY_READY only) | Advances status, appends to `status_history` |
| `open_position()` | `ENTRY_READY` | Sets entry data, transitions to `ACTIVE` (only path to ACTIVE) |
| `attach_position()` | Any | Attaches position sizing data |
| `link_report()` | Any | Adds linked report reference |
| `close()` | `ACTIVE` | Sets `CLOSED`, computes `outcome.pnl_*` and `holding_days` |
| `terminate()` | Any non-terminal | Transitions to `CLOSED` (delegates to close) or `INVALIDATED` with optional exit data |
| `mark_reviewed()` | Any non-terminal | Updates review dates and status based on review_date |
| `rebuild_index()` | — | Recreates `_index.json` from YAML files |
| `validate_state()` | — | Checks file ⇔ index consistency + schema validation |

**Important**:
- `transition()` only allows `IDEA → ENTRY_READY`. All terminal statuses are blocked.
- Use `open_position()` to reach `ACTIVE` (requires `actual_price` and `actual_date`).
- Use `close()` or `terminate(terminal_status="CLOSED")` to reach `CLOSED`.
- Use `terminate(terminal_status="INVALIDATED")` to reach `INVALIDATED`.

## Monitoring Cycle

1. On `register()`: `next_review_date` = `created_at + review_interval_days`
2. On review: `last_review_date` updated, `next_review_date` advanced
3. `list_review_due(as_of)` returns theses where `next_review_date <= as_of`
4. Review status: `OK` → `WARN` → `REVIEW` (escalation ladder)
