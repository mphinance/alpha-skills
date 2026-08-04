#!/usr/bin/env python3
"""
sync_export.py — close the loop: a checked-off Supernote export updates a master
Markdown checklist.

The Supernote exports handwritten notes (PDF/PNG) to the "EXPORT" folder on its
linked cloud. This script does the two MECHANICAL halves of the loop:

  latest  — find the newest export that matches your template (by filename/tag),
            so the agent knows which file to read.
  apply   — given the list of item labels the agent SAW as ticked (from reading
            the exported image), flip those boxes to [x] in the master .md and
            append a dated reconciliation line.

The one step in the middle — "which boxes are checked?" — is a vision read the
agent performs on the exported image. Handwriting/checkmark detection is not
reliable to do purely in code, so this script deliberately leaves that judgement
to the agent and only handles file-finding and text editing.

Examples:
    # 1. find the newest packing export the agent should read
    python3 sync_export.py latest ./EXPORT --contains PACKING

    # 2. after the agent reads it, apply the ticked labels
    python3 sync_export.py apply master.md --checked "Passport" "Gloves" "Boots"
"""
import argparse, glob, os, re, sys, datetime

def cmd_latest(a):
    files = []
    for ext in ("png", "PNG", "pdf", "PDF", "jpg", "jpeg"):
        files += glob.glob(os.path.join(a.folder, f"*.{ext}"))
    if a.contains:
        files = [f for f in files if a.contains.lower() in os.path.basename(f).lower()]
    if a.newer_than_hours:
        cutoff = __import__("time").time() - a.newer_than_hours * 3600
        files = [f for f in files if os.path.getmtime(f) >= cutoff]
    if not files:
        print("NONE")
        return
    newest = max(files, key=os.path.getmtime)
    print(newest)

def _norm(s):
    # loose match: lowercase, drop non-alphanumerics so "Sky Lagoon+spa" ~ "sky lagoon spa"
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

def cmd_apply(a):
    with open(a.master, encoding="utf-8") as f:
        lines = f.readlines()
    checked = [_norm(c) for c in a.checked]
    flipped = 0
    out = []
    for ln in lines:
        m = re.match(r"^(\s*[-*]\s*)\[ \](\s*)(.*)$", ln)
        if m:
            label = _norm(re.sub(r"[★*]", "", m.group(3)))  # strip star markers
            if any(c and (c in label or label in c) for c in checked):
                ln = f"{m.group(1)}[x]{m.group(2)}{m.group(3)}\n"
                flipped += 1
        out.append(ln)
    stamp = a.date or datetime.date.today().isoformat()
    log = f"- {stamp} - synced from Supernote export: {flipped} item(s) checked.\n"
    # append to a "Reconciliation log" section if present, else at end
    joined = "".join(out)
    if "reconciliation log" in joined.lower():
        out.append(log)
    else:
        out += ["\n---\n_Reconciliation log:_\n", log]
    with open(a.master, "w", encoding="utf-8") as f:
        f.writelines(out)
    print(f"Flipped {flipped} item(s) to [x] in {a.master}")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(required=True)

    p = sub.add_parser("latest", help="Print the newest matching export path (or NONE).")
    p.add_argument("folder", help="Local path to the synced EXPORT folder.")
    p.add_argument("--contains", default="", help="Only match filenames containing this string.")
    p.add_argument("--newer-than-hours", type=float, default=0, help="Ignore files older than this.")
    p.set_defaults(func=cmd_latest)

    p = sub.add_parser("apply", help="Flip ticked labels to [x] in the master .md.")
    p.add_argument("master", help="Path to the master Markdown checklist.")
    p.add_argument("--checked", nargs="*", default=[], help="Item labels the agent saw as ticked.")
    p.add_argument("--date", default="", help="Override the log date (YYYY-MM-DD).")
    p.set_defaults(func=cmd_apply)

    a = ap.parse_args()
    a.func(a)

if __name__ == "__main__":
    main()
