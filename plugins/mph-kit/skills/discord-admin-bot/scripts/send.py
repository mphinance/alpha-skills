#!/usr/bin/env python3
"""Send a message to a Discord channel.

  python scripts/send.py "your message"
  python scripts/send.py --channel general "hi general"
  python scripts/send.py --channel-id 123... "raw id route"
  echo "from stdin" | python scripts/send.py -
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _client import request, resolve_channel


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("message", nargs="?", help="Message content. Use '-' to read from stdin.")
    ap.add_argument("--channel", help="Channel name (default: admin-discussion)")
    ap.add_argument("--channel-id", help="Channel ID (bypasses name lookup)")
    args = ap.parse_args()

    if args.message == "-" or args.message is None:
        text = sys.stdin.read().strip()
    else:
        text = args.message.strip()

    if not text:
        print("Refusing to send empty message.", file=sys.stderr)
        sys.exit(2)
    if len(text) > 2000:
        print(f"Message too long ({len(text)} chars). Discord limit is 2000.", file=sys.stderr)
        sys.exit(2)

    channel_id, channel_name = resolve_channel(name=args.channel, channel_id=args.channel_id)
    result = request("POST", f"/channels/{channel_id}/messages", body={"content": text})

    print(f"Sent to #{channel_name}  (message id: {result.get('id')})")


if __name__ == "__main__":
    main()
