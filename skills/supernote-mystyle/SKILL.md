---
name: supernote-mystyle
description: "A round-trip system for Supernote e-ink tablets. A small JSON spec is the shared contract between human and agent: the agent renders it into a device-correct 'MyStyle' template PNG, the human writes/ticks on the tablet, exports the note, and the agent reconciles the marks back into a master list. Use when the user wants a Supernote/Nomad/Manta/A5X custom template, a reusable pen-and-paper checklist for e-ink, a 'MyStyle' background, or a hand-off loop where a tablet note updates a tracked list. Triggers: 'supernote template', 'mystyle template', 'nomad checklist', 'e-ink template', 'make a template I can tick off', 'sync my supernote note back'."
---

# Supernote MyStyle round-trip

This skill is a **process for passing a checklist back and forth between a person
and an agent** through a Supernote tablet. The moving parts:

```
spec.json  ──render──▶  template.png  ──drop in MyStyle──▶  write on tablet
   ▲                                                              │
   │                                                          export
 reconcile ◀──read ticked boxes──  EXPORT/*.png  ◀────────────────┘
```

The **spec is the contract.** It is small, human-editable JSON, so either side
can author or amend it: the agent generates one from a conversation, or the
person hands one over to regenerate a template. Everything else (device sizing,
house style, the export read) hangs off that spec.

Supernote tablets show any PNG in their cloud `MyStyle` folder as a writable
template (Create Note → template → My Style), and export handwritten notes to a
`EXPORT` folder that Google Drive OCRs — which is what makes the round-trip work.

Design a template as a **reusable form** (a weekly reset, a review checklist, a
packing list), not a one-off — it repeats on every page created from it.

## When to reach for this

- The user wants a checklist/log/form they pen-check on a Supernote.
- They mention MyStyle, Nomad, Manta, A5X/A6X, or "e-ink template."
- They want a tablet note to feed back into a list that's tracked somewhere.

## Steps

1. **Pick the device.** The template MUST match the screen's native pixel
   resolution or it renders soft. Presets and specs are in
   `references/devices.md` (Nomad/A6X2 = 1404×1872, Manta/A5X2 = 1920×2560,
   A5X/A6X = 1404×1872).

2. **Author or accept a spec.** JSON with `title`, one-line `subtitle`, an
   all-caps footer `tag` (a version stamp like `RESET_V1`), optional
   `footer_left`, and one or two `columns` of `{"section": ...}` and
   `{"item": ..., "pri": true}` rows (`pri` → ★ don't-skip marker). One page;
   two columns fit ~60 items on a Nomad. Start from `examples/checklist.spec.json`.

3. **Render** — always `--mono` (1-bit; e-ink-crisp and ~25KB):
   ```
   python3 scripts/make_template.py examples/checklist.spec.json --device nomad --mono -o RESET_V1.png
   ```
   Read the PNG back and check nothing collides with the footer; trim or split if
   a column overruns.

4. **Deliver to MyStyle.** Hand the PNG to the user to drop into `Supernote/MyStyle`
   on their Drive/Dropbox (reliable). Only place it directly if a cloud connector
   with write access is present AND the small file uploads cleanly — otherwise a
   corrupt upload is worse than a drag-and-drop, so deliver the file.

5. **(Optional) Close the loop** when they've written on it — see below.

## The round-trip loop (export → master list)

The person ticks boxes on the tablet and exports the note; it lands in the cloud
`EXPORT` folder. Three parts — the middle one is a vision read, not code:

1. **Find** the newest matching export:
   ```
   python3 scripts/sync_export.py latest ./EXPORT --contains RESET --newer-than-hours 36
   ```
2. **Read** it — open the PNG/PDF and see which boxes are ticked (check, X, or
   filled box). Handwriting detection is the agent's judgement; don't fake it in code.
3. **Apply** the ticked labels to the master Markdown list (source of truth, one
   `- [ ] item` per line):
   ```
   python3 scripts/sync_export.py apply master.md --checked "Item A" "Item B"
   ```
   It flips `[ ]` → `[x]` on loose label matches and appends a dated reconciliation
   line.

To run it unattended, schedule a task that does 1–3 on a cadence and reports
what's still open. That needs the cloud connector and master list reachable in
the scheduled session; if they aren't, have it say so rather than guess.

## The spec contract, in full

```json
{
  "title":       "WEEKLY RESET",
  "subtitle":    "Nomad · tick as you go ·  * = must-do",
  "tag":         "RESET_V1",
  "footer_left": "SUPERNOTE NOMAD · MYSTYLE",
  "columns": [
    [ {"section":"MORNING"}, {"item":"Inbox to zero","pri":true}, {"item":"Plan the day"} ],
    [ {"section":"WEEKLY"},  {"item":"Review goals","pri":true},  {"item":"Back up files"} ]
  ]
}
```

- 1 column = full width; 2 columns = split page. Keep to one page.
- `pri` adds the ★ marker and pairs with a `* = …` note in the subtitle.
- The `tag` is the version signature — bump it (`RESET_V2`) when you change the
  form, so old exports stay distinguishable.

## Design system

Monospace bold, hairline rules, checkbox squares, ★ priority polygons, all-caps
version tag in the footer — deliberately spare so handwriting dominates. Palette
and the important **1-bit threshold rule** (light greys vanish under `--mono`;
keep elements darker than the cutoff) are in `references/house-style.md`. Reskin
by editing the palette constants or fonts in `make_template.py`.

## Sync with an are-we-there-yet trip (shared source of truth)

If the list also lives in an [are-we-there-yet](https://github.com/mphinance/are-we-there-yet)
trip PWA, don't maintain it twice. That app reads a `bring` array (and `lists`)
from `<trip>/event.json`. Generate the Supernote template FROM that same file, so
the tablet and the PWA always show the same items:

```
python3 scripts/from_event.py <trip>/event.json --list bring --device nomad --mono -o BRING_V1.png
```

`from_event.py` shortens the PWA's long descriptive lines into tight e-ink labels
and marks must-do items ★ by keyword. **`event.json` stays the single master** —
edit it, regenerate, both views match.

What syncs, and what doesn't:

- **Items (the list):** fully shared — one `event.json` feeds both. ✅
- **Checked state, Supernote → tracker:** the export loop above reads ticks off
  the tablet and can write them into a master `*.md` or a committed
  `<trip>/checklist-state.json`. ✅
- **Checked state, PWA ↔ Supernote (live, two-way):** NOT possible as-is. The PWA
  is static (GitHub Pages) and stores checks in per-device `localStorage`, which
  nothing outside that browser can read or write. True two-way check sync needs a
  shared backend, or a rework where the app hydrates its initial check state from
  a committed `checklist-state.json` that the export loop writes. Ink on paper
  can't be pushed back automatically either. Be upfront about this limit rather
  than implying live sync.

## Notes

- One page per template; prefer two columns over two pages.
- The EXPORT folder holds unrelated notes — always filter by `tag`/`--contains`
  and only touch the target list.
- `examples/` ships two specs: a generic `checklist.spec.json` and a real
  `packing.spec.json` to show a fuller, two-column layout.
- `scripts/from_event.py` bridges to an are-we-there-yet `event.json` (above).
