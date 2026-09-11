---
name: build-ebook-kdp
description: Turn a finished manuscript (DOCX or Markdown) plus cover art into everything Amazon KDP needs — print-ready paperback AND hardcover interiors and cover wraps, a validated Kindle EPUB (plus AZW3/MOBI for device proofing), and formatted DOCX/ODT. Use this WHENEVER someone wants to publish, format, or upload a book to KDP or Amazon; asks to "format this manuscript for Kindle", "make my book KDP-ready", "resize the cover for KDP", "build the paperback interior", "what spine width do I need", "convert my book to EPUB/ODT/Kindle format", or hands over a manuscript and cover images and wants uploadable files. Also use for any single piece of that job — spine-width math, cover wrap sizing, trim/bleed/margin questions, barcode placement, recto chapter starts, running heads, or fixing an interior PDF that KDP rejected.
---

# Build a book for Amazon KDP

Take a finished manuscript and cover art, produce files that upload to KDP
without rejection. The two failure modes worth designing against are: a file
Amazon rejects (annoying, visible, fixable) and a file Amazon *accepts* that
prints wrong (expensive, invisible until a box of books arrives). Most of the
care here goes into the second.

## Start here

1. Read the manuscript and cover art. Get the **word count** and the **cover art
   pixel dimensions and aspect ratio** before promising anything.
2. Decide trim size, binding(s), and paper — these three lock everything
   downstream. See `references/kdp-specs.md`.
3. Build the interior first. **Page count comes out of the interior, and spine
   width comes out of page count.** Building a cover before the interior is
   settled means building it twice.
4. Build the covers against KDP's own measurements (below).
5. Verify by rendering and looking, not by trusting exit codes.
6. Package it so the author cannot upload the wrong file, and ship the build
   alongside it so the job is repairable later — see
   [Handover package](#handover-package--this-is-the-deliverable-not-the-loose-files).
   This step is not optional; loose PDFs in a folder is an unfinished job.

## The three decisions that gate everything

**Trim size.** Hardcover supports only five trims. If the book might ever be a
hardcover, pick from that list now — otherwise the interior has to be reset
later. Cover art designed at a different trim will need refitting; check the
aspect ratio early and say so plainly rather than discovering it at cover time.

**Page count vs binding minimums.** Paperback starts at 24 pages, **hardcover at
75**. Spine *text* needs 79+ (KDP recommends 100+). A short manuscript can be a
legal paperback and still be impossible as a hardcover. If the count is
marginal, raise it honestly — larger type, recto-only chapter starts, notes or
reflection pages, part dividers — or tell the author the spine has to be blank.
Do not pad with filler; padding a reader notices is worse than a blank spine.

**Paper.** Cream is ~11% thicker than white, which changes spine width. Lock it
before the cover is built, and state it loudly at handover — a cover cut for
cream and printed on white has its spine art off the fold.

## Cover geometry: ask KDP, never guess

KDP publishes the paperback spine formula but **deliberately does not publish one
for hardcover**. Their Cover Calculator is backed by a plain form POST, so query
it and use Amazon's real production math:

```bash
python3 scripts/kdp_calculator.py --binding hardcover --trim 6x9 --pages 100 --paper cream
```

It returns full-cover width/height, panel size, spine width, hinge, safe area,
spine margin and barcode margins, caches to `.kdp_cover_cache.json` for offline
rebuilds, and self-checks that the panels plus spine reconstruct the full width.

Two things surprise people about hardcover: the **panels are larger than the
trim** (a 6×9 hardcover has 6.197 × 9.236 panels, because the boards overhang the
text block), and there is a **0.4" hinge** beside the spine that must stay clear
of text. A hardcover is not a wide paperback.

## Interior

One 6×9 interior PDF can serve both bindings — the margin table is identical, so
if it clears paperback it clears hardcover at the same page count.

What a trade interior needs, and what each thing costs if skipped:

- **Mirrored margins with a real gutter.** Symmetric margins make text crawl into
  the spine on the inner edge.
- **Chapter openers on rectos.** Openers on versos read as amateur.
- **Running heads and folios**, suppressed on openers, blanks and display pages.
- **Live table of contents** whose page numbers come from the *rendered* PDF, not
  from an estimate. Render once to learn the numbers, fill them in, render again.
- **Publisher typography**: curly quotes, em dashes, hyphenation on, no straight
  quotes anywhere. This is the single clearest amateur/professional tell.
- **Every font embedded, no Type3.** KDP preflight checks this.
- **Even total page count.**

`scripts/render_html.py` → headless Chrome → `paginate.py` → `finalize.py`
implements this. The pagination is deliberately done at the PDF layer rather
than in CSS — see `references/gotchas.md` for why that is not optional.

Dead blank pages created by recto-forcing are an opportunity: stamping a
pull-quote from the upcoming chapter onto them turns ~15 wasted leaves into
design, at no page cost.

## Covers

- **Crop-test before committing.** Render candidate crop offsets side by side and
  look at them. Art with type on one side and a subject on the other usually
  wants the crop taken entirely off the quiet edge, not centred.
- **Padding beats cropping.** Making art taller can be done by replicating edge
  rows (invisible); making it narrower always costs content.
- **Re-set a dense back cover rather than scaling it.** Squeezing an 8.5×11 back
  cover into 6×9 drops body copy to ~7pt and pushes it into the barcode reserve.
- **Keep both bottom corners of the back cover clear** unless you are certain
  which one the barcode lands in.
- **Spine text needs 0.0625" clearance each side.** At a 0.25" spine that leaves
  ~0.125" of band — about 10pt. Size the type from the band, not from a guess.
- **Always output a guides proof** (trim, safe area, spine folds, hinge, barcode)
  and actually look at it before handing over.

## eBook

EPUB is what you upload — **MOBI has not been accepted since August 2022** and
AZW3 never was. Build both anyway for sideloading to a real Kindle to proofread;
just label clearly which file goes to KDP.

Run `epubcheck` and require zero errors *and* zero warnings.

Notes/worksheet pages that work in print are pointless in an ebook — convert them
to a short "Think about it" prompt instead of shipping ruled lines nobody can
write on.

## Verify by looking

Structural checks that pass while the output is wrong are the norm in this
toolchain. Before handing anything over:

```bash
# page count, trim, embedded fonts, recto openers, mirrored margins
python3 scripts/verify.py dist/1_PAPERBACK/Interior.pdf --expect-trim 6x9
epubcheck dist/2_KINDLE/Book.epub
```

Render actual pages to PNG and look at them — title page, contents, a chapter
opener, a body spread, the back matter. Do the same for the cover proof. Reading
a spec table is not verification.

For DOCX/ODT, render via LibreOffice **with blank-page export enabled**, or your
verification will lie to you:

```bash
soffice --headless --convert-to \
  'pdf:writer_pdf_Export:{"IsSkipEmptyPages":{"type":"boolean","value":"false"}}' \
  --outdir build/verify/docx dist/3_EDITABLE/Book.docx
```

## Handover package — this is the deliverable, not the loose files

A folder of correctly-built PDFs is not a finished job. The author is standing in
front of a web form with dropdowns, and every ambiguity in the folder is a chance
to upload the wrong file against the right cover. Always produce this exact
structure:

```
dist/
├── READ_ME_FIRST.TXT          <- what every folder is and what to do with it
├── UPLOAD_THESE/
│   ├── 1_PAPERBACK/
│   │   ├── READ-ME-FIRST.txt                    exact dropdown values
│   │   ├── 1_INTERIOR__upload-as-Manuscript.pdf
│   │   └── 2_COVER__upload-as-Book-Cover.pdf
│   ├── 2_HARDCOVER/           same three files, hardcover geometry
│   └── 3_KINDLE_EBOOK/
│       ├── READ-ME-FIRST.txt
│       ├── 1_MANUSCRIPT__upload-as-eBook.epub
│       ├── 2_COVER__upload-as-eBook-Cover.jpg
│       └── EXTRA_for-device-proofing/   .azw3 / .mobi, clearly NOT uploads
├── CONTENT_TO_PASTE/          one file per KDP form field
├── PROOFS/                    guides proofs + cover parts; nothing uploads
├── EDITABLE_SOURCE/           .docx / .odt for editing, NOT for uploading
├── AGENTS.md                  orientation for the next AI assistant
└── scripts/                   the whole build, self-contained and runnable
```

Generate it with:

```bash
python3 scripts/package_kdp.py --pages 100     # UPLOAD_THESE/ PROOFS/ EDITABLE_SOURCE/ + root README
python3 scripts/write_listing.py               # CONTENT_TO_PASTE/
python3 scripts/ship_sources.py --pages 100    # scripts/ + AGENTS.md
```

Two conventions do most of the work. **Filenames name the form field they go
into** (`1_INTERIOR__upload-as-Manuscript.pdf`), so the mapping needs no memory.
And **every folder that is not an upload says so in its own name** —
`PROOFS`, `EDITABLE_SOURCE`, `EXTRA_for-device-proofing`.

`CONTENT_TO_PASTE/` splits the listing copy one file per field, because KDP's
form has hard limits and quirks — 7 keyword slots, a 4000-char description that
accepts only a subset of HTML (`<b> <i> <br> <p> <ul> <li>`, never `<div>` or
`<a>`), and the same content re-entered for each format. Emit character counts
next to the limits, and mark anything you were not given as an explicit TODO —
never invent an author bio or a sales claim.

Write listing copy only from the manuscript and the author's own cover text.
Descriptions are where fabricated credentials creep in; if a claim is not in the
author's material, it does not go in the description.

### Ship the build with the book

`ship_sources.py` copies the scripts, fonts, source art and manuscript into
`dist/scripts/` — a faithful, runnable clone of the working directory — and
writes `dist/AGENTS.md` from `assets/AGENTS.md.template`.

This exists because of what happens six months later. Someone asks an assistant
to "fix the spine" or "change a chapter title". That assistant has the output
files and none of the reasoning, so it re-derives the wrong answers: it recentres
a crop that was deliberately taken off one edge, hand-calculates a hardcover
spine KDP does not publish a formula for, or trusts a LibreOffice render that
silently dropped the blank pages. AGENTS.md is how the reasoning survives.

Two sections are marked REWRITE PER BOOK and you must actually fill them in:

- **How the covers were built** — which edge the front was cropped from and why,
  whether the back was scaled or redrawn, photo crop coordinates, and anything
  that was wrong in the supplied art (a mis-spelled spine, a mockup at the wrong
  aspect ratio). A future agent will otherwise undo these decisions.
- **Things a human must decide** — every change made to the author's own words,
  and every unsourced claim you noticed but did not fix.

Verify the shipped copy actually runs before handing it over. Ours reproduced
the 100-page interior from a cold start, and doing that caught a real bug:
`cover.py` assumed its output directories already existed, which only worked
because the original run had created them earlier.

```bash
cd dist/scripts && PY=python3 ./build/all.sh      # must reproduce the page count
```

### State these plainly at handover

Each is a way the work silently ends up wrong:

- **Which file is the print master.** DOCX/ODT paginate differently from the PDF
  (90 vs 100 pages on one real book). Spine width comes from the PDF's page
  count, so the PDF is what uploads.
- **Paper colour**, because the spine depends on it.
- **Page count**, because the cover is cut for exactly that number.
- **EPUB uploads; AZW3/MOBI are for proofing on a device.**
- **Anything you changed in the author's content** — cut copy, fixed typos,
  reflowed art. Name it and offer to revert.

## Tooling

```bash
brew install --cask calibre libreoffice        # ebook-convert, soffice
brew install pandoc imagemagick epubcheck
pip install python-docx pypdf pillow reportlab fonttools pypdfium2
```

Chrome/Chromium is required for the print PDF (headless `--print-to-pdf`).

Fonts: `scripts/fonts.py` downloads Google Fonts variable files and instances
static weights, which embed more predictably than variable fonts.

## Files in this skill

| Path | What it is |
|---|---|
| `scripts/kdp_calculator.py` | Queries KDP's Cover Calculator; the only trustworthy source for hardcover spine width |
| `scripts/kdpcfg.py` | Loads `book.json`, derives geometry, palette, paths |
| `scripts/fonts.py` | Fetches + instances the type family |
| `scripts/extract.py`, `model.py` | DOCX → paragraph dump → canonical book structure |
| `scripts/typo.py` | Curly quotes, em dashes, ellipses |
| `scripts/render_html.py`, `paginate.py`, `finalize.py` | Print interior: HTML → Chrome → recto forcing → folios/heads/mirroring |
| `scripts/cover.py` | Front/back/spine/wrap/ebook cover/proof, per binding |
| `scripts/epub_build.py` | EPUB 3 (passes epubcheck clean) |
| `scripts/docx_build.py`, `odt_build.py` | Editable formats with real styles |
| `scripts/verify.py` | Post-build assertions |
| `scripts/package_kdp.py` | Builds `UPLOAD_THESE/`, `PROOFS/`, `EDITABLE_SOURCE/` and the root `READ_ME_FIRST.TXT` |
| `scripts/write_listing.py` | Builds `CONTENT_TO_PASTE/` — one file per KDP form field |
| `scripts/ship_sources.py` | Ships a runnable clone of the build into `dist/scripts/` and writes `dist/AGENTS.md` |
| `assets/book.json.template` | The single config every script reads |
| `assets/book.json.example` | A real, complete config from a shipped book |
| `assets/AGENTS.md.template` | Orientation doc for whoever picks this up later |
| `references/kdp-specs.md` | Verified KDP numbers, with sources |
| `references/gotchas.md` | Toolchain traps that report success while producing wrong output — **read this before debugging anything** |

The build scripts are working reference implementations, not a general-purpose
typesetting engine. Every manuscript has its own structure, so expect to adjust
`model.py`'s classification and the back-cover layout per book — the parts worth
reusing verbatim are the KDP geometry, the pagination strategy, and the
verification.

## Cover QA gotchas learned the hard way (2026-09-09)

- **Ghost layer.** If the "art" you embed at print resolution is the *ebook JPEG* (which already
  has the title baked in) and you then draw the typography again, every line appears twice and an
  old tagline shows through the new one. Build the print wrap from the text-free art only. Check:
  `pdftotext` shows one "AiBook", but the render is what proves it.
- **Resolution is per embedded image, not per PDF.** A 13 x 9 in wrap can embed a 1024 x 1536
  front (164 dpi) next to a 2172 x 724 strip (350 dpi). Check each: regex `/Width` `/Height` per
  `/Subtype /Image`, divide by placed inches; or `pdfimages -list`.
- **`/FontFile` grep can return 0 while fonts are embedded** (compressed object streams). Use
  `pdffonts file.pdf` before declaring fonts missing.
- **Stale copy.** Chapter numbers and counts on the cover come from the brief at the time it was
  written; a renumber later leaves "Chapter 41" and "60 chapters" on a book with 61. Diff the
  cover text against the locked copy file after every manuscript restructure.
- **Author photo slot.** Column text starting at a hardcoded y collides with any portrait taller
  than the headline. Start the column at `min(rule_y, caption_bottom) - gap` and cap the portrait
  at ~1.1–1.3 in; rebalance bullets between columns to remove the whitespace it creates.
- **Spine width moves with the cut.** 157k words → 135k words moved the estimate from 0.90 in to
  0.93 in at 6 x 9. Rebuild the wrap at the final page count, not the draft count.

## Photographs in a book interior: four things that bite

Measured 2026-09-10 while placing three family photos into a 6x9 interior.

### PIL silently ignores EXIF rotation

`Image.open()` returns the stored pixels, **not** the orientation the camera recorded. A phone
photo stored 4032x3024 with a rotate flag comes back landscape, and every crop you compute from
it is wrong. It produced a diptych with one subject lying on her side, and nothing errored.

```python
from PIL import Image, ImageOps
im = ImageOps.exif_transpose(Image.open(src))     # do this FIRST, always
```

**The tell:** a portrait-orientation photo reports landscape dimensions, or a centre crop cuts
across the subject in a way that makes no sense.

### A photo of a document can publish someone's live credentials

A photo of a cheque reproduced at print resolution carries the **MICR line** — the payer's bank
routing and account number, legible at 4 inches wide. Anyone with those two numbers can initiate
ACH debits. The photo also carries a signature and often a street address. This is a real harm
to a third party who has no idea they are in your book.

**Crop it out of frame rather than masking it.** Masking a tilted object requires a rotated
region; an axis-aligned box runs off the object onto the background and reads as a censorship
bar. Cropping above the offending strip looks like a normal photograph.

Same check applies to: prescription labels, boarding passes, envelopes, screens showing tokens,
badges, and anything with a barcode or QR code.

### Chrome does NOT downsample `file://` images in HTML-to-PDF, and alpha survives

Verified with `pdfimages -list`: a 3419x2400 PNG referenced directly landed at **1150 ppi** with
its transparency intact as an `smask`. So for a handful of images you can skip whatever
placeholder-and-swap machinery exists for the bulk path. Confirm with `pdfimages -list -f N -l N`
rather than assuming either way.

### Use the artifact's OWN existing treatment before inventing one

The book already had `manuscript/assets/thumbs/feather.py` — a Gaussian edge fade applied to all
130 chapter thumbnails. Applying that same proportional 5% fade to the new photos made them
consistent with the rest of the book, which no amount of new design would have achieved.

**Before generating or designing anything new for an existing artifact, grep the repo for how the
existing instances of that thing were made.** It is faster and the result matches.

## Moving one element invalidates everything sized around its old position

Pulling an author portrait inward to satisfy KDP's 0.4in spine rule silently broke the headline
above it: `headline_width` was a hardcoded `314`, the portrait's left edge moved to `320.7`, and
the last word of every headline line was drawn underneath the photo and clipped.

Worse, a sibling branch in the same file already had the correct derived form
(`W-27-PROFILE_W_PT-12-20`) while the branch actually in use hardcoded the number.

**After moving any element to satisfy a constraint, re-render and re-check every neighbour that
was positioned or sized relative to it** — not just the one you were fixing. And when a file
contains both a derived and a hardcoded version of the same measurement, the hardcoded one is
the bug waiting to happen.
