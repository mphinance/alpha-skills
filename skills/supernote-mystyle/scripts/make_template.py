#!/usr/bin/env python3
"""
make_template.py — turn a checklist/list spec into a Supernote MyStyle template.

Renders a device-correct PNG sized to the exact e-ink resolution, in the house
style (monospace, hairline rules, checkbox squares, star priority markers, a
version-tag footer). Output is a grayscale PNG by default, or a crisp 1-bit PNG
with --mono (recommended for e-ink and smallest file size).

Usage:
    python3 make_template.py SPEC.json --device nomad --mono -o OUT.png

SPEC.json shape:
{
  "title":    "ICELAND & FAROE  ·  PACKING",
  "subtitle": "Nomad · Aug 9-16 · tick as you pack ·  * = don't-skip",
  "tag":      "ICELAND_PACKING_V1",          # footer version tag (house style)
  "footer_left": "SUPERNOTE NOMAD · MYSTYLE",
  "columns": [                                 # 1 or 2 columns
    [
      {"section": "DOCUMENTS & MONEY"},
      {"item": "Passport", "pri": true},       # pri => star marker
      {"item": "Boarding pass"}
    ],
    [
      {"section": "FOOTWEAR"},
      {"item": "Waterproof boots", "pri": true}
    ]
  ]
}

Drop the resulting PNG into the Supernote "MyStyle" folder on the device's
linked cloud (Google Drive / Dropbox). It then appears under
Create Note -> template -> My Style.

See references/devices.md for the pixel spec of every device, and
references/house-style.md for the design system this renders.
"""
import argparse, json, math, sys
from PIL import Image, ImageDraw, ImageFont

# Native e-ink resolutions (w, h) in px. See references/devices.md.
DEVICES = {
    "nomad": (1404, 1872),   # A6 X2, 7.8"
    "a6x2":  (1404, 1872),
    "a6x":   (1404, 1872),   # A6 X, 7.8"
    "a5x":   (1404, 1872),   # A5 X, 10.3"
    "manta": (1920, 2560),   # A5 X2, 10.7"
    "a5x2":  (1920, 2560),
}

# Grayscale palette (survives 1-bit thresholding at >140).
INK, MID, LIGHT, BOX = (30, 30, 32), (116, 118, 122), (116, 118, 122), (70, 72, 76)

def load_font(size, bold=True):
    """Prefer a bundled/DejaVu monospace; fall back to PIL default."""
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "DejaVuSansMono-Bold.ttf", "DejaVuSansMono.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()

def render(spec, device="nomad", mono=False):
    if device not in DEVICES:
        sys.exit(f"Unknown device '{device}'. Options: {', '.join(sorted(DEVICES))}")
    W, H = DEVICES[device]
    scale = H / 1872.0                      # design was tuned at Nomad height
    M = int(64 * scale)

    f_title = load_font(int(50 * scale))
    f_sub   = load_font(int(23 * scale), bold=False)
    f_sec   = load_font(int(29 * scale))
    f_item  = load_font(int(27 * scale))
    f_tag   = load_font(int(23 * scale))

    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    # Header
    d.text((M, int(54 * scale)), spec.get("title", "TEMPLATE"), font=f_title, fill=INK)
    rule_y = int(130 * scale)
    d.line([(M, rule_y), (W - M, rule_y)], fill=INK, width=max(2, int(3 * scale)))
    if spec.get("subtitle"):
        d.text((M, int(140 * scale)), spec["subtitle"], font=f_sub, fill=MID)

    ROW = int(45 * scale)
    SEC_GAP = int(14 * scale)
    SEC_H = int(44 * scale)
    box_s = int(30 * scale)
    COL_TOP = int(188 * scale)

    cols = spec.get("columns", [])
    two = len(cols) >= 2
    if two:
        col_xs = [M, W // 2 + int(20 * scale)]
        col_w = (W // 2) - M - int(20 * scale)
    else:
        col_xs = [M]
        col_w = W - 2 * M

    def star(cx, cy, r):
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.42
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        d.polygon(pts, fill=INK)

    def draw_col(x, rows):
        y = COL_TOP
        for r in rows:
            if "section" in r:
                y += SEC_GAP
                d.text((x, y), r["section"], font=f_sec, fill=INK)
                d.line([(x, y + int(40 * scale)), (x + col_w, y + int(40 * scale))],
                       fill=LIGHT, width=max(1, int(2 * scale)))
                y += SEC_H
            else:
                pri = bool(r.get("pri"))
                bx = x + (int(26 * scale) if pri else 0)
                d.rectangle([bx, y, bx + box_s, y + box_s], outline=BOX,
                            width=max(2, int(3 * scale)))
                if pri:
                    star(x + int(11 * scale), y + box_s // 2, int(11 * scale))
                d.text((bx + int(44 * scale), y - 1), r["item"], font=f_item, fill=INK)
                y += ROW
        return y

    for x, rows in zip(col_xs, cols):
        draw_col(x, rows)
    if two:
        d.line([(W // 2, COL_TOP), (W // 2, H - int(96 * scale))],
               fill=LIGHT, width=1)

    # Footer (house-style version tag)
    fy = H - int(78 * scale)
    d.line([(M, fy), (W - M, fy)], fill=LIGHT, width=max(1, int(2 * scale)))
    if spec.get("footer_left"):
        d.text((M, fy + int(14 * scale)), spec["footer_left"], font=f_tag, fill=MID)
    if spec.get("tag"):
        tw = d.textlength(spec["tag"], font=f_tag)
        d.text((W - M - tw, fy + int(14 * scale)), spec["tag"], font=f_tag, fill=MID)

    if mono:
        img = img.convert("L").point(lambda p: 255 if p > 140 else 0).convert("1")
    return img

def main():
    ap = argparse.ArgumentParser(description="Render a Supernote MyStyle template PNG.")
    ap.add_argument("spec", help="Path to the JSON spec file.")
    ap.add_argument("--device", default="nomad", help=f"One of: {', '.join(sorted(DEVICES))}")
    ap.add_argument("--mono", action="store_true", help="1-bit output (best for e-ink).")
    ap.add_argument("-o", "--out", default="template.png", help="Output PNG path.")
    a = ap.parse_args()
    with open(a.spec) as f:
        spec = json.load(f)
    img = render(spec, device=a.device, mono=a.mono)
    img.save(a.out, "PNG", optimize=True)
    print(f"Saved {a.out}  ({img.size[0]}x{img.size[1]}, {'1-bit' if a.mono else 'grayscale'})")

if __name__ == "__main__":
    main()
