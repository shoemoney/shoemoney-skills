---
name: kdp-print-cover-rejections
description: Diagnose and fix an Amazon KDP paperback or hardcover cover that keeps getting rejected, and verify a cover programmatically BEFORE uploading it. Covers the two complaints that produce most print rejections (no clear 2.0 x 1.2 in barcode zone on the back cover, and text closer than 0.4 in to the spine edge / 0.375 in paperback or 0.716 in hardcover to the outer edges), the subject-line trap that makes authors fix the wrong thing for months ("Attention needed - Please review your TITLE" means your listing, NOT the book's name), the off-by-two-thousandths failure from setting a margin constant to exactly the spec floor, and how paperback and hardcover wrap geometry differ. Use WHENEVER a KDP print title will not leave review, whenever a cover bounces more than once, whenever you see "We are unable to place a barcode on your file" or "text is too close to the edges", before uploading any print cover, and whenever a cover is built by a script with hardcoded panel coordinates.
---

# KDP print covers: why they bounce, and how to prove yours will not

Nearly all repeat print rejections are the **cover**, not the manuscript, and they are
mechanical. Measured 2026-09-10 on a title that had been rejected **eight times over four
months** (2026-05-21, 05-24, 06-30 x2, 08-17 x2, 09-09 x2) across two ISBNs.

## The trap that costs months

KDP's rejection email is subject-lined:

> **Attention needed: Please review your title, <Book Name> (ISBN: ...)**

In KDP's vocabulary **"your title" means your listing/book record, not the book's *name***.
Authors read it as "Amazon has a problem with what I called my book", go look at the name,
find nothing wrong, and give up. The actual complaint is two paragraphs down in the body.

**The tell:** repeated identical-looking emails with no obvious action, and an author who
believes the problem is naming or content. **Always open the email body and read the
"Cover"/"Interior" section.** Fetch them programmatically if there are several:

```python
m.literal = b'from:kdp "<Book Name>"'
typ, data = m.uid("SEARCH", "CHARSET", "UTF-8", "X-GM-RAW")
```

## The two complaints that cause most rejections

**1. No barcode zone.**
> "We are unable to place a barcode on your file. Adjust your cover file to leave a space on
> the back cover that is free from any text, images, or design elements, and measures
> 2 inches wide by 1.2 inches tall... light-colored and solid."

**2. Text too close to an edge.**
> Paperback: all text >= **0.375 in** from every trim edge.
> Hardcover: viewable elements >= **0.716 in** from outer edges.
> Both: back-cover text >= **0.4 in** from the **spine edge**.

## Never set a margin constant to exactly the spec floor

The single most expensive line in that four-month failure:

```python
BYLINE_RIGHT_IN = 0.40     # right edge inset from trim
```

0.40 is exactly KDP's minimum. After antialiasing it **rendered at 0.398 in** and failed by
**0.002 in**, eight times. Rasterization, font hinting and PDF rounding all move a value by a
fraction of a point. **Leave real margin** (0.55 was used) and re-measure the rendered output,
never the source constant.

## Paperback and hardcover wrap geometry are different objects

A hardcover case wrap is not a paperback wrap with a wider spine, and **it is not derivable
from a formula**. The numbers come from KDP's Cover Calculator (kdp.amazon.com/cover-calculator)
for the exact binding, paper, trim and page count. A formula-built hardcover wrap was rejected
on 2026-09-10 ("expected cover size is 14.704x10.417 but the submitted file size is 14.565x10.417").

```
paperback   EDGE = 0.125 in (bleed) on every side; spine = pages x paper thickness
            wrap = 2(trim_w) + spine + 2(0.125)  x  trim_h + 2(0.125)
            paper: cream 0.0025 in/page, white 0.002252 in/page

hardcover   read the calculator. For 6x9, B&W, cream, 376 pp it says:
            full cover 14.704 x 10.417 | wrap 0.591 every side | boards 6.197 x 9.236 each
            spine 1.129 (safe area 1.004 x 8.986) | hinge 0.394 each side | barcode margin 0.25 x 0.375
            The boards are LARGER than the trim. Scale the 6x9 design up to fill a board;
            do not centre a 6x9 panel inside it or a strip of wrap colour shows on the board face.
            Make the wrap colour match the spine, not the back-panel paper.
```

**Matching the total width is not enough.** A sibling fix inflated the spine to 1.079 so the
wrap hit 14.704 while keeping 0.8125 in edges and 6x9 panels. The previewer would accept the
size and the printed book would carry a pale 0.2 in frame around the front art where the wrap
colour lands on the board face. Check panel placement, not just the page size.

**The back panel starts at the wrap, not at the bleed.** Measuring a hardcover back panel with
paperback coordinates samples the middle of the artwork and produces a confident, wrong verdict.

The calculator's form **resets every dependent dropdown when binding type changes**; set binding
first, then the rest in order, then Calculate. Driving it with Playwright works: set each
`<select>` through the native value setter and dispatch `change`, then click the enabled submit.

## Verify before uploading

```python
import subprocess, numpy as np
from PIL import Image
subprocess.run(["gs","-dNOPAUSE","-dBATCH","-sDEVICE=png16m","-r150",
                "-sOutputFile=/tmp/wrap.png", COVER_PDF], capture_output=True)
im  = Image.open("/tmp/wrap.png").convert("RGB"); W,H = im.size; dpi = 150
a   = np.asarray(im).astype(int)
lum = 0.299*a[:,:,0] + 0.587*a[:,:,1] + 0.114*a[:,:,2]
back_r = EDGE_H + TRIM_W                      # spine edge of the back panel, inches

# barcode zone: 2.0 x 1.2 in, 0.25 in inside the back panel's bottom-right trim
zx2, zy2 = back_r - 0.25, H/dpi - EDGE_V - 0.25
z = np.asarray(im.crop((int((zx2-2.0)*dpi), int((zy2-1.2)*dpi),
                        int(zx2*dpi),       int(zy2*dpi))).convert("L")).astype(int)
assert z.mean() > 230 and (z < 200).mean() < 0.02, "barcode zone obstructed"
```

Passing looks like `mean 255.0, obstruction 0.00%`.

## Measure the right thing (this bit lies)

Three wrong verdicts were produced in one session by a probe that "worked":

- **Polarity.** One cover was light text on dark, the next was dark text on light. Reusing the
  same threshold reported the entire background as "text" and the whole panel as violating.
  **Check the panel's ground colour first**, or sample a known-empty region as a control.
- **Art is not text.** A full-width photo strip and a portrait both registered as violations.
  Only *text* must clear the rules; artwork is expected to bleed. Restrict the measured band to
  the copy, or accept that you must look.
- **Seams and exact-spec hits.** Two dark pixels sat at *exactly* 0.4000 in. "At least 0.4 in"
  includes 0.4 in, and 2 px at 150 dpi is 0.013 in of a descender. Do not chase sub-pixel purity.

**Render the panel with the safe zone drawn on it and look at it before reporting anything.**
A rectangle in `ImageDraw` at the safe-zone bounds settles in one glance what pixel statistics
argue about for an hour.

## Two more things that bite

**Bleed setting must match the interior's page box.** KDP's "Bleed" option expects 6x9 pages to
be **441 x 666 pt (6.125 x 9.25 in)**. An interior that is exactly 432 x 648 pt with
`BleedBox == TrimBox == MediaBox` must be uploaded as **No Bleed** or it is rejected or silently
rescaled. Check with `pdfinfo -box`.

**Every format needs its own ISBN.** Paperback, hardcover and any new edition each get a
separate number, and the interior should print *its own*. Rebuild the interior per format
rather than shipping the paperback's ISBN inside the hardcover.

## Duplicated build scripts drift, and the stale one ships

Two copies of the same cover script existed. One said `PAGES=374, SPINE=0.935`, the other
`PAGES=370, SPINE=0.925`. The copy that built the shipped file was the stale one, so the wrap
was cut for a book four pages longer than the book — every element 0.005 in off the fold.
Whichever file you grep gives a confident answer and one of them is wrong.

**The tell:** `git status` shows a build output modified without its script, or two paths match
`find . -name "*build*cover*"`. Identify the real one by **mtime against the artifact**, sync
them, and re-derive the spine from page count after *any* interior rebuild.

## Ghost copy: art with text baked in

The front art of a cover must be the **text-free** render. On 2026-09-10 the AiBook cover
build was invoked as `v8` alone; the variant logic fell through to `cover-ebook.jpg`, the
finished ebook cover with the OLD title, strapline and byline baked in. The new type was drawn
over it, and everywhere the two did not overlap exactly, the old copy showed through faint and
grey. It survived three sessions, a commit, a KDP hardcover upload, and every measurement
script, because every check measured geometry. Jeremy caught it by eye.

**What does not catch it:** OCR. Tesseract read nothing from the ghosted composite, and read
nothing from the baked JPEG either (display type, white on dark). Do not build a guard on OCR.

**What catches it:**
- **Pin the art by hash in the build script** and refuse to run on any other bytes
  (`APPROVED_ART_SHA256` in `build_selected.py`). Changing the art becomes a deliberate act
  with a checklist attached: look at the new file at 200% for type before updating the hash.
- **Delete the fallback.** A variant ladder that silently picks a different source when no
  flag matches is the bug. One art source, no `else`.
- **Look at every text block at 200% before uploading**, on a fresh render, not the PNG from
  the last build. Crop the strapline, title, subtitle, byline and back headline separately;
  ghost copy hides under similar text and is invisible at fit-to-window.
- **Order the printed proof** from KDP before approving anything for sale. It costs print
  price plus shipping and is the only check that sees what the buyer sees.

## A quoted flag pair builds the wrong cover and says "built"

`for v in "v8" "v8 nobarcode" "v8 hardcover"; do python3 build_selected.py $v; done` passes
`v8 nobarcode` as ONE argv entry. The flag ladder matches neither word, falls through to its
oldest variant, writes `cover-print-v2.pdf`, exits 0, and the loop prints "built". The file you
meant to rebuild keeps its old spine and old art. Caught 2026-09-10 only because the wrap width
was checked against the page count after the loop.

**Rule:** after every cover build, `pdfinfo` the file you meant to write and compare the width to
`2*edge + 2*trim + spine` computed from the page count. Never trust the loop's echo. And pass
flags unquoted, or better, make the script refuse unknown argv.
