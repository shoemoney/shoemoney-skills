---
name: refresh-resume
description: Harvest the session's durable lessons into skills with get-skillz, write a fresh per-project handoff file to ~/.claude/resumes/ so the user can /clear with zero context loss, and — only when the day genuinely TURNED — write a narrative post to blog/ in the project repo. Three artifacts for three audiences: skills are what transfers to other projects, the resume is what is true right now for the next session, the blog is what happened and why for a human reading later. Use when the user says "/refresh-resume", "refresh the resume", "dump the context", "save a resume so I can clear", or wants a clean handoff before clearing context. Also use when they ask to chronicle or write up the build, journey, or story so far — and note the bar for a post is a turn (a belief killed by measurement, a fix that broke something invisible, a retraction, the moment the question itself changed), never mere activity; most days do not qualify and writing one anyway buries the days that do.
---

# refresh-resume

Three different things are worth saving at the end of a session, and they belong in different places:

- **What transfers to other work** — gotchas, bug patterns, style corrections, techniques. These go
  in skills, where every future session sees them.
- **What is true about *this* project right now** — state, decisions, blockers, paths, credentials.
  This goes in `~/.claude/resumes/`, which the next session loads and eventually outgrows.
- **What actually happened, and why** — the turns, the dead ends, the measurement that
  changed the plan. This goes in `blog/` in the project repo, and only when a day genuinely
  turned. Most days don't.

Sending everything to the resume is the common failure: a hard-won general lesson gets buried in a
project file and dies with the project. So harvest first, then hand off.

Handoffs live in `~/.claude/resumes/` as one file per run — never overwritten, never deleted. A
single shared `~/RESUME.md` used to get clobbered whenever two sessions raced to write it at once
(whoever finished last won, silently destroying the other session's handoff). Per-run files make
that collision structurally impossible: two sessions can never pick the same filename.

## Steps

**1. Run `get-skillz` first.** Invoke the `get-skillz` skill and let it mine the conversation for
durable, reusable knowledge — creating or updating skills, and routing project-only facts onward to
the resume. Do this *before* writing the resume, while the session is still fully in context.

If `get-skillz` isn't available, do the equivalent inline: scan for anything that would help on a
*different* project next month and capture it as a skill rather than a resume line.

**2. Derive the project slug.** This identifies which project the handoff belongs to, so pickup can
find it later:

- If the cwd is inside a git repo, use the repo's top-level directory name (`basename "$(git rev-parse --show-toplevel)"`).
- Else use the cwd's own basename.
- Else (no clear project context) use `global`.

**3. Dispatch a Haiku subagent to write a NEW file
`~/.claude/resumes/<slug>-$(date +%Y%m%d-%H%M%S)-$BASHPID.md`.** Use the Agent tool with
`model: "haiku"`. This is writing and formatting over facts you already hold, so it doesn't need a
frontier model, and delegating keeps the main session's budget for real work.

**Pick the PID variable by shell — this bites silently.** In *bash*, prefer `$BASHPID` over `$$`:
`$$` is fixed at shell startup and stays the *parent* shell's PID even inside a backgrounded
subshell, so it can collide. But **`$BASHPID` is a bash builtin that does not exist in zsh** — on
a zsh box (macOS default) it expands to the empty string and you silently get
`slug-20260805-025040-.md`, with the collision-safety the suffix existed for quietly gone.
Verified 2026-08-05 on `/bin/zsh`: `BASHPID=''` while `$$=68957`.

**The tell:** the written filename ends in `-.md`. Always read back the *actual* path after
writing — the subagent will report success either way, because `mv`/heredoc to an odd-but-valid
filename is not an error.

Portable form:

```bash
PID="${BASHPID:-$$}"     # bash: real subshell PID | zsh: falls back to $$, which zsh sets correctly
```

Never delete or overwrite any other file in `~/.claude/resumes/` — this is append-only. The
timestamp+pid suffix makes the filename unique per run, so concurrent sessions writing at the same
moment simply produce two different files instead of colliding.

The subagent cannot see this conversation, so paste the actual values into its prompt — paths,
versions, commands, error strings, decisions and their reasoning. A vague prompt produces a vague
resume, and the entire point is that the next session inherits specifics.

Have it produce:

- **Header** — the project slug, today's date, one line on what we're working on, which host/repo/session
  this is. Multiple resumes now coexist, so the slug in the header is how pickup (and a human skimming
  `ls ~/.claude/resumes/`) tells them apart.
- **Current status** — what's DONE and *verified* (say how), what's IN PROGRESS, what's blocked and
  on whom.
- **Key decisions & why** — the rationale, so the next session doesn't relitigate settled choices.
- **Open items / TODO** — concrete next steps in priority order.
- **Gotchas & hard facts** — real file paths, model IDs, URLs, credential locations, exact commands,
  and the failure modes learned this session. Favour the ones that cost time.
- **How to pick up** — the exact first command to run.
- Links to relevant memories with `[[name]]`.

**4. Verify before reporting.** Read the file the subagent wrote. A resume that invents state is
worse than no resume, because the next session will act on it confidently. Confirm every command,
path and version actually appeared this session, and that anything uncertain is marked uncertain.

**5. Ask whether anything actually TURNED, and if so write a blog post.** This is a third
artifact, distinct from the other two: skills are what transfers, the resume is what is true
right now, and this is *what happened and why* — for a human, later, possibly a public one.

**Only write one when the answer is yes.** A daily log nobody reads is worse than nothing,
because it buries the two or three days a project has that are genuinely worth reading. The bar
is a TURN, not activity:

- a belief that got measured and killed (especially a cheap measurement that saved expensive work)
- a fix that broke something invisible, or a conclusion that had to be retracted
- the moment the question itself changed — you set out to do X and discovered X was the wrong goal
- a number that decided a strategy

Shipping features is not a turn. A busy day is not a turn.

Write it to `blog/<YYYY-MM-DD>-<slug>.md` in the project repo (flat files, one per post,
timestamped — no index to maintain, no single file to merge-conflict on). Source it from the
commit messages and any research/decision log, which usually already carry the narrative.

**Keep the wrong turns in.** Retractions, dead ends, the diagnosis that took three wrong guesses
— those are the substance. A build log containing only the conclusions that survived is a
marketing document, and it teaches nobody anything. If an entry was overturned later, say so in
place rather than quietly editing it.

Include real numbers. "We killed a plan for $0.03" and "282x slower on the actual write shape"
are what make it credible; "we improved performance" is what makes it skippable.

**6. Confirm** the written path, a one-line summary of what was captured, which skills
`get-skillz` created or updated, and whether a blog post was written (and if not, why the day
did not clear the bar).

The companion skill to reload this file next session is `pickup`.
