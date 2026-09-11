---
name: pickup
description: Find and read the newest per-project handoff from ~/.claude/resumes/ and load it as working context to continue exactly where a previous session left off. Use when the user says "/pickup", "pickup", "pick up where we left off", "load the resume", "continue", or right after a /clear to restore context from the handoff file written by refresh-resume.
---

# pickup

Restore context from the handoff file so we continue seamlessly.

## Steps

1. **Derive the slug and find the file.** Derive the same project slug refresh-resume would use for
   the current cwd (git repo top-level dirname, else cwd basename, else `global`), then find the
   newest matching file: `ls -t ~/.claude/resumes/<slug>-*.md | head -1`.
   - If none exist for that slug, fall back to listing the newest few across *all* slugs
     (`ls -t ~/.claude/resumes/*.md | head -5`) and ask the user which project's handoff to load —
     never guess across projects.
   - If `~/.claude/resumes/` is empty or missing, fall back once to legacy `~/RESUME.md` if it still
     has real content (not just the deprecation pointer). Otherwise tell the user there's nothing to
     pick up.
2. **Read the chosen file** in full.
3. Internalize the status, key decisions, gotchas, and open items. Verify any critical facts that are cheap to check (e.g. a file/version still exists) before acting on them — a resume is point-in-time and may be stale.

   **The resume's *diagnoses* decay far faster than its *facts*, and they are what you're about to act on.** Paths, credentials and commands mostly stay true. The ranked bottleneck, "the real problem is X", the priority order — those were one session's inference from the data it had, and they are exactly what determines your next hours of work.

   Confirmed 2026-08-07: a resume named one skip reason as bottleneck #1 and repeated it in a second section, which read as corroboration. **One `GROUP BY` killed it** — that reason was 1.8% of failures; a different one, never mentioned in the resume, was 78%. The stated goal would have spent a day optimizing a 1.8% path. Repetition inside a single document is one belief written twice, never a second source.

   So before starting the top priority: **re-measure the number the priority rests on.** If the resume says "X is the bottleneck", run the count. If it says "Y is failing", query Y. Usually one query, and it either confirms the plan cheaply or saves the whole day.
   Confirmed again 2026-09-05: the resume said rounds "should now take about a minute" and suggested
   doubling the batch size; one `SHOW STATUS` showed the DB at 152 of 151 connections, rounds hitting
   a 40-minute deadline, and an optimizer that had never evaluated a single real candidate. The
   resume also named the wrong checkout path and the wrong Redis queue keys, which made an outage
   look like an idle farm — verify paths and keys by probing, not by reading.

4. **Check whether work landed after the resume was written.** `git log` timestamps against the resume's filename timestamp. A handoff written mid-session is stale the moment work continues, and it will confidently describe a state several commits old. Check *terminal* states, not just open ones: a resume saying "open a PR for branch X" can be satisfied already — fetch and look for a merge of X into main (`git log origin/main --merges --oneline | head`) before creating anything, because "no open PRs" and "nothing to do" are different facts (confirmed 2026-08-11: a duplicate PR was opened while the real one had merged 10 minutes earlier).
5. **Summarize back** to the user: where things stand, and the top 2–3 next actions from the resume. Say plainly which of the resume's claims you re-verified and which you are taking on trust.
6. **Do not auto-execute.** Confirm the next step with the user first, then proceed. Go step by step.

The companion skill that writes this file is `refresh-resume`.
