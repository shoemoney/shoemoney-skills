#!/usr/bin/env python3
"""Post-process EPUB from kdp-book-generator to embed referenced image files.

kdp-book-generator emits `<img src="images/..."/>` in chapter XHTML but does
NOT bundle the image files into the EPUB or add manifest entries for them.
This script fixes the gap in-place:

1. Scans every OEBPS/*.xhtml for `<img src="...">`
2. Copies each referenced file from the project root into OEBPS/<src>
3. Adds a manifest entry to content.opf for any new asset
4. Rewrites the EPUB zip (mimetype first, uncompressed — EPUB spec compliant)

Idempotent: if you re-run with the same EPUB, image files that already exist
in the archive are copied over (same path) and manifest entries that already
exist are skipped.

Usage:
    python3 epub_embed_images.py <path/to/book.epub>
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import add_config_arg, find_config  # noqa: E402

MIME_BY_EXT = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("epub", help="Path to the EPUB to patch in-place")
    add_config_arg(ap)
    args = ap.parse_args()

    epub_path = Path(args.epub).resolve()
    if not epub_path.exists():
        sys.exit(f"EPUB not found: {epub_path}")

    project = find_config(args.config).parent

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        with zipfile.ZipFile(epub_path, "r") as z:
            z.extractall(tmp)

        oebps = tmp / "OEBPS"
        if not oebps.exists():
            sys.exit(f"no OEBPS/ in {epub_path}")

        img_pat = re.compile(r'<img[^>]*\bsrc="([^"]+)"')
        refs = set()
        for xhtml in oebps.glob("*.xhtml"):
            for src in img_pat.findall(xhtml.read_text()):
                refs.add(src)
        print(f"Found {len(refs)} unique image refs")

        copied = []
        for src in sorted(refs):
            source = project / src
            if not source.exists():
                print(f"  WARN: missing source: {source}", file=sys.stderr)
                continue
            dest = oebps / src
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            copied.append(src)
        print(f"Copied {len(copied)} images into OEBPS/")

        opf = oebps / "content.opf"
        opf_text = opf.read_text()
        existing = set(re.findall(r'href="([^"]+)"', opf_text))

        items = []
        for i, src in enumerate(sorted(copied)):
            if src in existing:
                continue
            ext = Path(src).suffix.lower()
            mime = MIME_BY_EXT.get(ext, "image/png")
            item_id = f"img-{i}-" + re.sub(r"[^a-zA-Z0-9]", "-", Path(src).stem)
            items.append(f'    <item id="{item_id}" href="{src}" media-type="{mime}"/>')

        if items:
            opf_text = opf_text.replace("  </manifest>", "\n".join(items) + "\n  </manifest>", 1)
            opf.write_text(opf_text)
            print(f"Added {len(items)} manifest entries")

        # Repack — mimetype FIRST and uncompressed per EPUB spec.
        if epub_path.exists():
            epub_path.unlink()
        with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED) as z:
            mimepath = tmp / "mimetype"
            if mimepath.exists():
                z.write(mimepath, "mimetype", compress_type=zipfile.ZIP_STORED)
            for root, _, files in os.walk(tmp):
                for fn in files:
                    full = Path(root) / fn
                    rel = full.relative_to(tmp).as_posix()
                    if rel == "mimetype":
                        continue
                    z.write(full, rel)

        print(f"Wrote {epub_path} ({epub_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
