#!/usr/bin/env python3
"""Build a print-ready PDF for paperback / hardcover interior.

Pipeline:
1. Read `_build_book.md` (must already be built via `build_book_md.py --print`)
2. Convert markdown to HTML via pandoc
3. Wrap with print CSS (6x9 trim, KDP-friendly margins, EB Garamond)
4. Render to PDF via headless Chrome

Why headless Chrome: it embeds local file:// images directly into the PDF
and respects @page CSS for proper page breaks. kdp-book-generator's PDF
output references images by URL rather than embedding, which fails KDP's
print review.

Platform note: this script defaults to macOS Chrome path. Override with
`--chrome` or `$CHROME_BIN`. On Linux use `google-chrome` or `chromium`.

Required tools:
    brew install pandoc          (or apt-get install pandoc)
    Google Chrome / Chromium     (path below or via --chrome)

Usage:
    python3 build_print_pdf.py dist/book-paperback.pdf
    python3 build_print_pdf.py dist/book.pdf --chrome /usr/bin/chromium
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import add_config_arg, load_config, project_root  # noqa: E402

DEFAULT_CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]

CSS = r"""
@page {
    size: 6in 9in;
    margin: 0.625in 0.625in 0.625in 0.875in;
    @bottom-center {
        content: counter(page);
        font-family: "EB Garamond", "Garamond", "Georgia", serif;
        font-size: 10pt;
    }
}
@page:first { margin: 0; @bottom-center { content: none; } }

html, body { margin: 0; padding: 0; }

body {
    font-family: "EB Garamond", "Garamond", "Georgia", "Times New Roman", serif;
    font-size: 11pt; line-height: 1.45; text-align: justify; color: #000; hyphens: auto;
}

h1 {
    font-family: "EB Garamond", "Garamond", "Georgia", serif;
    font-size: 26pt; text-align: center;
    margin-top: 1.5in; margin-bottom: 0.4in;
    letter-spacing: 2px; text-transform: uppercase; font-weight: bold;
    page-break-before: always; page-break-after: avoid;
}
h1:first-of-type { page-break-before: avoid; }

h2 {
    font-family: "EB Garamond", "Garamond", "Georgia", serif;
    font-size: 11pt; font-style: italic; font-weight: normal;
    text-align: center; margin: 0.05in 0; color: #444; page-break-after: avoid;
}

img {
    display: block; margin: 0.4in auto;
    max-width: 4.5in; max-height: 6in;
    page-break-inside: avoid; page-break-after: avoid;
}

p { text-indent: 0.25in; margin: 0; orphans: 3; widows: 3; }
p:first-of-type, h1 + p, h2 + p, hr + p, blockquote + p,
img + p, p + img, figure + p { text-indent: 0; }

hr { border: none; text-align: center; margin: 1em 0; }
hr::before { content: "* * *"; letter-spacing: 0.5em; color: #444; }

em { font-style: italic; }
strong { font-weight: bold; }

blockquote {
    font-style: italic; margin: 1em 0.4in;
    padding-left: 0.2in; border-left: 2px solid #888;
}

table {
    width: 100%; border-collapse: collapse;
    margin: 0.5em 0; font-size: 9.5pt; page-break-inside: auto;
}
th { background-color: #eee; font-weight: bold; text-align: left;
     padding: 4pt 6pt; border-bottom: 1.5pt solid #333; }
td { padding: 4pt 6pt; border-bottom: 0.5pt solid #ccc; vertical-align: top; }

ul, ol { margin: 0.4em 0 0.4em 0.4in; }
li { margin: 0.15em 0; }

code, pre {
    font-family: "Courier New", monospace; font-size: 9.5pt;
    background-color: #f5f5f5;
}
"""

HTML_WRAPPER = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8" />
<title>{title}</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""


def find_chrome(override: str | None) -> str:
    if override:
        return override
    env = os.environ.get("CHROME_BIN")
    if env and Path(env).exists():
        return env
    for p in DEFAULT_CHROME_PATHS:
        if Path(p).exists():
            return p
    sys.exit("Could not find Chrome/Chromium. Pass --chrome or set $CHROME_BIN.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out_pdf", help="Output PDF path")
    ap.add_argument("--chrome", default=None, help="Path to Chrome/Chromium binary")
    add_config_arg(ap)
    args = ap.parse_args()

    cfg = load_config(args.config)
    root = project_root(args.config)
    build_md = root / cfg["paths"]["build_md"]
    if not build_md.exists():
        sys.exit(f"{build_md} not found — run build_book_md.py first")

    chrome = find_chrome(args.chrome)
    out_pdf = Path(args.out_pdf).resolve()
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    body_html = subprocess.check_output([
        "pandoc",
        "--from", "markdown+yaml_metadata_block+pipe_tables+raw_html",
        "--to", "html5",
        "--wrap=preserve",
        str(build_md),
    ]).decode("utf-8")

    full_html = HTML_WRAPPER.format(
        lang=cfg.get("language", "en"),
        title=cfg.get("title", "Book"),
        css=CSS,
        body=body_html,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", dir=str(root), delete=False) as f:
        html_path = Path(f.name)
        f.write(full_html)
    try:
        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--no-sandbox",
            f"--print-to-pdf={out_pdf}",
            "--virtual-time-budget=20000",
            f"file://{html_path.resolve()}",
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        try:
            html_path.unlink()
        except OSError:
            pass

    print(f"Wrote {out_pdf} ({out_pdf.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
