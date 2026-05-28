"""Open a PR to mphinance/alpha-skills for a forged or refined skill."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


HOME = Path.home()
SKILL_FORGE_ROOT = HOME / ".claude" / "skills" / "skill-forge"
SKILLS_ROOT = HOME / ".claude" / "skills"
CACHE_DIR = HOME / ".cache" / "skill-forge" / "alpha-skills"
PROPOSALS_DIR = SKILL_FORGE_ROOT / "proposals"
AUDIT_REPORT = SKILL_FORGE_ROOT / "reports" / "latest.json"
REPO_SLUG = "mphinance/alpha-skills"


def run(cmd: list[str], cwd: Path | None = None, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a subprocess and return the completed process."""
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=check,
        text=True,
        capture_output=capture,
    )


def ensure_cache_clone(dry_run: bool) -> None:
    """Clone alpha-skills into the cache dir if missing. Skip network in dry-run when cache exists."""
    if CACHE_DIR.exists():
        return
    if dry_run:
        # We still need a working tree to diff against. Try to clone, but if offline, fail loud.
        pass
    CACHE_DIR.parent.mkdir(parents=True, exist_ok=True)
    run(["gh", "repo", "clone", REPO_SLUG, str(CACHE_DIR)])


def sync_main(dry_run: bool) -> None:
    """Fetch and hard-reset cache main to origin. Skip in dry-run to stay offline."""
    if dry_run:
        # Stay offline. Use whatever main happens to be locally.
        # If origin/main does not exist locally, callers should ensure_cache_clone first.
        try:
            run(["git", "-C", str(CACHE_DIR), "checkout", "main"], capture=True)
        except subprocess.CalledProcessError:
            pass
        return
    run(["git", "-C", str(CACHE_DIR), "fetch", "origin"])
    run(["git", "-C", str(CACHE_DIR), "checkout", "main"])
    run(["git", "-C", str(CACHE_DIR), "reset", "--hard", "origin/main"])
    run(["git", "-C", str(CACHE_DIR), "pull", "--ff-only", "origin", "main"])


def make_branch(name: str) -> str:
    """Create a skill-forge/<name>-<ts> branch and check it out."""
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    branch = f"skill-forge/{name}-{ts}"
    # Delete pre-existing branch with same name (rare).
    try:
        run(["git", "-C", str(CACHE_DIR), "branch", "-D", branch], capture=True, check=False)
    except subprocess.CalledProcessError:
        pass
    run(["git", "-C", str(CACHE_DIR), "checkout", "-b", branch])
    return branch


def refine_guard(src_dir: Path, dest_dir: Path) -> list[str]:
    """Return list of error strings if any non-whitespace line was removed from existing files."""
    errors: list[str] = []
    if not dest_dir.exists():
        return errors
    for dest_file in dest_dir.rglob("*"):
        if not dest_file.is_file():
            continue
        rel = dest_file.relative_to(dest_dir)
        src_file = src_dir / rel
        if not src_file.exists():
            errors.append(f"refine guard: existing file {rel} would be deleted")
            continue
        try:
            src_lines = src_file.read_text(encoding="utf-8").splitlines()
            dest_lines = dest_file.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        src_norm = {line.strip() for line in src_lines if line.strip()}
        for line in dest_lines:
            normalized = line.strip()
            if not normalized:
                continue
            if normalized not in src_norm:
                errors.append(f"refine guard: line removed from {rel}: {normalized!r}")
    return errors


EXCLUDE_DIRS = {".git", "__pycache__", "reports", "proposals", ".pytest_cache", ".mypy_cache", ".cache"}
EXCLUDE_SUFFIXES = (".pyc", ".pyo")


def _excluded(rel: Path) -> bool:
    """True if any path component is an excluded dir or the file has an excluded suffix."""
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return True
    if rel.suffix in EXCLUDE_SUFFIXES:
        return True
    return False


def copy_skill(src_dir: Path, dest_dir: Path) -> None:
    """Copy source skill dir into destination, skipping .git, __pycache__, reports, proposals, etc."""
    if not dest_dir.exists():
        dest_dir.mkdir(parents=True, exist_ok=True)
    for item in src_dir.rglob("*"):
        rel = item.relative_to(src_dir)
        if _excluded(rel):
            continue
        target = dest_dir / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def load_audit_evidence(name: str) -> str:
    """Return a markdown evidence block from reports/latest.json for this skill name, or empty string."""
    if not AUDIT_REPORT.exists():
        return ""
    try:
        data = json.loads(AUDIT_REPORT.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""
    candidates = data.get("new_skill_candidates") or []
    top = None
    for cand in candidates:
        if cand.get("suggested_name") == name:
            top = cand
            break
    if top is None and candidates:
        top = candidates[0]
    if not top:
        return ""
    parts = ["## Mined evidence", ""]
    if top.get("rationale"):
        parts.append(f"Rationale: {top['rationale']}")
        parts.append("")
    examples = top.get("example_messages") or []
    if examples:
        parts.append("Example user messages from transcripts:")
        parts.append("")
        for ex in examples[:5]:
            parts.append(f"- {ex}")
        parts.append("")
    return "\n".join(parts)


def write_pr_body(name: str, proposals_dir: Path, from_audit: bool, refine: bool) -> Path:
    """Write proposals/<name>/PR_BODY.md and return the path."""
    proposals_dir.mkdir(parents=True, exist_ok=True)
    body_path = proposals_dir / "PR_BODY.md"
    summary = (
        f"Refine the {name} skill with additive-only changes."
        if refine
        else f"Add the {name} skill scaffolded by skill-forge."
    )
    triggers_line = f"See `skills/{name}/SKILL.md` frontmatter description for trigger phrases."
    smoke = f"Invoke via `/{name}` or by saying a trigger phrase from the SKILL.md description."
    body = [
        f"# {summary}",
        "",
        "## What this skill does",
        "",
        f"Source of truth: `skills/{name}/SKILL.md`. Read the When-to-invoke and Flow sections there.",
        "",
        "## Key triggers",
        "",
        triggers_line,
        "",
        "## Smoke-test invocation",
        "",
        smoke,
        "",
    ]
    if from_audit:
        evidence = load_audit_evidence(name)
        if evidence:
            body.append(evidence)
    body.append("Generated by skill-forge. Never auto-merge.")
    body_path.write_text("\n".join(body), encoding="utf-8")
    return body_path


def write_diff(branch: str, proposals_dir: Path) -> Path:
    """Run git format-patch and write the diff to proposals/<name>/CHANGES.diff."""
    proposals_dir.mkdir(parents=True, exist_ok=True)
    diff_path = proposals_dir / "CHANGES.diff"
    proc = run(
        ["git", "-C", str(CACHE_DIR), "format-patch", "origin/main..HEAD", "--stdout"],
        capture=True,
    )
    diff_path.write_text(proc.stdout, encoding="utf-8")
    return diff_path


def build_args() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description="Open a PR to mphinance/alpha-skills for a forged skill.")
    parser.add_argument("name", help="Skill name (must exist under ~/.claude/skills/<name>)")
    parser.add_argument("--dry-run", action="store_true", help="Write diff to proposals/<name>/CHANGES.diff; no push/PR")
    parser.add_argument("--from-audit", action="store_true", help="Include mined evidence from reports/latest.json in PR body")
    parser.add_argument("--refine", action="store_true", help="Refine mode: enforce additive-only changes vs alpha-skills main")
    parser.add_argument("--message", help="Custom commit message")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    args = build_args().parse_args(argv)
    name = args.name
    src_dir = SKILLS_ROOT / name
    if not src_dir.exists():
        print(f"error: source skill not found at {src_dir}", file=sys.stderr)
        return 1
    commit_message = args.message or (f"Refine {name} skill" if args.refine else f"Add {name} skill")
    proposals_dir = PROPOSALS_DIR / name

    ensure_cache_clone(args.dry_run)
    sync_main(args.dry_run)
    branch = make_branch(name)

    dest_dir = CACHE_DIR / "skills" / name

    if args.refine:
        errs = refine_guard(src_dir, dest_dir)
        if errs:
            for line in errs:
                print(line, file=sys.stderr)
            print("refine mode rejected: additive-only changes required", file=sys.stderr)
            return 2

    copy_skill(src_dir, dest_dir)

    run(["git", "-C", str(CACHE_DIR), "add", f"skills/{name}"])
    # Skip empty commits cleanly.
    status = run(
        ["git", "-C", str(CACHE_DIR), "diff", "--cached", "--name-only"],
        capture=True,
    )
    if not status.stdout.strip():
        print("error: no staged changes to commit", file=sys.stderr)
        return 1
    run(["git", "-C", str(CACHE_DIR), "commit", "-m", commit_message])

    if args.dry_run:
        diff_path = write_diff(branch, proposals_dir)
        print(str(diff_path.resolve()))
        return 0

    body_path = write_pr_body(name, proposals_dir, args.from_audit, args.refine)
    run(["git", "-C", str(CACHE_DIR), "push", "-u", "origin", branch])
    pr_proc = run(
        [
            "gh", "pr", "create",
            "--repo", REPO_SLUG,
            "--title", commit_message,
            "--body-file", str(body_path),
        ],
        cwd=CACHE_DIR,
        capture=True,
    )
    url = pr_proc.stdout.strip()
    print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
