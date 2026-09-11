#!/usr/bin/env python3
"""Compose paperback + hardcover wrap PDFs from generated cover art.

Takes the front-cover JPG, back-cover JPG, and a programmatically rendered
spine, and stitches them into a single landscape PDF sized to KDP wrap
specifications.

Layout (left to right, viewing the flat wrap):
    [ BACK COVER ] [ SPINE ] [ FRONT COVER ]

KDP 6x9 paperback wrap (B&W or color interior, white paper):
- Per-cover trim: 6" x 9"
- Bleed: 0.125" on all 4 outside edges  (per-cover = 6.125" x 9.25")
- Spine width (B&W on white paper): pages * 0.002252"
- Spine width (color on standard paper): pages * 0.002347"

KDP 6x9 hardcover wrap (case binding overhead):
- Spine width: pages * 0.0025" + 0.06"
- Wrap dimensions are larger than paperback; we render a first-pass at
  trim + bleed + spine and let the author make final adjustments in
  KDP's cover-template tool.

Usage:
    python3 compose_cover_wrap.py --page-count 276
    python3 compose_cover_wrap.py --page-count 320 --color-interior
    python3 compose_cover_wrap.py --page-count 276 --front covers/v2-front.jpg
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import add_config_arg, load_config, project_root  # noqa: E402

DPI = 300
COVER_W_IN = 6.125
COVER_H_IN = 9.25

GEORGIA_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"


def paperback_spine_in(pages: int, color_interior: bool) -> float:
    rate = 0.002347 if color_interior else 0.002252
    return pages * rate


def hardcover_spine_in(pages: int) -> float:
    return pages * 0.0025 + 0.06


def in_to_px(inches: float) -> int:
    return int(round(inches * DPI))


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    s = hex_str.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def make_spine(width_px: int, height_px: int, title: str, author: str,
               color_rgb, top_rgb, bot_rgb) -> Image.Image:
    img = Image.new("RGB", (width_px, height_px), top_rgb)
    for y in range(height_px):
        t = y / max(height_px - 1, 1)
        r = int(top_rgb[0] * (1 - t) + bot_rgb[0] * t)
        g = int(top_rgb[1] * (1 - t) + bot_rgb[1] * t)
        b = int(top_rgb[2] * (1 - t) + bot_rgb[2] * t)
        ImageDraw.Draw(img).line([(0, y), (width_px, y)], fill=(r, g, b))

    rot = Image.new("RGBA", (height_px, width_px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(rot)

    target_text_pct = 0.55
    title_max_w = int(height_px * target_text_pct)
    fsize = max(8, int(width_px * 0.55))
    while fsize > 10:
        f = ImageFont.truetype(GEORGIA_BOLD, fsize)
        bbox = f.getbbox(title)
        if (bbox[2] - bbox[0]) <= title_max_w and (bbox[3] - bbox[1]) <= width_px * 0.7:
            break
        fsize -= 2
    f = ImageFont.truetype(GEORGIA_BOLD, fsize)
    bbox = f.getbbox(title)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((height_px - tw) // 2, (width_px - th) // 2 - bbox[1]), title, font=f, fill=color_rgb)

    afsize = max(8, int(width_px * 0.32))
    while afsize > 8:
        af = ImageFont.truetype(GEORGIA_BOLD, afsize)
        abox = af.getbbox(author)
        if (abox[2] - abox[0]) <= height_px * 0.45 and (abox[3] - abox[1]) <= width_px * 0.55:
            break
        afsize -= 2
    af = ImageFont.truetype(GEORGIA_BOLD, afsize)
    abox = af.getbbox(author)
    ah = abox[3] - abox[1]
    draw.text((int(height_px * 0.04), (width_px - ah) // 2 - abox[1]), author, font=af, fill=color_rgb)

    rot = rot.rotate(90, expand=True)
    img.paste(rot, (0, 0), rot)
    return img


def scaled(path: Path, w: int, h: int) -> Image.Image:
    return Image.open(path).convert("RGB").resize((w, h), Image.LANCZOS)


def compose_wrap(spine_in: float, back: Path, front: Path, label: str,
                 title: str, author: str, color_rgb, top_rgb, bot_rgb) -> Image.Image:
    cw, ch, sw = in_to_px(COVER_W_IN), in_to_px(COVER_H_IN), in_to_px(spine_in)
    wrap_w = cw + sw + cw
    wrap = Image.new("RGB", (wrap_w, ch), top_rgb)
    wrap.paste(scaled(back, cw, ch), (0, 0))
    wrap.paste(make_spine(sw, ch, title, author, color_rgb, top_rgb, bot_rgb), (cw, 0))
    wrap.paste(scaled(front, cw, ch), (cw + sw, 0))
    print(f"  [{label}] composed {wrap_w}x{ch} px = {wrap_w/DPI:.2f}\"x{ch/DPI:.2f}\" "
          f"at {DPI} DPI (spine {spine_in:.4f}\")")
    return wrap


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--page-count", type=int, required=True, help="Manuscript page count for spine calc")
    ap.add_argument("--color-interior", action="store_true", help="Color interior paperback (different spine rate)")
    ap.add_argument("--front", default=None, help="Front cover JPG (default: cover.front_final_path from config)")
    ap.add_argument("--back",  default=None, help="Back cover JPG (default: cover.back_final_path from config)")
    ap.add_argument("--out-dir", default=None, help="Output dir (default: paths.dist_dir from config)")
    ap.add_argument("--basename", default=None, help="Basename for output PDFs (default: <title>-paperback-wrap)")
    add_config_arg(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    root = project_root(args.config)

    out_dir = Path(args.out_dir) if args.out_dir else (root / cfg["paths"].get("dist_dir", "dist"))
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cover = cfg.get("cover", {})
    front = Path(args.front) if args.front else (root / cover.get("front_final_path", "covers/front-cover.jpg"))
    back  = Path(args.back)  if args.back  else (root / cover.get("back_final_path",  "covers/back-cover.jpg"))
    if not front.is_absolute():
        front = root / front
    if not back.is_absolute():
        back = root / back
    if not front.exists():
        sys.exit(f"front cover not found: {front}")
    if not back.exists():
        sys.exit(f"back cover not found: {back}")

    spine_cfg = cover.get("spine", {})
    title = spine_cfg.get("title", cfg.get("title", "TITLE")).upper()
    author = spine_cfg.get("author", cfg.get("author_display", cfg.get("author", "AUTHOR"))).upper()
    color_rgb = _hex_to_rgb(spine_cfg.get("color_hex", "#c9a227"))
    top_rgb   = _hex_to_rgb(spine_cfg.get("bg_color_top_hex", "#0a0a0f"))
    bot_rgb   = _hex_to_rgb(spine_cfg.get("bg_color_bottom_hex", "#19120a"))

    pb_spine = paperback_spine_in(args.page_count, args.color_interior)
    hc_spine = hardcover_spine_in(args.page_count)

    basename = args.basename or _safe_basename(cfg.get("title", "book"))

    pb = compose_wrap(pb_spine, back, front, "paperback", title, author, color_rgb, top_rgb, bot_rgb)
    hc = compose_wrap(hc_spine, back, front, "hardcover", title, author, color_rgb, top_rgb, bot_rgb)

    pb_pdf = out_dir / f"{basename}-paperback-wrap.pdf"
    hc_pdf = out_dir / f"{basename}-hardcover-wrap.pdf"
    pb.save(pb_pdf, "PDF", resolution=DPI)
    hc.save(hc_pdf, "PDF", resolution=DPI)
    print(f"OK {pb_pdf} ({pb_pdf.stat().st_size/1024/1024:.1f} MB)")
    print(f"OK {hc_pdf} ({hc_pdf.stat().st_size/1024/1024:.1f} MB)")

    pb.save(out_dir / f"{basename}-paperback-wrap.png")
    hc.save(out_dir / f"{basename}-hardcover-wrap.png")


def _safe_basename(s: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in s.lower()).strip("-") or "book"


if __name__ == "__main__":
    main()
