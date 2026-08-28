#!/usr/bin/env python3
"""Skill Validator for Alpha Skills Suite.

Validates that every skill directory has a valid SKILL.md with:
1. Valid YAML frontmatter demarcated by ---
2. 'name' matching the parent directory name
3. Non-empty 'description'
"""

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required. Install via: pip install pyyaml")
    sys.exit(1)


def validate():
    root = Path(__file__).resolve().parent.parent
    skills_dir = root / "skills"
    
    if not skills_dir.exists():
        print(f"Error: {skills_dir} does not exist.")
        sys.exit(1)
        
    errors = []
    total = 0

    for s in sorted(skills_dir.iterdir()):
        if not s.is_dir() or s.name.startswith("."):
            continue
        total += 1
        skill_md = s / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"{s.name}: Missing SKILL.md")
            continue
            
        content = skill_md.read_text(encoding="utf-8")
        if not content.startswith("---"):
            errors.append(f"{s.name}: Missing opening frontmatter '---'")
            continue
            
        parts = content.split("---", 2)
        if len(parts) < 3:
            errors.append(f"{s.name}: Invalid frontmatter delimiters")
            continue
            
        try:
            fm = yaml.safe_load(parts[1])
            if not isinstance(fm, dict):
                errors.append(f"{s.name}: Frontmatter must be a YAML dictionary")
                continue
            if "name" not in fm:
                errors.append(f"{s.name}: Frontmatter missing 'name'")
            elif fm["name"] != s.name:
                errors.append(f"{s.name}: Name '{fm['name']}' does not match directory '{s.name}'")
            if "description" not in fm or not str(fm["description"]).strip():
                errors.append(f"{s.name}: Frontmatter missing or empty 'description'")
        except Exception as e:
            errors.append(f"{s.name}: YAML parse error: {e}")

    print(f"Validated {total} skills: {total - len(errors)} passed, {len(errors)} errors.")
    if errors:
        for err in errors:
            print(f"  [ERROR] {err}")
        sys.exit(1)
    else:
        print("✓ All skills conform to the Alpha Skills specification.")


if __name__ == "__main__":
    validate()
