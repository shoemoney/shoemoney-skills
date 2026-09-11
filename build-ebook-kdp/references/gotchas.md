# Traps in the toolchain

Every entry here cost real debugging time on a live book. They share a shape:
**the tool reports success and the output is quietly wrong.** That is why each
one is paired with the check that actually catches it.

## Contents
- [Headless Chrome / print CSS](#headless-chrome--print-css)
- [reportlab overlays](#reportlab-overlays)
- [LibreOffice verification](#libreoffice-verification)
- [python-docx](#python-docx)
- [ODF / ODT](#odf--odt)
- [Cover art](#cover-art)
- [Cross-format page counts](#cross-format-page-counts)

## Headless Chrome / print CSS

**`break-before: right` is not reliable, and `left` is a no-op.**
Chromium in headless print treats page 1 as a *left* page, so `break-before:
right` lands content on **even** pages; `break-before: left` does nothing at all.
Do not fight this in CSS. Emit plain `page-break-before: always`, then force
recto placement at the PDF layer where you know real page indices — walk the
pages, and insert a blank before any opener that landed on an even page. That is
deterministic and survives Chrome upgrades.

To find the openers after rendering, put an invisible marker in each opener
(`<span style="position:absolute;color:#fff;font-size:2pt">[[OP:ch-3]]</span>`)
and locate it with a text extraction pass. Render **twice**: once with markers to
learn the pagination, once without for the shipping file. Removing an absolutely
positioned zero-height span does not reflow anything, so both renders paginate
identically — assert the raw page counts match before trusting it.

**A block whose height equals the page box, plus `page-break-after`, emits a
phantom blank page.** `height: 7.5in` on a 7.5in content box overflows by a hair
and the break then fires twice. Let natural height drive full-page elements and
let `page-break-after: always` alone end the page.

**Justified text needs `lang` for hyphenation.** Without `<html lang="en">`
Chrome will not hyphenate, and justified body text at a 4.5" measure develops
rivers. One attribute, large payoff.

**A missing glyph becomes a Type3 font.** A `★` that the display face does not
carry makes Chrome synthesise a Type3 font, which KDP preflight dislikes. Check
for `/Subtype /Type3` in the output and replace the character with a drawn rule
or a glyph the font actually has.

## reportlab overlays

**reportlab declares `/F1 Helvetica` in every page's resources whether you use it
or not**, and Helvetica is not embedded — so a font-embedding audit fails on a
file whose visible text is fully embedded. Pass
`canvas.Canvas(..., initialFontName="<a registered TTF>", initialFontSize=9)`.

**A canvas with nothing drawn produces zero pages.** Call `showPage()` before
`save()` or merging that overlay raises `IndexError`.

**Order matters when mirroring margins.** If you shift page content
horizontally to create a gutter, shift *first*, then stamp folios and running
heads — otherwise the furniture moves with the text and the folios stop being
centred on the trim.

## LibreOffice verification

**`--convert-to pdf` silently drops auto-inserted blank pages.** Odd-page section
breaks create blanks that Word and LibreOffice both honour when printing, but the
PDF export skips them by default. The rendered PDF then shows chapter openers on
what look like versos and folios that disagree with physical page numbers — and
you "fix" a bug that was never there. Export with:

```
--convert-to 'pdf:writer_pdf_Export:{"IsSkipEmptyPages":{"type":"boolean","value":"false"}}'
```

**Converting two files into one `--outdir` in a single command overwrites**, since
the output name is derived from the input basename and both were the same stem.
Use separate output directories per format.

## python-docx

**`doc.styles.add_style(name)` throws on builtin names**, and some names you would
never expect are builtins — `"Book Title"` is a builtin *character* style, so
adding it returns a `CharacterStyle` with no `paragraph_format` and blows up
later with a confusing `AttributeError`. Prefix custom style names (`OCS Body`)
and only reuse a builtin deliberately — `Heading 1` should be reused, because
`STYLEREF` and the TOC field key off it.

**Mirrored margins are a document setting, not a section property.** Append
`<w:mirrorMargins/>` to `settings.xml` and set `w:gutter` on the section. Setting
left/right margins alone gives you a symmetric block.

**Running heads that follow the chapter want `STYLEREF`, not one section per
chapter.** `{ STYLEREF "Heading 1" \* MERGEFORMAT }` pulls the current chapter
title automatically. Combine with `<w:evenAndOddHeaders/>` for verso/recto
variation, and `different_first_page_header_footer` to keep heads off openers.

## ODF / ODT

**`style:page-usage="right"` silently disables `<style:header-left>`.** It gives
you the odd-page chapter starts you wanted, but LibreOffice then treats every
page as a right page, so the recto header is used on versos too and the chapter
title leaks onto both sides. Split it in two:

- master `Chapter` → right-only layout, header suppressed, plus
  `style:next-style-name="ChapterBody"`
- master `ChapterBody` → mirrored layout carrying the real verso/recto headers

The opener lands on a recto with no head and hands off to a properly mirrored
body. This is the ODF equivalent of Word's "different first page".

**The live chapter title is `<text:chapter text:display="name"
text:outline-level="1"/>`** — the ODF analogue of `STYLEREF`. It only works if
chapter titles are real `<text:h text:outline-level="1">` headings.

**`mimetype` must be the first entry in the zip and stored uncompressed.** Same
rule as EPUB. Write it with `ZIP_STORED` before anything else.

## Cover art

**Check the aspect ratio before anything else.** Art designed at one trim rarely
fits another: 8.5 × 11 is ratio 0.773, 6 × 9 is 0.667. Something has to give.

**Crop-test visually before committing.** Render two or three candidate crop
offsets side by side and look at them. A centred crop is often wrong — art with a
subject on one side and type on the other usually wants the crop taken entirely
off the quiet edge.

**Prefer extending background over cropping subject.** To make art *narrower*
you must lose width; to make it *taller* you can replicate the edge rows, which
is invisible on a soft background and loses nothing. Reach for padding first.

**Scaling a dense back cover down is usually the wrong move.** Going 8.5 → 6
inches wide drops 11 pt body copy to about 7 pt *and* pushes the design into the
barcode reserve. Re-setting the back cover at the target trim, reusing the real
photo and palette, beats a 65% raster every time.

**Bleed by edge replication, not by scaling the art up.** Replicate the outer row
of pixels into the bleed strip. Scaling the whole design to fill the bleed pushes
type toward the trim and into the safe margin.

**Verify with a guides proof.** Render the wrap with trim, safe area, spine folds
and barcode reserve drawn on top, and actually look at it. It catches in seconds
what a spec table will not.

## Cross-format page counts

**The DOCX, the ODT and the print PDF will not have the same page count.**
Different engines, different hyphenation, different widow handling. On one real
book the PDF was 100 pages and the DOCX/ODT were 90.

This matters because **spine width is derived from page count**. Pick one file as
the print master — the PDF — and derive the cover from that. If someone uploads
the DOCX instead, they get a shorter book with a cover cut for a longer one, and
the spine art walks onto the front. State this explicitly when handing over
files; it is the single easiest way for all of this work to end up wrong.
