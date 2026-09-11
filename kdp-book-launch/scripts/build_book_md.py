#!/usr/bin/env python3
"""Assemble manuscript markdown into `_build_book.md` for kdp-book-generator.

Reads `{paths.manuscript_md}` and writes `{paths.build_md}` after:

1. Stripping any author-supplied H1 title + tagline (replaced by YAML).
2. Prepending YAML front matter + Title page + Copyright page (both H1).
3. Inserting chapter images after each chapter's location/date block.
4. Promoting `## CHAPTER`, `## PROLOGUE`, `## EPILOGUE`, `## DRAMATIS PERSONAE`
   to H1 so kdp-book-generator paginates them as page-break chapters.
5. Demoting remaining `### subsection` lines to `##`.
6. Optional --print mode swaps the color images for the B&W chapter images.

The script keys off each chapter's `manuscript_header` literal in your
launch config (e.g. `## CHAPTER 1:` or `## PROLOGUE`). It uses two
patterns: first tries header+optional-blank+###locationblock+blank
(then inserts after the ### block); falls back to header-then-blank
(inserts immediately after).

Usage:
    python3 build_book_md.py
    python3 build_book_md.py --print          # swap to B&W images
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import add_config_arg, load_config, project_root  # noqa: E402


def resolve_image_path(slug: str, root: Path, color_dir: str, bw_dir: str, print_mode: bool) -> str | None:
    if print_mode:
        candidate = Path(bw_dir) / f"{slug}.png"
        if (root / candidate).exists():
            return str(candidate)
    for ext in (".jpg", ".png"):
        candidate = Path(color_dir) / f"{slug}{ext}"
        if (root / candidate).exists():
            return str(candidate)
    return None


def insert_image(body: str, header_literal: str, image_rel: str) -> tuple[str, bool]:
    # Pattern A: header + optional blank + ### location block + trailing blank
    pat_loc = re.compile(
        r"(^" + re.escape(header_literal) + r"[^\n]*\n)"
        r"(\n)?"
        r"((?:### [^\n]*\n)+)"
        r"(\n)",
        flags=re.M,
    )
    def sub_loc(m: re.Match) -> str:
        return m.group(1) + (m.group(2) or "") + m.group(3) + f"\n![]({image_rel})\n\n"
    new_body, n = pat_loc.subn(sub_loc, body, count=1)
    if n:
        return new_body, True

    # Pattern B: header line then blank line — insert directly after
    pat_no_loc = re.compile(
        r"(^" + re.escape(header_literal) + r"[^\n]*\n\n)",
        flags=re.M,
    )
    def sub_no_loc(m: re.Match) -> str:
        return m.group(1) + f"![]({image_rel})\n\n"
    new_body, n = pat_no_loc.subn(sub_no_loc, body, count=1)
    return (new_body, bool(n))


def make_front_matter(cfg: dict) -> str:
    title = cfg["title"]
    subtitle = cfg.get("subtitle", "")
    author = cfg["author"]
    lang = cfg.get("language", "en")
    publisher = cfg.get("publisher", author)
    year = cfg.get("year", "")
    tagline_lines = cfg.get("tagline_lines", [])
    copyright_text = cfg.get("copyright_text", f"Copyright © {year} {author}. All rights reserved.")

    yaml_block = f'''---
title: "{title}"
subtitle: "{subtitle}"
author: "{author}"
language: "{lang}"
publisher: "{publisher}"
date: "{year}"
---

'''
    title_block = f"# {title}\n\n"
    if tagline_lines:
        for line in tagline_lines:
            title_block += f"*{line}*\n\n"
    title_block += f"{author}\n\n"

    copyright_block = "# Copyright\n\n" + copyright_text.strip() + "\n\n"
    return yaml_block + title_block + copyright_block


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--print", dest="print_mode", action="store_true",
                    help="Use B&W chapter images for paperback/hardcover build")
    add_config_arg(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    root = project_root(args.config)
    paths = cfg["paths"]
    src = root / paths["manuscript_md"]
    out = root / paths["build_md"]

    if not src.exists():
        sys.exit(f"manuscript not found: {src}")

    text = src.read_text()
    chapters = cfg["chapters"]

    # Find the first chapter header in the manuscript to mark where body starts.
    first_header = chapters[0]["manuscript_header"]
    m = re.search(r"^" + re.escape(first_header), text, flags=re.M)
    if not m:
        sys.exit(f"could not find first chapter header in manuscript: {first_header!r}")
    body = text[m.start():]

    # Insert chapter images.
    for chapter in chapters:
        slug = chapter["slug"]
        header_literal = chapter["manuscript_header"]
        rel = resolve_image_path(
            slug, root, paths["color_images_dir"], paths["bw_images_dir"], args.print_mode
        )
        if rel is None:
            print(f"  WARN: no image for {slug}", file=sys.stderr)
            continue
        body, ok = insert_image(body, header_literal, rel)
        if not ok:
            print(f"  WARN: header pattern not matched for {slug} ({header_literal})", file=sys.stderr)

    # Promote ## CHAPTER / PROLOGUE / EPILOGUE / DRAMATIS PERSONAE to H1.
    body = re.sub(r"^## (CHAPTER [^\n]+)$", r"# \1", body, flags=re.M)
    body = re.sub(r"^## (PROLOGUE)\s*$",    r"# \1", body, flags=re.M)
    body = re.sub(r"^## (EPILOGUE)\s*$",    r"# \1", body, flags=re.M)
    body = re.sub(r"^## (DRAMATIS PERSONAE)\s*$", r"# \1", body, flags=re.M)

    # Demote ### subsection lines to ##.
    body = re.sub(r"^### ", "## ", body, flags=re.M)

    front = make_front_matter(cfg)
    out.write_text(front + body.rstrip() + "\n")

    h1_count = len(re.findall(r"^# ", out.read_text(), flags=re.M))
    mode = "PRINT/BW" if args.print_mode else "COLOR"
    print(f"Wrote {out} ({mode} mode)")
    print(f"H1 count: {h1_count}")


if __name__ == "__main__":
    main()
