# STATUS — <project / change name>

*Written by the orchestrator at end of run. In the user's voice if known.*

## TL;DR (one paragraph)

<What was attempted. What works end-to-end now. What's stubbed. Where the user should start tomorrow morning.>

## What works end-to-end

- [ ] <Feature/slice 1> — verified via <how>
- [ ] <Feature/slice 2> — verified via <how>
- [ ] <Feature/slice 3> — verified via <how>

`feature_list.json`: **X / Y** passing.

## What's stubbed (and how to swap in real values)

| Stub | Where | How to swap |
|---|---|---|
| <e.g. API key> | `<file>:<line>` | Set `<ENV_VAR>` in `.env`, restart |
| <e.g. mock data> | `<file>` | Replace with call to `<real endpoint>` once <prereq> |
| <e.g. placeholder copy> | `<file>` | Replace string `<placeholder>` with final copy |

## Known gaps (honest reasons, not excuses)

- **<Gap 1>** — <why it's not done: out-of-scope / blocked on X / hit complexity wall>
- **<Gap 2>** — <reason>
- **<Gap 3>** — <reason>

## File index (what lives where)

- `<path1>` — <one-line purpose>
- `<path2>` — <one-line purpose>
- `<path3>` — <one-line purpose>

## Commit history (waves)

```
<git log --oneline since the start of this run>
```

## What I'd do first if I were you

1. <Highest-leverage next action>
2. <Second action>
3. <Third action>

## How to resume

```bash
cd <repo>
<command to boot the stack>
# Then open <URL or file> and you'll see <expected state>
```

If you want to keep orchestrating, the unfinished work in `feature_list.json` (rows with `"passes": false`) is the next batch. Run `/orchestrate continue` or just say "keep going" and the orchestrator will pick up from the next wave.

---

## Notes for the orchestrator filling this in

- Lead with what works, not what's missing — momentum matters at handoff.
- Be honest about gaps. Don't sandbag with "polish needed" if a feature is actually broken.
- "What I'd do first if I were you" should be 1-3 items, not a backlog. Force a ranking.
- If the user has a known voice (mphinance Substack, internal Slack tone, etc.), match it. Otherwise be plain and direct.
- Append, don't replace — if a previous STATUS.md exists, prepend the new one with a date header.
