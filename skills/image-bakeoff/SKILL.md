---
name: image-bakeoff
description: Compare OpenRouter image-generation models on the same prompts and produce a contact sheet (HTML + PNG) with per-image cost and wall-clock time. Use when the user wants to bake off, benchmark, or visually compare image models, or asks "which image model is best/cheapest for X", or wants to add a model to an existing image comparison.
---

# image-bakeoff

Serial runs of N models x M prompts through the `openrouter-images` skill, saved with real cost and timing, then rendered as a models-by-prompts grid. Built from the 2026-10-08 bakeoff (winner: openai/gpt-image-2, see memory `image-model-choice-gpt-image-2`).

## Workflow

1. **Pick models.** Check live prices first: `cd ~/.claude/skills/openrouter-images/scripts && npx tsx discover.ts <model>` (pricing lines per endpoint; token-priced models have no per-image price, so estimate or measure). Also see `list-daily-model-rankings` with `modality=image_output` for usage.
2. **State the estimated cost to the user before running** (models x prompts x $/image). Per the global cost rule, never batch without saying so. Typical: $0.007 to 0.09 per image; 8 models x 2 prompts is about $0.6.
3. **Write prompts** to a JSON file: `{"p1": "text", "p2": "text"}`. Mix a text-in-image prompt, a photoreal portrait, a product shot, a stylized illustration.
4. **Run** (serial; some models take 60-90s per image, so use a background run for big sets):
   ```
   python3 ~/.claude/skills/image-bakeoff/scripts/bakeoff.py run --models openai/gpt-image-2,recraft/recraft-v4.1-flash --prompts prompts.json --out ~/projects/openrouter/imgbakeoff-YYYY-MM-DD
   ```
   Re-running into the same `--out` accumulates into `results.json` (same model+prompt replaces). Extra generate.ts flags: `--gen-args "--quality high"`.
5. **Sheet**:
   ```
   python3 ~/.claude/skills/image-bakeoff/scripts/bakeoff.py sheet --results DIR/results.json --models a/b,c/d --name combined --title "..."
   ```
   Writes `<name>.html` and `<name>.png` next to `results.json`. Filter with `--models` / `--prompts` to keep the sheet wide, not tall (models are rows, prompts are columns). Always view the PNG after rendering to confirm nothing is clipped.
6. **Save everything** (images, prompts, results.json, sheet) in a project folder, never the scratchpad. Always report cost and time per model.

## Gotchas

- Time includes ~1-2s `npx` startup, and results.json stores seconds measured by the script, not by the API.
- Some models report no cost (cost shows `n/a`), e.g. nano-banana-2.1.
- Output extensions vary by model (png/jpg/webp); the script records the real saved path.
- Hand-built manifests may span folders: cell `file` is relative to the manifest's directory, and an optional `"tiers": {"model": "CHEAP"}` adds a label.
- Cells are center-cropped squares in the sheet; open the originals before judging framing (e.g. tall posters get cropped).
- Image price scales with quality/size for token-priced models (gpt-image-2 family); default-quality runs are not representative of `--quality high`.
