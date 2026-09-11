# 5-Phase Launch Checklist

A copy-pasteable task list. Each phase has gates the author should
explicitly approve before money is spent on the next phase. The hard
cost gate is Phase 2 (chapter image generation) where the OpenRouter
bill is real.

---

## PHASE 1 — Manuscript Lock

Goal: a frozen manuscript ready for typesetting. After this phase, the
manuscript should not change again except for typo fixes.

- [ ] Manuscript exists as a single markdown file (e.g. `Manuscript.md`)
      with one H1 title at the top and `## CHAPTER N:` / `## PROLOGUE`
      / `## EPILOGUE` H2 headers throughout
- [ ] Copy `templates/launch_config.json.template` to project root as
      `_launch_config.json` and fill in: title, subtitle, author, year,
      keywords, chapters[]
- [ ] Copy `templates/book_config.json.template` to project root as
      `_book_config.json` (this is for kdp-book-generator)
- [ ] Editorial read: spawn a subagent using
      `templates/editorial-prompt.md.template` against the manuscript;
      output goes to `.planning/notes/MANUSCRIPT-NOTES.md`
- [ ] **GATE:** author reviews HIGH findings and decides which to fix
- [ ] Apply HIGH fixes
- [ ] Run one more editorial pass on the fixed manuscript (only the
      changed sections) to verify the fixes didn't introduce new
      contradictions
- [ ] Commit the locked manuscript with a tag like `manuscript-locked-v1`

Cost: $0 (LLM editorial via your existing subscription).

---

## PHASE 2 — Chapter Illustrations

Goal: one finished color illustration per chapter, ready to embed.

- [ ] Collect 3-5 high-quality reference photos of the protagonist
      into `ref_images/` (canonical headshot + 2-4 variations covering
      different angles / expressions / lighting)
- [ ] Write one prompt per chapter into `prompts/chapters/{slug}.txt`
      using `templates/chapter-image-prompt.txt.template` as the
      starting structure (SUBJECT / SCENE / LIGHTING / COMPOSITION /
      NEGATIVE / STYLE blocks)
- [ ] Verify `$OPENROUTER_API_KEY` is set
- [ ] Generate one test image FIRST:
      `python3 generate_chapter_images.py {first-slug}`
- [ ] **GATE:** author looks at the test image; does the protagonist
      actually look like the reference? If no, see
      `references/cover-regen-troubleshooting.md`
- [ ] Generate all chapter images:
      `python3 generate_chapter_images.py --all --regen-log`
- [ ] Run a likeness audit using `references/likeness-audit-methodology.md`
- [ ] Regenerate any flagged chapters (see troubleshooting doc for
      strong-refs / custom-refs patterns)
- [ ] Generate B&W variants for print:
      `python3 make_bw_variants.py`
- [ ] **GATE:** author approves the final image set

Cost: ~$0.14 per image x (N chapters x 1-3 attempts each) = roughly
$3-$10 for a 20-chapter book in our production runs. Set a mental
budget of $20 and stop if you hit it.

---

## PHASE 3 — Cover Production

Goal: production-ready cover artwork (front, back, wrap PDF).

- [ ] Write front-cover prompt to `prompts/Covers/front-prompt.txt`
      using `templates/front-cover-prompt.txt.template`
- [ ] Write back-cover prompt to `prompts/Covers/back-prompt.txt`
- [ ] Generate front cover art (will iterate):
      `python3 generate_front_cover.py`
- [ ] Generate back cover art:
      `python3 generate_back_cover.py`
- [ ] **GATE:** author picks the best front and best back from any
      iterations; saves them as `covers/front-cover-art.png` and
      `covers/back-cover-art.png`
- [ ] Overlay typography (title, tagline, author byline, blurb, ISBN
      barcode placeholder) in a vector editor (Affinity Publisher,
      Adobe InDesign, Figma, Canva). The AI never gets text right —
      this step is non-negotiable.
- [ ] Export overlaid covers as `covers/front-cover.jpg` and
      `covers/back-cover.jpg` (high-quality JPG, RGB, 300+ DPI)
- [ ] Build the full wrap PDFs once you know your page count:
      `python3 compose_cover_wrap.py --page-count {N}`
- [ ] **GATE:** author checks the wrap PDFs at full size — does the
      spine width look right? Does the front-back-spine layout flow?
      Anything text-clipped at the bleed line?

Cost: ~$0.14 x 4-8 cover regen attempts each = $1-$2.

---

## PHASE 4 — Build & Compile

Goal: shippable EPUB, paperback PDF, and hardcover PDF.

- [ ] Build the markdown for COLOR (EPUB) output:
      `python3 build_book_md.py`
- [ ] Run kdp-book-generator (local checkout at `~/Projects/kdp-book-generator`) to produce EPUB:
      `node ~/Projects/kdp-book-generator/dist/cli/index.js generate _build_book.md --format kindle --output dist/book.epub`
- [ ] Embed chapter images into EPUB:
      `python3 epub_embed_images.py dist/book.epub`
- [ ] Validate EPUB:
      `epubcheck dist/book.epub` (brew install epubcheck)
- [ ] Build the markdown for PRINT (B&W) output:
      `python3 build_book_md.py --print`
- [ ] Build the paperback interior PDF:
      `python3 build_print_pdf.py dist/book-paperback.pdf`
- [ ] Build the hardcover interior PDF (same content, but separate
      file for spine math):
      `python3 build_print_pdf.py dist/book-hardcover.pdf`
- [ ] Set PDF metadata on all three:
      `python3 postprocess.py dist/book-paperback.pdf dist/book-hardcover.pdf`
- [ ] **GATE:** author opens each file end-to-end. Page breaks correct?
      Images embedded? Image captions readable? No widow/orphan
      paragraphs? Page count matches what was passed to compose_cover_wrap?
- [ ] If page count changed: rerun `compose_cover_wrap.py` with the new
      number

Cost: $0 (pure local compilation).

---

## PHASE 5 — KDP Launch Prep

Goal: everything you need to paste into KDP and into your launch comms.

- [ ] Fill in `templates/kdp-listing.md.template` with this book's copy
      and save to `.planning/kdp-listing.md`
- [ ] Build the visual companion PDF for newsletter / press kit:
      `python3 build_visual_companion.py`
- [ ] Build the social media graphic pack:
      `python3 build_social_pack.py`
- [ ] Draft launch collateral (see `kdp-specifications.md` for what
      each one is). Suggested files in `.planning/launch/`:
  - `press-release.md` — for PRNewswire / direct press outreach
  - `subscriber-email.md` — for your email list
  - `blog-post.md` — for your own blog
  - `goodreads.md` — Goodreads author dashboard updates
  - `a-plus-content.md` — KDP A+ Content slot copy
  - `amazon-ads.md` — Sponsored Products ads headlines + descriptions
  - `bonus-pdf-delivery-email.md` — autoresponder for the visual companion
- [ ] Upload to KDP:
  - Kindle eBook: `dist/book.epub` + thumbnail of `covers/front-cover.jpg`
  - Paperback: `dist/book-paperback.pdf` interior + `dist/{book}-paperback-wrap.pdf` cover
  - Hardcover: `dist/book-hardcover.pdf` interior + `dist/{book}-hardcover-wrap.pdf` cover
- [ ] Paste KDP listing copy fields from `kdp-listing.md`
- [ ] Set 7 keywords + 2 BISAC categories
- [ ] **GATE:** author hits "Submit for review" on each format

Cost: $0 in tools (KDP is free to publish; you pay only when readers buy).
