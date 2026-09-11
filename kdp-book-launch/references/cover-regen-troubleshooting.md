# Cover & Image Regen Troubleshooting

When OpenRouter Gemini 3 Pro Image Preview produces something that
doesn't match your prompt, the fix is almost always one of the patterns
below. This doc indexes the recoveries we used in production.

---

## Symptom: model added hair to a bald subject

**Cause:** single reference image not enough to anchor identity. The
SUBJECT block's "completely bald" instruction is being overridden by
the model's stock priors about thriller protagonists having hair.

**Fix:** use the `use_strong_refs` flag in `_launch_config.json`:

```json
{
  "slug": "ch12-key-scene",
  "use_strong_refs": true
}
```

And populate `protagonist.strong_refs` with 3-5 reference images
showing the bald head from different angles:

```json
"protagonist": {
  "canonical_ref": "ref_images/jeremy1.png",
  "strong_refs": [
    "ref_images/jeremy1.png",
    "ref_images/jeremy4.png",
    "ref_images/jeremy5.png"
  ]
}
```

Then regenerate that one chapter with `--force`:

```
python3 generate_chapter_images.py ch12-key-scene --force
```

---

## Symptom: text / writing / inscriptions appearing where they shouldn't

**Cause:** the SCENE block named an object with strong text-associations
(Bible, newspaper, manuscript, signpost).

**Fix:** rename the object to something less literal. "Ancient leather-
bound journal" instead of "Bible." "Folded parchment" instead of
"document." Then strengthen the NEGATIVE block:

```
NEGATIVE: Absolutely no text anywhere in the image. No inscriptions,
no readable writing, no labels, no signage. The journal is closed or
its pages blurred. No Latin, no English, no typography of any kind.
```

If text still appears, the model is responding to "Bible/manuscript/
letter" as a concept — try moving NEGATIVE before SCENE in the prompt
order.

---

## Symptom: wrong subject (model drew a generic person)

**Cause:** the canonical reference image isn't being attached, or the
chapter is configured `has_protagonist: false` but the prompt still
implies a protagonist.

**Fix:** check `_launch_config.json` for the chapter entry:

```json
{
  "slug": "ch04-antagonist-pov",
  "has_protagonist": false,
  "custom_refs": ["ref_images/antagonist1.png"]
}
```

If the chapter shows a DIFFERENT character (an antagonist POV chapter),
use `custom_refs` to attach reference images of THAT character.

If the chapter shows no people at all, set `has_protagonist: false`
and remove any "the protagonist..." language from the SCENE block.

---

## Symptom: face in shadow / unrecognizable

**Cause:** the LIGHTING block was too moody and didn't explicitly
require the face to be lit.

**Fix:** always include this line in the LIGHTING block:

```
His face must be clearly lit and recognizable. Do not hide
identity in shadow.
```

Move it to its own paragraph so the model treats it as a hard constraint.

---

## Symptom: subject in wrong part of the frame for typography overlay

**Cause:** Gemini follows compositional hints but needs them stated
twice. Saying "subject in the left half" once leaves the right side as
contested space.

**Fix:** state both sides of the composition explicitly:

```
COMPOSITION: Subject placed in the LEFT HALF. The RIGHT THIRD must be
quieter and darker — soft shadow, deep falloff, no faces, no high-
contrast objects. Held quiet for title typography overlay.
```

For cover work specifically, also use the back-cover technique of
mentioning what the "quiet zone" will hold:

```
The RIGHT THIRD will receive the book blurb and ISBN barcode in
post-production. Keep it darker than the left side.
```

---

## Symptom: wrong period / wardrobe / setting

**Cause:** the SCENE block didn't pin a date.

**Fix:** add an explicit date. Dates anchor wardrobe, technology,
architecture, and lighting in ways no other instruction can:

```
SCENE: Chapter 8, "The Newberry Cipher." Chicago, Illinois,
November 14, 2020, 2:30 AM. {NAME}...
```

For historical scenes, also name the architectural era:

```
SCENE: The Vatican Secret Archives, late Renaissance vaulted stone
construction, 17th-century iron fittings. The lights are modern
LED panels in older sconces.
```

---

## Symptom: composition has too many people

**Cause:** the SCENE block used "they" or referred to companions
without specifying who's on-camera.

**Fix:** in the SCENE block, explicitly state how many people are
visible and which ones:

```
TWO people visible: {NAME} (foreground, center) and his daughter
{NAME} (background, blurred). No one else in frame.
```

For solo portraits:

```
ONE person visible: {NAME} alone in the room. No other figures.
```

---

## Symptom: cover came out perfect but text won't fit

**Cause:** the composition put the subject's head in the top third
where the title needs to go, or put their feet across the bottom
where the author byline sits.

**Fix:** regenerate the cover with explicit "TOP THIRD MUST BE
EMPTY" or "BOTTOM 20% MUST BE QUIET" in the COMPOSITION block. Move
this to its own short paragraph for emphasis.

If you only have one good cover image and don't want to regen,
overlay your title typography on a semi-transparent dark band rather
than on the raw photo. Acceptable for thrillers; less elegant for
literary fiction.

---

## Symptom: hardcover spine text is too small

**Cause:** the spine width for a thin book (<150 pages) doesn't fit
the title font the compose_cover_wrap script picked.

**Fix:** the script auto-sizes the spine font but bottoms out at 8pt.
For very thin books, edit the title to be shorter on the spine (drop
a subtitle, abbreviate). For very thick books (>500 pages), bump the
script's target_text_pct from 0.55 to 0.70.

---

## Symptom: PDF interior has weird page breaks / orphans

**Cause:** Chrome headless respects most CSS page-break properties
but is conservative about widow/orphan control on tight pages.

**Fix:** in `build_print_pdf.py`'s CSS, increase the orphans/widows
counts from 3 to 4. Or add `page-break-inside: avoid` to specific
elements (figures, blockquotes, ASCII art).

If a chapter's first paragraph keeps falling at the bottom of a
page, increase the `margin-top` on `h1 + p` so the first paragraph
gets pushed.

---

## Symptom: EPUB validation fails on `epubcheck`

**Common errors:**

| Error | Fix |
|-------|-----|
| `OPF-014: Image not found in package` | Run `epub_embed_images.py` again |
| `RSC-005: namespace not declared` | kdp-book-generator version mismatch; pin to ^1.x |
| `CSS-018: position: fixed not allowed` | Edit CSS in your kdp-book-generator config |
| `OPF-049: 'cover' not found` | Make sure the EPUB has a cover image at `OEBPS/cover.jpg`; the kdp-book-generator output should include this by default, but if missing, manually drop it in and add a manifest entry |
| `HTM-004: irregular DOCTYPE` | Source markdown is producing raw HTML that pandoc passed through — strip it before build |

---

## Symptom: total bill exceeded budget

**Cause:** retries on a single chapter going past 3 attempts, or a
loop running unattended.

**Fix:**
- The chapter generator hard-caps at 3 attempts per slug
- The cover generators are single-shot per invocation
- If you're iterating manually, watch the OpenRouter dashboard at
  https://openrouter.ai/activity
- Each Gemini 3 Pro Image call costs ~$0.14 in production (NOT
  $0.04 as published)
- A 20-chapter book at 2 attempts each = ~$5.60
- 5 cover regen iterations (front + back) = ~$1.40

Total realistic launch budget for art: $20 hard cap, $10 typical.
