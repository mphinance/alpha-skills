#!/usr/bin/env python3
"""Read the last N messages from a Discord channel.

  python scripts/read.py --limit 20
  python scripts/read.py --channel general --limit 50
  python scripts/read.py --format full
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _client import request, resolve_channel


def format_compact(messages, channel_name):
    print(f"# Last {len(messages)} in #{channel_name}")
    print()
    for m in reversed(messages):
        author = m.get("author", {}).get("username", "?")
        content = (m.get("content") or "").replace("\n", " ").strip()
        if not content and m.get("attachments"):
            content = f"[{len(m['attachments'])} attachment(s)]"
        ts = m.get("timestamp", "")[:16].replace("T", " ")
        print(f"  {ts}  {author}: {content}")


def format_full(messages, channel_name):
    print(f"# Last {len(messages)} in #{channel_name}")
    print()
    for m in reversed(messages):
        author = m.get("author", {})
        name = author.get("global_name") or author.get("username", "?")
        ts = m.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S %Z")
        except (ValueError, AttributeError):
            pass
        print(f"---")
        print(f"**{name}**  _{ts}_")
        content = m.get("content") or "_(no text)_"
        print(content)
        for a in m.get("attachments", []) or []:
            print(f"  [attachment] {a.get('filename')} → {a.get('url')}")
        for e in m.get("embeds", []) or []:
            if e.get("title"):
                print(f"  [embed] {e['title']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=20, help="Number of messages (1-100, default 20)")
    ap.add_argument("--channel", help="Channel name (default: admin-discussion)")
    ap.add_argument("--channel-id", help="Channel ID (bypasses name lookup)")
    ap.add_argument("--format", choices=["compact", "full"], default="compact")
    args = ap.parse_args()

    limit = max(1, min(args.limit, 100))
    channel_id, channel_name = resolve_channel(name=args.channel, channel_id=args.channel_id)
    messages = request("GET", f"/channels/{channel_id}/messages", query={"limit": limit})

    if not messages:
        print(f"No messages in #{channel_name}")
        return

    if args.format == "full":
        format_full(messages, channel_name)
    else:
        format_compact(messages, channel_name)


if __name__ == "__main__":
    main()
