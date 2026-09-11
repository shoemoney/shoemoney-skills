# Editorial Review Methodology

How to run a one-pass editorial read that produces findings the
author can act on. The template at `templates/editorial-prompt.md.template`
is the prompt you give to a subagent; this doc explains the philosophy
behind it.

---

## What an editorial read IS

An editorial read produces a CLASSIFIED, ACTIONABLE list of findings.
Each finding is:
- Quoted (the actual text)
- Specific (which line / chapter)
- Explained (why this matters)
- Fixable (the proposed replacement)

A "good" editorial read for a 55,000-word manuscript produces 50-80
findings split roughly:
- 20-30 HIGH (must fix)
- 25-35 MEDIUM (author judgment)
- 10-20 LOW (optional polish)

Too few findings = the reader wasn't paying attention. Too many = the
reader is flagging style preferences instead of problems.

---

## What an editorial read is NOT

It is NOT:
- A line edit. Don't fix grammar; flag a category of issue if it
  recurs.
- A developmental edit. Don't propose new chapters or new structure;
  flag specific structural problems with specific fixes.
- A taste review. "I don't love this line" is not a finding. "This
  line contradicts the line on page 12" is a finding.
- A cheerleading read. The job is to surface problems. The author
  knows the book is good; they're paying for what's broken.

---

## Categories worth flagging

### 1. Numeric continuity

The single largest source of HIGH findings. Track:
- Character ages
- Years and "N years ago" math
- Generation counts (if the book has lineage)
- Day-of-week / date math
- Time-of-day in scenes that cross-cut

### 2. Character name collisions

Two characters with the same first name and no clear disambiguator.
Especially dangerous when:
- One is the protagonist's parent and one is their in-law
- One is a minor character early and one is a major character later
- Both are referenced by first name only across the manuscript

### 3. Internal canon violations

Dramatis Personae or appendix says X; prose does Y. See
`canon-audit-methodology.md` for the dedicated pattern.

### 4. Chapter length vs. genre standard

- Dan Brown / thriller: 1,500-3,000 words per chapter
- Literary fiction: variable, but watch for >8,000-word chapters that
  could be split
- Romance: tighter than thriller, often 1,000-2,500 words
- Memoir: longer, 2,500-5,000 words, but breaks recommended

Flag chapters >150% of the genre standard. Recommend a split point.

### 5. Cliffhanger strength

Score each chapter ending 1-10 on whether it pulls the reader forward.
A 1-3 score = author wraps the scene up; reader can put the book
down. A 9-10 score = mid-action cut, revelation, threat. Most
chapters should be 7+. Flag any below 5.

### 6. Show-vs-tell exposition

Find any scene where ONE character delivers a 1,000+ word monologue
that explains backstory or worldbuilding. Recommend interspersing
external pressure (a phone interrupting, a perimeter alert, another
character entering) or cutting the redundant beats.

### 7. Repetitive structural patterns

If the same beat-type appears three times in the same book ("I'll
hold them, you run" sacrifice scene; "the bad guy reveals their grand
plan during a car ride" scene; "the protagonist has a panic attack
in a bathroom"), flag the third one as diluting the first.

### 8. Set-and-never-paid-off Chekhov's guns

A character or detail is introduced like it matters and then never
returns. Choose: pay it off or cut it.

### 9. Voice drift

Compare a character's dialogue in chapters 1, 8, and 15. Do they
sound like the same person? Antagonists are the most likely to drift
into "thriller villain expositor mode." Flag specific lines where
the voice slips.

### 10. Plot logic / pieces in two places

A character is in two locations at once. A timeline runs in parallel
but the numbers don't match. A vehicle moves faster than physics
allows. These reads catch in skim mode; flag them.

---

## How to score severity

HIGH if:
- The reader will probably notice and stop
- It contradicts something the author has explicitly written
  elsewhere
- It's a genre convention violation that pulls the reader out
- Fixing it is mechanical (replace word, change number)

MEDIUM if:
- A careful reader will notice; a casual one won't
- It's a slip in tone or voice, not in fact
- Fixing it requires the author's taste call
- It might be intentional and the author should decide

LOW if:
- A copy-editor would flag it; most readers won't
- It's a polish item, not a problem
- The book ships fine without it

---

## How to deliver fixes

Always include the literal replacement text, not a vibe-fix.

**Bad:**
> "This chapter feels too long. Consider tightening."

**Good:**
> "Cut lines 1453-1620 to ~1,000 words by removing the three redundant
> skepticism beats at 1467 ('That's impossible'), 1502 ('You can't be
> serious'), and 1564 ('I don't believe this'). Keep the first one as
> the legitimate doubt and replace the next two with action — Crawford
> walking in with a perimeter update, then a phone alert about the
> daughters."

The first is editorial chatter. The second is a 30-second author task.

---

## Process

1. **First pass — skim.** Read end-to-end without stopping. Note
   anything that catches the eye but don't write findings yet.
2. **Second pass — deep.** Read with a tracker for the ten categories
   above. Write each finding with a literal quote and a literal fix.
3. **Classify.** HIGH / MEDIUM / LOW. Be honest — flag fewer HIGHs
   to keep the author's focus tight.
4. **Group root causes.** If one rename fixes 12 collisions, write
   ONE finding ("rename X to Y") not 12.
5. **Write the executive summary.** Two paragraphs: what's working,
   what's the biggest single risk to the book, where the HIGHs cluster.
6. **Output to `.planning/notes/MANUSCRIPT-NOTES.md`.**

---

## Iteration

After the author applies HIGH fixes, run a TARGETED second pass on
only the changed chapters. New finding count should be ≤ 5% of the
original. If it's higher, the edits introduced new problems and
deserve a third pass.
