# Canon Audit Methodology

A canon audit catches cases where the manuscript contradicts itself
on facts you've explicitly set. Typically run after the editorial
read, when the manuscript is otherwise locked.

There are usually two canons worth auditing for a fiction book:

1. **Family / character canon** — who is related to whom, what are
   their ages, denominations, jobs, names
2. **Setting / cultural canon** — religion-specific details, period-
   correct technology, regional dialect, professional terminology

---

## How to run a canon audit

A canon audit is essentially: "the appendix / Dramatis Personae /
worldbuilding bible says X — does the manuscript hold X?"

### Step 1: Extract the canon

Look for the file(s) where the author has written down the canonical
truth. Usually:
- The Dramatis Personae block at the top of the manuscript
- An appendix at the back
- A separate worldbuilding doc in the planning directory
- The author's notes in `CLAUDE.md`

Pull every factual claim into a small list:

```
- Protagonist's age: {AGE}
- Protagonist's birthplace: {CITY}
- Protagonist's religion: {DENOMINATION}
- Father's death year: {YEAR}
- Father's notable medical / historical event year: {YEAR} ({DELTA} years before death)
- Older daughter's age: {AGE}
- Younger daughter's age: {AGE}
- Antagonist's father killed: age {AGE}, in {LOCATION} {YEAR}
- Mother-in-law's name: {NAME} (NOT the same as protagonist's mother's name)
```

A real canon list might look like:

```
- Protagonist's age: 46
- Protagonist's birthplace: Cedar Falls, IA
- Protagonist's religion: Lutheran
- Father's death year: 2020
- Father's heart transplant year: 1988 (32 years before death)
- Older daughter's age: 18 (named Alex)
- Younger daughter's age: 15 (named Mia)
- Antagonist's father killed: age 3, in Naples 1955
- Mother-in-law's name: Diane (NOT the same as protagonist's mother Carol)
```

### Step 2: Spec the audit subagent

Tell a subagent to read the manuscript looking ONLY for contradictions
of the canon list. Have it produce findings in this format:

```markdown
### Finding N — {ONE-LINE HEADLINE} ({SEVERITY})
- Line: {NUMBER}
- Current text:
  > {QUOTE}
- Issue: {ONE PARAGRAPH EXPLAINING THE CONTRADICTION}
- Proposed fix:
  > {LITERAL REPLACEMENT TEXT}
- Severity: HIGH / MEDIUM / LOW
```

### Step 3: Triage with the author

Each finding has three possible resolutions:
1. **Fix the manuscript** — replace the text to match the canon
2. **Fix the canon** — author changes the canon to match what the
   manuscript actually does (often happens when a character grew on
   the author and the original canon entry was stale)
3. **Accept the contradiction** — sometimes a character's age is wrong
   in one scene for thematic reasons; author decides to leave it

Default to (1) unless the author actively says otherwise.

---

## Patterns we've seen in production

### Religion canon

A character's denomination is canonically established (e.g.,
"Lutheran") but a scene gives them a denominationally specific prop
or ritual that contradicts. Common collisions:

- Lutheran character holding rosary beads (Catholic only)
- Protestant character calling a hall "the parish hall" (Catholic vocab)
- Catholic character calling clergy "Pastor" (Protestant vocab)
- Jewish character at a "service" instead of a "minyan" / "Shabbat"

These read fine to most readers but the religious readers WILL email
the author. Fix the props, not the people.

### Family canon

Names, ages, relationships, professions. Common collisions:

- Two characters named the same first name without surname disambiguation
- A child's age contradicts the parent's age (math is wrong)
- A character's profession in one scene contradicts another
- A "deceased" character appears alive later
- A backstory event happens in two different years across scenes

### Numerical canon

Year math, anniversary math, "N years ago" math. Common collisions:

- "Thirty-four years since {event in 1986}" — but the speaker is in
  2020, which is 34 years AFTER 1986, so this is right; check both
  directions
- "He was twelve" + "30 years ago" — birth year math
- Multiple characters' birth years that imply an impossible parent age
- A career length that doesn't fit the character's age

### Geographic canon

Places exist and have specific names. Common collisions:

- A street name in the wrong neighborhood
- An interior layout that doesn't match the real building (Newberry
  Library, Vatican Archives, named real locations)
- A drive time / flight time that's physically impossible
- A landmark used as a backdrop for a scene where it can't be seen

---

## When to involve a subject-matter expert

If the canon includes specialized knowledge (Masonic ritual, Catholic
liturgy, military jargon, medical procedure, legal procedure, foreign-
language dialogue), get a human SME to read those scenes before launch.
LLMs are good at flagging gross errors but miss the kind of nuance
that domain experts catch (e.g., a 32° Mason wouldn't address a
Worshipful Master that way; a Catholic priest wouldn't bless that way
in that vestment).

The cost of an SME read is small ($50-$500). The cost of shipping a
book with a Masonic ritual wrong is years of "actually..." emails.

---

## Output: the audit file

`.planning/notes/{TYPE}-AUDIT.md`. Examples:
- `RELIGION-AUDIT.md`
- `FAMILY-AUDIT.md`
- `MASONIC-AUDIT.md`
- `TIMELINE-AUDIT.md`

Same structure as the editorial-notes file (HIGH/MEDIUM/LOW with
quoted text and proposed fixes), but scoped to ONE canon dimension.
Easier to apply in one pass than a 60-finding kitchen-sink doc.
