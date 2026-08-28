# Field Mapping: Source Skill → Thesis Canonical Fields

## Mapping Table

| Source Skill | Raw Field | Canonical Field | Notes |
|---|---|---|---|
| kanchi-dividend-sop | `ticker` | `ticker` | Direct |
| kanchi-dividend-sop | `buy_target_price` | `entry.target_price` | |
| kanchi-dividend-sop | `current_yield_pct` | `origin.raw_provenance.current_yield_pct` | Preserved in raw |
| kanchi-dividend-sop | `signal` | `origin.raw_provenance.signal` | Preserved in raw |
| earnings-trade-analyzer | `symbol` | `ticker` | Renamed |
| earnings-trade-analyzer | `grade` | `origin.screening_grade` | A/B/C/D |
| earnings-trade-analyzer | `composite_score` | `origin.screening_score` | 0-100 |
| earnings-trade-analyzer | `gap_pct` | `origin.raw_provenance.gap_pct` | Preserved in raw |
| earnings-trade-analyzer | `sector` | `market_context.sector` | |
| vcp-screener | `symbol` | `ticker` | Renamed |
| vcp-screener | `entry_ready` | `origin.raw_provenance.entry_ready` | Boolean |
| vcp-screener | `distance_from_pivot_pct` | `origin.raw_provenance.distance_from_pivot_pct` | |
| vcp-screener | `composite_score` | `origin.screening_score` | |
| pead-screener | `symbol` | `ticker` | Renamed |
| pead-screener | `entry_price` | `entry.target_price` | |
| pead-screener | `stop_loss` | `exit.stop_loss` | |
| pead-screener | `status` | `origin.raw_provenance.pead_status` | SIGNAL_READY/BREAKOUT/etc |
| canslim-screener | `symbol` | `ticker` | Renamed |
| canslim-screener | `rating` | `origin.screening_grade` | |
| canslim-screener | `composite_score` | `origin.screening_score` | |
| edge-candidate-agent | `id` | `origin.raw_provenance.edge_id` | |
| edge-candidate-agent | `hypothesis_type` | `origin.raw_provenance.hypothesis_type` | |
| edge-candidate-agent | `mechanism_tag` | `mechanism_tag` | behavior/structure/uncertain |

## Position Sizer (Update Operation, not Register)

| Raw Field | Canonical Field | Notes |
|---|---|---|
| `final_recommended_shares` | `position.shares` | |
| `final_position_value` | `position.position_value` | |
| `final_risk_dollars` | `position.risk_dollars` | |
| `final_risk_pct` | `position.risk_pct_of_account` | |
| `mode` | — | Must be "shares" (budget mode rejected) |

## Phase 1 Constraints

- **Single ticker only**: Each thesis tracks exactly one stock symbol
- **edge-candidate-agent**: Only tickets with `research_only=False` and a single `ticker`/`symbol` field are accepted. `MARKET_BASKET` or `research_only` tickets are skipped with a warning log.
- **pair-trade-screener** and **options-strategy-advisor** are Phase 2 (multi-leg)

## Raw Provenance

All adapter-specific fields not listed in the canonical mapping are preserved in `origin.raw_provenance`. This allows:
1. No data loss during transformation
2. Recovery of original values if canonical mapping changes
3. Skill-specific analysis using raw data
