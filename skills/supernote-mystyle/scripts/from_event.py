#!/usr/bin/env python3
"""
from_event.py — build a Supernote MyStyle template FROM an are-we-there-yet
trip's event.json, so the tablet template and the PWA checklist stay in sync
because they share one source of truth.

An are-we-there-yet `event.json` carries a `bring` array (the packing / bring
checklist the PWA renders) and `lists` (goal lists with a `must`/`stretch`
tone). This adapter maps either into the `spec` that make_template.py renders,
shortening the PWA's long descriptive item text into tight e-ink labels.

Keep editing `event.json` as the master. Regenerate the template whenever it
changes and the two views match.

Examples:
    # packing/bring list -> Nomad template
    python3 from_event.py ../are-we-there-yet/obsidian/event.json --list bring \
        --device nomad --mono -o OBSIDIAN_BRING_V1.png

    # a goal list by title (must-tone items become priority ★)
    python3 from_event.py .../event.json --list "The whole point" --mono -o goals.png

    # or just emit the spec to hand back and forth
    python3 from_event.py .../event.json --list bring --emit-spec > bring.spec.json
"""
import argparse, json, re, sys
import make_template  # same folder

PRI_KEYWORDS = ("non-negotiable", "passport", "must", "essential", "meds")
MAX_LABEL = 34  # chars that fit an e-ink half-column comfortably

def shorten(text):
    """Long PWA sentence -> tight label: first clause, capped."""
    first = re.split(r"[,.;:]| - | – ", text.strip())[0].strip()
    if len(first) > MAX_LABEL:
        first = first[:MAX_LABEL - 1].rstrip() + "…"
    return first

def item_rows(raw_items):
    rows = []
    for it in raw_items:
        text = it["text"] if isinstance(it, dict) else str(it)
        pri = any(k in text.lower() for k in PRI_KEYWORDS)
        rows.append({"item": shorten(text), "pri": pri})
    return rows

def pick_list(event, name):
    if name == "bring":
        b = event.get("bring") or []
        return "BRING / PACKING", "must", b
    for l in event.get("lists", []):
        if isinstance(l, dict) and l.get("title", "").lower() == name.lower():
            return l["title"].upper(), l.get("tone", ""), l.get("items", [])
    sys.exit(f"No list named '{name}'. Available: bring, " +
             ", ".join(repr(l.get("title")) for l in event.get("lists", []) if isinstance(l, dict)))

def build_spec(event, list_name):
    section, tone, raw = pick_list(event, list_name)
    rows = item_rows(raw)
    # split into two balanced columns, section header on top of the first
    half = (len(rows) + 1) // 2
    col1 = [{"section": section}] + rows[:half]
    col2 = rows[half:]
    tid = re.sub(r"[^A-Z0-9]+", "_", (event.get("id", "TRIP")).upper()).strip("_")
    lid = re.sub(r"[^A-Z0-9]+", "_", list_name.upper()).strip("_")
    return {
        "title": event.get("title", "TRIP").upper(),
        "subtitle": f"{event.get('subtitle','')}  ·  * = must".strip(" ·"),
        "tag": f"{tid}_{lid}_V1",
        "footer_left": "SUPERNOTE · MYSTYLE  ·  from event.json",
        "columns": [col1, col2] if col2 else [col1],
    }

def main():
    ap = argparse.ArgumentParser(description="Render a Supernote template from an event.json list.")
    ap.add_argument("event", help="Path to an are-we-there-yet event.json.")
    ap.add_argument("--list", default="bring", help="'bring' or a lists[].title.")
    ap.add_argument("--device", default="nomad")
    ap.add_argument("--mono", action="store_true")
    ap.add_argument("--emit-spec", action="store_true", help="Print the spec JSON instead of rendering.")
    ap.add_argument("-o", "--out", default="from_event.png")
    a = ap.parse_args()
    event = json.load(open(a.event))
    spec = build_spec(event, a.list)
    if a.emit_spec:
        print(json.dumps(spec, indent=2, ensure_ascii=False))
        return
    img = make_template.render(spec, device=a.device, mono=a.mono)
    img.save(a.out, "PNG", optimize=True)
    print(f"Saved {a.out}  ({img.size[0]}x{img.size[1]}) from {a.list} in {a.event}")

if __name__ == "__main__":
    main()
