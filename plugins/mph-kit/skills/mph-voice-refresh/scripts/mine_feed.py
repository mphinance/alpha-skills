#!/usr/bin/env python3
"""Mine Michael Hanko's Substack feed for published-voice patterns.

Complement to mine_voice.py:
  - mine_voice.py  → chat voice (unfiltered, conversational)
  - mine_feed.py   → Substack voice (curated, published)

Surfaces openers (first 2 sentences), closers (last 2 sentences), and short
punchy sentences from each post. Never modifies VOICE.md directly.
"""

import argparse
import html
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_FEED = "https://mphinance.substack.com/feed"

NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

PROFANITY_MARKERS = re.compile(r"\b(damn|hell|bullsh|f\*ck|sh\*t|crap)\b", re.IGNORECASE)
VOICE_MARKERS = re.compile(
    r"(\.{2,}|\blol\b|\bor whatever\b|\bI mean\b|\bI find\b|\bkinda\b|\bsorta\b|"
    r"\bdamn\b|\bbullsh|\bf\*ck|admitting losses|recovery|sober|character defect|"
    r"perfection is boring|here's the truth|let's be honest)",
    re.IGNORECASE,
)


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (voice-miner)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def strip_html(text):
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_sentences(text):
    # Naive but practical splitter; respects .!? as terminators
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'\(])", text)
    return [p.strip() for p in parts if 8 <= len(p.strip()) <= 280]


def parse_feed(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.iterfind(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pubdate = (item.findtext("pubDate") or "").strip()
        encoded = item.find("content:encoded", NS)
        content = (encoded.text if encoded is not None and encoded.text else "") or ""
        if not content:
            content = item.findtext("description") or ""
        items.append({"title": title, "link": link, "pubdate": pubdate, "content": content})
    return items


def load_existing_phrases():
    voice_md = Path(__file__).resolve().parent.parent / "VOICE.md"
    if not voice_md.exists():
        return set()
    text = voice_md.read_text(encoding="utf-8", errors="ignore")
    phrases = set()
    for line in text.splitlines():
        for m in re.findall(r'`([^`]+)`|"([^"]+)"', line):
            phrase = (m[0] or m[1]).lower().strip()
            if len(phrase) >= 8:
                phrases.add(phrase)
    return phrases


def is_distinctive(sentence):
    if VOICE_MARKERS.search(sentence):
        return True
    if PROFANITY_MARKERS.search(sentence):
        return True
    # Short declarative + ends with punchy punctuation
    if len(sentence) <= 80 and sentence.endswith((".", "!", "?")):
        words = sentence.split()
        if 4 <= len(words) <= 14:
            return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--feed", default=DEFAULT_FEED, help=f"RSS feed URL (default: {DEFAULT_FEED})")
    ap.add_argument("--limit", type=int, default=10, help="Posts to analyze (default 10, most recent)")
    ap.add_argument("--top-distinctive", type=int, default=20, help="Max distinctive sentences (default 20)")
    args = ap.parse_args()

    try:
        raw = fetch(args.feed)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"# Feed fetch FAILED\n{type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        items = parse_feed(raw)
    except ET.ParseError as e:
        print(f"# Feed parse FAILED\n{e}", file=sys.stderr)
        sys.exit(1)

    existing = load_existing_phrases()
    items = items[:args.limit]

    out = []
    out.append("# Feed Mining Report")
    out.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    out.append(f"Source: {args.feed}")
    out.append(f"Posts analyzed: {len(items)}")
    out.append("")

    openers = []
    closers = []
    distinctive = []

    for it in items:
        text = strip_html(it["content"])
        sentences = split_sentences(text)
        if not sentences:
            continue
        meta = f"({it['title'][:60]} — {it['pubdate'][:16]})"
        # Openers: first 2 sentences
        for s in sentences[:2]:
            if s.lower() not in existing:
                openers.append((s, meta))
        # Closers: last 2 sentences
        for s in sentences[-2:]:
            if s.lower() not in existing:
                closers.append((s, meta))
        # Distinctive middle
        for s in sentences[2:-2]:
            if is_distinctive(s) and s.lower() not in existing:
                distinctive.append((s, meta))

    def dedup_keep_order(pairs):
        seen = set()
        out = []
        for s, m in pairs:
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append((s, m))
        return out

    openers = dedup_keep_order(openers)
    closers = dedup_keep_order(closers)
    distinctive = dedup_keep_order(distinctive)

    out.append("## Candidate OPENERS (first 2 sentences of each post)")
    out.append("")
    if not openers:
        out.append("_None new._")
    else:
        for i, (s, m) in enumerate(openers[:args.top_distinctive], 1):
            out.append(f"{i}. \"{s}\"")
            out.append(f"   _{m}_")
            out.append("")

    out.append("## Candidate CLOSERS (last 2 sentences of each post)")
    out.append("")
    if not closers:
        out.append("_None new._")
    else:
        for i, (s, m) in enumerate(closers[:args.top_distinctive], 1):
            out.append(f"{i}. \"{s}\"")
            out.append(f"   _{m}_")
            out.append("")

    out.append("## Candidate DISTINCTIVE sentences (middle of posts)")
    out.append("")
    if not distinctive:
        out.append("_None new._")
    else:
        for i, (s, m) in enumerate(distinctive[:args.top_distinctive], 1):
            out.append(f"{i}. \"{s}\"")
            out.append(f"   _{m}_")
            out.append("")

    print("\n".join(out))


if __name__ == "__main__":
    main()
