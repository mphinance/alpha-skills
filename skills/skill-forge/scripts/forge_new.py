"""Scaffold a new skill from a brief by rendering templates/SKILL.md.tmpl."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SKILL_FORGE_ROOT = Path.home() / ".claude" / "skills" / "skill-forge"
TEMPLATE_PATH = SKILL_FORGE_ROOT / "templates" / "SKILL.md.tmpl"
SKILLS_ROOT = Path.home() / ".claude" / "skills"
AUDIT_REPORT = SKILL_FORGE_ROOT / "reports" / "latest.json"


def title_case(name: str) -> str:
    """Turn a kebab-name into a Display Title."""
    return " ".join(part.capitalize() for part in name.replace("_", "-").split("-") if part)


def default_when_to_invoke(name: str, triggers: str) -> str:
    """Sensible placeholder for the When-to-invoke section."""
    base = f"Invoke {name} when the user requests the behavior described above."
    if triggers:
        base += f" Trigger phrases: {triggers}."
    base += " If the request is ambiguous, ask one clarifying question before proceeding."
    return base


def default_flow() -> str:
    """Sensible placeholder for the Flow section."""
    return (
        "1. Confirm the user's intent and capture any required inputs.\n"
        "2. Execute the core task in small, verifiable steps.\n"
        "3. Report results with absolute file paths and next-step suggestions.\n"
    )


def default_hard_rules() -> str:
    """Sensible placeholder for the Hard rules section."""
    return (
        "- Do not invent dependencies. Use stdlib first.\n"
        "- Never auto-commit or auto-push without explicit user request.\n"
        "- No emojis, no em dashes (U+2014). Use commas or periods.\n"
        "- Surface absolute paths for any file you create or modify.\n"
    )


def load_audit_seed() -> tuple[str | None, str | None]:
    """Return (suggested_name, rationale) from reports/latest.json top candidate, or (None, None)."""
    if not AUDIT_REPORT.exists():
        return None, None
    try:
        data = json.loads(AUDIT_REPORT.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None, None
    candidates = data.get("new_skill_candidates") or []
    if not candidates:
        return None, None
    top = candidates[0]
    return top.get("suggested_name"), top.get("rationale")


def render(template: str, mapping: dict[str, str]) -> str:
    """Replace {{key}} placeholders with mapping values."""
    out = template
    for key, value in mapping.items():
        out = out.replace("{{" + key + "}}", value)
    return out


def build_args() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description="Scaffold a new skill from a brief.")
    parser.add_argument("--name", help="Kebab-case skill name")
    parser.add_argument("--brief", help="One-paragraph description of the skill")
    parser.add_argument("--title", help="Display title (default: title-case of name)")
    parser.add_argument("--triggers", default="", help="Comma-separated trigger phrases")
    parser.add_argument("--from-audit", action="store_true", help="Prefill from reports/latest.json")
    parser.add_argument("--force", action="store_true", help="Overwrite existing skill dir")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    args = build_args().parse_args(argv)
    name = args.name
    brief = args.brief
    if args.from_audit and (not name or not brief):
        seed_name, seed_brief = load_audit_seed()
        if not name and seed_name:
            name = seed_name
        if not brief and seed_brief:
            brief = seed_brief
    if not name:
        print("error: --name is required (or use --from-audit with a populated report)", file=sys.stderr)
        return 1
    if not brief:
        print("error: --brief is required (or use --from-audit with a populated report)", file=sys.stderr)
        return 1
    if not TEMPLATE_PATH.exists():
        print(f"error: template not found at {TEMPLATE_PATH}", file=sys.stderr)
        return 1
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    title = args.title or title_case(name)
    description = brief.strip()
    triggers = (args.triggers or "").strip()
    if triggers:
        description = description.rstrip(".") + ". Triggers: " + triggers
    mapping = {
        "name": name,
        "description": description,
        "title": title,
        "when_to_invoke": default_when_to_invoke(name, triggers),
        "flow": default_flow(),
        "hard_rules": default_hard_rules(),
    }
    rendered = render(template, mapping)
    dest_dir = SKILLS_ROOT / name
    dest_file = dest_dir / "SKILL.md"
    if dest_dir.exists() and not args.force:
        print(f"error: skill dir already exists at {dest_dir} (use --force to overwrite)", file=sys.stderr)
        return 1
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file.write_text(rendered, encoding="utf-8")
    print(str(dest_file.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
