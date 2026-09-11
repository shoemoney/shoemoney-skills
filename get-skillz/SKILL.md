---
name: get-skillz
description: Mine the current conversation for durable, reusable knowledge and turn it into new or updated skills — house style, gotchas, FAQs, recurring bug patterns, and optimizations. Use this whenever the user says "/get-skillz", "get skillz", "extract skills", "what did we learn", "turn this into a skill", "capture the lessons", "retro", "retrospective", "postmortem this session", or asks what from this work should be remembered or reused. Also reach for it proactively at the end of a long or painful session, after an outage or a hard-won debugging win, after shipping a big feature, or any time the same mistake showed up twice — the knowledge is perishable and the session is where it lives.
---

# get-skillz

A session is the only place certain knowledge exists. The four hours you spent finding out that
`config:cache` run as the wrong user silently swaps your database — that's not in the repo, not in
the commit, not in anyone's head tomorrow. This skill harvests it before it evaporates.

The goal is not a summary. It is durable, reusable artifacts that make the *next* session faster.

## The core judgment: durability

Most of what happens in a session is not worth extracting. Before writing anything, put each
candidate through one question:

> **Would this help someone on a different project, next month?**

- **Yes** → a skill. It transfers.
- **Only on this project** → project memory or a repo doc (`resume.md`, `docs/`, `CLAUDE.md`).
  A global skill full of one project's deploy paths is noise in every unrelated session.
- **Only in this conversation** → let it go.

This is the single highest-leverage decision in the whole skill. Getting it wrong in the generous
direction pollutes the skill library — and a library nobody trusts gets ignored, which costs more
than the extraction saved. When genuinely torn, prefer memory over a skill; memory is cheap to
write and cheap to ignore.

## What to look for

Sweep the whole conversation, including your own reasoning, not just the final outputs. The best
material usually hides in the middle of the session — in the moment something *surprised* you.

**Gotchas** — the highest-value category. Something behaved in a way a competent person would not
predict, and finding out cost real time. Signals: an outage, a silent failure, a "wait, why is it
doing that", a fix that took several wrong attempts. Capture the *surprise* and the *tell*, not
just the fix. The tell is what makes it findable next time.

**Bug patterns** — a defect whose *shape* will recur. Not "we had a null pointer" but "a test that
constructs its own precondition proves nothing and hides dead code." If you can state it as a class
rather than an instance, it's a pattern.

**House style** — a preference the user corrected you on, especially more than once. Corrections are
gold: they are the user telling you their taste in the cheapest possible form. Include the *why*
when they gave it; a rule with a reason survives, a bare rule gets rationalized away.

**FAQs** — a question that got asked and answered with real effort. Where does X live, which tool
handles Y, what's the credential path. Cheap to write down, embarrassing to re-derive.

**Optimizations** — a way of working that measurably beat the obvious approach. Parallelization
shapes, verification strategies, tool choices. Include the cost, not just the benefit, so the next
reader can judge whether it applies.

## Method

**1. Sweep, don't recall.** Actually re-read the conversation. Memory of a long session is
compressed and biased toward the end. Look specifically for:
- moments of surprise ("huh", "wait", "that's not…")
- anything the user corrected, repeated, or pushed back on
- time sinks — where did the session actually spend its hours?
- anything that broke, especially anything that broke *silently*
- decisions made with reasoning, so the next session doesn't relitigate them

**2. Demand evidence.** Every extraction cites where it came from — the command that failed, the
error, the exchange. Nothing invented, nothing embellished, nothing you merely believe is true.
An extracted "gotcha" that is actually a guess will send someone down a wrong path with false
confidence, which is worse than silence. If you're not sure it's real, say so in the artifact or
drop it.

**3. Check what already exists.** List the skills already installed. Duplicating an existing skill
is worse than adding nothing — now there are two sources of truth that will drift. Prefer updating
an existing skill over creating a near-neighbour. If a new skill overlaps an old one, say which and
why the split is right.

**4. Route each finding.** For each survivor of the durability test:

| Destination | When |
|---|---|
| New skill | A coherent, reusable capability or body of practice with several related findings |
| Update existing skill | The finding belongs to something already installed — usually the right answer |
| Project memory | True and useful, but only for this project |
| Repo doc | Operational detail the next person needs at the keyboard (runbook, resume, README) |
| Drop | Interesting, not durable |

**5. Write it properly.** Skills follow the format in `skill-creator`: YAML frontmatter with `name`
and a *pushy, specific* `description` covering both what it does and when to trigger, then
imperative instructions that explain their own reasoning. Keep SKILL.md under ~500 lines and push
detail into `references/`.

**6. Report what you did and what you deliberately skipped.** The skipped list is not filler — it
shows the user your judgment and lets them overrule it. They know things about their future work
that you don't.

## Writing an extraction well

A gotcha is worth writing only if a stranger could act on it. Include:

- **The surprise** — what a reasonable person would have expected instead
- **The tell** — how it presents, so it's recognizable next time. This is the part people skip and
  it's the part that makes it findable.
- **The fix** — exact, runnable
- **The check** — how to confirm you're actually out of the woods. Silent failures need a positive
  verification, not an absence of errors.

Compare:

> ❌ Don't run config:cache as the wrong user.

> ✅ **`artisan config:cache` as a user who can't read `.env` silently builds config from
> framework defaults.** No error. The app switches to sqlite and every page 500s within seconds —
> it presents as a total outage minutes after a deploy that reported success.
> Fix: run it as the user owning `.env`, then `chmod o= bootstrap/cache/*.php`.
> Check: `php -r '$c=require "bootstrap/cache/config.php"; echo $c["database"]["default"];'`
> must print your real driver, not `sqlite`.

The second one costs four more lines and saves the next person an outage.

## Anti-patterns

- **Extracting everything.** A session that yields 3 sharp findings beat one that yields 20 vague
  ones. Volume is not value here.
- **Project-specific paths in a global skill.** `/var/www/thisapp` helps nobody in another repo.
- **Restating what the model already knows.** "Remember to write tests" is not knowledge.
- **Capturing the fix without the tell.** Fixes are searchable once you know what you're looking
  at; the whole difficulty is recognizing it.
- **Laundering a guess into an artifact.** Written down, a maybe becomes a fact. Mark uncertainty
  explicitly or leave it out.
- **Rewriting an existing skill from scratch** because you didn't check first.

## Output

End with a short, scannable report:

```
## Extracted
- <skill name> (new|updated) — one line on what it captures and why it transfers

## Routed elsewhere
- <finding> → project memory / repo doc, because <reason>

## Skipped
- <finding> — <why it didn't clear the durability bar>
```

Then offer to test any new skill with `skill-creator`, since a skill that has never been invoked is
a hypothesis rather than a tool.

## A note on your own reasoning

You have access to something no reviewer does: what you were *thinking* when you got it wrong.
The moment you formed a wrong hypothesis and the observation that broke it is often the most
valuable thing in the entire session — it names the trap, not just the escape. Mine your own
mistakes at least as hard as the code's.
