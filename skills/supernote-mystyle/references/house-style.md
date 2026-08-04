# House style — the MyStyle design system

The look is deliberately spare so that handwriting is the loudest thing on the
page. It reads as one system across every template.

## Elements

- **Type:** monospace, bold. Consolas on the device's own exports; the renderer
  uses DejaVu Sans Mono Bold (a close, freely-bundled stand-in). Monospace keeps
  checkbox columns aligned and looks intentional on e-ink.
- **Header:** all-caps title, a solid rule under it, then a one-line grey subtitle
  (device · date · legend). No form fields unless asked.
- **Rows:** a hollow checkbox square + item label. Priority rows get a filled ★
  polygon to the left of the box (the `pri` flag). The legend defines ★ as
  "don't-skip."
- **Section headers:** all-caps label with a hairline rule beneath.
- **Footer:** left = context (`SUPERNOTE NOMAD · MYSTYLE`), right = an all-caps
  **version tag** (`PACKING_V1`). The version tag is the signature move — it lets
  you tell revisions apart and matches the device's own `NOMAD_CONTINUUM_*`
  templates.

## Palette (grayscale, e-ink)

| Role | RGB | Note |
|------|-----|------|
| Ink (text, title rule) | 30, 30, 32 | near-black |
| Box outline | 70, 72, 76 | dark grey |
| Rules / secondary text | 116, 118, 122 | mid grey |

## The 1-bit rule

E-ink wants pure black/white, and a 1-bit PNG is ~10× smaller than grayscale
(≈25KB vs ≈250KB), so it syncs fast. But 1-bit thresholds every pixel at a
cutoff (the renderer uses >140 → white). **Any grey lighter than that vanishes.**
That is why the rules here are drawn at ~116, not a soft 200 — they survive the
threshold as crisp thin lines instead of disappearing. If you reskin the palette,
keep every element you want to see **darker than 140**, or render grayscale
instead of `--mono`.

## Reskinning

Change the palette constants or the two `load_font` paths in
`scripts/make_template.py`. The layout scales from a reference height of 1872px,
so proportions hold on any device. Keep contrast above the 1-bit threshold.
