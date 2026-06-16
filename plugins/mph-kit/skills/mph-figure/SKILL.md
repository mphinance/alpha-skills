---
name: mph-figure
description: Render markdown or HTML into a crisp, accurately-rendered PNG — tables, data figures, stat cards — for inlining into Substack posts (where markdown tables render as garbage) or anywhere a real-browser-rendered image beats a hand-drawn one. Use whenever a post or doc needs a table-as-image, or any markdown/HTML turned into a picture.
---

# MPH Figure

Turns markdown (or raw HTML) into a pixel-accurate image: it renders the content in a
real browser via Playwright and screenshots it. Because a browser does the layout, the
output has full CSS fidelity — real fonts, text wrapping, column alignment, the lot.
More accurate than SVG-shortcut generators, which only support a subset of CSS.

Built mainly for one job: **Substack cannot render markdown tables.** The
`mph-substack-writer` skill mandates "generate an image instead." This skill is how you
generate it.

## When to use it

- A Substack post (or any doc) needs a **table** — render it as an image instead of
  writing a raw markdown table.
- Any time structured content (a comparison, a stat block, a small data card) reads
  better as a clean image than as plain markdown.

## One-time setup

This skill bundles a script with dependencies. Run once:

```
cd ~/.claude/skills/mph-figure
npm install
npx playwright install chromium   # skip if Playwright's browser is already installed
```

## How to use it

1. Write the figure as **markdown** (a normal markdown table works; column alignment
   with `:---:` is respected) and save it to a file, e.g. `figure.md`.
2. Render it:

   ```
   node ~/.claude/skills/mph-figure/scripts/render.mjs --in figure.md --out figure.png
   ```

3. Inline the result in the post: `![caption](figure.png)`.

Need full control of the markup? Pass a `.html` file (or add `--html`) instead.

## Options

- `--in <file>`     markdown or HTML input (required)
- `--out <file>`    output PNG (required)
- `--width <px>`    figure width, default 720 (a good Substack inline width)
- `--scale <n>`     sharpness / device scale, default 2 (retina-crisp)
- `--theme <name>`  visual theme, default `bloomberg`
- `--html`          treat the input as raw HTML regardless of extension

## Theme

`bloomberg` — a dark, sharp, data-first look: near-black card, amber accents, clean
tables with uppercase headers and tabular numerals. This is the "dark theme, Bloomberg
aesthetic" `mph-substack-writer` asks for. Add more themes to the `THEMES` map in
`scripts/render.mjs`.
