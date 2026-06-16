"""Shared Discord REST client for the discord-admin-bot skill.

Token loading order:
  1. $DISCORD_BOT_TOKEN
  2. <skill_root>/discord.txt
  3. ./discord.txt (CWD)
  4. walk up from CWD until a parent has discord.txt
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API = "https://discord.com/api/v10"
USER_AGENT = "DiscordBot (https://github.com/mphinance/alpha-skills, 1.0)"

SKILL_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_ROOT / "discord_config.json"


def find_token():
    env = os.environ.get("DISCORD_BOT_TOKEN")
    if env:
        return env.strip()

    candidates = [SKILL_ROOT / "discord.txt", Path.cwd() / "discord.txt"]
    cur = Path.cwd().resolve()
    for _ in range(8):
        cur = cur.parent
        candidates.append(cur / "discord.txt")
        if cur == cur.parent:
            break

    for p in candidates:
        if p.exists() and p.is_file():
            token = p.read_text(encoding="utf-8").strip()
            if token:
                return token

    raise SystemExit(
        "No Discord bot token found. Set $DISCORD_BOT_TOKEN or place discord.txt "
        f"in {SKILL_ROOT} or the alpha-skills repo root."
    )


def load_config():
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def request(method, path, token=None, body=None, query=None):
    if token is None:
        token = find_token()
    url = API + path
    if query:
        url += "?" + urllib.parse.urlencode(query)

    data = None
    headers = {
        "Authorization": f"Bot {token}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, method=method, headers=headers)

    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                if not raw:
                    return None
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace") if e.fp else ""
            if e.code == 429 and attempt == 0:
                try:
                    retry_after = float(json.loads(body_text).get("retry_after", 1))
                except (json.JSONDecodeError, ValueError):
                    retry_after = float(e.headers.get("Retry-After", "1"))
                time.sleep(min(retry_after + 0.25, 10))
                continue
            raise SystemExit(f"Discord API {method} {path} failed: HTTP {e.code} — {body_text[:300]}")
        except urllib.error.URLError as e:
            raise SystemExit(f"Discord API {method} {path} unreachable: {e}")


def resolve_channel(name=None, channel_id=None):
    """Returns (channel_id, channel_name). Channel name lookup uses discord_config.json."""
    cfg = load_config()
    if channel_id:
        return channel_id, name or "(unknown)"
    target_name = (name or "admin-discussion").lower().lstrip("#")
    channels = cfg.get("channels", {})
    if target_name in channels:
        entry = channels[target_name]
        return entry["id"], entry["name"]
    raise SystemExit(
        f"Channel '{target_name}' not found in discord_config.json. "
        "Run `python scripts/discover.py` to populate it."
    )
