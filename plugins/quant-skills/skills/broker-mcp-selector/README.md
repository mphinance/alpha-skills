# broker-mcp-selector

**The hands.** The rest of the Alpha Skills suite decides *what* to trade; this skill
answers *where to place the order and whether it's safe to let an agent do it.*

It picks a broker [MCP](https://modelcontextprotocol.io) server for execution based on
asset class, region, and how much autonomy you want to give an agent — then wires it up
with paper-by-default, least-privilege settings.

The data is backed by **[awesome-broker-mcp](https://github.com/mphinance/awesome-broker-mcp)**,
a continuously re-verified directory of which brokers ship an MCP server, which can
actually trade, and how each behaves if an agent does something careless. A condensed
snapshot ships in [`references/brokers.md`](references/brokers.md); the live list is the
source of truth.

See [`SKILL.md`](SKILL.md) for the full workflow.

## Pairs with

- `portfolio-manager` — read the account you connect.
- `ghost-auto-trader` — automate execution once you've picked a broker (keep a gate).
- any screener / regime skill — the brain that produces the plan this skill executes.
