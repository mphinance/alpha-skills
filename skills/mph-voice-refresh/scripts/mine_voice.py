#!/usr/bin/env python3
"""Mine Claude Code transcripts for Michael Hanko's voice.

Reads ~/.claude/projects/*/*.jsonl, surfaces:
  1. Candidate ADDITIONS — distinctive user phrasing not yet in VOICE.md
  2. Candidate RETIREMENTS — 5-grams Claude has repeated across 3+ sessions

Outputs a markdown report to stdout. Never modifies VOICE.md directly —
voice is subjective, human reviews before applying.
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECTS_ROOT = Path.home() / ".claude" / "projects"

MIN_USER_LEN = 10
MAX_USER_LEN = 400

VOICE_MARKERS = [
    r'\.{2,}',
    r'\blol\b', r'\blmao\b', r'\btbh\b', r'\bngl\b', r'\bidk\b',
    r'\bor whatever\b', r'\bkinda\b', r'\bsorta\b', r'\bbasically\b',
    r'\bI mean\b', r'\bI guess\b', r'\bI find\b',
    r'\bwait\b', r'\bactually\b', r'\byeah\b',
    r'\bdamn\b', r'\bbullsh', r'\bf[*u]ck',
]
MARKER_RE = re.compile("|".join(VOICE_MARKERS), re.IGNORECASE)

SKIP_PREFIX_RE = re.compile(r'^(?:[A-Z]:\\|/[a-z]|https?://|<|```)')

NGRAM_STOPS = {"the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "but"}


def parse_timestamp(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def iter_messages(days, include_ssh=False):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    if not PROJECTS_ROOT.exists():
        return
    for project_dir in PROJECTS_ROOT.iterdir():
        if not project_dir.is_dir():
            continue
        if not include_ssh and project_dir.name.startswith("ssh-"):
            continue
        for jsonl in project_dir.glob("*.jsonl"):
            try:
                with jsonl.open(encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        dt = parse_timestamp(obj.get("timestamp"))
                        if dt and dt < cutoff:
                            continue
                        yield obj, jsonl.stem, project_dir.name
            except (OSError, PermissionError):
                continue


def is_voicey(text):
    if SKIP_PREFIX_RE.match(text):
        return False
    if not (MIN_USER_LEN <= len(text) <= MAX_USER_LEN):
        return False
    return MARKER_RE.search(text) is not None


def extract_assistant_text(obj):
    msg = obj.get("message", {})
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text", ""))
        return " ".join(parts)
    return ""


def normalize_for_ngrams(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^A-Za-z'\s]", " ", text)
    return text.lower()


def ngrams(text, n=5):
    words = [w for w in normalize_for_ngrams(text).split() if len(w) > 1]
    for i in range(len(words) - n + 1):
        gram_words = words[i:i + n]
        if all(w in NGRAM_STOPS for w in gram_words):
            continue
        yield " ".join(gram_words)


def load_existing_voice():
    voice_md = Path(__file__).resolve().parent.parent / "VOICE.md"
    if not voice_md.exists():
        return set(), set()
    text = voice_md.read_text(encoding="utf-8")
    current = set()
    retired = set()
    in_retired = False
    for line in text.splitlines():
        if line.startswith("## RETIRED"):
            in_retired = True
            continue
        if line.startswith("##"):
            in_retired = False
            continue
        m = re.findall(r'`([^`]+)`|"([^"]+)"', line)
        for a, b in m:
            phrase = (a or b).lower().strip()
            if len(phrase) < 4:
                continue
            (retired if in_retired else current).add(phrase)
    return current, retired


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30, help="Look back N days (default 30)")
    ap.add_argument("--top-user", type=int, default=20, help="Max user candidates (default 20)")
    ap.add_argument("--top-stale", type=int, default=15, help="Max stale n-grams (default 15)")
    ap.add_argument("--include-ssh", action="store_true", help="Include ssh-* project transcripts")
    args = ap.parse_args()

    existing, retired = load_existing_voice()

    user_lines = []
    assistant_grams = Counter()
    assistant_gram_sessions = defaultdict(set)
    sessions_seen = set()

    for obj, session, project in iter_messages(args.days, args.include_ssh):
        if obj.get("type") not in ("user", "assistant"):
            continue
        msg = obj.get("message", {})
        role = msg.get("role")
        content = msg.get("content")

        if role == "user" and isinstance(content, str):
            if obj.get("userType") != "external":
                continue
            text = content.strip()
            if is_voicey(text):
                user_lines.append((text, session, project))
                sessions_seen.add(session)

        elif role == "assistant":
            text = extract_assistant_text(obj)
            if not text or len(text) < 40:
                continue
            for gram in ngrams(text, n=5):
                assistant_grams[gram] += 1
                assistant_gram_sessions[gram].add(session)

    seen_keys = set()
    unique_user = []
    for text, session, project in reversed(user_lines):
        key = text.lower()
        if key in seen_keys or key in existing:
            continue
        seen_keys.add(key)
        unique_user.append((text, session, project))

    repeated = []
    for gram, count in assistant_grams.items():
        n_sessions = len(assistant_gram_sessions[gram])
        if n_sessions >= 3 and gram not in retired:
            repeated.append((gram, count, n_sessions))
    repeated.sort(key=lambda x: (-x[2], -x[1]))

    out = []
    out.append("# Voice Mining Report")
    out.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    out.append(f"Window: last {args.days} days")
    out.append(f"Sessions scanned: {len(sessions_seen)}")
    out.append("")
    out.append("## Candidate ADDITIONS (distinctive user phrasing)")
    out.append("")
    if not unique_user:
        out.append("_No new voice-worthy lines found in window._")
    else:
        for i, (text, session, project) in enumerate(unique_user[:args.top_user], 1):
            snippet = text.replace("\n", " ").strip()
            out.append(f"{i}. \"{snippet}\"")
            out.append(f"   _source: {session[:8]}…  project: {project[:40]}_")
            out.append("")
    out.append("## Candidate RETIREMENTS (Claude 5-grams reused across 3+ sessions)")
    out.append("")
    if not repeated:
        out.append("_No reused phrasings detected in window._")
    else:
        for i, (gram, count, n_sessions) in enumerate(repeated[:args.top_stale], 1):
            out.append(f"{i}. `{gram}` — {count}x across {n_sessions} sessions")

    print("\n".join(out))


if __name__ == "__main__":
    main()
