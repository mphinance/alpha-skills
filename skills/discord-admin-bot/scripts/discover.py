#!/usr/bin/env python3
"""Discover Discord guilds and channels the bot can see; populate discord_config.json.

Run this:
  - First-time setup
  - After the bot is added to a new guild
  - When send/read fails with 404 (channel deleted/recreated)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _client import request, load_config, save_config


def main():
    token_check = request("GET", "/users/@me")
    print(f"Bot identity: {token_check.get('username')}#{token_check.get('discriminator', '0')}  ({token_check.get('id')})")
    print()

    guilds = request("GET", "/users/@me/guilds")
    if not guilds:
        print("Bot is in 0 guilds. Invite it to TraderDaddy-Pro first.")
        sys.exit(1)

    cfg = load_config()
    cfg.setdefault("channels", {})
    cfg.setdefault("guilds", {})

    target_substrings = {"admin-discussion"}

    def matches_target(name):
        n = name.lower()
        for t in target_substrings:
            if t in n:
                return t
        return None

    print(f"Found {len(guilds)} guild(s):")
    for g in guilds:
        guild_id = g["id"]
        guild_name = g["name"]
        print(f"  • {guild_name}  ({guild_id})")
        cfg["guilds"][guild_name.lower()] = {"id": guild_id, "name": guild_name}

        try:
            channels = request("GET", f"/guilds/{guild_id}/channels")
        except SystemExit as e:
            print(f"    ! cannot list channels: {e}")
            continue

        text_channels = [c for c in channels if c.get("type") == 0]
        text_channels.sort(key=lambda c: (c.get("position", 0), c.get("name", "")))
        for c in text_channels:
            name = c["name"]
            matched = matches_target(name)
            marker = "  ←" if matched else ""
            print(f"      #{name}  ({c['id']}){marker}")
            if matched:
                cfg["channels"][matched] = {
                    "id": c["id"],
                    "name": name,
                    "guild_id": guild_id,
                    "guild_name": guild_name,
                }

    save_config(cfg)
    print()
    print(f"Wrote {len(cfg['channels'])} channel mapping(s) to discord_config.json")
    for k, v in cfg["channels"].items():
        print(f"  #{v['name']} → {v['id']}  (in {v['guild_name']})")


if __name__ == "__main__":
    main()
