---
name: kdp-book-launch
description: Use when the user wants to take a manuscript through a full KDP (Amazon Kindle Direct Publishing) launch — editorial review, AI-generated chapter illustrations, cover art with baked-in title text, EPUB + paperback PDF + hardcover PDF builds, full cover wraps, bonus visual companion PDF, social media graphic pack, and launch collateral (KDP listing, press release, ads, A+ Content). Works for thrillers, memoirs, nonfiction, fiction — the framework is genre-agnostic.
---

# kdp-book-launch

End-to-end runbook for taking a finished manuscript through an Amazon KDP launch. The skill wraps a parameterized Python toolkit, prompt templates, and methodology docs that survived a real production launch (the "Jeremy Christ" thriller — see *Reference Implementation* at the bottom).

> **Built on Get Shit Done (GSD)** by [TÂCHES](https://github.com/gsd-build) — https://github.com/gsd-build/get-shit-done. This skill assumes GSD's `/gsd-*` slash commands and `.planning/` artifact structure are available. If they aren't, install GSD first: `npx get-shit-done-cc@latest`. The framework architecture, parallel subagent dispatch, atomic-commit guarantees, and five-command workflow loop all come from GSD. This skill is a domain-specific extension that plugs into them.

This skill ORCHESTRATES — it does the editorial polish, the AI image generation, the cover production, the launch-collateral packaging. It does NOT itself build the EPUB / PDF. For that it shells out to the [`kdp-book-generator`](https://www.npmjs.com/package/kdp-book-generator) Node CLI (which the user has a local checkout of at `~/Projects/kdp-book-generator/`).

---

## When to load this skill

Trigger phrases:
- "launch a book on KDP", "publish on Amazon", "ship the manuscript"
- "format manuscript for Amazon", "build the EPUB", "make the print PDF"
- "generate chapter illustrations", "make chapter art", "illustrate my book"
- "make a book cover", "generate cover art", "design the cover wrap"
- "build a visual companion", "lead magnet PDF", "subscriber bonus"
- "social pack for the book launch", "Instagram graphics for the book"
- "write the KDP listing", "Amazon book description", "A+ Content"
- "press release for my book", "launch collateral"

DO NOT load this skill for:
- Mid-draft writing (use `prose-writing` / `prose-critique`)
- General book brainstorming (use `brainstorming` / `story-architecture`)
- One-off image generation that isn't part of a book

---

## The 5-phase workflow

Detailed checklist at `references/phase-checklist.md`. Each phase has author-approval gates. The hard-cost gate is Phase 2 (OpenRouter API spend on chapter images).

**Driving this via GSD:** initialize the project with `/gsd-new-project` (creates `.planning/PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md` with one roadmap phase per phase below). From there, the loop is `/gsd-discuss-phase N` → `/gsd-plan-phase N` → `/gsd-execute-phase N` → `/gsd-verify-work N` per phase, or `/gsd-autonomous` to run end-to-end with parallel subagent dispatch and atomic per-task commits. The author-approval gates in each phase below are the natural `/gsd-verify-work` checkpoints.

```
PHASE 1 — Manuscript Lock          (editorial read + canon audit, $0)
   ↓
PHASE 2 — Chapter Illustrations    (per-chapter AI image gen, ~$5-10)
   ↓
PHASE 3 — Cover Production         (front + back + wrap, ~$1-2)
   ↓
PHASE 4 — Build & Compile          (EPUB + paperback + hardcover, $0)
   ↓
PHASE 5 — KDP Launch Prep          (listing + companion + social + ads, $0)
```

Total realistic launch cost in API spend: **$10-15**. Hard cap: $20.

---

## Required ingredients (from the user)

1. **Manuscript markdown** — a single `.md` file with the manuscript. Has H1 title at top and `## CHAPTER N: Title`, `## PROLOGUE`, `## EPILOGUE` H2 headers throughout.
2. **Reference photos of the protagonist** — 3-5 high-resolution photos showing the protagonist from different angles. Drop these in a `ref_images/` folder. The skill anchors the AI image generation off these.
3. **OpenRouter API key** — `export OPENROUTER_API_KEY=sk-or-v1-...` in the user's shell. The skill bills against this for AI image generation.

---

## Optional ingredients

1. **Book canon doc** — a Dramatis Personae and/or appendix in the manuscript, or a separate worldbuilding doc. Used in the canon audit step.
2. **Prior books / brand assets** — if this isn't the author's first book, the cover prompts and social pack benefit from cross-promo references to the prior cover art.
3. **Comp titles** — a list of three to five book titles your book is "for fans of." Used heavily in the KDP listing and Amazon Ads collateral.

---

## Toolchain requirements

The skill ships Python 3 scripts that depend on:

**Python libraries (preinstalled on this system, do NOT pip install — PEP 668 blocks it):**
- `pypdf` (for PDF metadata postprocessing)
- `PIL` / Pillow (for visual companion, cover wrap, social pack)
- Standard library only otherwise

If a library is missing on a fresh system, install via pipx or a venv. Do NOT use `pip install --user` — the user has PEP 668 protection enabled.

**Brew-installable tools (verify before Phase 4):**
```bash
brew install pandoc imagemagick epubcheck
```

- **pandoc** — converts markdown to HTML for `build_print_pdf.py`
- **imagemagick** — used by `make_bw_variants.py` for grayscale conversion
- **epubcheck** — validates the EPUB before KDP submission

**Other tools:**
- **Google Chrome / Chromium** — `build_print_pdf.py` shells out to headless Chrome to render the print PDF. The skill defaults to the macOS Chrome path; override with `--chrome` or `$CHROME_BIN`.
- **kdp-book-generator (Node)** — local checkout at `~/Projects/kdp-book-generator/`. The skill shells out to it for the actual EPUB build.

---

## The launch config

A single JSON file at the project root drives every script in the skill. Copy `templates/launch_config.json.template` to `_launch_config.json` in the user's project and fill in the placeholders.

Schema highlights:
- `title`, `subtitle`, `author`, `year`, `language`
- `keywords` — array of 7 strings (KDP limit)
- `protagonist.canonical_ref` — single reference image (default)
- `protagonist.strong_refs` — 3-5 references (used when one image isn't enough to anchor identity)
- `chapters[]` — one entry per chapter: `slug`, `display_title`, `manuscript_header`, `has_protagonist`, optional `use_strong_refs`, optional `custom_refs`
- `cover` — paths to generated cover art, spine colors, spine text
- `social` — quotes, comp titles, premise text used by the social pack
- `pdf_metadata` — passed through to `postprocess.py`

EVERY script in `scripts/` reads from this config. You shouldn't need to edit any script directly to launch a book — edit the JSON.

---

## Phase-by-phase procedure

### PHASE 1 — Manuscript Lock

Goal: a frozen manuscript ready for typesetting.

1. **Verify the manuscript shape.** Open the `.md` file. Confirm:
   - One H1 title at the very top (will be stripped by `build_book_md.py`)
   - Optional tagline / italic lines under the H1 (will be replaced by config)
   - `## PROLOGUE`, `## CHAPTER N: Title`, `## EPILOGUE`, `## DRAMATIS PERSONAE` H2 headers
   - Optional `### Location, Date, Time` H3 location blocks under each chapter header (the build script inserts the chapter image after these)

2. **Initialize the config.**
   ```bash
   cp ~/.claude/skills/kdp-book-launch/templates/launch_config.json.template ./_launch_config.json
   cp ~/.claude/skills/kdp-book-launch/templates/book_config.json.template  ./_book_config.json
   ```
   Edit `_launch_config.json`: fill `title`, `subtitle`, `author`, `year`, `keywords`, `chapters[]`, `protagonist.canonical_ref`. Don't fill cover paths yet — those come in Phase 3.

3. **Run an editorial read.** Spawn a subagent with the prompt template:
   ```
   Read templates/editorial-prompt.md.template and follow its
   methodology against {project}/Manuscript.md. Output to
   .planning/notes/MANUSCRIPT-NOTES.md.
   ```
   See `references/editorial-review-methodology.md` for what to look for. Expect 50-80 findings classified HIGH / MEDIUM / LOW.

4. **GATE** — author reviews HIGHs and approves a fix list.

5. **Apply fixes** to the manuscript. Use a `MSS-NN` git-commit prefix per pass so the revision history is legible.

6. **Optional but recommended:** run a canon audit per dimension (religion, family, timeline). See `references/canon-audit-methodology.md`.

7. **Commit the locked manuscript.** Tag it `manuscript-locked-v1` so you can return.

### PHASE 2 — Chapter Illustrations

Goal: one finished color illustration per chapter.

1. **Drop reference photos** into `ref_images/`. Update `protagonist.canonical_ref` and `protagonist.strong_refs` in `_launch_config.json`.

2. **Write one prompt per chapter** to `prompts/chapters/{slug}.txt`. Use `templates/chapter-image-prompt.txt.template` as the starting structure. The slug must match `chapters[].slug` in the config.

   See `references/prompt-structure-guide.md` for the 6-block structure (SUBJECT / SCENE / LIGHTING / COMPOSITION / NEGATIVE / STYLE) and `references/aesthetic-libraries.md` for genre-specific STYLE blocks.

3. **Generate one TEST image first:**
   ```bash
   export OPENROUTER_API_KEY=sk-or-v1-...
   python3 ~/.claude/skills/kdp-book-launch/scripts/generate_chapter_images.py {first-slug}
   ```
   Cost: ~$0.14. **GATE** — does the protagonist look like the reference? If no, see `references/cover-regen-troubleshooting.md` ("model added hair to a bald subject" etc).

4. **Generate all chapters:**
   ```bash
   python3 ~/.claude/skills/kdp-book-launch/scripts/generate_chapter_images.py --all --regen-log
   ```
   The script is idempotent — re-running skips existing files. Use `--force` to rebuild.

5. **Likeness audit.** Follow `references/likeness-audit-methodology.md`. Output to `.planning/notes/IMAGE-AUDIT.md`. PASS / BORDERLINE / MISS each chapter.

6. **Regenerate misses.** For each MISS, set `use_strong_refs: true` on that chapter in the config and run `generate_chapter_images.py {slug} --force`.

7. **Build B&W variants for print:**
   ```bash
   python3 ~/.claude/skills/kdp-book-launch/scripts/make_bw_variants.py
   ```
   Requires `brew install imagemagick`. Outputs to `images/chapters-bw/`.

### PHASE 3 — Cover Production

Goal: production-ready front, back, and wrap PDFs.

1. **Write the cover prompts.** Use `templates/front-cover-prompt.txt.template` and `templates/back-cover-prompt.txt.template`. Save to `prompts/Covers/front-prompt.txt` and `prompts/Covers/back-prompt.txt`.

   Critical: do NOT bake title text or blurb text INTO the AI prompt as something to render. The model can't reliably render readable text. Generate ART ONLY; overlay typography later.

2. **Generate covers** (expect 4-8 iterations each):
   ```bash
   python3 ~/.claude/skills/kdp-book-launch/scripts/generate_front_cover.py
   python3 ~/.claude/skills/kdp-book-launch/scripts/generate_back_cover.py
   ```
   Each run produces 1-2 images in `covers/`. Iterate by editing the prompt and re-running, or pass `--prompt-file` to use an alt prompt.

3. **GATE** — author picks the best front + best back. Save as `covers/front-cover-art.png` and `covers/back-cover-art.png` (or update the paths in `_launch_config.json`).

4. **Overlay typography** (title, tagline, author byline, blurb, ISBN barcode placeholder) in a vector editor — Affinity Publisher, Adobe InDesign, Figma, or Canva. Export as `covers/front-cover.jpg` and `covers/back-cover.jpg` at 300 DPI.

5. **Build the wrap PDFs** once you know the interior page count (you'll know this after Phase 4 first pass; for now estimate or set to 0 and rebuild later):
   ```bash
   python3 ~/.claude/skills/kdp-book-launch/scripts/compose_cover_wrap.py --page-count 276
   ```
   Add `--color-interior` if the paperback uses color paper (rare for fiction).

6. **GATE** — author opens the wrap PDFs at full size. Spine width correct? Front-back-spine layout flows? Anything text-clipping at bleed?

### PHASE 4 — Build & Compile

Goal: shippable EPUB + paperback PDF + hardcover PDF.

1. **Build markdown for COLOR (EPUB):**
   ```bash
   python3 ~/.claude/skills/kdp-book-launch/scripts/build_book_md.py
   ```
   Outputs `_build_book.md` with YAML frontmatter, Title page, Copyright page, chapter images inserted, headings promoted/demoted for kdp-book-generator.

2. **Run kdp-book-generator** (the separate Node CLI) for EPUB:
   ```bash
   cd ~/Projects/kdp-book-generator
   node dist/cli/index.js generate /path/to/_build_book.md --format kindle --output /path/to/dist/book.epub
   ```
   (`--format kindle` is what actually produces an EPUB — see `node dist/cli/index.js generate --help` for the rest of the flags.)

3. **Embed chapter images into the EPUB** (kdp-book-generator references them but doesn't bundle):
   ```bash
   python3 ~/.claude/skills/kdp-book-launch/scripts/epub_embed_images.py dist/book.epub
   ```

4. **Validate the EPUB:**
   ```bash
   epubcheck dist/book.epub
   ```
   Zero errors required for KDP submission. See `references/cover-regen-troubleshooting.md` for common epubcheck error fixes.

5. **Build markdown for PRINT (B&W):**
   ```bash
   python3 ~/.claude/skills/kdp-book-launch/scripts/build_book_md.py --print
   ```
   Same outputs as step 1 but with B&W images swapped in.

6. **Build paperback and hardcover PDFs:**
   ```bash
   python3 ~/.claude/skills/kdp-book-launch/scripts/build_print_pdf.py dist/book-paperback.pdf
   python3 ~/.claude/skills/kdp-book-launch/scripts/build_print_pdf.py dist/book-hardcover.pdf
   ```
   These use headless Chrome under the hood — requires Chrome/Chromium installed.

7. **Set PDF metadata:**
   ```bash
   python3 ~/.claude/skills/kdp-book-launch/scripts/postprocess.py dist/book-paperback.pdf dist/book-hardcover.pdf
   ```

8. **GATE** — author opens each file end-to-end. Page breaks correct? Images embedded? No widows/orphans? Page count matches what was passed to `compose_cover_wrap.py`? If not, go back to Phase 3 step 5 with the corrected page count.

### PHASE 5 — KDP Launch Prep

Goal: everything needed to publish + market the book.

1. **Build the visual companion PDF:**
   ```bash
   python3 ~/.claude/skills/kdp-book-launch/scripts/build_visual_companion.py
   ```
   Output: a Letter-size PDF with the cover, every chapter illustration, and captions extracted from the prompts. Use as a free newsletter giveaway or press-kit asset.

2. **Build the social media graphic pack:**
   ```bash
   python3 ~/.claude/skills/kdp-book-launch/scripts/build_social_pack.py
   ```
   Output: 30-50 JPGs across 6 platforms (Instagram square/story, Facebook, Twitter post/header, LinkedIn, Pinterest). Copy strings (quotes, premise, comp titles) come from `social.*` in `_launch_config.json`.

   **Recipe customization:** the script ships 6-8 default recipes (cover-card, three quote cards, premise card, comp-titles card, optional social-proof card). If the defaults don't fit the genre (e.g., a children's book wouldn't use the "FROM THE BESTSELLING THRILLER..." pattern), edit the `recipes` list in `build_social_pack.py`. The visual primitives at the top of the file (cover_card, quote_card, premise_card, etc.) are reusable building blocks.

3. **Draft the KDP listing.** Copy `templates/kdp-listing.md.template` to `.planning/kdp-listing.md` and fill in:
   - Title / subtitle / series
   - Description (4000 char HTML block)
   - About the Author (2400 char HTML block)
   - From the Author (4000 char HTML block, optional but recommended)
   - 7 keywords
   - 2 BISAC categories
   - Pricing across formats

4. **Draft launch collateral** in `.planning/launch/`. Suggested files (the user can adapt the structure from the reference implementation listed at the bottom of this doc):
   - `press-release.md` — PRNewswire / direct press outreach
   - `subscriber-email.md` — email blast to the author's list
   - `blog-post.md` — long-form launch post for the author's blog
   - `goodreads.md` — Goodreads author dashboard / Q&A copy
   - `a-plus-content.md` — KDP A+ Content module copy
   - `amazon-ads.md` — Sponsored Products ad headlines + descriptions
   - `bonus-pdf-delivery-email.md` — autoresponder for the visual companion

5. **Upload to KDP:**
   - Kindle eBook: `dist/book.epub` + `covers/front-cover.jpg` (upscaled to 1600x2560)
   - Paperback: `dist/book-paperback.pdf` interior + `dist/{book}-paperback-wrap.pdf` cover
   - Hardcover: `dist/book-hardcover.pdf` interior + `dist/{book}-hardcover-wrap.pdf` cover

6. **GATE** — author hits Submit on each format. KDP review is usually 24-72 hours.

---

## Common failure modes and recoveries

A condensed index — full detail in `references/cover-regen-troubleshooting.md`.

| Symptom | Fix |
|---|---|
| Model adds hair to a bald protagonist | Set `use_strong_refs: true` on that chapter, regen with `--force` |
| Text appearing in image where it shouldn't | Strengthen NEGATIVE block; rename text-associated objects ("journal" not "Bible") |
| Wrong subject (model drew a stranger) | Verify `has_protagonist` flag; populate `custom_refs` for non-protagonist chapters |
| Face in shadow / unrecognizable | Add "face must be clearly lit and recognizable" to LIGHTING block |
| Composition leaves no negative space for title | Restate composition explicitly: "subject in LEFT HALF; RIGHT THIRD must be quiet/dark" |
| Wrong period clothing | Add explicit date to SCENE block |
| epubcheck fails on `OPF-014: Image not found` | Re-run `epub_embed_images.py` |
| Cover spine text won't fit | Edit `compose_cover_wrap.py` font auto-sizer bottom, or shorten the spine title |
| Total OpenRouter bill creeping past $20 | The chapter generator hard-caps at 3 retries per slug. Cover generators are single-shot. Check the OpenRouter dashboard. |

---

## Cost expectations

OpenRouter Gemini 3 Pro Image Preview, observed pricing as of 2026:

- **~$0.14 per image** (the published rate is $0.04 — production runs consistently bill closer to $0.14 in our experience; budget against the higher number)
- 20 chapters x 1.5 attempts each ≈ **$4.20**
- Front cover x 4 iterations ≈ **$0.56**
- Back cover x 4 iterations ≈ **$0.56**
- **Realistic launch budget: $10-15**. Hard cap: $20. If you hit $20, stop and audit which step is over-iterating.

Everything else (editorial reads via Claude subscription, PDF compilation, social pack via PIL) is $0 in marginal cost.

---

## What's in this skill

```
~/.claude/skills/kdp-book-launch/
├── SKILL.md                                   <-- you are here
├── scripts/
│   ├── _config.py                             shared config loader
│   ├── generate_chapter_images.py             AI chapter art (Gemini)
│   ├── generate_front_cover.py                AI front cover (Gemini)
│   ├── generate_back_cover.py                 AI back cover (Gemini)
│   ├── make_bw_variants.py                    color → B&W for print
│   ├── build_book_md.py                       manuscript → kdp-book-generator input
│   ├── epub_embed_images.py                   bundle images into KDP EPUB
│   ├── build_print_pdf.py                     pandoc → headless Chrome → PDF
│   ├── compose_cover_wrap.py                  paperback + hardcover wrap PDFs
│   ├── build_visual_companion.py              bonus PDF (newsletter giveaway)
│   ├── build_social_pack.py                   30+ social media JPGs
│   └── postprocess.py                         PDF metadata
├── templates/
│   ├── launch_config.json.template            the central config
│   ├── book_config.json.template              kdp-book-generator config
│   ├── chapter-image-prompt.txt.template      6-block prompt structure
│   ├── front-cover-prompt.txt.template
│   ├── back-cover-prompt.txt.template
│   ├── editorial-prompt.md.template           subagent prompt for editorial read
│   └── kdp-listing.md.template                Amazon listing copy structure
└── references/
    ├── phase-checklist.md                     5-phase task checklist
    ├── kdp-specifications.md                  KDP trim/spine/bleed spec sheet
    ├── prompt-structure-guide.md              how to write a chapter image prompt
    ├── cover-regen-troubleshooting.md         when image gen goes sideways
    ├── likeness-audit-methodology.md          how to audit AI image likeness
    ├── canon-audit-methodology.md             family/religion canon audit
    ├── editorial-review-methodology.md        how to run the editorial read
    └── aesthetic-libraries.md                 genre-by-genre STYLE block presets
```

---

## Quick-start command summary

```bash
# Phase 1 - manuscript lock
cp ~/.claude/skills/kdp-book-launch/templates/launch_config.json.template ./_launch_config.json
cp ~/.claude/skills/kdp-book-launch/templates/book_config.json.template  ./_book_config.json
# edit both, run editorial read via subagent

# Phase 2 - chapter illustrations
export OPENROUTER_API_KEY=sk-or-v1-...
python3 ~/.claude/skills/kdp-book-launch/scripts/generate_chapter_images.py --all --regen-log
python3 ~/.claude/skills/kdp-book-launch/scripts/make_bw_variants.py

# Phase 3 - cover production
python3 ~/.claude/skills/kdp-book-launch/scripts/generate_front_cover.py
python3 ~/.claude/skills/kdp-book-launch/scripts/generate_back_cover.py
# overlay typography in a vector editor
python3 ~/.claude/skills/kdp-book-launch/scripts/compose_cover_wrap.py --page-count 276

# Phase 4 - build & compile
python3 ~/.claude/skills/kdp-book-launch/scripts/build_book_md.py
node ~/Projects/kdp-book-generator/dist/cli/index.js generate _build_book.md --format kindle --output dist/book.epub
python3 ~/.claude/skills/kdp-book-launch/scripts/epub_embed_images.py dist/book.epub
epubcheck dist/book.epub
python3 ~/.claude/skills/kdp-book-launch/scripts/build_book_md.py --print
python3 ~/.claude/skills/kdp-book-launch/scripts/build_print_pdf.py dist/book-paperback.pdf
python3 ~/.claude/skills/kdp-book-launch/scripts/build_print_pdf.py dist/book-hardcover.pdf
python3 ~/.claude/skills/kdp-book-launch/scripts/postprocess.py dist/*.pdf

# Phase 5 - launch prep
python3 ~/.claude/skills/kdp-book-launch/scripts/build_visual_companion.py
python3 ~/.claude/skills/kdp-book-launch/scripts/build_social_pack.py
cp ~/.claude/skills/kdp-book-launch/templates/kdp-listing.md.template .planning/kdp-listing.md
# fill in .planning/kdp-listing.md and draft .planning/launch/*.md
# upload to https://kdp.amazon.com
```

---

## Reference implementation

The full production run that this skill was extracted from lives at `~/Projects/JeremyChrist/` (a religious-conspiracy thriller). When you need to see "how does this look when it works":

- A worked launch_config: see the `_book_config.json` and the chapter slug map at the top of `JeremyChrist/build_book_md.py`
- A 24-finding editorial read: `JeremyChrist/.planning/notes/MANUSCRIPT-NOTES.md`
- A worked likeness audit: `JeremyChrist/.planning/notes/IMAGE-AUDIT.md`
- A worked religion-canon audit: `JeremyChrist/.planning/notes/RELIGION-AUDIT.md`
- A worked KDP listing: `JeremyChrist/.planning/kdp-listing.md`
- Worked launch collateral: `JeremyChrist/.planning/launch/*.md`
- 21 worked chapter prompts: `JeremyChrist/prompts/chapters/*.txt`
- Worked cover prompts: `JeremyChrist/prompts/Covers/front-prompt.txt`, `back-prompt.txt`

These are PROJECT-SPECIFIC artifacts — they're the worked examples of the pattern, not the pattern itself. Don't copy from them verbatim into a new project. Use the templates in this skill, then look at the JeremyChrist files only to see the level of specificity that worked.
