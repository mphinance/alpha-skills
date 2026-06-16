#!/usr/bin/env python3
"""Reconcile local ~/.mph-substack-cache workspaces against substack.com drafts."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CACHE_ROOT = Path.home() / ".mph-substack-cache"
SECRETS_PATH = Path("C:/Users/mphan/OneDrive/Documents/GitHub/mphinance/secrets.env")
DEFAULT_HOSTNAME = "mphinance.substack.com"
DEFAULT_STALE_DAYS = 3
DRAFT_API = "/api/v1/drafts?limit=20"

DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_")


@dataclass
class LocalWorkspace:
    slug: str
    path: Path
    post_md_path: Optional[Path]
    post_mtime: Optional[datetime]
    date_prefix: Optional[str]
    title_guess: Optional[str]


@dataclass
class ServerDraft:
    draft_id: int
    title: str
    slug: str
    edit_url: str
    updated_at: Optional[datetime]


def load_secrets() -> None:
    """Mirror create_draft_from_md.py — load secrets.env into os.environ."""
    if not SECRETS_PATH.exists():
        return
    for raw in SECRETS_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def extract_h1(text: str) -> Optional[str]:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def scan_local() -> List[LocalWorkspace]:
    if not CACHE_ROOT.exists():
        return []
    out: List[LocalWorkspace] = []
    for sub in sorted(CACHE_ROOT.iterdir()):
        if not sub.is_dir():
            continue
        post_md = sub / "post.md"
        post_mtime: Optional[datetime] = None
        title: Optional[str] = None
        if post_md.exists():
            try:
                post_mtime = datetime.fromtimestamp(post_md.stat().st_mtime, tz=timezone.utc)
                title = extract_h1(post_md.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                pass
        date_prefix: Optional[str] = None
        m = DATE_PREFIX_RE.match(sub.name)
        if m:
            date_prefix = m.group(1)
        out.append(LocalWorkspace(
            slug=sub.name,
            path=sub,
            post_md_path=post_md if post_md.exists() else None,
            post_mtime=post_mtime,
            date_prefix=date_prefix,
            title_guess=title,
        ))
    return out


def fetch_server_drafts(hostname: str, sid: str) -> List[ServerDraft]:
    url = f"https://{hostname}{DRAFT_API}"
    req = urllib.request.Request(url)
    req.add_header("Cookie", f"substack.sid={sid}")
    req.add_header("User-Agent", "substack-draft-status/1.0")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"substack api error: HTTP {exc.code} {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"substack api network error: {exc}") from exc

    items = payload if isinstance(payload, list) else payload.get("posts") or payload.get("drafts") or []
    drafts: List[ServerDraft] = []
    for d in items:
        if not isinstance(d, dict):
            continue
        draft_id = d.get("id") or d.get("post_id") or 0
        title = (d.get("draft_title") or d.get("title") or "").strip()
        slug = (d.get("slug") or d.get("draft_slug") or "").strip()
        updated_at = parse_iso(d.get("draft_updated_at") or d.get("updated_at") or d.get("post_date"))
        edit_url = f"https://{hostname}/publish/post/{draft_id}" if draft_id else ""
        drafts.append(ServerDraft(
            draft_id=int(draft_id) if draft_id else 0,
            title=title,
            slug=slug,
            edit_url=edit_url,
            updated_at=updated_at,
        ))
    return drafts


def normalize_title(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def match_local_to_server(local: LocalWorkspace, drafts: List[ServerDraft]) -> Optional[ServerDraft]:
    """Match by date-in-slug, then by title token overlap."""
    if local.date_prefix:
        date_compact = local.date_prefix.replace("-", "")
        for d in drafts:
            if d.slug and (local.date_prefix in d.slug or date_compact in d.slug.replace("-", "")):
                return d
            if d.updated_at and d.updated_at.strftime("%Y-%m-%d") == local.date_prefix:
                if local.title_guess and _title_overlap(local.title_guess, d.title):
                    return d
    if local.title_guess:
        for d in drafts:
            if _title_overlap(local.title_guess, d.title):
                return d
    return None


def _title_overlap(a: str, b: str, min_shared: int = 2) -> bool:
    a_tokens = set(normalize_title(a).split())
    b_tokens = set(normalize_title(b).split())
    a_tokens.discard("")
    b_tokens.discard("")
    short = {"the", "a", "an", "of", "to", "in", "on", "and", "or", "for"}
    a_tokens -= short
    b_tokens -= short
    return len(a_tokens & b_tokens) >= min_shared


def render_report(
    pushed: List[tuple],
    server_only: List[ServerDraft],
    local_fresh: List[LocalWorkspace],
    local_stale: List[LocalWorkspace],
    stale_days: int,
) -> str:
    lines: List[str] = []
    lines.append("# Substack draft status\n")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append(f"Stale threshold: {stale_days} days\n")

    lines.append("## Pushed (local + server match)")
    if not pushed:
        lines.append("_None._")
    else:
        for local, server in pushed:
            lines.append(f"- **{local.slug}** -> [{server.title}]({server.edit_url})")
    lines.append("")

    lines.append("## Server-only (created via web, no local workspace)")
    if not server_only:
        lines.append("_None._")
    else:
        for d in server_only:
            ts = d.updated_at.strftime("%Y-%m-%d") if d.updated_at else "?"
            lines.append(f"- [{ts}] **{d.title or '(untitled)'}** -> {d.edit_url}")
    lines.append("")

    lines.append(f"## Local-only STALE (older than {stale_days} days, not on server)")
    if not local_stale:
        lines.append("_None._")
    else:
        for w in local_stale:
            age = _age_days(w.post_mtime)
            title = w.title_guess or "(no H1)"
            lines.append(f"- **{w.slug}** ({age}d old) — {title} — `{w.path}`")
    lines.append("")

    lines.append("## Local-only fresh (recent, not yet pushed)")
    if not local_fresh:
        lines.append("_None._")
    else:
        for w in local_fresh:
            age = _age_days(w.post_mtime)
            title = w.title_guess or "(no H1)"
            lines.append(f"- **{w.slug}** ({age}d old) — {title} — `{w.path}`")
    lines.append("")

    if local_stale:
        lines.append(f"**Action:** {len(local_stale)} stale workspace(s) look forgotten. "
                     "Run `mph-substack-publish` on each, or delete the workspace if abandoned.")

    return "\n".join(lines).rstrip() + "\n"


def _age_days(when: Optional[datetime]) -> str:
    if not when:
        return "?"
    delta = datetime.now(timezone.utc) - when
    return str(int(delta.total_seconds() // 86400))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Show substack draft status: local vs server.")
    parser.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS,
                        help=f"Days after which a local-only workspace is stale (default {DEFAULT_STALE_DAYS})")
    parser.add_argument("--hostname", default=DEFAULT_HOSTNAME,
                        help=f"Substack hostname (default {DEFAULT_HOSTNAME})")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown")
    args = parser.parse_args(argv)

    load_secrets()
    sid = os.environ.get("SUBSTACK_SID", "")
    if not sid:
        sys.stderr.write(
            f"error: SUBSTACK_SID not set. Add it to {SECRETS_PATH} "
            "(see create_draft_from_md.py for the same auth pattern).\n"
        )
        return 2

    local = scan_local()
    drafts = fetch_server_drafts(args.hostname, sid)

    pushed: List[tuple] = []
    local_only: List[LocalWorkspace] = []
    matched_server_ids: set = set()

    for w in local:
        match = match_local_to_server(w, drafts)
        if match:
            pushed.append((w, match))
            matched_server_ids.add(match.draft_id)
        else:
            local_only.append(w)

    server_only = [d for d in drafts if d.draft_id not in matched_server_ids]

    now = datetime.now(timezone.utc)
    cutoff = args.stale_days * 86400
    local_stale = []
    local_fresh = []
    for w in local_only:
        age = (now - w.post_mtime).total_seconds() if w.post_mtime else None
        if age is None or age > cutoff:
            local_stale.append(w)
        else:
            local_fresh.append(w)

    if args.json:
        payload = {
            "generated_at": now.isoformat(timespec="seconds"),
            "stale_days": args.stale_days,
            "pushed": [{"slug": w.slug, "draft_id": s.draft_id, "edit_url": s.edit_url} for w, s in pushed],
            "server_only": [{"draft_id": d.draft_id, "title": d.title, "edit_url": d.edit_url} for d in server_only],
            "local_stale": [{"slug": w.slug, "path": str(w.path), "age_days": _age_days(w.post_mtime)} for w in local_stale],
            "local_fresh": [{"slug": w.slug, "path": str(w.path), "age_days": _age_days(w.post_mtime)} for w in local_fresh],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(render_report(pushed, server_only, local_fresh, local_stale, args.stale_days))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
