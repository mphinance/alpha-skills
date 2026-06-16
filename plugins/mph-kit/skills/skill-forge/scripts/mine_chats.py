#!/usr/bin/env python3
"""Mine Claude Code transcripts for new-skill candidates and refinement signals."""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECTS_ROOT = Path.home() / ".claude" / "projects"
SKILLS_ROOT = Path.home() / ".claude" / "skills"
DEFAULT_OUT_DIR = SKILLS_ROOT / "skill-forge" / "reports"

MIN_MSG_LEN = 8
MAX_MSG_LEN = 2000

RECURSION_PATTERNS = [
    re.compile(r"\bskill-forge\b", re.IGNORECASE),
    re.compile(r"\bskill\s+forge\b", re.IGNORECASE),
]

FRUSTRATION_PATTERNS = [
    (re.compile(r"\bugh\b", re.IGNORECASE), "ugh"),
    (re.compile(r"\bwhy do I have to\b", re.IGNORECASE), "why do I have to"),
    (re.compile(r"\bthis is annoying\b", re.IGNORECASE), "this is annoying"),
    (re.compile(r"\bkeep having to\b", re.IGNORECASE), "keep having to"),
    (re.compile(r"\bevery time\b", re.IGNORECASE), "every time"),
    (re.compile(r"\bwish\s+(?:you|claude|it|this)\s+(?:could|would)\b", re.IGNORECASE), "wish you could"),
    (re.compile(r"\bI hate\b", re.IGNORECASE), "I hate"),
]

NEED_PATTERNS = [
    re.compile(r"\bcan you\b", re.IGNORECASE),
    re.compile(r"\bhelp me\b", re.IGNORECASE),
    re.compile(r"\bI need to\b", re.IGNORECASE),
    re.compile(r"\bevery time I\b", re.IGNORECASE),
]

STOPWORDS = {
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "but",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "this", "that", "these", "those", "it", "its", "i", "you", "we", "they",
    "he", "she", "him", "her", "them", "us", "my", "your", "our", "their",
    "me", "what", "which", "who", "whom", "whose", "when", "where", "why",
    "how", "if", "so", "than", "then", "as", "at", "by", "from", "with",
    "into", "out", "up", "down", "over", "under", "just", "also", "not",
    "no", "yes", "ok", "okay", "yeah", "yep", "nope",
}

NAME_TRIGGER_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,40}$")

REFINEMENT_ASK_TEMPLATES = [
    r"(?:the\s+)?{skill}\s+(?:skill\s+)?should\s+(?:also\s+)?(?P<ask>[^.!?\n]{{6,160}})",
    r"(?:the\s+)?{skill}\s+(?:skill\s+)?doesn'?t\s+(?P<ask>[^.!?\n]{{6,160}})",
    r"(?:the\s+)?{skill}\s+(?:skill\s+)?can'?t\s+(?P<ask>[^.!?\n]{{6,160}})",
    r"(?:the\s+)?{skill}\s+(?:skill\s+)?needs?\s+to\s+(?P<ask>[^.!?\n]{{6,160}})",
    r"(?:the\s+)?{skill}\s+(?:skill\s+)?(?:is\s+)?missing\s+(?P<ask>[^.!?\n]{{6,160}})",
    r"wish\s+(?:the\s+)?{skill}\s+(?:could|would|did)\s+(?P<ask>[^.!?\n]{{6,160}})",
    r"add\s+(?:to\s+)?{skill}[:\s]+(?P<ask>[^.!?\n]{{6,160}})",
    r"(?:the\s+)?{skill}\s+(?:skill\s+)?(?:also\s+)?supports?\s+(?P<ask>[^.!?\n]{{6,160}})",
]


def find_explicit_asks(text: str, skill_name: str) -> List[str]:
    """Return user-stated refinement asks for skill_name found in text.

    Only matches explicit patterns like 'X should also Y', 'wish X could Y',
    'add to X: Y'. Word-overlap heuristics are deliberately not used.
    """
    asks: List[str] = []
    skill_re = re.escape(skill_name)
    for template in REFINEMENT_ASK_TEMPLATES:
        pattern = re.compile(template.format(skill=skill_re), re.IGNORECASE)
        for m in pattern.finditer(text):
            ask = m.group("ask").strip(" -:,;")
            if len(ask) < 6:
                continue
            asks.append(ask)
    return asks


def parse_timestamp(ts: Optional[str]) -> Optional[datetime]:
    """Parse ISO-8601 timestamps from JSONL, tolerant of Z suffix."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def extract_user_text(obj: dict) -> str:
    """Pull user-typed text from a Claude Code JSONL row, ignoring tool_result noise."""
    msg = obj.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text", ""))
        return " ".join(p for p in parts if p)
    return ""


SYSTEM_NOISE_PATTERNS = [
    re.compile(r"^<system-reminder>", re.IGNORECASE),
    re.compile(r"^<command-name>", re.IGNORECASE),
    re.compile(r"^<command-message>", re.IGNORECASE),
    re.compile(r"^<local-command-stdout>", re.IGNORECASE),
    re.compile(r"^<local-command-stderr>", re.IGNORECASE),
    re.compile(r"^<bash-input>", re.IGNORECASE),
    re.compile(r"^<bash-stdout>", re.IGNORECASE),
    re.compile(r"^<bash-stderr>", re.IGNORECASE),
    re.compile(r"^<ide_selection>", re.IGNORECASE),
    re.compile(r"^<task-notification>", re.IGNORECASE),
    re.compile(r"^<stdin-input>", re.IGNORECASE),
    re.compile(r"^Caveat:", re.IGNORECASE),
    re.compile(r"^\[Request interrupted", re.IGNORECASE),
    re.compile(r"^This session is being continued", re.IGNORECASE),
    re.compile(r"^The user opened the file", re.IGNORECASE),
    re.compile(r"^The user has updated the IDE", re.IGNORECASE),
    # Skill-invocation prefix injected by the harness when a skill fires.
    # The whole SKILL.md gets prepended to the user message; we do not want to
    # mine that text as if the user typed it.
    re.compile(r"^Base directory for this skill", re.IGNORECASE),
    # Bare powershell prompts pasted as evidence of failures.
    re.compile(r"^PS [A-Z]:\\", re.IGNORECASE),
]


def is_system_noise(text: str) -> bool:
    """True if a 'user' row is actually a harness-injected system message."""
    stripped = text.lstrip()
    for pat in SYSTEM_NOISE_PATTERNS:
        if pat.match(stripped):
            return True
    # The Caveat wrapper sometimes appears mid-string after stripped command tags
    head = stripped[:200].lower()
    if head.startswith("caveat:") or "caveat: the messages below were generated" in head:
        return True
    # Discard messages that are mostly file paths. 3% slash density catches
    # paste-heavy messages without flagging normal prose that mentions one path.
    sample = stripped[:500]
    if len(sample) >= 40:
        slashes = sample.count("/") + sample.count("\\")
        if slashes / max(len(sample), 1) > 0.03:
            return True
    return False


def looks_like_recursion(text: str) -> bool:
    """True if the user message references skill-forge itself."""
    for pat in RECURSION_PATTERNS:
        if pat.search(text):
            return True
    return False


def is_ssh_session(cwd: Optional[str], project_slug: str) -> bool:
    """SSH transcripts use posix /home/ cwd or ssh- prefixed project slug."""
    if project_slug.startswith("ssh-"):
        return True
    if cwd and cwd.startswith("/home/"):
        return True
    return False


def normalize_for_ngrams(text: str) -> str:
    """Strip code fences, urls, paths, punctuation; lowercase for n-gram extraction."""
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    # Strip Windows-style absolute paths (C:\..., C:/...) and posix paths (/home/...).
    text = re.sub(r"[A-Za-z]:[\\/][^\s]+", " ", text)
    text = re.sub(r"(?:^|\s)/[A-Za-z][\w./-]+", " ", text)
    # Strip leftover multi-segment backslash paths.
    text = re.sub(r"\\[A-Za-z0-9_.-]+(?:\\[A-Za-z0-9_.-]+)+", " ", text)
    text = re.sub(r"[^A-Za-z'\s]", " ", text)
    return text.lower()


def ngrams(text: str, n: int = 5) -> Iterator[str]:
    """Yield n-grams of non-stopword tokens of length > 1."""
    words = [w for w in normalize_for_ngrams(text).split() if len(w) > 1]
    for i in range(len(words) - n + 1):
        gram_words = words[i:i + n]
        if all(w in STOPWORDS for w in gram_words):
            continue
        if any(w in STOPWORDS for w in gram_words[:1] + gram_words[-1:]):
            # require non-stopwords at both edges to avoid noise like "to the and a be"
            continue
        yield " ".join(gram_words)




def iter_jsonl_rows(
    days: int,
    verbose: bool,
    skip_log: List[str],
) -> Iterator[Tuple[dict, str, str, Optional[str]]]:
    """Walk projects/**/*.jsonl yielding (obj, session_id, project_slug, cwd) for rows in window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    if not PROJECTS_ROOT.exists():
        if verbose:
            skip_log.append(f"projects root missing: {PROJECTS_ROOT}")
        return
    for project_dir in PROJECTS_ROOT.iterdir():
        if not project_dir.is_dir():
            continue
        slug = project_dir.name
        for jsonl in project_dir.glob("*.jsonl"):
            session_skipped_ssh = False
            try:
                with jsonl.open(encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            if verbose:
                                skip_log.append(f"parse error in {jsonl.name}")
                            continue
                        dt = parse_timestamp(obj.get("timestamp"))
                        if dt and dt < cutoff:
                            continue
                        cwd = obj.get("cwd")
                        if is_ssh_session(cwd, slug):
                            if verbose and not session_skipped_ssh:
                                skip_log.append(f"ssh-session skipped: slug={slug} cwd={cwd}")
                                session_skipped_ssh = True
                            continue
                        sid = obj.get("sessionId") or jsonl.stem
                        yield obj, sid, slug, cwd
            except (OSError, PermissionError) as exc:
                if verbose:
                    skip_log.append(f"io error {jsonl}: {exc}")
                continue


def suggest_kebab_name(phrase: str) -> str:
    """Convert a free-text phrase into a kebab-case skill name candidate."""
    cleaned = re.sub(r"[^a-z0-9\s-]", "", phrase.lower()).strip()
    parts = [p for p in cleaned.split() if p and p not in STOPWORDS]
    if not parts:
        parts = phrase.lower().split()[:3]
    name = "-".join(parts[:4])[:48].strip("-")
    return name or "candidate-skill"


def shorten(text: str, limit: int = 240) -> str:
    """Collapse whitespace, truncate for readable evidence snippets."""
    snippet = re.sub(r"\s+", " ", text).strip()
    if len(snippet) > limit:
        snippet = snippet[:limit].rstrip() + "..."
    return snippet


def discover_skills() -> List[Tuple[str, Path]]:
    """Return list of (skill_name, SKILL.md path) for every skill subdir."""
    if not SKILLS_ROOT.exists():
        return []
    out: List[Tuple[str, Path]] = []
    for sub in SKILLS_ROOT.iterdir():
        if not sub.is_dir():
            continue
        if sub.name.startswith("."):
            continue
        skill_md = sub / "SKILL.md"
        out.append((sub.name, skill_md))
    return out


def load_skill_text(skill_md: Path) -> str:
    """Read SKILL.md text or empty string if missing."""
    if not skill_md.exists():
        return ""
    try:
        return skill_md.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return ""


def build_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Mine Claude Code transcripts for skill-forge signals.")
    ap.add_argument("--days", type=int, default=30, help="Look back N days (default 30)")
    ap.add_argument("--verbose", action="store_true", help="Print skip reasons to stderr")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Where to write reports")
    ap.add_argument("--min-sessions", type=int, default=3, help="Min distinct sessions for new-skill 5-gram (default 3)")
    ap.add_argument("--top-skills", type=int, default=25, help="Max new-skill candidates emitted (default 25)")
    ap.add_argument("--top-pain", type=int, default=30, help="Max pain points emitted (default 30)")
    return ap.parse_args()


def collect_signals(
    days: int,
    verbose: bool,
    min_sessions: int,
) -> Tuple[Dict[str, dict], List[dict], Dict[str, dict], dict]:
    """Single-pass collector. Returns (gram_index, pain_points, skill_signals, stats)."""
    skip_log: List[str] = []

    gram_sessions: Dict[str, Set[str]] = defaultdict(set)
    gram_examples: Dict[str, List[str]] = defaultdict(list)
    gram_counts: Counter = Counter()

    pain_points: List[dict] = []

    skill_names = [name for name, _ in discover_skills()]
    skill_text: Dict[str, str] = {name: load_skill_text(md) for name, md in discover_skills()}

    # Explicit refinement asks keyed by skill name then by ask-string.
    explicit_asks: Dict[str, Dict[str, List[dict]]] = {
        name: defaultdict(list) for name in skill_names
    }

    session_user_messages: Dict[str, List[str]] = defaultdict(list)

    total_user = 0
    total_rows = 0
    recursion_skipped = 0
    sessions_seen: Set[str] = set()

    for obj, session_id, project_slug, cwd in iter_jsonl_rows(days, verbose, skip_log):
        total_rows += 1
        msg_type = obj.get("type")
        msg = obj.get("message") or {}
        role = msg.get("role")
        text = extract_user_text(obj) if isinstance(msg.get("content"), (str, list)) else ""

        if msg_type == "user" and role == "user":
            sessions_seen.add(session_id)
            if obj.get("userType") and obj.get("userType") != "external":
                continue
            if not text:
                continue
            if is_system_noise(text):
                if verbose and len(skip_log) < 200:
                    skip_log.append(f"system-noise skipped session={session_id[:8]}")
                continue
            if not (MIN_MSG_LEN <= len(text) <= MAX_MSG_LEN * 4):
                continue
            if looks_like_recursion(text):
                recursion_skipped += 1
                if verbose:
                    skip_log.append(f"recursion skipped session={session_id[:8]}")
                continue
            total_user += 1
            session_user_messages[session_id].append(text)

            for gram in ngrams(text, n=5):
                gram_counts[gram] += 1
                gram_sessions[gram].add(session_id)
                if len(gram_examples[gram]) < 3:
                    gram_examples[gram].append(shorten(text))

            for pat, marker in FRUSTRATION_PATTERNS:
                if pat.search(text):
                    pain_points.append({
                        "marker": marker,
                        "message": shorten(text, 320),
                        "session_id": session_id,
                        "timestamp": obj.get("timestamp", ""),
                    })
                    break

            # Explicit refinement asks: only fire when the user clearly says
            # "X should...", "wish X could...", etc. Word-overlap heuristics
            # produced too much noise in early runs.
            lowered = text.lower()
            for sname in skill_names:
                if sname == "skill-forge":
                    continue
                if sname not in lowered:
                    continue
                for ask in find_explicit_asks(text, sname):
                    explicit_asks[sname][ask.lower()].append({
                        "session_id": session_id,
                        "ask": ask,
                        "message": shorten(text, 320),
                    })

    # Build new_skill_candidates from grams meeting threshold
    candidates: List[dict] = []
    for gram, sids in gram_sessions.items():
        if len(sids) < min_sessions:
            continue
        candidates.append({
            "phrase": gram,
            "session_count": len(sids),
            "total_occurrences": gram_counts[gram],
            "example_messages": gram_examples[gram][:3],
            "suggested_name": suggest_kebab_name(gram),
            "rationale": (
                f"Phrase recurs across {len(sids)} distinct sessions "
                f"({gram_counts[gram]} total mentions) within the {days}-day window."
            ),
        })
    candidates.sort(key=lambda c: (-c["session_count"], -c["total_occurrences"]))

    # Build refinement_candidates from explicit user asks only.
    # Drop asks whose text already appears in the existing SKILL.md.
    refinements: Dict[str, dict] = {}
    for sname, asks_by_key in explicit_asks.items():
        existing = skill_text.get(sname, "")
        for ask_key, hits in asks_by_key.items():
            if ask_key in existing:
                continue
            sessions = {h["session_id"] for h in hits}
            evidence = []
            for h in hits[:3]:
                if h["message"] not in evidence:
                    evidence.append(h["message"])
            refinements[f"{sname}::{ask_key}"] = {
                "skill": sname,
                "missing_topic": hits[0]["ask"],
                "session_count": len(sessions),
                "occurrences": len(hits),
                "evidence_messages": evidence,
            }

    stats = {
        "total_rows": total_rows,
        "total_user_messages": total_user,
        "sessions_seen": len(sessions_seen),
        "recursion_skipped": recursion_skipped,
        "skip_log": skip_log,
        "skills_scanned": len(skill_names),
    }

    return (
        {"candidates": candidates},
        pain_points,
        {"refinements": list(refinements.values())},
        stats,
    )


def render_markdown(
    generated_at: str,
    days: int,
    candidates: List[dict],
    pain_points: List[dict],
    refinements: List[dict],
    stats: dict,
    top_skills: int,
    top_pain: int,
) -> str:
    """Render the human-facing latest.md report."""
    lines: List[str] = []
    lines.append("# skill-forge audit report")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append(f"Window: last {days} days")
    lines.append(
        f"Rows scanned: {stats['total_rows']} | user messages: {stats['total_user_messages']} | "
        f"sessions: {stats['sessions_seen']} | skills tracked: {stats['skills_scanned']}"
    )
    lines.append("")

    lines.append("## New skill candidates")
    lines.append("")
    if not candidates:
        lines.append("_No recurring 5-grams crossed the session threshold._")
    else:
        for i, c in enumerate(candidates[:top_skills], 1):
            lines.append(
                f"{i}. `{c['phrase']}` ({c['session_count']} sessions, "
                f"{c['total_occurrences']} mentions) suggested name: `{c['suggested_name']}`"
            )
            for ex in c["example_messages"]:
                lines.append(f"   - {ex}")
            lines.append("")

    lines.append("## Pain points")
    lines.append("")
    if not pain_points:
        lines.append("_No frustration markers detected._")
    else:
        for i, p in enumerate(pain_points[:top_pain], 1):
            lines.append(f"{i}. **{p['marker']}** [{p['timestamp'][:19]}] {p['message']}")
        lines.append("")

    lines.append("## Refinement candidates")
    lines.append("")
    if not refinements:
        lines.append("_No additive topics surfaced for existing skills._")
    else:
        by_skill: Dict[str, List[dict]] = defaultdict(list)
        for r in refinements:
            by_skill[r["skill"]].append(r)
        for sname in sorted(by_skill):
            lines.append(f"### {sname}")
            for r in sorted(by_skill[sname], key=lambda x: -x.get("session_count", 0)):
                sess_n = r.get("session_count", 0)
                lines.append(f"- `{r['missing_topic']}` ({sess_n} sessions)")
                for ex in r["evidence_messages"]:
                    lines.append(f"  - {ex}")
            lines.append("")

    if stats.get("skip_log"):
        lines.append("## Skip log (verbose)")
        lines.append("")
        for entry in stats["skip_log"][:50]:
            lines.append(f"- {entry}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = build_args()
    grams, pain_points, refinements_bundle, stats = collect_signals(
        days=args.days,
        verbose=args.verbose,
        min_sessions=args.min_sessions,
    )

    candidates = grams["candidates"]
    refinements = refinements_bundle["refinements"]

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    out_dir: Path = args.out_dir.expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": generated_at,
        "days_window": args.days,
        "new_skill_candidates": candidates[:args.top_skills],
        "pain_points": pain_points[:args.top_pain],
        "refinement_candidates": refinements,
        "stats": {k: v for k, v in stats.items() if k != "skip_log"},
    }

    json_path = out_dir / "latest.json"
    md_path = out_dir / "latest.md"

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    md_text = render_markdown(
        generated_at=generated_at,
        days=args.days,
        candidates=candidates,
        pain_points=pain_points,
        refinements=refinements,
        stats=stats,
        top_skills=args.top_skills,
        top_pain=args.top_pain,
    )
    md_path.write_text(md_text, encoding="utf-8")

    if args.verbose:
        for entry in stats["skip_log"][:80]:
            sys.stderr.write(f"skip: {entry}\n")
        sys.stderr.write(
            f"summary: rows={stats['total_rows']} user_msgs={stats['total_user_messages']} "
            f"sessions={stats['sessions_seen']} skills={stats['skills_scanned']} "
            f"recursion_skipped={stats['recursion_skipped']}\n"
        )

    print(f"wrote {md_path}")
    print(f"wrote {json_path}")
    print(
        f"candidates={len(candidates)} pain_points={len(pain_points)} "
        f"refinements={len(refinements)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
