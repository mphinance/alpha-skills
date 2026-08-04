# Supernote device pixel specs

Custom (MyStyle) templates must be authored at the device's **native screen
resolution** in pixels. A template at the wrong size renders soft or misaligned
because the device does not rescale MyStyle backgrounds cleanly. Portrait
orientation, PNG. 1-bit (pure black/white) is ideal for e-ink and keeps the file
tiny; grayscale also works.

| Device | Codename | Screen | Native px (W×H) | `--device` |
|--------|----------|--------|-----------------|------------|
| Supernote Nomad | A6 X2 | 7.8" | 1404 × 1872 | `nomad` / `a6x2` |
| Supernote A6 X | A6 X | 7.8" | 1404 × 1872 | `a6x` |
| Supernote A5 X | A5 X | 10.3" | 1404 × 1872 | `a5x` |
| Supernote Manta | A5 X2 | 10.7" | 1920 × 2560 | `manta` / `a5x2` |

Notes:

- The A5 X and A6 X/X2 share the same 1404 × 1872 pixel grid despite different
  physical sizes (different DPI, same pixels), so a template made for one displays
  correctly on the others.
- The Manta (A5 X2) is the odd one out at 1920 × 2560 — always render Manta
  templates with `--device manta` so the type and rules scale up.
- If Supernote ships a new device, add its `(width, height)` to the `DEVICES`
  dict in `scripts/make_template.py`. The renderer scales all elements from a
  reference height of 1872, so a new size Just Works.

## Where MyStyle lives

On the linked cloud (Google Drive or Dropbox), Supernote creates a top-level
`Supernote/` folder with subfolders including `MyStyle`, `EXPORT`, `Note`,
`Document`, `SCREENSHOT`, and `INBOX`. Custom templates go in `MyStyle`; exported
notes land in `EXPORT`. Drop a PNG into `MyStyle`, wait for the device to sync,
then pick it under Create Note → template → My Style.
