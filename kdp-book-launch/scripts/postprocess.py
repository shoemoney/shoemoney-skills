#!/usr/bin/env python3
"""Set PDF metadata (title, author, subject, keywords) on built PDFs.

KDP doesn't reject PDFs without good metadata, but Goodreads / Apple Books /
Calibre / library systems mine it heavily. Always set it.

Reads pdf_metadata block from your launch config.

Requires: pypdf (`pip install pypdf` — Python 3.10+)
Note: this system uses Python's PEP 668 protection. Use pipx or a venv.

Usage:
    python3 postprocess.py dist/book-paperback.pdf
    python3 postprocess.py dist/book-paperback.pdf dist/book-hardcover.pdf
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import add_config_arg, load_config  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pdfs", nargs="+", help="PDFs to patch in-place")
    add_config_arg(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    md = cfg.get("pdf_metadata", {})
    meta = {
        "/Title":    md.get("title", cfg.get("title", "")),
        "/Author":   md.get("author", cfg.get("author", "")),
        "/Subject":  md.get("subject", cfg.get("subtitle", "")),
        "/Keywords": md.get("keywords", ", ".join(cfg.get("keywords", []))),
        "/Producer": md.get("producer", "kdp-book-generator + kdp-book-launch"),
        "/Creator":  md.get("creator", cfg.get("author", "")),
    }

    for path in args.pdfs:
        p = Path(path)
        if not p.exists():
            print(f"  WARN: missing: {p}", file=sys.stderr)
            continue
        r = PdfReader(str(p))
        w = PdfWriter(clone_from=r)
        w.add_metadata(meta)
        with open(p, "wb") as f:
            w.write(f)
        print(f"  metadata set: {p}")


if __name__ == "__main__":
    main()
