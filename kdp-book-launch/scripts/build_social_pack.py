#!/usr/bin/env python3
"""Build a social media graphic pack — pure PIL, no API calls.

Outputs:
    social/instagram/square/      1080x1080
    social/instagram/story/       1080x1920
    social/facebook/              1200x630
    social/twitter/post/          1200x675
    social/twitter/header/        1500x500
    social/linkedin/              1200x627
    social/pinterest/             1000x1500

Recipe set (8 default recipes — adjust via config or edit this file):
    01-cover-out-now              cover-centered "OUT NOW" card
    02-cover-coming-soon          cover-centered "COMING SOON" card
    03-quote-1 / 04-quote-2 / 05-quote-3    three pull-quote cards
    06-premise                    one-paragraph elevator pitch card
    07-comp-titles                "IF YOU LOVED X..." card
    08-social-proof               only generated if social_proof_quote is set

All copy (quotes, taglines, comp titles, premise text) is pulled from your
`_launch_config.json`. The visual recipes are deliberately generic — a
thriller, a memoir, and a fantasy book all benefit from the same eight
card layouts. Adjust the SIZES dict at the bottom to add platforms.

Usage:
    python3 build_social_pack.py
    python3 build_social_pack.py --force
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import add_config_arg, load_config, project_root  # noqa: E402

FONT_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
FONT_ITALIC = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"

GOLD = (201, 162, 39)
CREAM = (232, 223, 197)
DARK = (12, 10, 8)


def font(size: int, italic: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_ITALIC if italic else FONT_BOLD, size)


def text_size(f, text):
    bbox = f.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_text_with_shadow(draw, pos, text, f, fill, offset=2):
    x, y = pos
    shadow = (0, 0, 0)
    draw.text((x + offset, y + offset), text, font=f, fill=shadow)
    draw.text((x, y), text, font=f, fill=fill)


def draw_text_centered(draw, cx, y, text, f, fill, shadow=True):
    w, _ = text_size(f, text)
    pos = (cx - w // 2, y)
    if shadow:
        draw_text_with_shadow(draw, pos, text, f, fill)
    else:
        draw.text(pos, text, font=f, fill=fill)


def draw_letterspaced(draw, cx, y, text, f, fill, tracking=4, shadow=True):
    widths = [text_size(f, ch)[0] for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total // 2
    for ch, w in zip(text, widths):
        if shadow:
            draw_text_with_shadow(draw, (x, y), ch, f, fill)
        else:
            draw.text((x, y), ch, font=f, fill=fill)
        x += w + tracking


def wrap_text(text, f, max_width):
    words = text.split()
    lines, cur = [], []
    for w in words:
        trial = " ".join(cur + [w])
        if text_size(f, trial)[0] <= max_width or not cur:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


def gold_rule(draw, cx, y, length, thickness=2, color=GOLD):
    draw.rectangle([cx - length // 2, y, cx + length // 2, y + thickness], fill=color)


def add_solid_overlay(img, alpha, color=(0, 0, 0)):
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (color[0], color[1], color[2], int(255 * alpha)))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def add_gradient_overlay(img, top_alpha, bottom_alpha, color=(0, 0, 0)):
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = overlay.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        a = int(255 * (top_alpha + (bottom_alpha - top_alpha) * t))
        for x in range(w):
            px[x, y] = (color[0], color[1], color[2], a)
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def fill_background(size, src, blur=0, darken=0.0):
    img = Image.open(src).convert("RGB")
    iw, ih = img.size
    tw, th = size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale + 1), int(ih * scale + 1)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    img = img.crop((left, top, left + tw, top + th))
    if blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    if darken > 0:
        img = add_solid_overlay(img, darken, (0, 0, 0))
    return img


def solid_bg(size, color=DARK):
    return Image.new("RGB", size, color)


def add_copyright(img, copyright_text):
    if not copyright_text:
        return
    draw = ImageDraw.Draw(img, "RGBA")
    f = font(10)
    w, h = text_size(f, copyright_text)
    x = img.size[0] - w - 18
    y = img.size[1] - h - 14
    draw.text((x, y), copyright_text, font=f, fill=(GOLD[0], GOLD[1], GOLD[2], 140))


# -------------------- recipe primitives --------------------

def make_cover_card(size, banner_text, accent, front_cover, author_display, copyright_text):
    w, h = size
    canvas = solid_bg(size)
    bg = fill_background(size, front_cover, blur=22, darken=0.55)
    canvas.paste(bg, (0, 0))

    cover = Image.open(front_cover).convert("RGB")
    target_h = int(min(w, h) * 0.78) if w == h else int(h * 0.78)
    scale = target_h / cover.size[1]
    cover_resized = cover.resize((int(cover.size[0] * scale), target_h), Image.LANCZOS)
    cx = (w - cover_resized.size[0]) // 2
    cy = (h - cover_resized.size[1]) // 2
    shadow = Image.new("RGBA", (cover_resized.size[0] + 40, cover_resized.size[1] + 40), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle([20, 20, shadow.size[0] - 20, shadow.size[1] - 20], fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    canvas.paste(shadow, (cx - 20, cy - 20), shadow)
    canvas.paste(cover_resized, (cx, cy))

    draw = ImageDraw.Draw(canvas)
    banner_h = max(70, int(h * 0.09))
    by = 0 if accent == "TOP" else h - banner_h
    band = Image.new("RGBA", (w, banner_h), (0, 0, 0, 215))
    canvas.paste(band, (0, by), band)
    draw.rectangle([0, by, w, by + 3], fill=GOLD)
    draw.rectangle([0, by + banner_h - 3, w, by + banner_h], fill=GOLD)

    f_banner = font(int(banner_h * 0.42))
    draw_letterspaced(draw, w // 2, by + (banner_h - f_banner.size) // 2 - 4, banner_text, f_banner, GOLD, tracking=6)

    f_credit = font(int(min(w, h) * 0.018))
    credit = f"A NOVEL BY {author_display}"
    if accent == "TOP":
        draw_letterspaced(draw, w // 2, h - 60, credit, f_credit, CREAM, tracking=3)
    else:
        draw_letterspaced(draw, w // 2, 36, credit, f_credit, CREAM, tracking=3)

    add_copyright(canvas, copyright_text)
    return canvas


def make_quote_card(size, bg_src, quote, attribution, copyright_text, blur=8, darken=0.65):
    w, h = size
    canvas = fill_background(size, bg_src, blur=blur, darken=darken)
    canvas = add_gradient_overlay(canvas, 0.35, 0.55)
    draw = ImageDraw.Draw(canvas)

    gold_rule(draw, w // 2, int(h * 0.18), int(w * 0.22))

    quote_size = int(min(w, h) * 0.058) if w == h else int(min(w, h) * 0.055)
    f_quote = font(quote_size, italic=True)
    max_width = int(w * 0.82)
    lines = wrap_text(quote, f_quote, max_width)
    _, line_h = text_size(f_quote, "Ag")
    step = int(line_h * 1.3)
    block_h = step * len(lines)
    y = (h - block_h) // 2 - int(h * 0.02)
    for line in lines:
        draw_text_centered(draw, w // 2, y, line, f_quote, CREAM)
        y += step

    y += int(h * 0.02)
    gold_rule(draw, w // 2, y, int(w * 0.22))
    y += 24
    f_attr = font(int(min(w, h) * 0.022))
    draw_letterspaced(draw, w // 2, y, attribution, f_attr, GOLD, tracking=4)

    add_copyright(canvas, copyright_text)
    return canvas


def make_premise_card(size, bg_src, body, footer, title, copyright_text):
    w, h = size
    canvas = fill_background(size, bg_src, blur=10, darken=0.7)
    draw = ImageDraw.Draw(canvas)

    f_title = font(int(min(w, h) * 0.055))
    draw_letterspaced(draw, w // 2, int(h * 0.10), title.upper(), f_title, GOLD, tracking=8)
    gold_rule(draw, w // 2, int(h * 0.10) + f_title.size + 14, int(w * 0.18))

    f_body = font(int(min(w, h) * 0.034), italic=True)
    max_width = int(w * 0.84)
    lines = wrap_text(body, f_body, max_width)
    _, line_h = text_size(f_body, "Ag")
    step = int(line_h * 1.35)
    block_h = step * len(lines)
    y = (h - block_h) // 2 + int(h * 0.04)
    for line in lines:
        draw_text_centered(draw, w // 2, y, line, f_body, CREAM)
        y += step

    f_footer = font(int(min(w, h) * 0.02))
    draw_letterspaced(draw, w // 2, h - int(h * 0.09), footer, f_footer, GOLD, tracking=4)

    add_copyright(canvas, copyright_text)
    return canvas


def make_comp_titles_card(size, front_cover, lead, follow, author_display, copyright_text):
    w, h = size
    canvas = solid_bg(size, DARK)
    tex = fill_background(size, front_cover, blur=44, darken=0.85)
    canvas.paste(tex, (0, 0))
    draw = ImageDraw.Draw(canvas)

    f_hl = font(int(min(w, h) * 0.05))
    y = int(h * 0.10)
    draw_letterspaced(draw, w // 2, y, lead, f_hl, CREAM, tracking=4)
    y += int(f_hl.size * 1.25)
    f_italic = font(int(min(w, h) * 0.045), italic=True)
    # word-wrap the follow line
    fw_lines = wrap_text(follow, f_italic, int(w * 0.84))
    for line in fw_lines:
        draw_text_centered(draw, w // 2, y, line, f_italic, GOLD)
        y += int(f_italic.size * 1.2)

    cover = Image.open(front_cover).convert("RGB")
    th = int(h * 0.42)
    scale = th / cover.size[1]
    cv = cover.resize((int(cover.size[0] * scale), th), Image.LANCZOS)
    cv_x = (w - cv.size[0]) // 2
    cv_y = int(h * 0.40)
    canvas.paste(cv, (cv_x, cv_y))

    f_foot = font(int(min(w, h) * 0.018))
    draw_letterspaced(draw, w // 2, h - 60, f"BY {author_display}", f_foot, GOLD, tracking=3)

    add_copyright(canvas, copyright_text)
    return canvas


def make_social_proof_card(size, front_cover, quote, source, author_display, title, copyright_text):
    w, h = size
    canvas = solid_bg(size, DARK)
    tex = fill_background(size, front_cover, blur=40, darken=0.82)
    canvas.paste(tex, (0, 0))
    draw = ImageDraw.Draw(canvas)

    cover = Image.open(front_cover).convert("RGB")
    th = int(h * 0.46) if w == h else int(h * 0.6)
    scale = th / cover.size[1]
    cv = cover.resize((int(cover.size[0] * scale), th), Image.LANCZOS)
    cv_x = w - cv.size[0] - int(w * 0.06)
    cv_y = (h - cv.size[1]) // 2
    if w == h:
        cv_x = (w - cv.size[0]) // 2
        cv_y = int(h * 0.52)
    canvas.paste(cv, (cv_x, cv_y))

    f_hl = font(int(min(w, h) * 0.045))
    y = int(h * 0.10) if w == h else int(h * 0.18)
    lines = wrap_text(quote, f_hl, w - int(w * 0.12))
    for line in lines:
        if w == h:
            draw_text_centered(draw, w // 2, y, line, f_hl, GOLD)
        else:
            draw_text_with_shadow(draw, (int(w * 0.06), y), line, f_hl, GOLD)
        y += int(f_hl.size * 1.15)

    f_attr = font(int(min(w, h) * 0.024))
    if w == h:
        draw_text_centered(draw, w // 2, y + 6, f"— {source}", f_attr, CREAM)
    else:
        draw_text_with_shadow(draw, (int(w * 0.06), y + 6), f"— {source}", f_attr, CREAM)

    add_copyright(canvas, copyright_text)
    return canvas


# -------------------- sizes + recipe table --------------------

SIZES = {
    "instagram/square": (1080, 1080),
    "instagram/story": (1080, 1920),
    "facebook": (1200, 630),
    "twitter/post": (1200, 675),
    "linkedin": (1200, 627),
    "pinterest": (1000, 1500),
}


def build(cfg, root, force=False):
    paths = cfg["paths"]
    title = cfg["title"]
    author_display = cfg.get("author_display", cfg["author"]).upper()
    copyright_text = f"© {cfg.get('year','')} {cfg.get('author','')}"
    social_cfg = cfg.get("social", {})

    covers_dir = root / paths.get("covers_dir", "covers")
    chapters_dir = root / paths["color_images_dir"]
    out_dir = root / paths.get("social_dir", "social")

    front_cover = root / cfg.get("cover", {}).get("front_final_path", str(covers_dir / "front-cover.jpg"))
    if not front_cover.exists():
        sys.exit(f"front cover not found: {front_cover}")

    # Pick three different chapter images as quote-card backgrounds — round-robin
    available_chapters = sorted(p for p in chapters_dir.glob("*.png")) + sorted(p for p in chapters_dir.glob("*.jpg"))
    if not available_chapters:
        sys.exit(f"no chapter images in {chapters_dir}")

    def bg(i):
        return available_chapters[i % len(available_chapters)]

    quotes = social_cfg.get("quotes") or [cfg.get("subtitle", "")]
    while len(quotes) < 3:
        quotes.append(quotes[-1])

    premise = social_cfg.get("premise", cfg.get("subtitle", ""))
    comp_lead = social_cfg.get("comp_titles_lead", "")
    comp_follow = social_cfg.get("comp_titles_follow", "").replace("{TITLE}", title)
    attr = f"{title.upper()} - A BOOK BY {author_display}"

    recipes = [
        ("01-cover-out-now",
         lambda size: make_cover_card(size, "OUT NOW", "TOP", front_cover, author_display, copyright_text),
         None),
        ("02-cover-coming-soon",
         lambda size: make_cover_card(size, "COMING SOON", "TOP", front_cover, author_display, copyright_text),
         None),
        ("03-quote-1",
         lambda size: make_quote_card(size, bg(0), quotes[0], attr, copyright_text),
         None),
        ("04-quote-2",
         lambda size: make_quote_card(size, bg(1), quotes[1], attr, copyright_text, blur=10, darken=0.6),
         None),
        ("05-quote-3",
         lambda size: make_quote_card(size, bg(2), quotes[2], attr, copyright_text),
         None),
        ("06-premise",
         lambda size: make_premise_card(size, bg(3), premise, f"{title.upper()} - BY {author_display}", title, copyright_text),
         None),
    ]
    if comp_lead and comp_follow:
        recipes.append(("07-comp-titles",
                        lambda size: make_comp_titles_card(size, front_cover, comp_lead, comp_follow, author_display, copyright_text),
                        ["instagram/square", "instagram/story", "facebook", "pinterest"]))
    sp_quote = social_cfg.get("social_proof_quote")
    sp_source = social_cfg.get("social_proof_source")
    if sp_quote and sp_source:
        recipes.append(("08-social-proof",
                        lambda size: make_social_proof_card(size, front_cover, sp_quote, sp_source, author_display, title, copyright_text),
                        ["instagram/square", "facebook", "twitter/post", "linkedin"]))

    generated, skipped = [], []
    for slug, factory, only in recipes:
        for platform, size in SIZES.items():
            if only is not None and platform not in only:
                continue
            out = out_dir / platform / f"{slug}.jpg"
            if out.exists() and not force:
                skipped.append(out)
                continue
            try:
                img = factory(size)
                out.parent.mkdir(parents=True, exist_ok=True)
                img.convert("RGB").save(out, "JPEG", quality=92, optimize=True)
                generated.append(out)
                print(f"  wrote {out.relative_to(root)}")
            except Exception as e:
                print(f"  FAILED {out.relative_to(root)}: {e}")
                raise

    return {"generated": generated, "skipped": skipped}


def write_readme(cfg, root):
    social_dir = root / cfg["paths"].get("social_dir", "social")
    lines = [f"# {cfg.get('title','Book')} - Social Media Graphic Pack",
             "",
             f"Generated by `scripts/build_social_pack.py` (PIL only, no API calls).",
             "",
             "## Files", ""]
    for r, _, files in os.walk(social_dir):
        files = sorted(f for f in files if f.endswith(".jpg"))
        if not files:
            continue
        rel = Path(r).relative_to(social_dir)
        lines.append(f"### `{rel}/`")
        lines.append("")
        for f in files:
            p = Path(r) / f
            try:
                im = Image.open(p)
                size = f"{im.size[0]}x{im.size[1]}"
            except Exception:
                size = "?"
            lines.append(f"- `{f}` - {size}")
        lines.append("")
    lines.extend([
        "## Posting notes",
        "",
        "- Add platform-appropriate hashtags / URLs in the caption (none baked into images).",
        "- Stories (1080x1920) put the headline in the lower third — top is reserved for platform UI.",
        "",
    ])
    (social_dir / "README.md").write_text("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--force", action="store_true", help="Overwrite existing JPGs")
    add_config_arg(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    root = project_root(args.config)
    (root / cfg["paths"].get("social_dir", "social")).mkdir(parents=True, exist_ok=True)

    print(f"Building social pack in {cfg['paths'].get('social_dir', 'social')} ...")
    result = build(cfg, root, force=args.force)
    write_readme(cfg, root)
    print(f"Done. Generated: {len(result['generated'])}, skipped: {len(result['skipped'])}")


if __name__ == "__main__":
    main()
