---
name: discord-admin-bot
description: Send messages to and read messages from the TraderDaddy-Pro Discord (#admin-discussion by default) using the alpha-skills bot. Triggers on "post to discord", "send to admin-discussion", "discord post", "read discord", "what's in #admin-discussion", "last N discord messages", "ping the discord", or any natural-language request to message or check the TraderDaddy-Pro Discord.
---

# Discord Admin Bot

Send and read messages in the TraderDaddy-Pro Discord using the bot token at `discord.txt`. Default channel is `#admin-discussion`; can target other channels by name once they've been discovered.

## When to invoke
- "post to discord: <message>"
- "send to #admin-discussion: <message>"
- "what's been said in discord lately"
- "read last 20 messages from admin-discussion"
- Any request mentioning the TraderDaddy-Pro Discord, #admin-discussion, or "the bot"

## Flow

### Send a message
```
python scripts/send.py "Your message here"
```
Optional flags:
- `--channel <name>` — target a different channel by name (must be in `discord_config.json`)
- `--channel-id <id>` — target by raw ID

### Read recent messages
```
python scripts/read.py --limit 20
```
Optional flags:
- `--channel <name>` / `--channel-id <id>` — same as above
- `--format full` — include timestamps, authors, attachments; default is compact

### Discover channels (one-time, or when channel layout changes)
```
python scripts/discover.py
```
Lists every guild the bot is in and every text channel inside, and updates `discord_config.json` with the resolved IDs for `#admin-discussion`.

## Hard rules

- **Never print the token.** Loaded silently from `discord.txt` or `$DISCORD_BOT_TOKEN`.
- **Never commit `discord.txt` or `discord_config.json`.** The repo root `.gitignore` blocks both.
- **Confirm before destructive ops.** No deleting messages without explicit user instruction. Sending and reading are fine without confirmation; deletion requires Michael saying "delete that".
- **Respect Discord rate limits.** The client retries once on 429 with the `Retry-After` value; if a second 429 hits, fail loud rather than spam.
- **No automated cross-posting.** This skill is for direct user-driven sends, not webhook-style notifications. For algo entry/exit alerts, use the existing `core/discord_notify.py` webhook setup in the `mur` repo.

## Token loading order
1. `$DISCORD_BOT_TOKEN` env var (highest priority)
2. `discord.txt` in the skill folder (the install step copies it here from the alpha-skills repo)
3. `discord.txt` in the current working directory
4. `discord.txt` walking up from CWD until a parent contains it

## Setup (already done if installed via the build)
1. Discord developer portal → Bot → enable **MESSAGE CONTENT INTENT** (required to read message bodies, not just metadata).
2. Bot must be invited to the TraderDaddy-Pro guild with `View Channels` + `Send Messages` + `Read Message History` permissions on `#admin-discussion`.
3. `discord_config.json` populated by `discover.py`.

If sending or reading fails with 401 → token is wrong. With 403 → permissions missing. With 404 → channel ID stale, re-run `discover.py`.

See [api_reference.md](references/api_reference.md) for the underlying endpoints and rate-limit handling.
