#!/usr/bin/env python3
"""image-bakeoff: run prompts through OpenRouter image models, render a contact sheet.

  bakeoff.py run   --models a/b,c/d --prompts prompts.json --out DIR [--gen-args "--quality high"]
  bakeoff.py sheet --results DIR/results.json [--models a/b,c/d] [--prompts p1,p2] [--name sheet]

results.json: {"prompts": {"p1": "..."}, "cells": [{"model","prompt","file","cost","secs"}], "tiers": {"model": "CHEAP"}}
Cell files are paths relative to results.json, so a hand-built manifest can span several folders.
"""
import argparse, html, json, math, os, re, shlex, subprocess, sys, time

GEN = os.path.expanduser("~/.claude/skills/openrouter-images/scripts")


def slug(m):
    return re.sub(r"[^A-Za-z0-9-]+", "_", m)


def load(path):
    return json.load(open(path)) if os.path.exists(path) else {"prompts": {}, "cells": []}


def cmd_run(a):
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    rj = os.path.join(out, "results.json")
    R = load(rj)
    prompts = json.load(open(a.prompts))
    R["prompts"].update(prompts)
    extra = shlex.split(a.gen_args or "")
    for m in a.models.split(","):
        for k, p in prompts.items():
            base = os.path.join(out, f"{slug(m)}_{k}")
            t = time.monotonic()
            r = subprocess.run(["npx", "tsx", "generate.ts", p, "--model", m, "--output", base] + extra,
                               cwd=GEN, capture_output=True, text=True)
            secs = round(time.monotonic() - t, 1)
            cost = re.search(r"Cost: \$([0-9.]+)", r.stderr)
            try:
                saved = json.loads(r.stdout[r.stdout.index("{"):])["images_saved"][0]
            except Exception:
                print(f"FAIL {m} {k}: {(r.stderr or r.stdout)[-200:]}", file=sys.stderr)
                continue
            cell = {"model": m, "prompt": k, "file": os.path.relpath(saved, out),
                    "cost": float(cost.group(1)) if cost else None, "secs": secs}
            R["cells"] = [c for c in R["cells"] if not (c["model"] == m and c["prompt"] == k)] + [cell]
            json.dump(R, open(rj, "w"), indent=1)
            print(f"{m}\t{k}\t{secs}s\t{'$'+str(cell['cost']) if cell['cost'] is not None else 'cost n/a'}", flush=True)
    print("results:", rj)


def cmd_sheet(a):
    rj = os.path.abspath(a.results)
    base = os.path.dirname(rj)
    R = load(rj)
    models = a.models.split(",") if a.models else list(dict.fromkeys(c["model"] for c in R["cells"]))
    keys = a.prompts.split(",") if a.prompts else list(R["prompts"])
    cells = {(c["model"], c["prompt"]): c for c in R["cells"]}
    tiers = R.get("tiers", {})
    W = 56 + 200 + len(keys) * 312
    prow = math.ceil(len(keys) / 3)
    H = 204 + 66 * prow + 312 * len(models)
    h = f'''<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(a.title)}</title><style>
:root{{--bg:#0d0f14;--card:#171a22;--fg:#e8eaf0;--mut:#8b91a3;--acc:#7cf0c8;--line:#262b38}}
*{{box-sizing:border-box}}body{{margin:0;padding:28px;background:var(--bg);color:var(--fg);font:14px/1.4 system-ui,sans-serif;width:{W}px}}
h1{{margin:0 0 4px;font-size:26px}}.sub{{color:var(--mut);margin-bottom:16px}}
.prompts{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:20px}}
.p{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px}}.p b{{color:var(--acc)}}
.grid{{display:grid;grid-template-columns:200px repeat({len(keys)},300px);gap:12px;align-items:start}}
.hd{{color:var(--acc);font-weight:600;text-align:center;padding-bottom:2px}}
.meta{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px;height:300px}}
.tier{{font-size:11px;letter-spacing:.1em;color:var(--acc)}}.name{{font-size:16px;font-weight:600;margin:2px 0}}
.cell{{position:relative;width:300px;height:300px}}.cell img{{width:100%;height:100%;object-fit:cover;border-radius:10px;border:1px solid var(--line);display:block}}
.t{{position:absolute;right:6px;bottom:6px;background:#000b;padding:2px 8px;border-radius:99px;font-size:12px}}
.empty{{display:flex;align-items:center;justify-content:center;border:1px dashed var(--line);border-radius:10px;color:#4a5064}}
</style></head><body><h1>{html.escape(a.title)}</h1>
<div class="sub">cell tag = cost / wall-clock time (includes ~1-2s npx startup) · center-cropped to square, full images in the folders</div>
<div class="prompts">'''
    for k in keys:
        h += f'<div class="p"><b>{k}</b> {html.escape(R["prompts"][k])}</div>'
    h += '</div><div class="grid"><div></div>' + "".join(f'<div class="hd">{k}</div>' for k in keys)
    for m in models:
        h += f'<div class="meta"><div class="tier">{tiers.get(m,"")}</div><div class="name">{html.escape(m.split("/")[-1])}</div></div>'
        for k in keys:
            c = cells.get((m, k))
            if not c:
                h += '<div class="cell empty">not run</div>'
                continue
            cost = f"${c['cost']:.3f}" if c.get("cost") is not None else "n/a"
            secs = f"{c['secs']:g}s" if c.get("secs") is not None else "?"
            h += f'<div class="cell"><img src="{html.escape(c["file"])}"><span class="t">{cost} · {secs}</span></div>'
    h += "</div></body></html>"
    hp = os.path.join(base, a.name + ".html")
    open(hp, "w").write(h)
    pp = os.path.join(base, a.name + ".png")
    subprocess.run(["chromium", "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={W},{H}", "--virtual-time-budget=10000", f"--screenshot={pp}", "file://" + hp],
                   capture_output=True)
    print(hp)
    print(pp, f"({W}x{H})")


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
r = sp.add_parser("run")
r.add_argument("--models", required=True)
r.add_argument("--prompts", required=True, help='JSON file {"p1": "text", ...}')
r.add_argument("--out", required=True)
r.add_argument("--gen-args", default="")
r.set_defaults(f=cmd_run)
s = sp.add_parser("sheet")
s.add_argument("--results", required=True)
s.add_argument("--models")
s.add_argument("--prompts")
s.add_argument("--name", default="sheet")
s.add_argument("--title", default="Image model bakeoff")
s.set_defaults(f=cmd_sheet)
a = ap.parse_args()
a.f(a)
