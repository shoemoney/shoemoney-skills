---
name: md-to-pdf-render
description: Turn Markdown or HTML into a print-quality paginated PDF on macOS using pandoc plus headless Chrome, then verify the result by page count and by actually looking at it. Use whenever a document must land as a PDF with a specific page budget — resumes, CVs, cover letters, one-pagers, invoices, reports, leave-behinds — or when the user hands you a PDF to edit and there's no source file. Also use when a PDF needs regenerating repeatedly from a text source that should stay diffable and version-controlled.
---

# Markdown → paginated PDF (macOS)

Two situations bring you here. Either the user wants a polished PDF from text, or they hand
you a PDF and ask for edits. In the second case, say plainly that editing a PDF directly
mangles its layout, and offer to rebuild it from a Markdown source — you get a diffable file,
a one-command rebuild, and no more "which version is current".

## The toolchain that's actually present

macOS rarely has `weasyprint` or `wkhtmltopdf`, and installing them mid-task is a detour.
Check before choosing:

```bash
for c in pandoc weasyprint wkhtmltopdf; do printf "%-12s " "$c"; command -v $c || echo -; done
ls -d "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" 2>/dev/null
```

pandoc + headless Chrome is almost always the pair that exists. Chrome's print engine also
handles `@page`, `page-break-inside`, and modern CSS properly, which the alternatives don't.

```bash
#!/usr/bin/env bash
# build.sh <file.md> -> <file.pdf>
set -euo pipefail
cd "$(dirname "$0")"
md="${1:?usage: ./build.sh <file.md>}"; base="${md%.md}"

pandoc "$md" --standalone --embed-resources --css=style.css -o "$base.html"

"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$PWD/$base.pdf" "file://$PWD/$base.html" 2>/dev/null

rm -f "$base.html"
echo "built: $base.pdf"
```

`--embed-resources` inlines the CSS so Chrome doesn't need to resolve a relative stylesheet
from a `file://` URL. `--no-pdf-header-footer` removes Chrome's default URL-and-date chrome,
which otherwise appears on every page and instantly reads as "printed from a browser".

If the deliverable has a human-facing filename (`Jane Smith - Resume.pdf`) as well as a working
name, emit both from the script. A filename like `resume-acme-v3-final.pdf` reaching a
recruiter's ATS says things the user didn't intend to say.

## Print CSS that matters

```css
@page { size: letter; margin: 0.5in 0.55in; }
body  { font-family: "Helvetica Neue", Arial, sans-serif; font-size: 10pt; line-height: 1.3; }
h2    { page-break-after: avoid; }     /* no heading stranded at a page foot */
h3, li{ page-break-inside: avoid; }    /* no bullet split across pages */
```

Those two page-break rules do more for perceived quality than any font choice. Set them before
fiddling with anything else.

## 🚩 Ligatures silently corrupt the text layer

Chrome enables common ligatures by default, so `fi` and `fl` render as the single codepoints
`ﬁ` (U+FB01) and `ﬂ` (U+FB02) — and **that is what lands in the PDF's text layer.** The document
looks flawless to a human and is wrong to every machine that reads it.

**The tell.** The PDF looks perfect, but searching it for a word you can plainly see returns
nothing. `workflows` is stored as `workﬂows`. Nobody reports this, because the only readers who
notice are automated ones: ATS keyword scanners, `grep`, search indexers, extraction pipelines.
The trigger pairs are common enough — `identify`, `classification`, `profile`, `benefits`,
`qualified`, `final`, `office` — that on a résumé it hits much of the scored keyword surface.

Fix, globally, in the print stylesheet:

```css
*, *::before, *::after {
  font-variant-ligatures: none;
  -webkit-font-feature-settings: "liga" 0, "clig" 0, "dlig" 0, "hlig" 0;
  font-feature-settings: "liga" 0, "clig" 0, "dlig" 0, "hlig" 0;
}
```

Set both properties — `font-variant-ligatures` alone has not been reliable across Chrome versions.

**The check.** Assert on the *built PDF*, never the HTML: the substitution happens at render time,
so the source is always clean. Make it a build gate, because visual review cannot catch this:

```bash
if pdftotext out.pdf - 2>/dev/null | grep -q '[ﬁﬂﬀﬃﬄﬅﬆ]'; then
  echo "FAIL: ligatures in PDF text layer"; exit 1
fi
```

No poppler? `python3 -c "import pypdf,sys; t=''.join(p.extract_text() for p in pypdf.PdfReader('out.pdf').pages); sys.exit(any(c in t for c in 'ﬁﬂﬀﬃﬄ'))"`.
Either way it must be an assertion in the build — a document already sent is not fixable.

## Hitting a page budget

Documents overshoot. Count pages without needing poppler installed:

```bash
python3 -c "
d=open('out.pdf','rb').read()
print('pages:', d.count(b'/Type /Page') - d.count(b'/Type /Pages'))"
```

When it's one page over, adjust the CSS *scale* before cutting the user's content — they wrote
it for a reason. Tighten in this order, rebuilding and recounting each time: line-height →
body font-size → section margins → page margins. Moving `line-height` from 1.34 to 1.26 and
font-size from 10.2pt to 9.6pt typically reclaims a full page while still reading comfortably.
Below about 9pt or 1.2 line-height it starts to look cramped — past that point, tell the user
the content genuinely needs trimming and let them choose what goes.

## Look at it before saying it's done

Page count says it fits, not that it's right. Widow headings, blown-out tables, and a
stylesheet that silently failed all pass a page count.

The Read tool renders PDFs only when poppler is installed (`pdftoppm`). When it isn't, don't
install it mid-task — screenshot the intermediate HTML with the same Chrome binary and read
that image:

```bash
pandoc doc.md --standalone --embed-resources --css=style.css -o /tmp/doc.html
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --screenshot="/tmp/doc.png" --window-size=850,2200 --hide-scrollbars "file:///tmp/doc.html"
```

Then actually view the PNG. It catches broken layout in one glance.

## Marking work-in-progress

When facts are missing, leave visible placeholders in the source rather than inventing
plausible values — a fabricated metric on a résumé is worse than a gap. Backticked markers
render as inline code, so give `code` a loud background in the stylesheet and they're
impossible to miss in the PDF and trivial to grep before shipping:

```bash
grep -n 'NEED FROM YOU\|TODO\|CONFIRM' source.md
```

## Headless Chrome cannot produce a page number from CSS (2026-08-20)

`chrome --headless --print-to-pdf` **cannot render a folio**, and neither can your stylesheet:

- Chrome does not implement CSS paged-media margin boxes, so
  `@page { @bottom-right { content: counter(page) " / " counter(pages) } }` renders **nothing**.
  No warning. You get a PDF with no page numbers and no indication why.
- The CLI's built-in header/footer (what you get by omitting `--no-pdf-header-footer`) is an
  unstyled date + document title, and in current builds carries **no page number at all**.

The only route to `07 / 15` in your own type is the DevTools protocol —
`Page.printToPDF` accepts `displayHeaderFooter`, `headerTemplate`, `footerTemplate`, where the
templates may use the magic classes `.pageNumber`, `.totalPages`, `.title`, `.url`, `.date`.
Inline styles only; set an explicit `font-size` or the text renders microscopically.

**Node 22+ ships a global `WebSocket`, so CDP needs zero dependencies:** launch with
`--remote-debugging-port=N`, `GET http://127.0.0.1:N/json/list` for a page target, connect to its
`webSocketDebuggerUrl`, then `Page.enable` → `Page.navigate` → wait for `Page.loadEventFired` →
`Page.printToPDF`. Also unavailable from the CLI and available here: exact margins, `preferCSSPageSize`,
and paper size in inches.

## Two silent failures that ship a plausible PDF

**Link annotations resolve against the page's origin.** Render from `localhost` and every internal
link in the distributed PDF points at `127.0.0.1` — dead the moment the file is emailed. Verify:

    python3 -c "import re,sys;d=open(sys.argv[1],'rb').read();\
    print([u for u in set(re.findall(rb'/URI\s*\(([^)]+)\)',d)) if b'127.0.0.1' in u or b'localhost' in u])" out.pdf

To iterate print CSS against a staging host while keeping production URLs, render the production
URL and remap DNS at the browser:
`--host-resolver-rules="MAP example.com 10.0.0.5,MAP assets.example.com 10.0.0.5"`
(add `--ignore-certificate-errors` if the cert will not match). The page still believes it is
production, so annotations stay correct.

**If the stylesheet 404s you get an unstyled PDF, not an error.** Especially where assets are on a
CDN whose origin lags the page host. Gate the render on the stylesheet actually returning 200, and
fail on a suspiciously small output — both failures produce a believable file.

## Print-CSS traps worth knowing

- **A `display:flex` + `min-height:100vh` wrapper fragments badly**: each child is kept whole and
  every section lands on a fresh sheet with a page of white beneath it. Flatten to `display:block`
  and `min-height:0` inside `@media print`.
- **`break-inside: avoid` on tall prose blocks is counterproductive** — it pushes a page of white
  ahead of every section. Reserve it for atomic things: `pre`, `figure`, table rows, small data boxes.
- **`thead { display: table-header-group }`** or a long table loses its column meanings at the break.
- **Hiding a child leaves the parent's border**: hiding an ad `<a>` left its bordered container as an
  empty box on the page. Hide the wrapper.
- **Tailwind's responsive prefixes never match print.** A masthead shipped as `hidden lg:block`
  disappears entirely, because print media has no `lg`. Force it visible explicitly.
- **Specificity beats cascade order and will surprise you**: `a[href^='/']::after` scores (0,1,1)
  because an attribute selector counts at class level, so `header a::after` at (0,0,3) loses to it
  *even with `!important` on both*. A letterhead printed a URL glued to the logo because of this.

## Verify a PDF by rasterising it, never by extracting its text

The most dangerous PDF defect is one where the **text layer is correct and the render is not**.
Observed: `::marker` set in a subsetted mono font drew `..` `!.` `i.` in place of `1. 2. 3.`,
because the embedded subset carried no digit glyphs for the marker box. `pdftotext` read
`"1. Hand-write it"` — perfectly correct — so text-based checking passed. It was also invisible at
60 dpi and only legible at 150.

    pdftoppm -png -r 150 -f 4 -l 4 out.pdf page   # then LOOK at it

Fix for that class: `::marker { font-family: inherit }` in print. More generally, never set a
subsetted font on a generated box (markers, counters) you did not supply glyphs for.
