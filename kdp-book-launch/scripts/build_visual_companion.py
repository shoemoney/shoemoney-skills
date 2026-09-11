#!/usr/bin/env python3
"""Build a Visual Companion PDF for newsletter / lead-magnet distribution.

Composes one PDF page per color chapter illustration in the order from
your launch config:
    Cover page  ->  N chapter pages  ->  End page

Letter (8.5x11) portrait at 200 DPI. Each chapter page renders:
    - Chapter title at top
    - Illustration sized to fit a 6x9 area
    - 1-2 sentence caption extracted from the prompt's SCENE: block

Useful as:
    - Free PDF for newsletter subscribers (the "visual companion")
    - Press kit / preview PDF for podcast interviews
    - Bonus PDF emailed to early reviewers

Usage:
    python3 build_visual_companion.py
    python3 build_visual_companion.py --force        # rebuild
    python3 build_visual_companion.py --output custom.pdf
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import add_config_arg, load_config, project_root  # noqa: E402

DPI = 200
PAGE_W = int(8.5 * DPI)
PAGE_H = int(11.0 * DPI)
MARGIN = int(0.75 * DPI)
IMG_FRAME_W = int(6.0 * DPI)
IMG_FRAME_H = int(9.0 * DPI)

BG = (255, 255, 255)
FG = (20, 20, 20)
MUTED = (90, 90, 90)

FONT_BOLD = [
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
    "/Library/Fonts/Georgia Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
FONT_REG = [
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "/Library/Fonts/Georgia.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
FONT_ITALIC = [
    "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf",
    "/Library/Fonts/Georgia Italic.ttf",
]


def load_font(candidates, size):
    for p in candidates:
        try:
            return ImageFont.truetype(p, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def extract_caption(prompt_path: Path) -> str:
    """Return 1-2 sentence caption distilled from the prompt's SCENE block."""
    if not prompt_path.is_file():
        return ""
    text = prompt_path.read_text(encoding="utf-8")
    m = re.search(r"SCENE:\s*(.*?)(?=\n[A-Z][A-Z \-]{2,}:|\Z)", text, re.DOTALL)
    if not m:
        return ""
    scene = re.sub(r"\s+", " ", m.group(1)).strip()
    # Strip opening meta phrases like 'Chapter 3, "Title."' or 'Prologue: "Title."'
    scene = re.sub(
        r'^(The\s+)?(Prologue|Epilogue|Chapter\s+\w+)'
        r'(\s+of|\s*[:,])?\s*"[^"]+\.?"\s*\.?\s*',
        "", scene, flags=re.IGNORECASE,
    )
    scene = re.sub(
        r'^(The\s+)?(Prologue|Epilogue|Chapter\s+\w+)\s*\.\s*',
        "", scene, flags=re.IGNORECASE,
    )
    sentences = re.split(r"(?<=[.!?])\s+", scene)
    keep = []
    for s in sentences:
        s = s.strip()
        if len(s) < 8:
            continue
        keep.append(s)
        if len(keep) == 2:
            break
    caption = " ".join(keep).strip()
    if len(caption) > 420:
        caption = caption[:417].rsplit(" ", 1)[0] + "..."
    return caption


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, current = [], []
    for w in words:
        trial = " ".join(current + [w])
        if draw.textlength(trial, font=font) <= max_width or not current:
            current.append(w)
        else:
            lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return lines


def draw_centered_text(draw, text, font, y, color):
    w = draw.textlength(text, font=font)
    draw.text(((PAGE_W - w) // 2, y), text, fill=color, font=font)
    ascent, descent = font.getmetrics() if hasattr(font, "getmetrics") else (font.size, 0)
    return y + ascent + descent


def make_cover_page(cfg):
    page = Image.new("RGB", (PAGE_W, PAGE_H), BG)
    draw = ImageDraw.Draw(page)
    title_font = load_font(FONT_BOLD, 110)
    subtitle_font = load_font(FONT_REG, 56)
    author_font = load_font(FONT_REG, 48)
    tag_font = load_font(FONT_ITALIC, 38)

    title = cfg.get("title", "Book Title").upper()
    author = cfg.get("author", "")

    y = int(PAGE_H * 0.30)
    y = draw_centered_text(draw, title, title_font, y, FG) + 40
    y = draw_centered_text(draw, "Visual Companion", subtitle_font, y, FG) + 120
    rule_w = int(PAGE_W * 0.30)
    rule_x = (PAGE_W - rule_w) // 2
    draw.line([(rule_x, y), (rule_x + rule_w, y)], fill=MUTED, width=2)
    y += 80
    y = draw_centered_text(draw, f"by {author}", author_font, y, FG) + 60
    draw_centered_text(draw, "Newsletter exclusive", tag_font, y, MUTED)
    return page


def make_chapter_page(slug, title, color_dir: Path, prompt_dir: Path):
    page = Image.new("RGB", (PAGE_W, PAGE_H), BG)
    draw = ImageDraw.Draw(page)
    title_font = load_font(FONT_BOLD, 64)
    caption_font = load_font(FONT_ITALIC, 34)

    title_y = MARGIN
    title_h = draw_centered_text(draw, title, title_font, title_y, FG) - title_y
    after_title_y = title_y + title_h + 40

    caption = extract_caption(prompt_dir / f"{slug}.txt")
    text_max_w = PAGE_W - 2 * MARGIN
    caption_lines = wrap_text(draw, caption, caption_font, text_max_w) if caption else []
    line_h = caption_font.size + 14
    caption_block_h = line_h * len(caption_lines) if caption_lines else 0
    bottom_pad = MARGIN + caption_block_h + (40 if caption_lines else 0)

    avail_top = after_title_y
    avail_bottom = PAGE_H - bottom_pad
    avail_h = avail_bottom - avail_top
    avail_w = PAGE_W - 2 * MARGIN
    frame_w = min(IMG_FRAME_W, avail_w)
    frame_h = min(IMG_FRAME_H, avail_h)

    src_img = None
    for ext in (".jpg", ".jpeg", ".png"):
        c = color_dir / f"{slug}{ext}"
        if c.is_file():
            src_img = c
            break
    if src_img is None:
        raise FileNotFoundError(f"No image found for slug {slug!r} in {color_dir}")

    img = Image.open(src_img).convert("RGB")
    iw, ih = img.size
    scale = min(frame_w / iw, frame_h / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    img = img.resize((nw, nh), Image.LANCZOS)
    img_x = (PAGE_W - nw) // 2
    img_y = avail_top + (avail_h - nh) // 2
    page.paste(img, (img_x, img_y))

    if caption_lines:
        cap_y = img_y + nh + 40
        if cap_y + caption_block_h > PAGE_H - MARGIN:
            cap_y = PAGE_H - MARGIN - caption_block_h
        for line in caption_lines:
            w = draw.textlength(line, font=caption_font)
            draw.text(((PAGE_W - w) // 2, cap_y), line, fill=MUTED, font=caption_font)
            cap_y += line_h
    return page


def make_end_page(cfg):
    page = Image.new("RGB", (PAGE_W, PAGE_H), BG)
    draw = ImageDraw.Draw(page)
    end_font = load_font(FONT_ITALIC, 52)
    y = int(PAGE_H * 0.45)
    text = f"End. Thank you for reading {cfg.get('title','')}. — {cfg.get('author','')}"
    draw_centered_text(draw, text, end_font, y, FG)
    return page


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--force", action="store_true", help="Regenerate the PDF even if it already exists.")
    ap.add_argument("--output", default=None, help="Override output path (default: paths.visual_companion_pdf)")
    add_config_arg(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    root = project_root(args.config)
    color_dir = root / cfg["paths"]["color_images_dir"]
    prompt_dir = root / cfg["paths"]["prompts_dir"]
    out_pdf = Path(args.output) if args.output else (root / cfg["paths"].get("visual_companion_pdf", "visual-companion.pdf"))
    if not out_pdf.is_absolute():
        out_pdf = root / out_pdf

    if out_pdf.exists() and not args.force:
        print(f"PDF already exists at {out_pdf}. Use --force to regenerate.")
        return 0

    pages = []
    print("  building cover page...")
    pages.append(make_cover_page(cfg))
    for chapter in cfg["chapters"]:
        slug = chapter["slug"]
        title = chapter.get("display_title", slug)
        print(f"  building page: {title}")
        pages.append(make_chapter_page(slug, title, color_dir, prompt_dir))
    print("  building end page...")
    pages.append(make_end_page(cfg))

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    print(f"  saving {len(pages)} pages -> {out_pdf}")
    first, rest = pages[0], pages[1:]
    first.save(out_pdf, "PDF", resolution=float(DPI), save_all=True, append_images=rest)
    print(f"Done. {len(pages)} pages -> {out_pdf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
