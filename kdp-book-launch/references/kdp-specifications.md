# KDP Specifications Cheat Sheet

Distilled spec sheet for the KDP formats we ship in this kit. KDP publishes
the canonical version at https://kdp.amazon.com but the numbers here are
the ones the scripts in this skill assume.

---

## Trim Sizes

The skill defaults to **6" x 9"** (152 x 229 mm), which is the standard
KDP trade paperback for adult fiction and most nonfiction. Other common
choices:

| Trim | Inches | Fits |
|------|--------|------|
| 5 x 8 | 5.0 x 8.0 | Pocket fiction / poetry |
| 5.25 x 8 | 5.25 x 8.0 | Trade fiction |
| **6 x 9** | **6.0 x 9.0** | **Standard adult fiction/nonfiction (skill default)** |
| 6.14 x 9.21 | 6.14 x 9.21 | UK B-format equivalent |
| 7 x 10 | 7.0 x 10.0 | Textbooks, workbooks |
| 8.5 x 11 | 8.5 x 11.0 | Manuals, large-format nonfiction |

To change the default, edit the `@page { size: 6in 9in }` line in
`scripts/build_print_pdf.py` and the `COVER_W_IN` / `COVER_H_IN`
constants in `scripts/compose_cover_wrap.py`.

---

## Bleed

KDP requires 0.125" (3.175mm) bleed on the three outside edges of every
page IF the book contains full-bleed images. Most fiction doesn't —
text-only interiors don't need bleed. Set `bleed: false` in
`_book_config.json`.

For COVER WRAPS: bleed is REQUIRED on all 4 outside edges of the wrap
(both covers + outside top + outside bottom). The cover-wrap script
hard-codes 0.125" bleed per cover (`COVER_W_IN = 6.125`, `COVER_H_IN
= 9.25`).

---

## Spine Width Formulas

These are the KDP-published formulas as of 2025/2026. The cover-wrap
script implements them.

### Paperback, B&W interior, white paper

```
spine_inches = page_count * 0.002252
```

Example: 276 pages → 0.6216" spine.

### Paperback, B&W interior, cream paper

```
spine_inches = page_count * 0.0025
```

KDP cream is slightly thicker than white. Adjust if you choose cream.

### Paperback, color interior, standard paper

```
spine_inches = page_count * 0.002347
```

Pass `--color-interior` to `compose_cover_wrap.py` to use this rate.

### Paperback, premium color interior

```
spine_inches = page_count * 0.002525
```

Rare for fiction; common for art books / cookbooks.

### Hardcover (case binding)

```
spine_inches = page_count * 0.0025 + 0.06
```

The +0.06 accounts for the board hinge. KDP hardcovers also have a wrap
overhang that this skill's script doesn't fully compute — for hardcover
production, take the output PDF as a first draft and use KDP's online
cover-template tool to finalize.

### Spine text rule

KDP doesn't print spine text on books under **80 pages**. The skill's
spine renderer will still draw text but you should suppress it (edit
`compose_cover_wrap.py` to skip the title/author block if page count
< 80).

---

## Cover Wrap Dimensions (paperback, 6x9)

For an N-page paperback, the full wrap is:

```
wrap_width  = 6 + 0.125 + spine(N) + 6 + 0.125 = 12.25 + spine_inches
wrap_height = 9 + 0.125 + 0.125 = 9.25
```

At 300 DPI (the skill default) this is approximately:

| Pages | Spine (B&W) | Wrap WxH (inches) | Wrap WxH (300dpi pixels) |
|-------|-------------|-------------------|--------------------------|
| 120 | 0.270 | 12.520 x 9.250 | 3756 x 2775 |
| 200 | 0.450 | 12.700 x 9.250 | 3810 x 2775 |
| 276 | 0.622 | 12.872 x 9.250 | 3862 x 2775 |
| 400 | 0.901 | 13.151 x 9.250 | 3945 x 2775 |

KDP recommends **300 DPI** minimum for cover art. The skill renders at
exactly 300 DPI.

---

## Interior PDF Specs

- **PDF/A** is NOT required. Standard PDF 1.4-1.7 accepted.
- **Embedded fonts** required (Chrome headless does this automatically).
- **Color space:** sRGB for color interior, grayscale for B&W. The
  `make_bw_variants.py` script outputs grayscale PNGs which Chrome
  passes through correctly.
- **Image resolution:** 300 DPI minimum at the printed size. The skill's
  prompts generate at 1024x1536 which becomes ~170 DPI on a full-page
  6x9 print — acceptable but soft. For a sharper interior, run the
  generated images through an upscaler before `build_print_pdf.py`.
- **Margins:** KDP requires at least 0.375" (gutter side) and 0.25"
  (other three sides). The skill defaults to 0.875" gutter and 0.625"
  outside — comfortable for adult fiction.
- **Page count must match** what you used in `compose_cover_wrap.py`.
  If the interior changes, rerun the wrap.

---

## EPUB Specs

- **EPUB 3.0** preferred. EPUB 2.0 accepted.
- **No DRM** at upload — KDP applies its own (optional) DRM.
- **Cover image** must be 1600 x 2560 pixels (JPG or PNG), ≤ 50MB.
  Use `covers/front-cover.jpg` upscaled to this size.
- **Image limit:** ≤ 50MB per image, ≤ 650MB total per EPUB.
- **Validated with epubcheck.** Always run:
  ```
  brew install epubcheck
  epubcheck dist/book.epub
  ```
  Zero errors required for KDP submission.

---

## KDP Listing Field Limits

| Field | Limit |
|-------|-------|
| Title | 200 chars |
| Subtitle | 200 chars |
| Series name | 200 chars |
| Author display name | 50 chars |
| Description | 4,000 chars (HTML allowed) |
| About the Author | 2,400 chars (HTML allowed) |
| From the Author | 4,000 chars (HTML allowed) |
| Keywords | 7 slots, 50 chars each |
| BISAC | 2 codes |
| ISBN | KDP-assigned free, or BYO ISBN |

Allowed HTML tags in description fields: `<b> <i> <u> <h4> <h5> <h6>
<br> <p> <ul> <ol> <li>`. No links. No tables.

---

## A+ Content

After publication you can add A+ Content via KDP Author Central.
Up to 7 modules. Each module is one of:
- Image with text
- Image header + caption
- Comparison table
- Single image full-width
- Standard image text overlay
- Standard four image / text
- Standard product description text

A+ Content is search-indexed by Amazon and significantly improves
conversion. Make time for it.

---

## Author-Side Decisions Not Covered by the Scripts

The scripts don't decide:
- Pricing tiers
- KDP Select enrollment (90-day Amazon exclusivity for 70% royalty up
  to $9.99)
- ISBN: free KDP ISBN vs. your own (the free one is fine for most
  authors, but a paid ISBN gives you portability if you later list on
  IngramSpark or Apple Books)
- Print-on-demand vs. order short runs
- Pre-order strategy (Kindle supports pre-order; KDP print does not)
- Newsletter / email automation for the visual companion PDF
- Goodreads pre-launch giveaway
