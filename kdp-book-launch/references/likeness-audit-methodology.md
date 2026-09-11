# Likeness Audit Methodology

After generating every chapter image, do a quick audit to catch
likeness drift before you ship.

---

## When to run

Run an audit AFTER the first complete generation pass (with
`--all`) and BEFORE you build the PDF / EPUB. Audit before regen,
not after — it's cheaper to catch all the misses in one pass and
fix them together than to keep re-running individual chapters.

---

## What you need

- The reference photo(s) you used for the protagonist
- A short profile description of the protagonist's distinguishing
  features (e.g., "completely bald, fair skin, blue eyes, mid-40s,
  broad-shouldered solid build")
- The generated images in `{color_images_dir}` (e.g., `images/chapters/`)

---

## Methodology — one image at a time

For each generated image, write three lines:

1. **Should show protagonist?** Yes / No.
   - Yes = the chapter is from the protagonist's POV or features them
     visibly
   - No = the chapter is an antagonist POV, an object close-up, or a
     landscape

2. **Verdict.** PASS / BORDERLINE / MISS.
   - **PASS** = recognizable as the same person as the reference. Most
     of the distinguishing features are present. A reader who saw the
     reference would say "yes, same guy."
   - **BORDERLINE** = some features right, some off. A casual reader
     might accept it; a careful reader will pause. Examples: right
     build but wrong eye color; right face but model added 10 lbs;
     right wardrobe but slightly different facial structure.
   - **MISS** = doesn't look like the reference. Different person.
     Wrong age, wrong build, wrong hair (added hair on a bald
     subject), wrong skin tone.

3. **Notes.** One sentence stating what's right and what's wrong.

4. **Regenerate?** Yes / No.

---

## Example audit entry

```markdown
### ch12-forbidden-gospel.png
- Should show protagonist: YES
- Verdict: MISS
- Notes: Model added a full head of dark hair. Otherwise build and
  age look correct. Wardrobe is appropriate. Setting is good.
- Regenerate recommendation: YES, with strong_refs
```

---

## Where likeness misses tend to cluster

In production we found likeness drift correlated with these scene
types:

1. **Action / chase scenes** — face often partly obscured by motion;
   model fills in with "generic action protagonist"
2. **Crowd scenes** — model picks a random face in the crowd to be
   the protagonist; not the right one
3. **Dark / shadow-heavy scenes** — model uses shadow as an excuse
   to not commit to identity
4. **Chapters where the protagonist is mid-action with a weapon or
   tool** — model substitutes a more "competent looking" face

For each of these, the fix is usually `use_strong_refs: true` in the
config — 3-5 reference images amplifies the identity signal enough
to override the model's stock priors.

---

## When to accept a BORDERLINE

A BORDERLINE on a chapter where the protagonist is:
- In silhouette (back to camera, far away)
- One of several characters and not the central figure
- Reduced to a hand / shoulder / detail
- Behind glass / underwater / through a window

...is usually fine. Ship it. The reader won't notice.

A BORDERLINE on a chapter that's effectively a HERO SHOT of the
protagonist (looking at the camera, central, well-lit) — regenerate.
That image is going to be the visual the reader builds their mental
model around.

---

## Output: the audit file

Put the audit in `.planning/notes/IMAGE-AUDIT.md`. Suggested structure:

```markdown
# Chapter Image Likeness Audit — {DATE}

Reference: `{path to canonical reference}`
Profile: {one-sentence description of distinguishing features}.

## Summary
- PASS: N
- BORDERLINE: N
- MISS: N

## Per-image

### {slug}.png
- Should show protagonist: YES / NO
- Verdict: PASS / BORDERLINE / MISS
- Notes: {one sentence}
- Regenerate recommendation: yes / no

### {next slug}.png
...
```

Commit the audit alongside the regenerated images. It's the
provenance trail that lets you debate "did this come out right" with
yourself two weeks later when you've forgotten what you decided.

---

## When to stop iterating

Stop when:
- All chapters that **must** show the protagonist hit PASS
- No more than one chapter that should show them sits at BORDERLINE
- No chapter that should show them is at MISS

If a single chapter keeps coming back as MISS after 3 strong-ref
attempts, it's likely the prompt itself is the problem (the scene
description is fighting the identity). Re-read the SCENE block and
look for action verbs that the model is interpreting as "fast
unrecognizable motion" (sprinting, diving, ducking). Replace with
slower verbs (running, leaning, turning).
