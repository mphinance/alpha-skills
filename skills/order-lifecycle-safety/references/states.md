# Order record states

| State | Meaning | Allowed next |
|---|---|---|
| `DECIDED_ALLOW` | gate approved, audit written | `FORWARDED`, `UNKNOWN` |
| `DECIDED_REFUSE` | gate refused | terminal |
| `FORWARDED` | broker acknowledged | `FILLED`, `CANCELED`, `REJECTED` |
| `UNKNOWN` | forward raised/timed out | reconcile -> any of the above, or stay UNKNOWN + alert |
| `REPLAY` | same id and terms seen again | return first result |
| `ID_REUSED` | same id, different terms | refuse, terminal |
