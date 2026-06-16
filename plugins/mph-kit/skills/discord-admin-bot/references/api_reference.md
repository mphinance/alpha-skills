# Discord API Reference

Notes for the `discord-admin-bot` skill. We use the public Discord REST API directly — no `discord.py` dependency.

## Base
- URL: `https://discord.com/api/v10`
- Auth header: `Authorization: Bot <token>`
- User-Agent header (required by Discord): `DiscordBot (https://github.com/mphinance/alpha-skills, 1.0)`

## Endpoints used

| Purpose | Method | Path |
|---|---|---|
| Verify token | GET | `/users/@me` |
| List bot's guilds | GET | `/users/@me/guilds` |
| List channels in a guild | GET | `/guilds/{guild_id}/channels` |
| Send a message | POST | `/channels/{channel_id}/messages` body `{"content": "..."}` |
| Read recent messages | GET | `/channels/{channel_id}/messages?limit=N` (max 100) |

## Required gateway intents

To read message **content** (not just metadata like author and ID), the bot must have the **MESSAGE CONTENT INTENT** enabled in the Discord developer portal. This is a privileged intent.

For REST reads of historical messages (what we do here), the MESSAGE CONTENT intent is also required as of API v10. Without it, `content` fields come back empty.

## Required permissions on `#admin-discussion`

- View Channel
- Read Message History
- Send Messages

If the bot can read but not send, check Send Messages. If it can send but reads return empty, check MESSAGE CONTENT intent.

## Rate limits

- Global: 50 req/sec/IP
- Per route: response headers `X-RateLimit-Remaining`, `X-RateLimit-Reset-After`
- 429 response body: `{"retry_after": <seconds>, "global": <bool>}`

The client retries once on 429, sleeping for `retry_after`. A second 429 raises rather than looping.

## Channel ID lookup

Channel IDs are stable until the channel is deleted and recreated. We cache them in `discord_config.json` and only refresh via `discover.py` when something breaks.

## What we deliberately don't support

- Message editing/deletion (one-off; ask user to run a custom command if needed)
- Slash commands / interactions (this is a bot for the user, not for end-users in the server)
- Voice channels
- File uploads (use the webhook or upload manually)
- Reactions, threads, pins
