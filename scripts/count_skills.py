#!/usr/bin/env python3
"""Single source of truth for the Alpha Skills Suite counts.

Counts are computed from the tree, never hand-written into the README. Run with
--check to fail (exit 1) when the README badge disagrees with reality, so the
number can never drift again.

Locations:
  skills/                     the top-level library
  plugins/<plugin>/skills/    what a `/plugin install` actually delivers

Reports: per-location counts, distinct names, cross-location duplicates,
drifted duplicates (same name, different SKILL.md), and skills that sit in
skills/ but are reachable by no plugin install.
"""
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def collect(location):
    """name -> SKILL.md path, for every skill dir under location."""
    out = {}
    base = os.path.join(ROOT, location)
    if not os.path.isdir(base):
        return out
    for entry in sorted(os.listdir(base)):
        skill = os.path.join(base, entry, "SKILL.md")
        if os.path.isfile(skill):
            out[entry] = skill
    return out


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


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

    # drifted: same name, different bytes between skills/ and a plugin
    drifted = []
    for name, where in sorted(dupes.items()):
        hashes = {}
        if name in lib:
            hashes["skills"] = sha(lib[name])
        for p, skills in plugins.items():
            if name in skills:
                hashes[p] = sha(skills[name])
        if len(set(hashes.values())) > 1:
            drifted.append({"name": name, "hashes": hashes})

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
    ap.add_argument("--check", action="store_true", help="exit 1 if README disagrees or any duplicate has drifted")
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
            print(f"    - {d['name']}: " + ", ".join(sorted(d["hashes"])))

    badge = readme_badge()
    if badge is not None:
        print(f"README badge               : {badge}")
        if badge != s["distinct"]:
            msg = (f"README badge says {badge}, tree has {s['distinct']} distinct skills")
            print(("FAIL: " if args.check else "WARN: ") + msg)
            if args.check:
                return 1
    if args.check and s["drifted_count"] > 0:
        names = ", ".join(d["name"] for d in s["drifted"])
        print(f"FAIL: {s['drifted_count']} drifted duplicate(s): {names}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
