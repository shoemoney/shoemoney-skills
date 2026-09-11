# Chapter Image Prompt Structure Guide

How to write a prompt that reliably produces a usable chapter
illustration on the first try. Based on production runs against
OpenRouter Gemini 3 Pro Image Preview.

---

## The 6-Block Structure

Every chapter prompt and cover prompt in this skill follows the same
six blocks, in the same order, in ALL CAPS heading form:

```
SUBJECT — IDENTITY IS CRITICAL: ...
SCENE: ...
LIGHTING: ...
COMPOSITION: ...
NEGATIVE: ...
STYLE: ...
```

The all-caps headings aren't cosmetic — Gemini parses them as
section markers and weights them differently. Skipping any of them
produces noticeably worse results.

---

## Block 1 — SUBJECT (identity anchoring)

Goal: make the model render YOUR specific protagonist, not a stock
{genre} character.

**Required content:**
1. Explicit instruction that the reference image(s) are the source of
   truth for identity
2. Five to seven specific physical features stated in declarative form
   (not "looks like" — say "has X, is Y, is Z")
3. An anti-instruction list: "Do not slim him down. Do not add hair.
   Do not change his features."
4. A goal sentence: "The goal is recognizable likeness — the buyer
   should look at this cover and see a specific real person."

**Example for a bald 45-year-old man:**
```
SUBJECT — IDENTITY IS CRITICAL: The man in this image MUST be the
exact same person as the man in the attached reference. He is
{NAME}, the book's protagonist. Preserve his identity precisely:
completely bald head, fair skin, blue eyes, mid-40s, broad-shouldered
solid build, the same facial structure visible in the reference. Do
not generate a generic bald man. Do not slim him down or change his
features. This is a portrait of a specific real person and his face
must be recognizable.
```

**Common failure:** model adds hair to a bald subject. Fix: amplify the
reference signal with 3 bald headshots from different angles, not 1.
See the `STRONG_REFS` pattern in `generate_chapter_images.py`.

---

## Block 2 — SCENE

Goal: place the protagonist in the chapter's setting, doing the
chapter's action.

**Structure:**
1. One sentence naming the chapter ("Chapter N, 'Title'") + place +
   date if useful. Date helps with period accuracy (wardrobe, tech,
   architecture).
2. Three to five sentences describing the protagonist's position,
   action, and environment. Concrete nouns. No abstractions.
3. One sentence on what they hold or interact with (the chapter's
   "object" — an amulet, a letter, a glass, a phone).
4. One sentence describing their wardrobe.
5. One sentence implying their emotion through posture or expression
   (NOT through telling the model how they feel).

**Example:**
```
SCENE: Chapter 1, "The Walnut Box." Rock Island, Illinois, November 7,
2020. {NAME} stands at his late father's wooden writing desk in the
study, the room hushed and still after a funeral. The desk is dark
walnut, the room paneled in old oak. On the desk sits an open walnut
box lined with faded green felt. He's holding a brass amulet up to a
desk lamp, examining it. His expression is a mix of grief, confusion,
and dawning recognition. He wears a dark suit, tie loosened, collar
unbuttoned. A framed photograph of his father sits on the corner of
the desk.
```

**Common failure:** the model misses a small but important prop. Fix:
state it as its own sentence. "On the desk: a small brass amulet."

---

## Block 3 — LIGHTING

Goal: give the model a single, strong light source so the image has
contrast and mood.

**Structure:**
1. The dominant source (named, with direction). "Single dominant
   source — a green-shaded banker's desk lamp from the right."
2. What the dominant source illuminates and what falls into shadow
3. One reference DP / film / painter for the lighting style
4. The non-negotiable: "His face must be clearly lit and recognizable."

**Example:**
```
LIGHTING: Single dominant source — a green-shaded banker's desk lamp.
Warm tungsten pool on the desk and the amulet; deep shadow recedes
behind him. His face clearly lit and recognizable. Subtle dust motes
drifting in the lamp light. Roger Deakins low-key interior style.
```

**Common failure:** model puts the face in shadow because the prompt
sounded "moody." Fix: always include "face must be clearly lit and
recognizable" as a non-optional sentence.

---

## Block 4 — COMPOSITION

Goal: place the subject in the frame so there's negative space for
typography overlay.

**Structure:**
1. Subject placement (left third / right half / center)
2. Which zone is kept quiet for text overlay
3. Frame proportion (portrait / landscape / aspect ratio)
4. Camera height and angle (chest height, slight low angle, slight
   high angle)
5. Depth of field (what's sharp, what's soft)

**Example:**
```
COMPOSITION: {NAME} in the LEFT HALF of the frame, the lit amulet
between his fingers near the center. RIGHT THIRD kept darker and
quieter for potential chapter title overlay. Shallow depth of field —
amulet and face in sharp focus, background shelves in soft falloff.
Camera at desk height, slight upward tilt.
```

---

## Block 5 — NEGATIVE

Goal: forbid the things the model loves to add that you don't want.

Always include:
```
NEGATIVE: No text, no letters, no signage, no logos, no on-image
typography, no readable inscriptions. No HDR. Photorealistic.
Subtle film grain.
```

Add as needed:
- "No motion blur" (the model adds this on chase scenes)
- "No multiple figures" (when you want a solo portrait but the model
  keeps drafting in extras)
- "No religious iconography on walls" (when a chapel scene is being
  busied up with decorations)
- "No firearms" (if your scene is action without weapons)

---

## Block 6 — STYLE

Goal: anchor the aesthetic to recognizable visual references.

**Best results come from naming three to five specific things:**
- Films (cinematographer + film, e.g., "Roger Deakins on 1917")
- Posters (theatrical-poster cinematography for thrillers)
- Painters (Caravaggio for chiaroscuro, Vermeer for window light,
  Edward Hopper for diner / motel interiors)
- Photographers (Annie Leibovitz for portrait restraint, Joel Meyerowitz
  for color, Walker Evans for documentary)

**Example for thrillers:**
```
STYLE: Da Vinci Code / Angels & Demons book-illustration aesthetic.
Comp films: The Da Vinci Code (2006) artifact-discovery interiors,
Spotlight (2015) office lighting, Knives Out (2019) study warmth.
The mood is inheritance-meets-mystery — a grieving son realizing his
father's life held secrets he was never told.
```

**Example for memoir:**
```
STYLE: Annie Leibovitz portrait restraint, Walker Evans documentary
authority, Joel Meyerowitz color and quietness. The mood is the
hard-won truth — a person looking honestly at the thing they spent
years not looking at.
```

See `aesthetic-libraries.md` for genre-by-genre style block presets.

---

## Iteration Patterns

The model rarely nails it on attempt 1. Budget for 2-3 attempts per
chapter on the protagonist's likeness, 4-8 attempts on covers.

**When the model gets the IDENTITY wrong:**
1. Add a second reference image and re-run
2. If still wrong, use the `use_strong_refs` flag in `_launch_config.json`
   so 3-5 references are sent
3. If STILL wrong, strengthen the SUBJECT block — add another anti-
   instruction ("do not generate a man with hair under any
   circumstances")

**When the COMPOSITION is wrong:**
- Restate the placement in two different ways: "Subject in the left
  half" AND "the right third should be empty"
- Ask for explicit aspect ratio: "2:3 portrait orientation"

**When the SCENE is wrong (wrong period, wrong setting):**
- Add a date to the SCENE block — "November 7, 2020" forces modern
  wardrobe and props
- Add architectural detail — "1920s Art Deco" or "1500s Italian
  Renaissance" gives the model a setting anchor

**When TEXT keeps appearing:**
- Strengthen the NEGATIVE block ("absolutely no text anywhere in the
  image — no inscriptions, no graffiti, no signs, no labels")
- Move the NEGATIVE block higher in the prompt (just after SUBJECT)
- Sometimes the model is responding to a noun like "manuscript" or
  "Bible" or "newspaper" — rename the object ("ancient leather-bound
  journal" instead of "Bible") so it doesn't reach for text

---

## When to Use `--no-ref`

The chapter generator can attach the protagonist reference or skip it.
Skip it when:
- The chapter is from another POV (antagonist, secondary character)
- The chapter shows an object without a person ("close-up of the amulet
  on a velvet cloth")
- The chapter shows a landscape ("the cathedral at dusk, no figures")

Attaching the reference for a NO-protagonist chapter biases the model
toward inserting the protagonist anyway. Set `has_protagonist: false`
in the chapter's config entry.
