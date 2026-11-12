#!/usr/bin/env python3
"""Single source of truth for the Alpha Skills Suite counts and copy drift.

Counts and drift are computed from the tree, never hand-written into the README.
Run with --check to fail (exit 1) when the README badge disagrees with reality OR
when any skill that exists in more than one location has forked, so neither can
drift again.

Locations:
  skills/                     the top-level library (source of truth)
  plugins/<plugin>/skills/    what a `/plugin install` actually delivers

A skill's *source* is every file under its directory except generated/run output
(__pycache__, *.pyc, runs/, history/, reports/, proposals/, .cache, node_modules,
venvs). Generated output is excluded so the check flags real forks only.
"""
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# path segments that are generated output, not skill source
GENERATED_DIRS = {"__pycache__", "runs", "history", "reports", "proposals",
                  ".cache", "node_modules", ".venv", "venv"}
GENERATED_SUFFIXES = (".pyc", ".pyo")


def collect(location):
    """name -> skill directory, for every skill dir (a dir holding SKILL.md)."""
    out = {}
    base = os.path.join(ROOT, location)
    if not os.path.isdir(base):
        return out
    for entry in sorted(os.listdir(base)):
        d = os.path.join(base, entry)
        if os.path.isfile(os.path.join(d, "SKILL.md")):
            out[entry] = d
    return out


def source_files(d):
    """Relative paths of a skill's source files (generated output excluded)."""
    rels = []
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in GENERATED_DIRS]
        for f in files:
            if f.endswith(GENERATED_SUFFIXES):
                continue
            rels.append(os.path.relpath(os.path.join(root, f), d))
    return sorted(rels)


def source_hash(d):
    h = hashlib.sha256()
    for rel in source_files(d):
        h.update(rel.encode())
        h.update(b"\0")
        with open(os.path.join(d, rel), "rb") as fh:
            h.update(hashlib.sha256(fh.read()).digest())
    return h.hexdigest()


def plugin_dirs():
    pdir = os.path.join(ROOT, "plugins")
    if not os.path.isdir(pdir):
        return []
    return [
        os.path.join("plugins", d, "skills")
        for d in sorted(os.listdir(pdir))
        if os.path.isdir(os.path.join(pdir, d, "skills"))
    ]


def survey():
    lib = collect("skills")
    plugins = {p: collect(p) for p in plugin_dirs()}

    distinct = set(lib)
    for skills in plugins.values():
        distinct |= set(skills)

    # duplicate names across locations
    dupes = {}
    for name in distinct:
        where = [p for p, skills in plugins.items() if name in skills]
        if name in lib:
            where = ["skills"] + where
        if len(where) > 1:
            dupes[name] = where

    # drifted: same name, different source bytes across locations
    drifted = []
    for name, where in sorted(dupes.items()):
        hashes = {}
        if name in lib:
            hashes["skills"] = source_hash(lib[name])
        for p, skills in plugins.items():
            if name in skills:
                hashes[p] = source_hash(skills[name])
        if len(set(hashes.values())) > 1:
            drifted.append({"name": name, "locations": hashes})

    # reachable by any plugin install
    reachable = set()
    for skills in plugins.values():
        reachable |= set(skills)
    unplugged = sorted(set(lib) - reachable)

    return {
        "library_count": len(lib),
        "plugins": {os.path.basename(os.path.dirname(p)): len(s) for p, s in plugins.items()},
        "plugin_total": sum(len(s) for s in plugins.values()),
        "distinct": len(distinct),
        "installable": len(reachable),
        "unplugged_count": len(unplugged),
        "unplugged": unplugged,
        "duplicate_count": len(dupes),
        "drifted_count": len(drifted),
        "drifted": drifted,
    }


def readme_badge():
    path = os.path.join(ROOT, "README.md")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.search(r"Agent_Skills-(\d+)", text)
    return int(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit 1 on a README badge mismatch or any forked copy")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    s = survey()
    if args.json:
        print(json.dumps(s, indent=2))
    else:
        print(f"library skills/            : {s['library_count']}")
        for name, n in s["plugins"].items():
            print(f"  plugin {name:<16}: {n}")
        print(f"distinct skill names       : {s['distinct']}")
        print(f"reachable by a plugin      : {s['installable']}")
        print(f"in skills/, in no plugin   : {s['unplugged_count']}")
        print(f"names in >1 location       : {s['duplicate_count']}")
        print(f"DRIFTED duplicates         : {s['drifted_count']}")
        for d in s["drifted"]:
            print(f"    - {d['name']}: " + ", ".join(sorted(d["locations"])))

    rc = 0
    badge = readme_badge()
    if badge is not None:
        print(f"README badge               : {badge}")
        if badge != s["distinct"]:
            print(f"{'FAIL' if args.check else 'WARN'}: README badge says {badge}, "
                  f"tree has {s['distinct']} distinct skills")
            if args.check:
                rc = 1
    if s["drifted_count"]:
        print(f"{'FAIL' if args.check else 'WARN'}: {s['drifted_count']} skill(s) forked "
              f"between locations; plugin copies must match skills/")
        if args.check:
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
