#!/usr/bin/env python3
"""warden_scan: deterministic grep-based scan of SKILL.md files and scripts.

Usage: python3 warden_scan.py [ROOT ...] [--json]
  ROOT defaults to the repo's skills/ directory.

Output is CANDIDATE EVIDENCE for a human. It is never a verdict: a hit may be
benign and a clean scan proves nothing. Exit code is always 0 unless a path is
unreadable/missing (2); it does not gate anything.
"""
import json
import re
import sys
from pathlib import Path

CATEGORIES = {
    "order_verb": r"place_order|create_order|\bsubmit\w*|--execute",
    "bypass_flag": r"--yes\b|confirm\s*=\s*true|--quiet\b",
    "curl_pipe_sh": r"curl\b[^\n|]*\|\s*(?:sudo\s+)?(?:ba|z)?sh\b|wget\b[^\n|]*\|\s*(?:sudo\s+)?(?:ba|z)?sh\b",
    "bind_all": r"0\.0\.0\.0",
    "raw_private_key": r"PRIVATE_KEY",
    "unpinned_fetch": r"pip3?\s+install\s+(?!-r\b)(?:-\S+\s+)*[A-Za-z][\w.\-]*(?![\w.\-]*(?:==|@))(?=\s|$)|npx\s+(?!-)[\w@/.\-]+(?!@\d)(?=\s|$)|git\s+clone\s+\S+(?!.*--branch)|(?:curl|wget)\s+[^\n|]*https?://[^\s|]*(?:/main/|/master/|/latest/)",
    "gate_pattern": r"isatty|\binput\(|exit\s+10|token_check|verify_token|hmac\.compare_digest|APPROVAL_TOKEN|confirm_token",
}
RX = {k: re.compile(v, re.I if k != "raw_private_key" else 0) for k, v in CATEGORIES.items()}
NEAR = 8  # lines either side of an order verb that count as "next to"
SUFFIXES = {".md", ".py", ".sh", ".bash", ".js", ".ts", ".mjs", ".json", ".yml", ".yaml"}


def scan_file(path):
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        return None, str(e)
    hits = {k: [] for k in CATEGORIES}
    for i, ln in enumerate(lines, 1):
        for k, rx in RX.items():
            if rx.search(ln):
                hits[k].append((i, ln.strip()[:160]))
    near = []
    gate_lines = {i for i, _ in hits["gate_pattern"]}
    for i, ln in hits["order_verb"]:
        g = sorted(x for x in gate_lines if abs(x - i) <= NEAR)
        near.append({"order_verb_line": i, "gate_lines_within_%d" % NEAR: g})
    return {"hits": hits, "gate_proximity": near}, None


def main(argv):
    as_json = "--json" in argv
    roots = [Path(a) for a in argv if not a.startswith("--")] or [Path(__file__).resolve().parents[2]]
    report, errors = {}, []
    for root in roots:
        if not root.exists():
            errors.append(f"missing: {root}")
            continue
        files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in SUFFIXES and ".git" not in p.parts)
        for f in files:
            res, err = scan_file(f)
            if err:
                errors.append(f"{f}: {err}")
            elif any(res["hits"].values()):
                report[str(f)] = res
    if as_json:
        print(json.dumps({"disclaimer": "candidate evidence, not a verdict", "files": report, "errors": errors}, indent=1))
    else:
        print("# warden_scan: CANDIDATE EVIDENCE for human review, not a verdict\n")
        for f, res in report.items():
            print(f)
            for k, items in res["hits"].items():
                for i, ln in items:
                    print(f"  [{k}] {i}: {ln}")
            for n in res["gate_proximity"]:
                g = n["gate_lines_within_%d" % NEAR]
                print(f"  [gate?] order verb @{n['order_verb_line']}: " + (f"gate-like pattern at lines {g} (check it actually blocks)" if g else "NO gate-like pattern nearby"))
        c = {k: sum(len(r["hits"][k]) for r in report.values()) for k in CATEGORIES}
        print(f"\nfiles with hits: {len(report)}; hit counts: {c}")
    for e in errors:
        print("ERROR " + e, file=sys.stderr)
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
