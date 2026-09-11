#!/usr/bin/env python3
"""Generate grayscale, print-ready variants of color chapter illustrations.

For each image in `{color_images_dir}` from your launch config:
  1. Convert to grayscale (single-channel)
  2. Apply a mild contrast level stretch (5%-95%) so the print version
     doesn't look muddy on KDP cream/white interior paper
  3. Save as PNG in `{bw_images_dir}` at the same resolution

Idempotent: existing outputs are skipped unless --force is given.

Requires ImageMagick:
    brew install imagemagick

Usage:
    python3 make_bw_variants.py
    python3 make_bw_variants.py --force
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import add_config_arg, load_config, project_root  # noqa: E402

SKIP_FILES = {"regen-log.md"}
IMG_EXTS = {".jpg", ".jpeg", ".png"}


def convert_one(src: Path, dst: Path) -> None:
    cmd = [
        "magick", str(src),
        "-colorspace", "Gray",
        "-level", "5%,95%",
        "-strip",
        str(dst),
    ]
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--force", action="store_true", help="Regenerate outputs even if they already exist.")
    add_config_arg(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    root = project_root(args.config)
    src_dir = root / cfg["paths"]["color_images_dir"]
    dst_dir = root / cfg["paths"]["bw_images_dir"]

    if not src_dir.is_dir():
        print(f"ERROR: source dir not found: {src_dir}", file=sys.stderr)
        return 1

    dst_dir.mkdir(parents=True, exist_ok=True)
    sources = sorted(
        p for p in src_dir.iterdir()
        if p.is_file() and p.name not in SKIP_FILES and p.suffix.lower() in IMG_EXTS
    )
    if not sources:
        print(f"ERROR: no source images in {src_dir}", file=sys.stderr)
        return 1

    made = skipped = 0
    for src in sources:
        dst = dst_dir / f"{src.stem}.png"
        if dst.exists() and not args.force:
            skipped += 1
            continue
        print(f"  bw: {src.name} -> {dst.name}")
        convert_one(src, dst)
        made += 1

    print(f"Done. {made} converted, {skipped} skipped. Output: {dst_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
