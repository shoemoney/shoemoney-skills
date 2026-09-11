# KDP manufacturing specs

Every number here was read off Amazon KDP's own help pages. Where KDP does not
publish something, this file says so rather than guessing — an invented spine
width produces a cover that gets rejected or, worse, prints wrong.

## Contents
- [Trim sizes](#trim-sizes)
- [Page-count limits](#page-count-limits)
- [Paper and caliper](#paper-and-caliper)
- [Interior margins](#interior-margins)
- [Paperback cover geometry](#paperback-cover-geometry)
- [Hardcover cover geometry](#hardcover-cover-geometry)
- [Spine text rules](#spine-text-rules)
- [Barcode reserve](#barcode-reserve)
- [Accepted file formats](#accepted-file-formats)

## Trim sizes

Paperback offers many trims. **Hardcover offers only five:**

| Trim | in | cm |
|---|---|---|
| 5.5 × 8.5 | 5.5 × 8.5 | 13.97 × 21.59 |
| 6 × 9 | 6 × 9 | 15.24 × 22.86 |
| 6.14 × 9.21 | 6.14 × 9.21 | 15.6 × 23.39 |
| 7 × 10 | 7 × 10 | 17.78 × 25.4 |
| 8.25 × 11 | 8.25 × 11 | 20.96 × 27.94 |

If a book must exist in both bindings, pick a trim from this list — otherwise the
hardcover cannot be produced at the same size and the interior has to be reset.

Source: <https://kdp.amazon.com/help/topic/GVBQ3CMEQW3W2VL6>

## Page-count limits

| Binding | Min | Max |
|---|---|---|
| Paperback | 24 | 828 |
| **Hardcover** | **75** | **550** |

Hardcover's 75-page floor is the one that bites: a short book that is a legal
paperback may be too thin to exist as a hardcover at all.

Source: <https://kdp.amazon.com/help/topic/GAVW3FZZAKA2KY3B>

## Paper and caliper

Caliper = thickness of one page, which is what spine width is built from.

| Paper | Caliper (in/page) |
|---|---|
| White | 0.002252 |
| Cream | 0.0025 |
| Standard color | 0.002347 |
| Premium color | 0.002252 |

Cream and white are both available for hardcover black-and-white interiors
(50–61 lb / 74–90 GSM). There is no groundwood option for hardcover.

**Paper choice changes the spine width.** Cream is ~11% thicker than white, so a
cover built for cream and printed on white will have the spine art sitting off
the fold. Lock the paper choice before building the cover.

Source: <https://kdp.amazon.com/help/topic/G201834180>

## Interior margins

Hardcover uses the **same** margin table as paperback. Minimum inside (gutter)
margin scales with page count; outside/top/bottom minimum is 0.25" without bleed.

| Page count | Min inside (gutter) |
|---|---|
| 24–150 | 0.375" |
| 151–300 | 0.5" |
| 301–500 | 0.625" |
| 501–700 | 0.75" |
| 701–828 | 0.875" |

These are *minimums*, not targets. A comfortable trade-book interior runs a
noticeably larger gutter than the floor.

Source: <https://kdp.amazon.com/help/topic/GVBQ3CMEQW3W2VL6>

## Paperback cover geometry

Fully specified — you can compute the whole wrap.

```
spine_width  = page_count × caliper
bleed        = 0.125"   (every outer edge)
safe area    = 0.25"    inside the trim
cover_width  = 0.125 + trim_w + spine_width + trim_w + 0.125
cover_height = 0.125 + trim_h + 0.125
```

Worked example — 6 × 9, 100 pages, cream:
`spine = 100 × 0.0025 = 0.250"`, wrap = **12.5 × 9.25 in** = 3750 × 2775 px @ 300 DPI.

## Hardcover cover geometry

Partly specified. KDP publishes the wrap, hinge and safe-margin numbers but
**deliberately does not publish a spine-width formula** — the help page routes
you to the Cover Calculator instead.

| Element | Value |
|---|---|
| Wrap allowance (each edge) | **0.51"** (15 mm) — folds around the board and glues inside |
| Spine hinge (each side of spine) | **0.4"** (10 mm) — flexes when the book opens; keep it empty |
| Text/image safe margin from book edge | **0.635"** (16 mm) |
| Spine width | **not published — use the Cover Calculator** |

```
cover_width  = 0.51 + trim_w + 0.4 + spine + 0.4 + trim_w + 0.51
cover_height = 0.51 + trim_h + 0.51
```

For a 6 × 9 that makes the height **10.02" = 3006 px @ 300 DPI**, and the width
unknown until the spine is supplied.

> **Get the spine width here:** <https://kdp.amazon.com/en-US/cover-calculator>
> Select Hardcover, the trim, the page count, and the ink/paper combination.
> The tool also emits a template you can lay the artwork against.

The hinge is the part people miss. A hardcover is not a wide paperback: 0.4" on
each side of the spine must stay clear of text, which effectively pushes the
front-cover design 0.4" further from the fold than on the paperback.

Source: <https://kdp.amazon.com/help/topic/GDTKFJPNQCBTMRV6>

## Spine text rules

- **Paperback:** spine text permitted from **79 pages**. KDP recommends 100+.
- **Hardcover:** a hardcover spine is flat; books over **120 pages** get a
  black-and-white headband top and bottom.
- Keep spine text **0.0625" clear of each spine edge** — printing shifts by up to
  that much, and text closer than this walks onto the front or back panel.

At the low end this is brutal: a 0.25" spine leaves only 0.125" of usable band,
which caps the type at roughly 9–10 pt. If the design needs a readable spine, the
real fix is more pages, not smaller type.

Source: <https://kdp.amazon.com/help/topic/GKZVNAAFYWVKZWL8>

## Barcode reserve

2" wide × 1.2" high, lower-right of the **back cover**. KDP prints it in a white
box over whatever is underneath, so anything you place there gets covered.

| Binding | Inset from bottom | Inset from side |
|---|---|---|
| Paperback | 0.25" | 0.25" from trim edge |
| Hardcover | **0.76"** | 0.25" from the **spine hinge** |

If you are unsure which corner a given wrap orientation puts the barcode in,
keep **both** bottom corners clear. It costs a little layout freedom and removes
an entire class of mistake.

Source: <https://kdp.amazon.com/help/topic/GDTKFJPNQCBTMRV6>

## Accepted file formats

**Print interior:** PDF (PDF/X-1a preferred). Fonts embedded, flattened, no
transparency, 300 DPI minimum for images, ≤650 MB.

**Print cover:** one single PDF containing back + spine + front.

**eBook:** EPUB, DOCX, KPF, HTML, RTF, TXT, PDF.
**MOBI is no longer accepted** — Amazon dropped it in August 2022. AZW3 was never
an upload format. Both are still useful for sideloading to a device to proofread,
but the file you upload to KDP is the **EPUB**.

Sources: <https://kdp.amazon.com/help/topic/GKYZRXFBZH2LDXAK>,
<https://kdp.amazon.com/help/topic/G202145060>
