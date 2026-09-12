---
name: scopecreep
description: Capture an idea raised mid-task WITHOUT acting on it, so the current work does not get derailed and the idea does not get lost. Appends it to the project's QUEUE.md with enough context to act on later, confirms in one line, and returns to what was already in progress. Use WHENEVER the user types "/scopecreep ...", raises something unrelated while you are mid-task ("we should also...", "another thing...", "maybe put my photo with...", "we really should do X"), or when YOU notice yourself about to chase a tangent. Also use before answering "did you build X yet" about something previously queued. Do NOT use for a change to the task actually in progress — that is not scope creep, that is the task.
---

# Capture it, do not chase it

The user has a track record of raising good ideas in the middle of unrelated work. Both failure
modes are real: chase it and the current task dies half-finished; ignore it and a good idea
evaporates. This skill is the third option.

**The whole value is that this takes ten seconds and one line of output.** A ceremonious capture
is itself a derailment. If you find yourself researching the queued item, you have already failed.

## What this is NOT for

- **A change to the task in progress.** "Actually use the studio photo instead" while you are
  building that cover is the task, not creep. Do it.
- **A correction.** "No, that's wrong" is never queued.
- **Something genuinely blocking.** If the current task cannot finish without it, it is not creep.

## Do

1. **Append to the queue.** `$CLAUDE_PROJECT_DIR/QUEUE.md` if the cwd is in a repo, else
   `~/.claude/QUEUE.md`. Create it with the section headings below if missing.

2. **Capture enough that a cold reader could act on it.** The failure mode of a queue is entries
   nobody can execute six weeks later. Include:
   - **What**, in the user's own words where they were specific
   - **Who and when** — `(Jeremy, 2026-09-10 05:04, via scopecreep)`
   - **Blast radius**, if you already know it from the work in front of you. This is the part
     that makes a queue worth keeping — you have the context *now* and will not later.
   - **Blockers**, explicitly, if any exist
   - Put it under `## Blocked` if it cannot proceed, `## Ready` if it can.

3. **Confirm in ONE line and stop.** "📋 Queued. Not touching it." Then return to the task
   mid-stride. No summary of the queue, no offer to do it now, no clarifying questions unless the
   entry would be meaningless without one.

4. **Never start the work.** Not "while I'm here", not "it's only a one-liner". The user asked
   for a queue precisely because one-liners are how a session gets eaten.

## Do not

- Do not reorganize or re-prioritize the whole queue on every capture.
- Do not silently drop an item because you judge it unwise. Queue it with your objection in one
  clause; the decision is theirs.
- Do not queue something you could genuinely finish in the current tool call *and* that touches
  the same files you already have open. Just do it and mention it in one clause.

## Queue format

```markdown
# Queue

Things raised mid-task and deliberately not acted on. Captured, not executed.
Nothing here is in progress unless it says so.

## Ready
- **<short title>** (<who>, <when>, via scopecreep). <What, in their words.>
  Blast radius: <files/systems you already know are involved>.

## Blocked
- **<short title>** — <what>. **Blocker:** <the specific thing in the way>.

## Notes worth keeping
- <observation that is not a task but should survive the session>

## Measured and deliberately dropped
- <thing> — killed by <evidence>. Do not re-raise without new data.
```

That last section matters more than it looks. A queue that only grows becomes noise. When
something is settled by evidence, move it there **with the number that settled it**, so nobody
re-litigates it in three weeks.

## Reading the queue back

When the user asks "what's queued", "what did we defer", or "did you ever do X":
- Answer from the file, not from memory of the conversation.
- Lead with `## Ready` items — those are the actionable ones.
- State plainly if something was queued and *deliberately* never built. Being asked about it is
  not a signal you should have built it.

## Optional: surface it automatically

`hooks/scopecreep-check.sh` (shipped next to this file) is a Stop hook that surfaces the queue
when it has ready items — throttled so it speaks at most once every two hours per session and
stays silent when the queue is empty. It is deliberately quiet: a nagging queue gets ignored,
which defeats the point.

Wire it in `~/.claude/settings.json` under `Stop`, pointing at wherever you installed the skill:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "bash ~/.claude/skills/scopecreep/hooks/scopecreep-check.sh", "timeout": 5 }
        ]
      }
    ]
  }
}
```

It exits 0 no matter what, so it can never block a session.
