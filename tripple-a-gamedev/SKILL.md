---
name: tripple-a-gamedev
description: >
  Run an "is this triple-A?" polish loop on the current Godot game. A consumer-persona
  reviewer (a multimodal model — gemini-3.6-flash by default) SEES the game's screenshots itself —
  verified real captures, never a blank one — and judges whether the game hits
  top-tier production value FOR ITS KIND (a 2D action game is measured against Dead Cells,
  not Call of Duty), naming the biggest fixable giveaways in vivid detail. Opus 5 then plans the fix, codes it, and gates
  the result - sending it back with a verified-good list until it passes, salvaging the
  sound part if it does not - then commits. Repeatable:
  the user passes an iteration count. Use WHENEVER the user types "/tripple-a-gamedev N",
  "/aaa-game", or asks to "see if my game looks AAA", "what gives away
  that this isn't AAA", "make the game feel triple-A", "AAA polish pass", or wants a
  consumer/blind-test review of the game's production value.
---

# tripple-a-gamedev — the "would a shopper believe a AAA studio made this?" loop

```
/tripple-a-gamedev <N>          # N = how many times to loop (default 1)

PREFLIGHT (once)    kill orphaned Godot processes, refresh the import cache (--import — a
                    warm-but-stale .godot/ makes every frame and art test in the run judge
                    OLD PIXELS), baseline the suite - ABORT if it is
                    already red - and record its RUNTIME + pre-existing SCRIPT ERROR
                    count so gates judge NEW errors and can spot a parse-hang;
                    load .aaa/ledger.json so this run does not re-derive what earlier
                    RUNS already shipped or dismissed; **check for stranded blessed diffs**
                    (`git branch --list 'rescue/*'` + `Backlog.md` RECOVERY beacon) — if a
                    rescue branch holds a gate-perfect (`closeness ≥95`) diff whose commit
                    or ledger flush died on 429/529, do not launch dossier/review on top of
                    the mixed dirty tree: extract the pure accepted diff first (see mixture
                    section), re-gate it, then proceed

per cycle:
  DOSSIER   (opus 5)  capture frames from a REAL RUN (live_capture.gd) plus posed shots
                      for the screens a short run never reaches, GATE them
                      (verify_shots.py - a blank capture aborts the cycle), VIEW them,
                      write the NON-VISUAL half (audio, timing, feel)
  REVIEW    (gemini)  SEES the screenshots itself: is this top-tier FOR THIS KIND OF GAME? names the
                      giveaways vividly (where / what I see / why it outs it / best-in-class
                      version), >=3 of them fixable craft, never an empty list
  REVIEW-B  (opus 5)  a SECOND lens, blind to pixels: reads src/sim and RUNS it to measure.
                      Same schema, so dedupe/batch/confirm/gate carry it unchanged. It takes the
                      PRIMARY batch slot and the VISUAL lens gets the reserved one - measured, the
                      other way round starved it: the consumer reviewer must return >=3 fixable
                      items so it won every lead slot, re-worded the same tells each cycle, and
                      the real defects only ever got banked (see below)
  CONFIRM   (opus 5)  TWO jobs. (a) real flaw, or an artifact of how the shots were posed?
                      artifacts are dismissed, never built - the shots are staged, not played.
                      (b) VERIFY THE SPECIFICS against real code and MEASURE them, then restate
                      the finding as corrected_detail - which replaces the reviewer's version
                      downstream. already_fixed=true skips the cycle cheaply.
  PLAN      (opus 5)  plan that kills the top BATCH (default 2) fixable tells, each with
                      an automated check that MUST FAIL on current HEAD
  CODE      (opus 5)  writes the failing check FIRST, confirms it fails, then fixes
  GATE      (opus 5)  perfect? -> commit. else -> back to the coder with feedback + the
                      verified-good list (max 4). Out of attempts but the rest is sound?
                      -> revert just the bad files, re-run tests, commit the remainder
                      as a PARTIAL fix. Otherwise full revert.
```

The reviewer sees the SCREENSHOTS and nothing else — no code, no file paths, no commit
messages. That blindness to everything except the rendered frame is the whole point: it judges
what reaches a player's eyes, ears, and hands. It is told to ignore any studio name visible in
the art, since the title screen carries a byline a shopper would read as indie.

## How to run it

1. **Parse the count.** The number after the command is `N` (`/tripple-a-gamedev 5` -> 5 cycles).
   No number -> 1.

1b. **Check this doc against its own scripts.** Run `scripts/check_doc_drift.sh`. It exits 1 when
   SKILL.md claims something `scripts/` does not do. Fix the doc before you quote any figure in it.

2. **Resolve the project.** `ROOT` = the current Godot project. Find the Godot binary
   (`/Applications/Godot.app/Contents/MacOS/Godot` here) and the real test command from CLAUDE.md
   (this repo: `godot --headless --path . -s res://tests/run_tests.gd`).

2b. **Quote the cost before launching, and say which roster it was measured on.** A cycle here
   is not cheap: **~40 minutes for a typical cycle, ~95 for one that needs three coder attempts**
   (dossier capture + a multimodal review + a measuring confirm + plan + code + a gate that
   re-renders). Measured steady state over an overnight run was **~42 min/cycle**, so budget
   `/tripple-a-gamedev 20` at **12-20 hours**, not an evening.

   ⚠️ **RE-MEASURED 2026-08-21 ON THE CURRENT ALL-OPUS ROSTER: ~4.3 HOURS PER CYCLE.** A live
   `/tripple-a-gamedev 5` ran **21.5 hours wall-clock for 5 cycles** (88 agents, 0 errors, 5/5
   accepted). That is **6x the ~42 min figure below**, which was measured on the older mixed
   roster and is now a historical floor, not an estimate. Quote the 4.3 h number: `N=1` is an
   afternoon, `N=5` is overnight-plus, and `N=20` is not a thing to start on a weekday.
   The yield at that price was good — 5 accepted commits, 44 owner decisions, 96 banked findings —
   so this is a cost correction, not an argument against running it. Re-time again if the roster
   moves; an estimate carried across a model change is failure mode 2c wearing a result's clothes,
   and this entry is what that failure looked like when it fired.

   The older figures below were measured on a **mixed roster**.
   `wf_aaa.js` today runs 18 of its 20 agents at `model:'opus', effort:'high'` — only `verdict:${i}`
   (sonnet/low) and `snap:${i}` (haiku/low) are cheaper. Treat the figures above as an
   un-re-measured **floor** and re-time one cycle before quoting them as fact: an estimate carried
   across a model change is an INPUT wearing a result's clothes, which is failure mode 2c below.

   Quote the **yield**, not just the clock. One real window: 4 runs, ~14 hours, **2 game commits** —
   against 10 commits to this skill in the same window. Budget at most one skill-improvement pass
   per run; if the backlog already holds defects with `file:line`, fix those instead of launching.

   If you touch the roster, state which agents are opus *on purpose* so the next session does not
   flatten it in either direction. `commit` ("return the SHA"), `revert` (`git reset --hard`) and
   `ledger-load` ("read this JSON file") are mechanical and currently sit on opus/high; if the
   all-opus move was aimed at the ledger-paraphrasing bug, that argues for opus on `ledger:${n}`
   and `ledger-load` specifically, not on `git reset --hard`.

   Tell the user the estimate and what N they probably want *before* you launch. In an
   autonomous/background dispatch where the caller already fixed N (an overnight runner, a
   task prompt saying "run /tripple-a-gamedev 4 and wait"), do NOT block on a question — state
   the estimate in your status message and proceed.

3. **Require a clean tree, and say which BRANCH the cycles will commit to.** Each accepted cycle
   commits. If `git status` is dirty, tell the user and stop. Cleanliness is not enough: the shell
   inherits whatever branch the session happened to be on, and a clean side branch passes every
   check while quietly collecting release work. Observed 2026-08-23: a release-march loop launched
   from `feat/riot-shield-flank` — a docs-only branch, 2 ahead / 2 behind main, no upstream, parked
   on a pending owner decision — and only a deliberate `git log main..HEAD` before launch caught it.
   Print the branch and its ahead/behind vs the integration branch. An autonomous or
   release-marching run belongs on **main** (fetched, 0 behind origin) unless the user named a
   branch; committing cycles onto a side branch is a decision to surface, never a default.

4. **Launch the workflow** (invoking this skill IS the multi-agent opt-in):

   ```
   Workflow({
     scriptPath: "~/.claude/skills/tripple-a-gamedev/scripts/wf_aaa.js",
     args: { root: "<ROOT>", cycles: <N>, godot: "<godot path>", test: "<test cmd>",
             batch: 2, live: true }
   })
   ```

   It runs in the background. Do NOT edit files in `ROOT` while it runs — the commit step would
   sweep your edits in.

5. **On completion**, ALWAYS surface `obj.result.decisions` to the user, verbatim and up front —
   these are the product calls the run found and correctly refused to guess at (a gate stranding a
   required objective, a meta currency exhausted in ~10 runs, tiers that stop escalating against a
   README promising they do not). They are the highest-value output of a review and they are worth
   nothing if they stay in the return value. Same for `obj.result.backlog`: real tells the run SAW
   and did not spend budget on — a run that fixed 3 things has not made the game clean.
   Then read `obj.result.cycles` and report per cycle: verdict, confidence, the
   giveaway that was attacked, attempts, accepted or not. Run the full suite once more, confirm
   determinism goldens are intact (or deliberately re-recorded with a why-note), then push if the
   user is on a pushable branch. A cycle with `accepted: false` had its work **reverted**
   (`reset --hard` + `clean -fd`) so the next cycle could not inherit gate-rejected code and
   sweep it into its own commit — report which giveaway went unfixed, and note that nothing
   from it survives in the tree. A cycle marked `salvaged` committed only PART of its fix (the
   gate rejected some files, which were reverted) — its giveaway is deliberately left un-marked
   so a later cycle can finish the job, and its commit body says so. A cycle carrying `blocked` never reached the reviewer at all (its
   screenshots failed the gate); report those separately and treat them as "not run", not as
   "the game passed" — and fix the capture before spending another cycle.

## Driving this skill from a scheduler (/loop, cron, an overnight runner)

A recurring prompt ("run tripple-a-gamedev hourly until vX ships") re-enters this skill on a clock that has
nothing to do with cycle time — and at ~4.3 h/cycle on the all-opus roster, an hourly fire lands
mid-run **most of the time**. Two runs in one ROOT is not contention, it is destruction: both
commit, and either reject path (`reset --hard` + `clean -fd`) erases the other run's in-flight
work — the exact class failure mode 3b and the rescue-snapshot section exist to contain, with the
second run playing the part of the destructive command. First identified 2026-08-23 by arithmetic
at launch (60 m interval vs 4.3 h cycle), before it could fire; treat it as designed-against, not
survived.

So every scheduled fire is a **guard first, launcher second**:

- **Check for an in-flight run before anything else** — TaskList / `/workflows` for a live
  `wf_aaa` task, or the journal-mtime + live-agents check the "is it hung?" gotcha describes. If
  one is running: report status in one line and no-op the tick. Never launch a second workflow
  into the same ROOT, and never "help" the live run by relaunching a stage.
- **If the last run just finished**, this fire is the harvest step: do everything in step 5
  (decisions verbatim, backlog delta, suite re-run, push) BEFORE deciding whether to launch the
  next cycle. A scheduler tick that launches without harvesting orphans the previous run's output.
- **State the real cadence to the user once**: the effective loop rate is the cycle time, not the
  requested interval. An hourly loop over 4.3 h cycles is a ~4–5 h loop with skipped ticks, and
  saying so up front is cheaper than a user wondering why nothing committed at :07.

**When the driver ties VERSION bumps to cycles** ("increment 0.1 per loop if significantly
improved"): a version is an owner-visible release claim, so hold it to the same evidence bar as a
severity. A bump is anchored to **accepted commits with measured player-facing improvement** in
that window — never to banked findings, docs churn, dismissed/already-fixed verdicts, or a
`blocked` cycle (which is "not run", not "passed"). The default answer each loop is "no bump", and
the summary says which commits would have to exist for the next one. Same spirit as the difficulty
rule: the loop surfaces the evidence; inflating a version to show progress is the severity-
inflation failure wearing release clothes.

### Max parallel for ralph-style release marches

Ralph loop wants very large dynamic workflows: fan out confirm/plan/code across `BATCH*2` agents with `isolation:worktree` when touching different files.
Use file-disjoint worktrees — one agent per file group — so parallel edits do not contend on the same path.
The 60m tick vs ~4.3h cycle means most ticks no-op (guard first, launcher second);
between ticks the run can still fan out sub-workflows for fast-lane fixes in parallel worktrees.
This is proven: the play/view workflow ran 10 agents + texture-filter 7 agents in parallel worktrees successfully.
Any parallel Godot must use private `user://` via `tools/run_tests.sh`; raw `godot --headless` shares `user://` and corrupts logs/fixtures.
The wrapper (`mktemp -d` HOME) is what lets suites overlap safely — require it for every concurrent suite.
Invoke godot-prompter skills per subagent (e.g. `godot-ui`, `hud-system`, `particles-vfx`, `shader-basics`, `audio-system`).
Each worktree invokes its lens independently rather than once at the top.
Effective cadence remains the cycle time (~4–5h for an hourly ralph); max-parallel buys throughput *within* a cycle, not more cycles.

## Pieces

- `scripts/aaa_review.py <dossier> [out.json] [--shots DIR] [--model SLUG]` — the consumer
  reviewer. With `--shots` it SEES the screenshots (quantized PNG, never JPEG: JPEG ringing on
  pixel-art edges is itself a visual defect it would report as ours). Default
  `google/gemini-3.6-flash` via OpenRouter — kept there by a **known-answer OCR probe**, NOT by
  the speed/citation proxies. Re-benchmarked 2026-07-26: grok-4.3 won every proxy (faster, cited
  a shot in 5/5 findings vs gemini's 1/5, zero hedges) and then misread `$1,990` as `$1,890` on a
  hand-read HUD, the same class of failure that got kimi rejected. A misread number does not lower
  accuracy, it **invents a defect**, and that costs a whole plan/code/gate cycle — far more than any
  latency saved. Proxies measure phrasing; only the known-answer probe measures the thing that
  matters. Re-run `bench_reviewers.py` **and** an OCR probe before changing the slug, and never swap
  on proxies alone (full log: `aaa_review.py:29-47`). `kimi-*` slugs route to the flat-rate kimi.com endpoint.
  Keys via `~/.claude/skills/shoop/scripts/or_call.py` (aigate). Runnable standalone.
- `scripts/verify_shots.py <shots_dir> [--min-shots N]` — the capture gate. Exit 0 = real
  images; exit 1 = refuse to proceed. Runnable standalone; use it any time you need to know
  whether a screenshot pass actually captured anything.
- `scripts/wf_aaa.js` — the N-cycle workflow.
- `scripts/check_doc_drift.sh` — fails when THIS FILE asserts something `scripts/` does not do.
  No args; exit 0 = clean. Run it in pre-flight, before quoting any number below to the user.
  This loop's most-found defect class is "the view asserts what the sim does not do" (see that
  section) and SKILL.md/`scripts/` is an instance of exactly that pair — the doc had drifted on
  the reviewer slug's rationale, the pacing probe path, the model roster, and a whole capture
  gate. When it fails, **fix SKILL.md, not the check.**

## Godot skill wiring

Every Godot run MUST invoke the matching `godot-prompter:*` skill per the GodotPrompter SESSION-CARD before writing any Godot system code. Workflow plugins decide *how* you work; GodotPrompter decides *what* you build. `wf_aaa.js` grepped 0 for `godot-prompter` before this section — findings stayed generic while the play/view workflow used 5 skills (`hud-system`, `shader-basics`, `scene-organization`, `audio-system`, `godot-testing`).

| Building… | Start with |
|---|---|
| Movement, input, cameras | `player-controller`, `input-handling`, `camera-system` |
| Architecture | `state-machine`, `event-bus`, `scene-organization`, `component-system`, `resource-pattern`, `dependency-injection` |
| Gameplay / AI | `inventory-system`, `ability-system`, `save-load`, `ai-navigation` |
| UI / HUD / i18n | `godot-ui`, `hud-system`, `responsive-ui`, `localization` |
| Shaders / VFX / math | `shader-basics`, `particles-vfx`, `procedural-generation`, `math-essentials` |
| Physics / 2D / 3D, anim, audio | `physics-system`, `2d-essentials`/`3d-essentials`, `animation-system`/`tween-animation`, `audio-system` |
| Test / debug / review | `godot-testing`, `godot-debugging`, `godot-optimization`, `godot-code-review` |

Dossier, review, plan, code, and gate prompts MUST contain `invoke godot-prompter:<skill> before implementing` mapped per surface: HUD→`hud-system`+`responsive-ui`, shader→`shader-basics`, scene/layout→`scene-organization`, physics→`physics-system`, audio→`audio-system`, tests→`godot-testing`, etc.
Subagents do NOT receive the GodotPrompter SESSION-CARD (SessionStart hook fires only on startup/resume/clear/compact) — `wf_aaa.js` MUST explicitly pass the card text into every subagent prompt that touches Godot code.

Verify: `grep -c 'godot-prompter:' SKILL.md` ≥ 8 and `grep -c 'godot-prompter:' scripts/wf_aaa.js` ≥ 5 — 0

## The five failure modes this loop is built to avoid

All five were observed live, and all produce confident, plausible, worthless-or-harmful
output. Each has a gate; none of the gates are optional.

**1. Blank screenshots that report success.** A broken harness writes byte-identical black
PNGs and still prints `SAVED` for every one. The dossier agent then has nothing to look at,
falls back to reading source code, and writes a lush description of a game nobody rendered —
sourced from developer comments, which are aspirational and self-flattering by nature. The
blind reviewer then judges *the comments*. Nothing in the chain notices.
Hence `verify_shots.py`, run before the dossier is allowed to exist: it fails on identical
images, near-zero colour count (`MIN_COLORS = 12` — a real frame has far more, a flat fill has
1-3), and flat luma. **`SAVED` proves nothing. Only the gate does.**

There is a **fourth** check, and it earns its keep more than the other three: all-real,
all-different, richly-coloured frames can still be a soldier standing still. `MIN_MOTION = 5.0`
(`verify_shots.py:35` — mean consecutive-frame luma delta; an input-less run measures ~2.0, a
played one ~14.7) is what catches it. `demo_autoplay` was off for **45 cycles** before that check
existed, and every review in that window judged a bot dying in sector 1. It then recurred in the
*other* mode — `LIVE_MODE=endless` still stood at wave 1 long after campaign was fixed — so
**gate every mode you capture, not just the one you fixed.**

**The mirror image is equally true: an ERROR in a log proves as little as `SAVED` does.** A log
line is a record of a PAST event; the gate reads CURRENT state, and only one of those answers
"is it broken now". Confirmed live 2026-07-26 outside this repo, on a fleet log sweep: a scanner
reported four services whose last recorded launchd exit was a SIGTERM, and all four were
`state = running` with live PIDs — the signal was a restart hours earlier. In the same sweep one
server's log held 22 tracebacks while the port it serves answered `200`. Every one of the
scanner's findings was a stale event, and the discriminator was never a better grep — it was
probing the thing itself. So when a log, a `stderr` tail, or an editor console accuses something,
**re-read the state before you spend a cycle on it**: query the live value, hit the endpoint,
re-run the capture. Cheaper than the fix, and it is usually the whole answer.

**2. Findings that are artifacts of the screenshot staging, not the game.** The shots come from a
harness that hand-poses sim state — so a field the harness never populates looks broken in a shot
while being perfectly correct in a real run. Observed live: the reviewer flagged *"the victory card
brags SCORE 264,500 directly above 0 KILLS"* as a shipped bug. It isn't. The shot builder sets
`score` and never touches the kill counter; a real victory screen is fine. Left unchecked the loop
sends two opus stages to "fix" correct code — worse than doing nothing, because it burns a cycle **and**
edits a working game. Hence the **Confirm** phase between Review and Plan: it traces where the
values actually come from in live play and kills the target if it only exists because of the posing
(naming the staged field so the *harness* gets corrected instead).

**The capture TOOL can composite its own overlay, and it looks exactly like a game defect.**
Artifact sources are not only the posed sim state — the thing taking the picture can draw into
it. Observed live: a computer-use MCP renders a synthetic **agent cursor** into every screenshot
it returns, showing where the agent is pointing. It appeared as a large blue arrow over the
middle of the playfield. A blind reviewer would report "a huge system cursor sits over the
battlefield" as a top-tier giveaway, with total confidence, and be wrong. It took three checks to
kill: the real pointer was elsewhere on screen (`screencapture -C`, since macOS omits the cursor
by default and its absence proves nothing), the OS accessibility cursor was normal-sized and
default-coloured, and the game already bakes its own crosshair. Before believing any chrome-like
defect — cursors, focus rings, letterboxing, scale bars, watermarks, tooltips — reproduce it with
a SECOND, independent capture path. If it appears in only one, it belongs to the tool.

**A CONTACT SHEET is a capture tool, and tiling is three destructive transforms at once.**
Tiling many frames into one image is the obvious way to collapse the multi-image review payload
(costed once under Gotchas — do not restate it here) into a single attachment, and it is genuinely
the right tool for **triage**: measured 2026-07-26 on a
non-game sorting task, 525 photographs were classified into 8 buckets from 15 tiled sheets at 36
tiles each — **18 image reads instead of 525**. It is the wrong tool for **judging craft**, because
a montage applies three transforms whose output a blind reviewer will attribute to the game:

- **The downscale.** Averaging neighbouring pixels *raises* measured contrast on any thin feature
  and erases sub-pixel defects outright. The rim tell in 2c was real at **1.67:1 with 11.7% of rim
  pixels clearing 3:1**, and a banked gate finding was a **median 1.93/255 luma delta** on a tread
  decal. Neither survives a 200px tile in recoverable form. The findings this loop is proudest of
  are precisely the ones a resize deletes.
- **The encoder.** `aaa_review.py` already refuses JPEG because ringing on hard pixel-art edges
  reads as our defect — and ImageMagick's `montage` picks its format from the output *extension*,
  silently, so `sheet.jpg` reintroduces exactly that artifact behind a convenience flag.
- **Anything drawn into the frame.** Tile labels, gutter colour and padding are new chrome *inside*
  the image boundary. A reviewer instructed to report overlap and letterboxing has no way to know
  the caption belongs to the tool — this is the agent-cursor failure above with a different author.

Rule: **triage with sheets, judge with the full-res quantized PNGs.** If a sheet ever does feed a
reviewer, it must ship an explicit index→filename manifest as *text*, because a tile has no
identity except its position in the grid — which makes "the third image" a value compared by
position through a lossy channel, the same shape as the ledger-title rot below.

**And the annotation you added needs its own gate.** Both label attempts on those sheets failed
silently: `montage -label` with no `-font` on macOS prints one FreeType warning per file, **exits
0**, and writes sheets containing no labels at all; supplying an explicit font then rendered them
white-on-white. Absent, then present-and-unreadable, and both runs looked successful from the
outside — the same shape as `SAVED` proving nothing. `verify_shots.py` gates that the pixels are
real; nothing gates that a thing you drew *onto* them actually rendered. The fallback that saved
that pass is worth copying: identity came from strict row-major ordering over contiguous
filenames, which is checkable arithmetic, not text that has to survive a renderer.

**One step further: YOUR OWN activity is inside the data you are auditing.** The overlay case is
the tool drawing into its picture; this is the tool writing into its evidence. Confirmed live
2026-07-26 on a fleet sweep: a host showed **4,357 root sessions opened in 7 days**, which reads
as a total compromise — and they were all local `sudo`, a large share of them the audit's *own*
commands, landing in the log while it was being read. The loop's local instances are everywhere
once you look: the capture run writes to `user://` and the editor console, `difficulty_probe.gd`
gets staged into `.aaa/`, worktrees and reverts churn git state — and the next agent greps exactly
those surfaces. So **timestamp-bound and identity-bound the evidence before counting it**: filter
to before your run started, or exclude your own uid/PID/paths, and say which you did. An anomaly
you introduced two minutes ago is the easiest finding in the file to "discover".

**2b. A finding that is right about the smell and wrong about every detail.** This is the same
failure one level down, and it is the common case rather than the exotic one. Measured across one
session of eight implementation briefs derived from audit findings, **eight of eight** were
materially wrong somewhere: ratios that did not reproduce (claimed 1.36:1, actually 1.82:1), a
magnitude off by 8×, the wrong file, a rule that had moved, an assumption about which enemies a
test harness even reaches. Three of four items in one brief were **already fixed**, and one flagged
`i == 1` had become *correct* under a newer sim — "fixing" it would have reintroduced the bug.
So Confirm does not just ask "is it real": it opens the code, **measures** (running the sim
headlessly when that is what it takes — a value you did not execute is a hypothesis), and rewrites
the finding as `corrected_detail`, which is what Plan and Code actually receive. `already_fixed`
is a first-class outcome, because in a tree several agents are working, the cheapest correct
result is often "a sibling already did this."

**A class above a wrong detail: the finding can name the wrong OBJECT entirely.** In one backlog
pass four of six items did. One blamed `m_heli_attack2` — a decorative flyby with no hitbox — while
`main.gd` draws the endless boss from that same texture at a different call-scale; the texture was
shared, the object was not. Another named the harmless one of four identical unclamped cooldowns,
while its twin `bk["spawn_cd"]` fed a live view reader that painted an "about to spawn" glow at
−332 for **1,758 ticks (29 s)**. So: **grep every call site of the symbol, texture or constant a
finding names before concluding what it is**, and when you fan Confirm out, **pair each scout with
a skeptic**. The skeptics here overturned two claims inside an hour — one of which had already been
reported to the user as fact.

**The backlog count is not a defect count — collapse it before reporting or planning.** One real
ledger held 73 entries that were **~17 distinct problems** (one route fork banked 17×, tread art
10×, a HUD collision 9×), and the duplicates *disagreed*: the same telegraph recorded once at
"1.1 s" and once at "1.7–10.6 s". Report the delta by theme, and reconcile contradictions rather
than banking both — an inflated count makes a run look productive while the same seventeen things
stay broken.

**2c. A check can FAIL FIRST and still be green-but-wrong.** The fail-first rule stops you
pinning behaviour that already works. It does *not* stop you pinning the wrong *quantity* — and
a check that fails for the right reason, then passes against a number that never reaches the
player, is worse than no check: it certifies the tell as fixed forever. Observed live
(2026-07-26): the tell was "enemy silhouettes have no separator against the ground". The fix
re-enabled a "warm-light rim" and shipped a test asserting **4.70:1** contrast. The gate
re-captured frames and measured what the rim actually painted: **rgb(31,28,11) dark olive at
1.67:1**, with only **11.7%** of rim pixels clearing 3:1. Root cause: `draw_texture(t, pos,
modulate)` *multiplies* the source texture, and these sprites bake a near-black keyline on
exactly the edge being rimmed — so `sprite_edge x warm` is near-black, never the warm constant.
The test was reading `Art.TINT`, an INPUT, and calling it the result.

Rule for the coder and the gate: **a visual check asserts measured output, not a source
constant.** Sample the re-rendered frame (or the composited texture) and assert on those pixels.
If a check names a constant that appears in the code you just edited, ask what the compositor
does to it before trusting the number.

**Know a status field's ENCODING before you compare it, or you will manufacture failures.** Same
class, cheaper to hit: the number is real and you are reading it in the wrong units. Confirmed
live 2026-07-26 on a fleet sweep — `launchctl list` column 2 shows `-9` / `-15` for dozens of
services, and those are *signals* (SIGKILL/SIGTERM), not exit codes; read as exit codes they look
like a fleet-wide outage, and every one was healthy. The local instance is this loop's own habit
of killing orphan Godot processes: a process you SIGKILLed exits nonzero, so **a nonzero status
from a run you terminated yourself is not a failing test** — and treating it as one will send a
cycle at a suite that passes. Before a status number becomes a finding, state what encoding it is
in and what its "fine" value looks like. The fix that followed was to add a flat-white silhouette
copy of the sprite's own alpha so `white x modulate == modulate` — i.e. make the painted value
*equal* the asserted one, rather than assert the value you wished were painted.

**2d. Confirm must establish SEVERITY, not just reality.** "Is it real?" and "how bad is it?"
are different questions. The loop only builds BATCH targets per cycle, so its target order is a
priority queue — and severity is what should be setting that priority, which makes an inflated
severity a budget error, not just a wording one. Reports inflate severity by a whole class: they observe *geometry* and infer
*reachability*, but in a sim/view codebase those are decoupled. Observed live (2026-07-26): a
required gate lock was reported as **stranded inside impassable scenery — a softlock**. The
geometry was exactly right; the consequence was wrong. The blocking predicate had four call
sites, **all gating on-foot player movement and nothing else**, and the only thing that damages
that object is an explosion — whose projectile has **zero in-flight collision**, so it ignored
the blocker entirely. Measured: killable by one lob from either side, both scripted bots opened
the gate. Real severity: **minor legibility**, not a softlock.

**Severity is consequence x RATE, and the rate is the part you will get wrong.** Across one
session I misjudged four severities, in BOTH directions, and every time the missing input was how
often the path actually executes — never the mechanism, which I had right each time. A "softlock"
was minor because the blocked path was not the one that kills the object. A dropped batch slot I
called cheap (correct: findings are re-derived) turned out to be the run's dominant failure, because
draining a backlog makes "stale entry" the COMMON verdict and every such cycle had already paid for
a dossier and two reviews. Reasoning from mechanism alone gives you a plausible severity and a
wrong one. So state the rate explicitly — "this path runs on ~50% of cycles" — and if you cannot
estimate it, say that instead of picking a severity adjective.

**Inverse case, and this section will walk you into it: when the RATE is the loud part, the
consequence is the term you skip.** Everything above trains you to go find the rate — so a
finding that arrives with a huge rate already attached feels measured when it is half-measured.
Confirmed live 2026-07-26 on a fleet sweep: a host logged **4,629 failed SSH auths in 24 h** from
dozens of IPs, the single loudest thing in its journal and trivially quantified. Real severity:
**zero** — password auth was disabled, so the mechanism could not succeed at any rate, and seven
days of records showed **0 successes** against those 4,629 attempts. **A count of ATTEMPTS is not
a count of EFFECTS.** The check that settled it was a capability question ("can this path succeed
at all?"), which is the same shape as 2d's opening lesson — enumerate whether the damage path
consults the thing at all — and it costs one command. Ask it *before* you total anything up:
a big number times zero consequence is still zero, and it will otherwise top your priority queue.

Before accepting any "can't reach / can't progress / too hard" claim, enumerate (a) every
call site of the blocking predicate and which actor class each one gates, and (b) the actual
damage-or-progress path, and whether it consults that geometry at all. Then report severity from
what you measured. Ship the fix if the underlying authoring bug is real — but say plainly, in
the commit and the summary, that the original premise was overstated. A real fix under an
inflated headline teaches the next reader to trust the inflation.

**3. A reviewer that attacks what the game IS.** Asked flatly "is this AAA (EA/Ubisoft tier)?",
a deliberate 640×360 pixel-art arcade game gets told its giveaways are *being 2D*, *not having
a 10-hour campaign*, and *lacking online matchmaking* — all `structural`, all unfixable, and
the loop can never terminate or produce a usable target. The reviewer now judges production
value **for the kind of game it is** (Dead Cells / Hades / Katana ZERO tier for a 2D action
game), treats genre, camera, art direction and price tier as givens, spends at most one entry
on structural notes, and must return **at least 3 fixable craft items** — and must return
giveaways even when the verdict is AAA, since "best in class" never means "nothing to improve".

Measured effect of that reframing on one real dossier: 3-of-6 giveaways unfixable (wanting 3D
worlds and battle passes) → **6-of-6 fixable and specific** (a stage banner colliding with the
caption plate, a truncated menu label, a boss health bar hidden behind the verb legend).

**Modes 4 and 5 are under `## Verifying an edit to wf_aaa.js — `node --check` is necessary and NOT sufficient

This loop has now been bitten **three separate ways** by treating a green syntax check as proof.
None were syntax errors; all three shipped silently.

1. **A template literal missing its opening backtick PARSED FINE** and dropped a whole clause out
   of the emitted prompt (2026-07-26, the `baseline_valid` edit). The agent would have received
   truncated instructions with no error anywhere.
2. **`batchList` built from a target that was later retired read STALE** — correct syntax, wrong
   value, fails only at runtime.
3. **An ordering change put the behaviour lens where nothing could ever select it** — the producer
   ran, cost tokens, and its output was unreachable by construction.

So the recipe, in order, and none of it is optional for a non-trivial edit:

- **`node --check scripts/wf_aaa.js`** — catches real syntax breakage. Start here, never stop here.
- **RENDER THE PROMPT YOU CHANGED AND READ IT.** `node scripts/render_prompts.js <label>` prints
  what an agent actually receives, with concatenation seams collapsed and `\n` expanded. Broken
  quoting, dropped clauses, doubled sentences and stray escapes are all obvious on sight and
  invisible to the parser. `node scripts/render_prompts.js` with no argument lists every stage and
  its size — a stage that suddenly halves is a dropped concatenation.
  *(Mutation-verified: reintroduce the missing backtick and `node --check` still passes while the
  clause disappears from the render.)*
- **Simulate control-flow changes against real data** before trusting them. Target selection,
  batching and retirement are ordering logic — mirror the function in a scratch script, feed it
  actual findings from a recent run, and check WHICH item gets picked. That is how the
  behaviour-primary change was verified, and `node --check` says nothing about any of it.
- **grep for stale and duplicate declarations** after a region rewrite — `const` shadowing and
  leftover bindings survive a clean parse.

**The general rule this file keeps re-deriving:** verify the OUTPUT, not the mechanism. A parser
tells you the file is valid JavaScript. It does not tell you the prompt says what you meant, that
the value read is the one you set, or that anything downstream can reach it.

## Gotchas`**, ~250 lines below — *4. a binary gate that discards work
it just called correct*, and *5. a lens whose output can never reach the builder*. Mode 5 is the
write-only-producer rule and the single most reused lesson in this file; read it now rather than
trusting that a section promising five modes delivered all five here.

## A drain slower than the fill is still a graveyard

Wiring the backlog to the builder is necessary but not sufficient — check the RATES. Measured over
one overnight run: the backlog went from **12 to 37 entries in ~6 cycles**. Each cycle banks
roughly four new findings (the visual reviewer is required to return >=3, the behaviour lens adds
several more) and, with `BATCH=2` and one slot reserved for behaviour, drains about **one every
two cycles**. Net **+3.5 per cycle** — so the graveyard still grows, just slower.

That is not automatically wrong: discovery outpacing repair is what an honest audit of a real
codebase looks like, and a 20-cycle run cannot close 80 findings. What is wrong is letting it
happen *silently*, so the run reads as "we fixed everything we found." Two levers:

- ~~Pass `batch: 3` on long runs~~ — **tried, and it backfired. Keep BATCH at 2.** See below.
- **Report the delta, not just the list.** "37 open, +25 this run, 4 shipped" is the honest
  headline; "here are 37 findings" invites the reader to assume they are new.

**Be honest that this loop cannot converge on its own.** With `BATCH=2` and one slot reserved for
behaviour, the primary is the ONLY drain slot, so the ceiling is one backlog item per cycle — while
the visual reviewer is *required* to return >=3 fresh items and the behaviour lens adds more. The
arithmetic never closes: it is a **triage queue, not a work queue**, and no scheduling tweak inside
these constraints changes that. Say so when you report, instead of implying the list is shrinking.
If you actually want the queue drained, that wants a dedicated mode that skips the visual reviewer
and spends every slot on banked findings — not yet built, and worth building before another
20-cycle run.

### Triage the backlog ONCE up front, not one expensive Confirm at a time

A backlog persists across runs, so its oldest entries are precisely the ones a sibling session or
an earlier run has since fixed. The loop used to discover that only by spending a full Confirm —
opus, reads the code, runs the sim — per entry, *mid-cycle*, after the cycle had already paid for a
dossier capture and two reviews.

Measured on the run that motivated this: **Confirm returned real:1, not-real:1, already_fixed:3.**
Four of five verifications bought nothing. An earlier run lost three consecutive cycles the same
way and produced zero fixes in 2.5 hours. Retire-and-promote stopped those cycles being *abandoned*
but did nothing about the cost — the verifications still ran.

Pre-flight now batches it: one agent reads the whole seeded backlog against HEAD and sorts every
entry into fixed / unreal / open before cycle 1 starts. Runs only when the backlog has ≥3 entries,
since below that Confirm is cheaper than a dedicated pass.

**The asymmetry is the whole design.** `dismissed` means *never look at this again*, so a wrong
"fixed" buries a live defect permanently, while a wrong "open" costs exactly one Confirm — which is
the status quo. So `open` is the stated default and the prompt says to choose it whenever the two
are close. The title matching is a second safety net in the same direction: reclassification is
keyed on the normalised title, so if the triage agent paraphrases (which they do — see the ledger
note below), the entry simply fails to match and **stays open**. Verified by simulation across five
cases including reworded titles, unknown titles, and a title appearing in both lists.

### The gate is your best auditor — give it somewhere to put what it finds

Confirmed working on first use (2026-07-26): with a `found_not_fixed` field to write into, two gate
attempts banked **13 specific defects**, most of them outside their own assigned tell —
"tread decal alpha is below the perceptual floor (median 1.93/255 luma delta)", "`_tracks` and
`_track_prev` are not cleared on restart", "`_track_prev` is keyed on compacting sim indices and is
missing from the documented slot-reuse prune list" (the index-invalidation class that has already
caused one live crash in this repo), "three new probe tools are committed without their `.gd.uid`
sidecars", and one it flagged explicitly as belonging to a different cycle's goal "because I
measured it".

That is a better yield per token than the visual reviewer, and it is free: the gate is already
reading the diff and re-rendering frames, so it trips over neighbouring defects whether or not you
give it a field. Two practical notes: these accumulate **per attempt**, not per cycle, so dedupe by
title when banking (a 4-attempt cycle can report the same wart four times); and they are the one
finding class that is NOT re-derived next cycle, because they come from gating one specific diff.

### Tell the coder how close it already is

`BATCH=2` restored the gate scores the moment it was reverted — **closeness 93 then 82**, against
55/68 at batch 3. So that correction landed. But the second number is the interesting one: the
attempt went BACKWARDS, from one-item-away to a regression.

The cause is an omission. The retry loop feeds the coder `feedback` (what to fix) and
`verified_good` (what not to touch), but never the **closeness score**, so an attempt sitting at 93
gets exactly the same "implement this plan" framing as one that is half wrong — and goes wide when
the correct move is a one-line touch-up. Observed twice now: 93 -> 82 here, and an earlier session
logged the identical shape (attempt 3 one-away, attempt 4 regressed).

`restore-best` means the 93 is kept, so the cost is a burnt attempt rather than lost work — but at
`MAX_TRIES=4`, burning the attempt you were about to win with is the expensive one. The loop now
passes the previous score in, with the instruction scaled to it: at **>=85**, make the smallest
change that clears the feedback and nothing else — no refactor, no untouched-file edits, no
"while I'm here", no re-tuning a constant nobody objected to, because at that score the only way to
lose is to introduce a NEW problem. Below that, the score is framed as distance still to cover so
the coder re-reads the plan's success criteria instead of patching only what the feedback names.

General shape, and it is the same one as failure mode 5: a signal the loop already computes was
being used for control flow (pick the best attempt) but never shown to the agent whose behaviour it
should change.

### Widening the batch fights the gate — do not do it

Measured 2026-07-26, one cycle at each setting, and the mechanism explains the numbers:

| BATCH | gate closeness per attempt | salvageable | outcome |
|---|---|---|---|
| 2 | 85 -> 88 -> **93** | true | **accepted on attempt 3** |
| 3 | 55 -> 68 | **false, both attempts** | two rejections, >2h, still grinding |

Two independent reasons, only one of which is about sample size:

1. **The gate is all-or-nothing.** N targets means N independent chances for one regression to sink
   the whole batch, so the accept probability falls as the batch grows. Closeness fell from the
   high 80s to the 50s-60s.
2. **It disables salvage, which is worse.** `salvageable` requires that dropping whole FILES leaves
   a coherent tree. Three targets touch more files and tangle them, so the gate correctly reports
   `salvageable=false` — and the partial-credit path that failure mode 4 exists to provide stops
   firing exactly when it is needed most. That one is structural, not a small sample.

So a wider batch buys more attempted targets per cycle and pays with a much lower chance that ANY
of them land, plus slower cycles. `BATCH=2` (one visual + one behaviour, different surfaces by
construction) is the setting that both ships and salvages.

## Difficulty feedback: play it, but never trust the raw number

Pacing runs by **DEFAULT** — the run PLAYS the game and measures the curve instead of guessing at
it from still frames. Pass `pacing: ''` explicitly to skip it; override the string only if the probe
moved. The default (`wf_aaa.js:37-45`) stages `difficulty_probe.gd` into `.aaa/` and runs:

```
SEEDS=0xC0FFEE,1,2,3 MAXT=40000 MODES=campaign,endless CALIB=<root>/.aaa/calibration.json \
  <godot> --headless --path <root> -s res://.aaa/difficulty_probe.gd
```

It measures **campaign and endless**, and it **steps the sim rather than awaiting frames**
(~7,000 ticks/s vs 60 — a 4-seed campaign is minutes, not hours). It runs once per run (the sim is
what moves the curve) and writes three files: `.aaa/pacing.json` (this run), which it diffs against
`.aaa/pacing_baseline.json` (the previous run), and `.aaa/calibration.json` — the measured per-stage
baselines it LOADS and then updates, so the next run has something to diff against instead of
starting blind. The table feeds the behaviour lens every cycle so nothing re-derives it.

**Report the median with its `n`, never the mean.** One pathological seed owned the mean here and
produced a confident "48% of all deaths" headline that sent an investigation at the wrong sector.

**The one thing to get right: a knockdown count from a scripted bot measures THE BOT.** This project
lost a whole session to that error — a sector was "too hard" for 45 cycles and turned out to be a bot
that could not track a 20px disc drifting at 2px/tick, absorbing 6,200 ticks against a design budget
of 150-320. So the probe reports **`offense` = player kills per 1000 ticks**, and every costly stage
lands in exactly one bucket:

- **costly + offense near the median** → real pressure. A genuine outlier.
- **costly + offense COLLAPSED** → the driver cannot fight there. `instrument_suspect`. Never tune it.

That distinction immediately earned itself. Five independent cycles had flagged sector 3 as *the*
difficulty outlier (37% of all knockdowns, 4.75x its neighbour). Measured:

```
s1 knockdowns=2   ticks=1045   kills=40   offense=38/1000t
s3 knockdowns=66  ticks=11383  kills=159  offense=13/1000t   <-- 92% of ticks made NO progress
s4 knockdowns=2   ticks=879    kills=48   offense=54/1000t
```

Sector 3's offense is a **third** of the median and it fails to advance 92% of the time — the
signature of a bot stuck on geometry, not a hard fight. Five agreeing cycles were five readings of
one broken instrument. (Not conclusive: n=2 seeds, and s3's ticks sit near MAXT so it is truncated —
which is exactly why the schema has `trustworthy`.)

### "Instrument blind" and "the game is softlocked" are the SAME telemetry — separate them by velocity

The offense gate above is right and it has a hole big enough to hide a softlock in. Collapsed
offense means "something alive is not dying". *A bot that cannot aim* and *an enemy that is
physically stuck and cannot be fought* produce *identical* columns — and the gate labels both
`instrument_suspect`, whose whole meaning is **do not tune this, it is about the driver**. So the
one verdict that should escalate hardest is the one the loop was told to ignore.

Found 2026-07-26 by the behaviour lens, which had no difficulty telemetry at all and just drove the
sim: `_advance_toward` reverts **both axes** when a step lands in a rock / sandbag / hulk AABB — no
axis separation, no slide along the face, no re-path — so a walker whose vector points into a face
recomputes the same vector and reverts forever. Isolated repro: a rusher moved **0.0 px in 600
ticks** with the rock present, **340.8 px** with it removed. Census over 12 driven runs: **5 of 6
endless and 6 of 6 campaign** runs had a live ground mover frozen ≥600 ticks; the four unambiguous
cases froze for 9,006 / 10,943 / 16,466 / 17,637 ticks. In Endless this is not cosmetic — a wave
advances only when every hostile is dead, so one wedged rusher **holds the wave open forever**.

`difficulty_probe.gd` now tracks per-enemy position and reports a `froze` column, and a stage with
any frozen mover returns **`GAME_SOFTLOCK`**, checked *before* the blind test so it outranks it.
Re-measured on the same seeds: endless waves 7/8/10/11 flipped from `INSTRUMENT_BLIND` to
`GAME_SOFTLOCK` (8 frozen movers at waves 10-11), while the wave-5 miniboss — 15 knockdowns,
offense 4.2, zero frozen — correctly stayed `INSTRUMENT_BLIND`. Both readings are needed; neither
is a superset of the other.

**The third bucket, found 2026-07-30: stillness that is the unit's JOB.** A census of every
"frozen" mover after the slide fix found **zero real wedges** — campaign's ~43 were all
SUBMERGED frogmen (ambush lurkers holding position by design until NOTICE_RADIUS, grenade-
killable, in runs that finished 4/4 campaigns) and endless's were broadcast masts (stationary
aura structures; the waves kept advancing 8 → 14 while the "softlock" sat at y=-308). The probe
cried wolf for three days and the wolf drove a "biggest defect family" headline — the same
severity-inflation failure as the softlock reports above, one level up in the instrument.
`STATIONARY_KINDS` now includes `broadcast`, and submerged frogmen are excluded (a NON-submerged
one still counts — that IS the wedge class). The exclusion list is design knowledge: when a new
hold-position-by-design archetype lands, the list moves with it or the verdict lies. **Before
designing a fix for an instrument's verdict, census the instances.** One classification pass
turned "fix the movement code" into "fix the detector" — the slide fix shipped 2026-07-26 had
already killed the real class.

**Note this is the THIRD instance of the revert-both-axes class in this repo** (the fork-divider
fix at `sim_world.gd:1062` was the same bug for the *player*). When a class recurs three times,
seed the behaviour lens with it by name — recurrence is far cheaper to find than novelty.

### A delta is only a regression if the game AND the instrument held still

The DELTA is the difficulty signal that does not depend on how good the driver is — and that is
true only while nothing else moved. The moment the loop ships a balance change, the baseline is
measuring a different game; the moment the driver gains a behaviour, it is a different instrument.
Neither announces itself, and both look exactly like a regression.

Worse, it inverts the safeguard. `tunable` REQUIRES a delta as its anchor, so after a balance
change every stage shows a large delta, every stage reads as anchored, and the guard against
tuning on bot noise becomes a false-positive generator precisely when the game is moving fastest.

Observed 2026-07-26 on a live run: `calibration.json` was written at 17:48 and was still being
diffed against after **six shipped gameplay changes** (tank dominance, Riot Shield, MG-nest lead,
Endless war chest, campaign losing-end, river/bridge) **and** a driver change the loop itself
flagged — a new foot-sapper behaviour moved on-foot kills from **34.23 to 30.75 per 1000 ticks**.

So calibration now records the `head` sha and a one-line `driver` fingerprint alongside the
numbers, and the pacing stage compares both BEFORE reading any delta. Mismatch on either =>
`baseline_valid: false`, movement reported as context only, `tunable` left empty. A delta across a
balance change is a **re-baseline event**, not evidence.

**General rule:** a comparison against history is only valid while the things it did not measure
stayed constant. Record what those were, and check them before trusting the diff.

**Two rules that follow.** First, prefer the **DELTA**: an absolute "too hard" from a scripted bot is
unanchored, but "sector 3 went 19 → 31 knockdowns since the last measurement" is trustworthy no
matter how good the driver is — so the baseline diff, not the raw table, is the signal to act on.
Second, **do not let the loop tune balance.** Difficulty is an owner decision; surface the numbers and
the classification and stop. A previous session guessed at exactly this and nerfed a sector that was
never hard.

## A "reuse these titles" list becomes a checklist unless you scope it hard

Feeding the reviewer its own prior titles fixes rename-drift (the dedupe key is the title, and a
re-worded title matches nothing). It also has two failure modes, and BOTH were shipped and caught
within two hours of each other on 2026-07-26. Neither showed up in testing, because the mechanism
worked perfectly each time — titles WERE reused verbatim. The bug was always *which* titles.

**1. Never send SHIPPED or DISMISSED titles.** `seen()` filters anything matching them, so asking
the reviewer to reuse those titles means its finding is silently discarded. Measured: 4 of 5
findings matched shipped/dismissed and the whole visual lens filtered to nothing. The deeper
hazard is that a REGRESSION of an already-shipped fix would be reported, match, and vanish — the
loop goes blind to exactly the failure it most needs to catch. That hazard pre-dated the flag but
only fired by luck, because reviewers reworded; making reuse reliable made the blindness reliable.

**2. Never send titles the receiving lens could not have produced.** With shipped/dismissed
removed, the list became the open backlog — which the behaviour lens now dominates. Measured on
the very next run: the pixels-only consumer reviewer returned FOUR of five findings straight off
the list, only ONE genuinely new, and two of the four were sim-derived
("the camera is clamped so you cannot push north", "HOW TO PLAY mis-sells the armor") and
invisible in any frame. Downstream that reads as two independent lenses agreeing when it is one
lens reciting a list. Backlog entries now carry `lens: 'visual' | 'behaviour'`, `--known` sends
visual-origin titles only, untagged legacy entries are withheld (fail closed — the worst case is
a reworded title, i.e. the old behaviour), and the prompt says plainly: spelling aid, not a
checklist; if you cannot point at the pixels, do not report it.

**The general rule, and it is the one this file keeps re-learning:** validate the OUTCOME, not the
mechanism. "Does it reuse titles?" was the wrong question and it passed twice. "What does the
reviewer now report, and where does each finding come from?" was the right one, and it only got
asked by tracing five actual titles back to their source.

## The run's discovery is gitignored — persist it or it dies with the worktree

This file already contains the argument: the owner decisions "are worth nothing if they stay in
the return value." The fix that followed only made the loop PRINT them. Everything the run learns
still lives in `.aaa/ledger.json`, and `.aaa/` is gitignored — so `git worktree remove` deletes a
run's entire output, and the only durable copy is whatever a human pasted somewhere.

Measured 2026-07-26: one run held **32 open findings and 7 owner decisions**, including things no
amount of re-reviewing cheaply re-derives — the tank measured 3.6x safer AND 1.44x deadlier at
38.7% of a campaign, the Riot Shield's advertised counterplay disproved over 5,040 trials, 46-58%
of a campaign spent camera-pinned. Reconstructing that into a readable file took a full manual
pass over ledger JSON plus gate transcripts, and nothing in the loop would have done it.

A `Report` phase now writes and commits **`Backlog.md`** in ROOT at the end of every run: owner
decisions first, then findings grouped by what a reader would DO with them, measured numbers
copied VERBATIM (a paraphrased measurement is just an opinion), shipped items marked RESOLVED with
their sha rather than deleted, and the standing severity warning in the header. It merges rather
than overwrites, so successive runs accumulate instead of clobbering.

**The general rule, and it is the third instance of the same shape in this file:** a producer
whose output cannot outlive the process is decoration. Ledger backlog was write-only until it was
wired to target selection; `owner_decisions` was returned and persisted nowhere; now the whole
ledger was durable only inside a directory built to be thrown away. After adding any producer,
ask not just "who reads this?" but "what survives the worktree being deleted?"

## The ledger rides in a prompt every cycle, and it grows without bound

The section below says never let a model serialise state you compare by value. This is the other
half of the same problem: HOW MUCH state you hand it. The ledger is rewritten wholesale each
cycle, so its entire contents sit inside a prompt, and the backlog grows ~10 entries per cycle
while draining ~1.

Measured on one live run: at cycle 1 the backlog was 32 entries and the write prompt was 12,272
chars. By cycle 6 the backlog was **126 entries and 169,364 chars** — a ~170 KB prompt, every
cycle, handed to a model whose only job is byte-for-byte reproduction. That is the exact task that
produced the documented title-drift corruption, and the payload had grown 14x.

Two bounds, and the split between them is the point:

- **`detail` capped at 400 chars**, and **dropped entirely for entries older than 3 cycles**
  (replaced with a pointer to `Backlog.md`). Combined: **169,364 -> 48,504 chars, 71% smaller.**
- **TITLES ARE NEVER TOUCHED.** All 126 survive. They are ~80 chars, they are the dedupe keys, and
  dropping one makes the loop re-attack something it already settled. Bound the bulk, never the key.

**Cap at SERIALISATION, not at bank time** — this is the part that is easy to get backwards. The
in-memory backlog keeps full detail so the run's `Report` phase still writes complete measurements
into the committed `Backlog.md`. Truncating when the finding is banked would strip the numbers
everywhere, and the numbers are the only thing separating a finding from an opinion. What a LATER
run inherits is a head plus a pointer; what the repo keeps is the whole thing.

**General rule:** any state a loop re-sends every iteration must have a size bound, and the bound
must fall on the payload rather than the identity. Unbounded context growth does not announce
itself — it just quietly makes the fidelity task harder every cycle.

## Never let a model serialise state you later compare by value

The ledger is written by an agent, because a workflow script has no filesystem access. That agent
paraphrases — and the ledger's `title` field is the **deduplication key**. Every cycle asks "have I
shipped or dismissed this already?" by normalising the title and comparing it, so a reworded title
silently stops matching and the loop pays to re-attack a defect it already fixed.

Measured 2026-07-26, after several flushes:

- `"The MG nest's 30-tick aim lane is drawn but never fired down — and the HUD tells you to dodge
  it"` came back as `"MG nest telegraph never fires down drawn lane"`.
- A route-fork defect ended up in **both** `shipped` and `backlog` under two different wordings, so
  it reads as still-open forever.
- Of six titles checked, some survived byte-exact and some drifted. **Intermittent corruption is
  worse than total corruption** — it works often enough that you trust it.

Details fared better (56 of 73 entries kept their numbers, mean 511 chars), so the measurements
mostly survive; it is specifically the identity that rots.

The fix is a prompt that says COPY THESE BYTES, explains that the title is a comparison key, and
tells the agent to refuse rather than approximate if it cannot reproduce the JSON exactly. The
general rule is bigger than this loop: **any value you will later compare, hash, or join on must
not pass through a paraphrasing step.** If it must, give the record a short opaque id and compare
on that instead of on prose.

## Gotchas

- A 13-shot review is a ~2.3 MB payload (~25 s). Metered on OpenRouter — if cost matters,
  `--model=google/gemini-3.5-flash` is far cheaper and on a live probe it was the only model to
  catch a real content bug (desert art under a "36m of JUNGLE" caption). `--model=kimi-for-coding-highspeed`
  is flat-rate but misread the score on a pixel font, and a misread invents defects.
- Screenshots need a GL context: `--rendering-method gl_compatibility`, not `--headless`.
  On a Mac with a normal desktop session this works fine — if shots come out black, suspect the
  capture code (pre-render grab, a frozen scene, an overlay covering the frame), NOT the display.
- The capture tool will not create `SHOT_DIR`; `save_png` fails silently into a missing
  directory. `mkdir -p` it first.
- **A warm-but-STALE `.godot/` makes a visual loop review OLD PIXELS.** `Art.tex()` loads
  `.godot/imported/*.ctex`, not the source PNG — so after any merge or worktree copy that touched
  `assets/`, both the captured frames and every art test read the previous import. The whole cycle
  then judges, fixes and gates artwork that is not on disk. Copying `.godot` to start a worktree
  warm (the documented cure for the cold-import stall) is exactly what creates this. Compare the
  cache mtime against the PNG and re-run `--import` whenever `assets/` moved; a green art suite is
  not evidence the cache is current.
- **"Safe to stop between cycles" means BETWEEN.** The ledger flushes on a cycle OUTCOME, so a run
  killed mid-cycle leaves that cycle's gate findings only in the workflow journal
  (`…/workflows/wf_*/journal.jsonl`). Merge them into the ledger before relaunching — done twice
  here, recovering 13 and then 8 specific defects that would otherwise have been re-derived at full
  price. The same file answers "is it hung?": an unchanged ledger with dirty files and live agents
  is a normal long cycle, not a stall.
- **zsh `noclobber` silently aborts `>` onto an existing file — and that CORRUPTS the fail-first
  evidence.** Hit live by the coder agent: it "reverted" a file to HEAD to watch the new check go
  red, the redirect no-op'd, and the check's result described the unreverted tree. It only
  surfaced because the agent diffed before/after. Use `>|`, or `git stash` / `git show >` via a
  temp path, and *verify the revert landed* (`git diff --stat`) before believing a red or a green.
- **A comment asserting something is unreachable is a measurement with an expiry date.** When
  determinism goldens move, do not conclude you broke determinism until you have re-measured
  reachability. Observed live: three sim comments justified edits as "torture-inert — never
  streams past gate 1 (probe-verified — camera_top ends ~43 units short of gate 2)". Re-measured,
  the torture streamed two gates further and ended **563px past** that gate; the golden move was
  entirely expected churn. Better, the tick a thing first appears divided by the sample interval
  *predicts which samples move* — a tick-1309 construction at `SAMPLE_EVERY=600` first lands in
  sample 2, and samples 2-5 were exactly the four that changed. Predict, then re-record, then
  write the arithmetic into the re-record note. Leave a committed probe so the next person can
  falsify the claim instead of inheriting it. **The sharper variant needs no expiry date at all:**
  a comment citing an acceptance test that was never written — observed 2026-07-29, sim comments
  promising a 50-70% pilot-rescue catch rate and citing tests absent from the suite. Grep the
  test name before believing any coverage claim.
- **`already_fixed` must be tested BEFORE `real:false`.** A confirm can legitimately return both
  ("it does not reproduce *because* it is already fixed"), and whichever branch runs first decides
  whether the ledger records it as `shipped` or as a `dismissed` staging artifact. Those are not
  interchangeable: dismissed means "never investigate this again", and filing a genuinely-fixed
  real defect that way destroys the truth. Seen live 2026-07-26.
- **The commit the loop writes needs a BODY, not just a subject.** One overnight commit
  re-recorded determinism goldens under a bare subject line. The reasoning was in the
  re-record note (which is the load-bearing place, so nothing was lost) — but a golden move with
  no commit body reads like an accident to anyone doing archaeology later.
- **Moving a call into a loop moves its side effects relative to every early exit.** Wrapping
  Confirm in a retry loop pushed the "bank this round's findings" step below it, which quietly made
  the bail-out path lossy — it used to bank before Confirm ran. Caught only because the PREVIOUS
  run's backlog had grown purely from cycles that died at Confirm, so the new code would have shown
  zero growth where the old showed +17. When you relocate a call, list every `continue`/`return`
  between its old and new position and ask what each one now skips.
- Working artifacts land in `ROOT/.aaa/` (gitignored by the dossier step).

**3b. A commit step that silently no-ops, and a reject step that then destroys the evidence.**
The most expensive failure in the loop, because the work was already reviewed and paid for.
Observed 2026-07-26, cycle 3 of a live 20-cycle run: the gate passed at **closeness 96**, the
commit stage returned **the PREVIOUS cycle's sha**, and **781 insertions across 7 files** sat
staged-but-uncommitted. Nothing noticed, because nothing ever compared HEAD before and after.

Two ways that ends, both bad. The next cycle commits and silently absorbs the orphaned work under
the wrong message — so an accepted fix ships attributed to an unrelated giveaway. Or the next
cycle is REJECTED, and its cleanup (`reset --hard` + `clean -fd`) erases an **accepted** cycle
outright. Failure mode 4 below exists to stop the gate throwing away good work; this throws away
work the gate already blessed.

Both halves are now guarded. The commit stage captures HEAD before and after and must report a
FAILURE, not the old sha, if they match — plus `git status --porcelain`, because anything still
modified after a "successful" commit is an accepted cycle about to be lost. The reject stage
snapshots with `git stash create` and tags it `rescue/cycle-N` **before** discarding: a dangling
commit costs nothing, survives both destructive commands, and makes the cleanup reversible.

**The general rule: verify the side effect, never the intent.** "Run git commit" is an
instruction; "HEAD moved" is a fact. Every irreversible step in a loop should assert the fact.

## The rescue snapshot could not recover what the destructive command deletes

Failure mode 3b added a `git stash create` snapshot before the reject path's
`reset --hard` + `clean -fd`, on the stated promise that "nothing is ever unrecoverable." That
promise was false for two months, in exactly one category — and it is the category `clean -fd`
exists to remove.

The two rescue sites were **asymmetric**, and the weaker one guarded the destructive step:

| site | command | captures untracked? |
|---|---|---|
| `snap:${i}.${tries}` (mid-attempt) | `git add -A -- . ':!.aaa' && git stash create` | **yes** |
| `revert:${i}` (the reject path) | bare `git stash create` | **no** |

⚠️ **The fix in that table was itself broken for every correctly-configured repo — corrected
2026-09-04.** `git add -A -- . ':!.aaa'` **exits 1** whenever `.aaa/` is gitignored, which this
skill *requires* it to be: naming an ignored path in a pathspec makes git refuse with *"the
following paths are ignored… use -f"*. So the `&&` never fired, nothing was staged, and the
snapshot fell straight back to tracked-only — reintroducing the exact hole this section exists to
close, wearing the fix's clothes. Both sites now read:

```
git add -A -- . ':!.aaa' 2>/dev/null || git add -A -- .
```

correct in both configurations (verified in a scratch repo each way: captures tracked **and**
untracked, never captures `.aaa`, because when `.aaa` is ignored gitignore already omits it and
when it is not, the first form succeeds and excludes it).

**How it surfaced is the reusable part: it killed a 25-cycle run, and not by failing.** `snap` is
`haiku`/`low` and its schema is one string, so the agent treated the exit-1 as noise, improvised
its way to a valid SHA, and then emitted `<StructuredOutput>` as literal *text* instead of calling
the tool — `agent({schema}): subagent completed without calling StructuredOutput`, three hours in,
with a gate-blessed 92/100 diff sitting uncommitted in the tree. Two of the three snap stages that
cycle recovered and one did not, which is the signature to watch for: **a command that fails but
is usually recovered from is not a working command, it is a coin-flip that pays for itself in
whole runs.** A broken first command is an improvisation surface, and improvisation is where an
agent stops following the output contract.

### …and the pathspec was only half of it: an output filter was eating the SHA

Fixing the `git add` did not stop it. The very next run died at the SAME stage, 13.7 hours and
five accepted cycles in. The rest of the cause, and it is the more transferable half:

**A bare `git stash create` never returned the SHA at all.** The session's shell sits behind a
token-reducing proxy (`rtk`) wired in by a hook, which rewrites a lone `git …` invocation and
prints a *summary* in place of the command's real stdout. The transcript is unambiguous:

```
git stash create                       ->  ok stash create          # SHA discarded
SNAP_SHA=$(git stash create); echo …   ->  SNAP_SHA=b2ba2ed4a6de…   # SHA survives
```

The command always succeeded. Its output was rewritten in flight, and the one value the stage
exists to produce was the value thrown away. The agent then spent four tool calls fighting its own
shell, found the `$(…)`-capture workaround, and — having burned its turn on plumbing — emitted
`<StructuredOutput>` as text again. **Both failures were the same shape: make the first command
not work, and the agent stops obeying the output contract.**

Two rules follow, and the second is the one that generalises past this loop:

1. **Any stage whose whole product is a captured value must read that value in a form an output
   filter cannot summarise** — `X=$(cmd); echo "X=$X"`, or a pipe. Both defeat it; a bare
   invocation does not. The prompt now says so explicitly, and says that returning an empty string
   beats reconstructing a SHA by hand.
2. **This is failure mode 2's tooling twin.** That mode says the capture tool can composite its own
   overlay into the picture; this says the *shell* can rewrite the answer on its way back. Same
   lesson, different layer: your own instrumentation is inside the data you are reading. When a
   command's output looks like a status word rather than the value you asked for (`ok stash
   create` where 40 hex characters belong), suspect the plumbing before the command — and check by
   running it in a shape the plumbing does not recognise.

`git stash create` with nothing staged snapshots TRACKED modifications only. `reset --hard`
handles those. `clean -fd` on the very next line handles the untracked ones — which the snapshot
does not hold. Proven in a scratch repo rather than argued:

```
bare `git stash create`      ->  captured: tracked.txt          (untracked_dir/ NOT captured)
git reset --hard && clean -fd ->  untracked_dir/ DELETED
recoverable from snapshot     ->  0 files
```

and the fix, same harness:

```
git add -A -- . ':!.aaa' 2>/dev/null || git add -A -- .   # see the warning above: the
                                                          # bare ':!.aaa' form exits 1
git stash create              ->  captured: tracked.txt, untracked_dir/work.txt
git reset --hard && clean -fd ->  untracked_dir/ deleted from disk
git checkout rescue/cycle-1 -- untracked_dir  ->  restored: precious
```

**Found because it nearly fired.** Pre-flight on 2026-08-20 found `.todo-worktrees/` in ROOT:
**316 MB, seven registered git worktrees, each holding an unmerged commit**, untracked and not
ignored. One rejected cycle would have removed all seven. The commits themselves would have
survived on their branch refs — but the worktrees, their registrations and the disk state would
not, and the rescue tag would have held none of it.

Two rules, and the second is the transferable one:

1. **A snapshot taken before a destructive command must cover the same set that command targets.**
   Enumerate what each half destroys — `reset --hard` takes tracked modifications, `clean -fd`
   takes untracked files and directories — and check the snapshot against both halves, not one.
2. **`clean -fd` skips ignored paths (it needs `-x`), and the script already relied on that** to
   protect `.aaa/`. Nobody generalised it. Anything untracked and valuable in ROOT should be
   gitignored *before* a run that can reject, which is one line and permanent. The pre-flight
   should say so: `git status --porcelain` showing an untracked directory is a standing hazard,
   not just an untidy tree.

## An API-killed stage strands work the gate already blessed — and the run's own logs lie about it

Failure mode 3b covers a commit stage that no-ops while CLAIMING success. This is the
infrastructure variant, paid for 2026-08-24 (run wf_a7d3399b-122, a 529-Overloaded storm followed
by the session usage limit): the stages themselves DIE, the workflow's narration carries on
regardless, and three separate lies land in the transcript at once. Measured, one run:

- Cycle 1's fix passed its gate at **closeness 96** — then `commit` and the ledger flush both died
  on 529. The accepted diff sat uncommitted, **and the ledger still recorded the finding as
  `shipped`** (the in-memory state was written by an earlier flush and the un-shipping never ran).
  A shipped-but-not-committed entry is the worst state the ledger has: the dedupe makes the loop
  permanently blind to a defect that is still live at HEAD.
- Cycle 3 was rejected and its `revert` stage died — yet the log printed the standard
  *"working tree reverted to HEAD"* line, because the script narrates its intent, not the agent's
  outcome. The tree actually held cycle 1's accepted work MIXED with cycle 3's rejected attempt in
  the same files.
- The final *"Backlog.md written: N findings"* line printed while the report agent died on the
  usage limit. `git status` showed Backlog.md untouched.

The recovery procedure, in order — it worked and lost nothing:

1. **Read the journal, not the logs.** `journal.jsonl` holds each agent's real return; the log
   lines between them are narration. A `result` line is evidence; a phase caption is not.
2. **Reconcile the tree against the journal's gate verdicts** before anything destructive: an
   accepted gate + unmoved HEAD = stranded blessed work; a rejected gate + dirty tree = the revert
   died. Both at once = a mixture you cannot commit (ours held a −88% contrast regression the gate
   had explicitly rejected).
3. **Rescue-branch the mixture** (`git add -A && git stash create` → `git branch rescue/<run>`),
   then reset clean. A branch, not a tag — the pre-flight's unmerged-branch inventory only lists
   branches, so a later Confirm can find the work there.
4. **Un-ship the phantom in the ledger** and bank a RECOVERY entry at the top of the backlog:
   where the blessed diff lives, what rejected residue is tangled with it, and the instruction
   *extract, don't re-derive*. Also try the per-attempt snap commits first (`git fsck` dangling
   commits, fingerprint by parent sha + diffstat against the gate's stated numbers) — a surviving
   snapshot of the accepted attempt makes the split mechanical; ours had been taken before the
   acceptance and only held scratch probes.
5. **Write Backlog.md from the reconstructed ledger** — the result JSON in the task output is the
   complete in-memory final state even when every disk flush died; merge it in.

Sizing note that follows: a run that will cross a usage-window boundary donates its tail to
exactly this failure. When the recent window shows 529s or a limit reset time is known, size
`cycles` so the run finishes inside the window — a completed 2-cycle run beats a 3-cycle run that
loses its third cycle, its revert, and its report.

### A mixture of accepted and rejected in one tree must not be committed as one

The recovery above snapshots the *mixture* — and the next step after it is to **not commit that
mixture**. Paid for 2026-08-24: a gate blessed a smear fix at closeness 96 (`screen_fx.gdshader`
focus-anchored ramp + `main.gd` focus/spare, probe 0.98 vs 0.04) and then the revert died, leaving
that accepted diff tangled with a rejected choke slab (`choke_band_span` + `ground_slab` /
`choke_slab_rect`, lane-seal SEALED contrast −88%, trench tint −61%, gate salvageable:false). The
dirty tree at next session start had `fix_is_pure_smear:false` — 6 files, 2 from the rejected
cycle. Committing the mixture ships a gate-rejected regression under an accepted commit message,
and the ledger then marks the tell shipped while HEAD is still defective.

So after rescue-branching the mixture: **extract, don't commit**. Diff the rescue branch against
its pre-mixture parent and allow-list only the accepted files (here: `screen_fx.gdshader`,
`main.gd` focus/spare plumbing, `tools/probe_concussion_hud.gd`, `tests/test_view_honesty.gd`);
if a per-attempt snap commit exists that matches the gate's diffstat (`+444/−32` vs `21290ee`)
that snapshot is the pure accepted tree and is mechanical to restore. Re-gate the extracted tree
before bumping a version — a version bump on a mixture is worse than no bump, because the call
site that consumes versions (ralph, changelog) then lies about what is fixed. Do not `git add -A`
a mixed tree; stage the allow-list and verify `fix_is_pure_smear` before the commit.

### The RECOVERY beacon is a record of a PAST event — check whether it already landed

The pre-flight rule above says a rescue branch holding a gate-perfect diff must be extracted
before anything launches. It never says to check whether someone already did. Measured 2026-09-05
at launch: `rescue/wf122-smear-mix` still existed, `Backlog.md` still opened §2 with the RECOVERY
entry ("must stay first until that branch is landed"), and the ledger still carried two open
entries for the knockdown smear — while `git log main -S'smear' -- src/view/screen_fx.gdshader`
returned **b9fdf03, landed twelve days earlier**. Followed literally, the pre-flight would have
re-extracted a diff that was already at HEAD. The beacon, the branch and the ledger are all
records of the moment the run died; none of them is updated when the work lands by another route.

So the rescue check is two questions, in this order:

1. **Did it land?** For each accepted file the beacon names, `git log <integration> -S<symbol>
   -- <file>` (or `git log --grep` on the beacon's own words). A hit means: delete the rescue
   branch, retire the beacon and the ledger entries, and say so — the backlog-triage pre-flight
   will retire the ledger side on its own only if the entries are ≥3 and it matches titles, so
   do not rely on it for the branch or the Backlog.md header.
2. **Only then** extract. A rescue branch whose accepted half is already at HEAD holds nothing
   but the rejected residue and scratch probes (here: 874/−1251 lines of test churn and four
   `probe_*.gd`), and re-gating that is a cycle spent buying a regression.

Same rule as failure mode 1's log sweep, pointed at the loop's own beacons: the artifact says
what was true when it was written, and the cheap check is the current state.

## A green local suite is not a green pipeline — check CI in pre-flight

The baseline gate refuses to start on a red SUITE, for a well-argued reason: a gate cannot tell
"my change broke it" from "it was already broken." That argument applies verbatim to CI, and the
pre-flight had **zero** awareness of it (`grep -ci 'gh run' wf_aaa.js` returned 0).

Measured 2026-08-20 on this repo: the last two completed CI runs on `main` were **failing** while
the local suite passed **1116 methods / 26,644 assertions clean**. The red was
`python3 tools/i18n_check.py` — a lint step **no test invokes** — catching two hint strings that
had shipped without their `.po` entries. Two sessions in a row had ended at "pushed" and never
looked. A five-cycle run was about to launch on top of it, and every cycle commits.

The baseline agent now reports `ci` alongside `green`. It does **not** abort: a red CI on someone
else's commit is context, not this run's failure. But it must be said out loud, because a run that
pushes onto an already-red pipeline cannot tell you whether it broke anything.

**And the obvious probe lies.** `gh run view --log-failed` frequently returns only post-job
CLEANUP noise — credential teardown, orphan-process reaping — and not the failing step; reading
that tail produces a confident wrong answer about why CI is red. Get the job id from
`gh run view <run> --json jobs`, then `gh run view --job <id> --log` and grep for the step's own
command.

**"Red" is not a severity — count the reds and find the job's FIRST appearance.** The rule above
reports `ci` as red/green, and a red on someone else's commit as context. That framing missed a
whole class for twelve days. Measured 2026-09-05 at launch: `main` was red on **~20 consecutive
runs** — every push and every nightly since 2026-08-24 — and every other job (3-OS test matrix,
lint, perf, soak, export-smoke) was green. Walking the one failing job back through
`gh run view <run> --json jobs -q '.jobs[] | select(.name=="gl-capture") | .conclusion'` per run
reached its first appearance (e133d1f, "GL capture gate — shader regressions now go red on CI")
**before it reached a single green**: the gate was born red. The probe it runs reads ~1000 px of
baseline HUD motion on the xvfb runner against a 400 px ceiling, reports INCONCLUSIVE, and the job
counts that as failure — a gate that cannot pass, so its red carries no information about any
commit and nobody had looked at it since the day it shipped.

Three consequences for the pre-flight:

- **Report the streak, not the colour.** "red" and "red for 20 runs, this job only, never green"
  are different findings; the second names the class (a broken gate, not broken code) and the
  first invites "context, proceed" forever.
- **A born-red job is fixed on the GATE, on a side branch, in parallel** — not by blocking the
  launch and not by leaving it. Hand it to a worktree agent with the "never touch ROOT while the
  loop runs" rule and the same bar the gate section applies to probes: fix the cause (frame
  pacing, sim ticks between captures, an idling glyph), never raise the ceiling, never let
  INCONCLUSIVE count as OK, and verify by watching the branch's own CI run go green. Merge it
  after the run — the loop cannot see a mid-run merge anyway.
- **A nightly schedule that nobody reads is not a backstop.** Thirteen scheduled failures in a
  row produced zero action because the signal had no consumer — the write-only-producer rule
  (failure mode 5) applied to CI. If the pre-flight is the only reader, it must be the one that
  counts.

**4. A binary gate that discards work it just called correct.** With accept-or-revert as the only
outcomes, three consecutive runs produced almost nothing: the coder kept landing a fix that was
~80% right, the gate rejected the whole thing over one regression, and the next cycle started from
zero and re-derived the same defect. Real rejection text from those runs opened with *"VERIFIED
GOOD (don't touch, don't redo)"* — and then it was all thrown away regardless. The gate now emits
`verified_good` (fed verbatim into the next attempt so it stops re-litigating settled work) and,
on the last attempt, `salvageable` + `revert_paths`. If dropping those files leaves a coherent tree
that still passes, the remainder is committed as an explicitly PARTIAL fix. Guardrails: the suite is
re-run AFTER the revert (reverting can break what remains), file-level only (a half-reverted file is
worse than none), and a salvaged giveaway is not marked shipped, so a later cycle can finish it.

**5. A lens whose output can never reach the builder.**

Adding a lens is not the same as wiring it in. The behaviour lens was added, ran at
`effort:'high'` every cycle, produced genuinely better findings than the visual reviewer — and
for its first full run **none of them could ever be built.** The target selection was
`all = visual.concat(behaviour)` then "take the first BATCH fixable", and the visual reviewer is
*required by its own prompt* to return at least 3 fixable craft items. So the slots filled with
visual tells every cycle and the behaviour findings went straight to backlog. Not a tendency —
near-deterministic.

The live proof: the lens reported an anti-camp mortar whip that fires almost entirely during the
fights that legally forbid you to advance (70% of its spawns), a dodge roll with **literally no
cost** (A/B'd at 2.1x traversal and 58% fewer knockdowns for pressing a free button), and a
difficulty curve peaking at the **mid-game** boss and then decaying into an 18-second finale.
The cycle spent both slots on a contrast tell and a toast overlap.

**UPDATE 2026-07-26 — the first fix was too timid; behaviour now takes the PRIMARY slot.**
Reserving behaviour a *secondary* slot fixed the starvation but kept the priority backwards, and
two cycles of one 20-cycle run showed why that is the wrong way round. The visual reviewer is
*required by its own prompt* to return >=3 fixable craft items, so it won the primary slot every
time — and it returns the same tells re-worded each cycle ("Text Contrast and Screen Cluttering"
-> "Text Contrast and Background Collision"; "Generic Box-Border Menu Framing" -> "Developer-Art
Menu Container Layouts"), which the title-keyed dedupe cannot catch, so the lead slot re-derives
the same three notes forever. Over those same two cycles the behaviour lens produced a wedged
mover that holds an Endless wave open forever (isolated repro: 0.0 px in 600 ticks; census: 5 of 6
runs), a mortar that punishes the gate objective while the camera clamp forbids the advance it
demands (46-58% of every campaign measured as pinned), and an advertised counterplay that is
geometrically impossible (5,040 trials, 774 rounds on target, 774 blocked, zero kills).

So the order is inverted and **the reserved slot flips to visual** — symmetric, because a
behaviour-only batch would reproduce this same starvation mirrored. Backlog draining still wins
the primary slot on odd cycles (that lever is independent and measured). Verified by simulating
the selection against the real cycle-1/2 findings, not by `node --check`, which passes on every
ordering bug in this region: even cycles lead with behaviour + one visual extra, odd cycles lead
with the backlog, retire-and-promote still advances instead of abandoning the cycle, and
structural findings stay filtered.

Historical note — the original fix: `wf_aaa.js` reserved one extra slot for the top unseen
behaviour finding when one exists, so
a `BATCH=2` cycle attacks one visual tell and one behaviour defect. This also satisfies the
existing "extras must touch a DIFFERENT surface" rule for free — a sim fix and a view fix are
maximally different surfaces.

**The general rule: after adding a producer, trace one of its outputs all the way to a commit.**
If you cannot name the line where it gets selected, it is decoration you are paying inference
for. Check the ordering, the cap, and every filter between the producer and the builder.

**Check the REFERENCE, not the part.** Every instance of this class looks identical from the
part's side: the lens exists, the backlog is populated, the decisions array is filled — and
nothing consumes them. So the check is never "does the producer look right", it is *grep the
consumer for the producer's name and read the line you find.* Confirmed again 2026-07-26 outside
this repo: three autofs map files were each perfectly correct and the one line in `/etc/auto_master`
REFERENCING them was missing, so the mountpoint was an ordinary empty directory and nothing
errored anywhere.

*Corollary:* when N sibling things fail at once, suspect the shared parent, not N causes. Three
unrelated shares dead simultaneously meant one config file; this loop's own instance was the
`user://` log collision that hit 3 of 6 parallel agents, where the temptation was to re-litigate
six clean diffs.

That rule immediately caught a second instance in this same file: **the ledger `backlog` was
write-only.** It was appended to every cycle, persisted across runs, and returned in the result
— and never read as a target source, so nothing could be built from it, while this very document
claimed the opposite ("still open and still fair game to attack"). It was found holding 12
entries, seven of them gameplay defects (an MG nest drawing an aim lane it never fires down, a
claymore that kills you 4 ticks after you plant it, a sandbag that eats 100% of your own
outgoing rounds). Fresh review now leads on even cycles and the oldest open backlog entry takes
the primary slot on odd ones, so a long run drains known defects instead of only ever answering
what the reviewer noticed this morning. Two producers, same bug, found minutes apart — assume
your third one has it too until you have traced it. **And a fourth turned up the next morning:**
the gate's `owner_decisions` went into a `decisions` array that was returned in the result and
persisted NOWHERE, so every entry evaporated at run end. Worse, the gate was using the field as a
dumping ground for real defects rather than product calls — one overnight run filed "the HOW TO
PLAY title is clipped off the top (identical on HEAD, verified by capture)" and "REBIND's P1|P2
selector renders two identical plates both reading PLAYER" as *owner decisions*. Unlike a lens
finding, these are **not re-derived**: they come from gating one specific diff, so unbanked means
gone. Fixed by persisting `decisions` in the ledger and adding a `found_not_fixed` field that is
banked into the backlog, with the schema now saying plainly which field a defect belongs in.

**A retired primary used to end the whole cycle — FIXED, and the severity I first assigned was
wrong.** When Confirm returned `real:false` or `already_fixed`, the loop `continue`d, dropping
every other slot including the reserved behaviour finding. I first called this cheap, on the
grounds that both lenses re-derive their findings every cycle so nothing is permanently lost.
That reasoning was right and the conclusion was still wrong, because it priced the wrong thing:
what the cycle loses is the dossier capture and both reviews it ALREADY PAID FOR.

Then the rate made it fatal. Draining a backlog means feeding Confirm the OLDEST entries, which
are exactly the ones most likely to be stale — so "not real" and "already fixed" become the
common verdicts, not the rare ones. Measured with a 56-entry backlog: **three consecutive cycles
died at the first confirm, and the run produced zero fixes in 2.5 hours** while 4-7 fresh findings
sat unbuilt in each abandoned batch.

Now the loop retires the candidate and promotes the next one: `fixable()` re-reads
`shipped`/`dismissed`, so re-running `candidates.find(fixable)` after the retirement advances by
itself. Simulated before shipping — three stale entries retired (one to `shipped`, two to
`dismissed`), promoted to the real item, behaviour slot intact, terminated in four iterations.

⚠️ The trap, paid for once: `batchList` MUST be computed after the loop. Build it from a target
that is then retired and it is read while stale — and `node --check` passes, so it only fails at
runtime. A first attempt at this refactor was abandoned mid-way for exactly that reason; rewrite
the region in one pass with explicit line splicing, keep the Confirm template verbatim, then grep
for duplicate and stale declarations before trusting a green syntax check.


## Why each pre-flight and gate exists

Every one of these was paid for by a real run, not designed in the abstract.

**Baseline, and delta-gating.** A dev-only autoload landed in `project.godot`, the suite went
red, and every gate rejected work for a pre-existing failure — 6 cycles, ~3 hours, zero output.
A gate cannot distinguish "my change broke it" from "it was already broken", so the run now
refuses to start on a red suite and records the pre-existing SCRIPT ERROR count for gates to
compare against.

**Real frames over posed states.** `tools/screenshots.gd` hand-poses sim state, and a field it
forgets to pose renders as a bug: the victory card was captured showing `0 KILLS` because the
builder set score and never touched the counter. The reviewer reported it, correctly, and a
whole cycle went to "fixing" working code. Frames from a run that actually happened cannot lie
that way. Posed shots still run, for the menu/victory screens a 15-second run never reaches.

**Batching.** The reviewer returns 4-6 detailed giveaways; acting on one and discarding the rest
meant paying to regenerate the same list next cycle — tile seams were re-found in five
consecutive cycles.

### Fast-lane for view-only / config-only fixes

A full dossier → review → review-B → confirm cycle for a one-line config change is waste. Measured 0.4→0.5: the texture-filter fix (`project.godot`, `textures/canvas_textures/default_texture_filter` `3`→`0`, `Nearest`) was **one line, view-only, no sim, no `checksum()` touch, no golden move**, suite stayed **1166/37693 PASS** — but the run still paid a full **~4.3 h cycle** (dossier capture + 2 reviews + confirm) to approve it. The gate's own `.ctex` staleness check was wrong for this class: texture *filter* is applied at draw time, **`.ctex` mtimes do not change** for a filter flip and `re-import` is a **NO-OP** — asserting a cache miss here gates on a file that never moves.

**Eligibility — all must hold, or use the full loop:**

- **Single file**, and that file is one of `project.godot`, `*.import`, `*.gdshader` — no `src/` edit, no multi-file batch.
- **Pure view.** `grep -R <symbol|resource> src/sim` returns **0 hits**, and `SimWorld.checksum()` does not cover the changed key — so **no golden re-record** is possible by construction.
- **No gameplay constant moves.** The changed value is a renderer/import hint (filter, compress mode, shader uniform default), not a number the sim or a HUD layout reads for placement.

**Reduced flow — skip dossier/review, keep the gates that matter:**

`confirm (is it real? one grep + one live capture if needed) → plan (one failing check: suite red or a --check-only parse probe that names the file:line) → code (one edit) → gate (suite + tools/lint_sim.gd + godot --check-only -s <touched>)` — no `verify_shots.py`, no reviewer, no second lens. The ledger still records the fix as `shipped` with the one-line diff so the next run's `seen()` dedupe holds.

**Worked example — the texture filter:**

- Dossier would have: filter `3` (`Linear`) blurs pixel art; `0` (`Nearest`) keeps it crisp. Fix is one project.godot line; no sim touch; re-import is a no-op for this key so the gate must not assert `.ctex` staleness.

**A check that fails first.** Without it the gate re-judges "is it gone?" from screenshots every
round, and the fix has nothing stopping it regressing. A check that passes *before* the fix is
pinning the wrong thing and is worse than none, so the coder must watch it fail first.

**A ledger on disk.** `shipped`/`dismissed` used to die with the process, so every RUN re-derived
the same findings. Six runs independently re-reported the terrain tiling, the banner overlaps and
the shop clutter.

## Three ways this loop wastes an hour, and the pre-flight that stops each

**A red baseline.** A dev-only autoload landed in `project.godot`, the suite went red, and
every gate rejected work for a pre-existing failure — 6 cycles, ~3 hours, zero output. A gate
cannot tell "my change broke it" from "it was already broken", so the run now refuses to start
on a red suite.

**Orphaned engine processes.** Finished agents leave Godot running; four of them sat for up to
an hour at 0.4% CPU. Pre-flight kills them by FULL BINARY PATH — `grep godot` also matches the
`godot-mcp` npm servers, which inflates the count and sends you chasing contention that isn't
there.

**A "hang" that is a parse error.** The suite runs in ~10s. When it ran for 10+ minutes the
obvious read was CPU contention; the truth was `test_hud.gd` failing to parse, leaving the
runner unable to instantiate it and spinning. The runtime baseline is threaded into the coder
and gate prompts precisely so nobody waits it out. Tell them apart: contention = many starved
processes; cold import = one process on an idle box, fixed by `--import`; parse-hang = one
process, idle box, and `--check-only` on the touched files names the file in seconds; a process
pinned at ~1% CPU indefinitely is a script that aborted in `_init` before installing a main loop.
**A healthy headless sim is CPU-BOUND — ~4,000 ticks in 1.87 s at 97%. Low CPU means broken,
never slow.**

**A "hang" that is a blocked stdout pipe.** The cheapest of these to misdiagnose and the only one
you cause yourself: Godot blocks when its ~16 KB stdout pipe fills, so `godot … | grep … | head`
deadlocks the instant the consumer stops draining. It looks identical to every stall above,
including the CPU signature. Redirect to a FILE and grep the file.

**Findings that evaporate because the cycle ran out of budget.** The reviewer returns 4–6
detailed giveaways; the loop attacks `BATCH` of them and used to drop the rest on the floor.
One live cycle returned five, fixed one, and silently discarded "the bark box never clears"
and "five HUD elements stack during the boss fight" — both real, both then re-derived from
scratch at full reviewer cost on later runs. Unattacked non-structural findings are now banked
in the ledger's `backlog` and returned with the run. Backlog is deliberately **not** `seen`:
these are still open and still fair game to attack. A run that fixes three things must hand
back the other seven, or its silence reads as "the game is clean now."

**A deliberate decision that reads as neglect.** The strongest signal this loop has produced
came from a commit whose stated purpose was AAA polish: it made the commander bark persistent,
and the very next blind reviewer called that exact persistence "missing display timers and
neglected UI lifecycle management" — while also catching a doubled speaker prefix the same
commit shipped. **Intent is invisible to a player; only the screen is real.** The planner is
told not to treat "it's intentional" as a defence, and to state plainly when it is overturning
an intentional choice so the gate knows it was not an accident. Corollary: run a cycle *after*
polish work, not only after feature work — polish commits are where this class of bug breeds.

**A gate that fails for a reason unrelated to the change.** The engine-error gate reads its own
log back out of a `user://` dir shared by every concurrent Godot on the machine, so a sibling
run rotates the log away and it reports "no log carried this run's marker." That is a false
negative; it hit 3 of 6 parallel agents in one afternoon, each burning an attempt re-litigating
a clean diff. It fails **closed**, which is right — so the fix is one serial re-run (killing
stray Godot by FULL binary path; `grep godot` also matches the godot-mcp npm servers and will
lie about the count), never an `ERROR_ALLOW` entry.

## Run the suite under a private `user://`

Godot resolves `user://` from the project NAME, not the path, so every worktree and every
concurrent session of a project shares one directory — logs, saves and settings alike. That is
what produces the "no log carried this run's marker" false negative above, and it also lets
concurrent save/settings tests corrupt each other's fixtures.

If the target repo has a wrapper that runs the suite under a private HOME (this one grew
`tools/run_tests.sh`), pass it as the loop's `test` arg instead of the raw godot command. The
loop then stops losing attempts to a gate failing for reasons that have nothing to do with the
diff under review, and its cycles can safely overlap with other agents.

Two traps worth knowing if you build such a wrapper elsewhere:
- **Canonicalize the temp dir.** macOS `$TMPDIR` ends in a slash, so a naive `mktemp -d
  "$TMPDIR/x.XXXX"` yields a HOME containing `//`. Godot's `DirAccess` compares its root against
  the realpath byte-for-byte and on mismatch `DirAccess.open("user://logs")` returns **non-null
  pointing at the project directory** rather than erroring — the wrapper silently reproduces the
  bug it exists to prevent. `pwd -P` fixes it.
- **Make the wrapper fail closed.** If the private log dir never appears, the redirect did not
  take and the run used the shared dir; exit non-zero and say the result is void. A wrapper that
  quietly falls back is worse than no wrapper, because now the green is unearned.

## Agents do not start in ROOT, and reading the wrong tree looks exactly like reading the right one

The single most dangerous defect found in a day of driving this loop, because nothing about it
looks wrong. Every agent's shell starts in the SESSION's cwd. When the loop is driven against a
worktree — which is the recommended setup — that is a DIFFERENT tree, on a DIFFERENT branch,
often carrying another session's uncommitted work. `ROOT` appears in the prompt as a path, but
no agent is told its shell is somewhere else, so a bare `grep src/sim/sim_world.gd` silently
reads the wrong file. Same filename, same functions, different line numbers, different code.

Measured 2026-07-26. The plan agent opened with, in its own words:

> "Verified on `aaa/polish-run-10` (working tree) and cross-read against the tree the shots came
> from (`.claude/worktrees/aaa-run`)."

`aaa/polish-run-10` was the main checkout: a stale branch, 13 uncommitted files, another
session's. On it the plan enumerated "one idiom copied into 8 lethal predicates" by line number
and called that set **the finding**. Spot-checking three of the eight against ROOT:

| line | main checkout | ROOT |
|---|---|---|
| :1256 | `if not p["alive"] or p["roll_iframe"] or p["in_tank"] >= 0:` | tank-boarding logic |
| :2542 | `if p["alive"] and p["in_tank"] < 0 …` | grenade-hold logic |
| :3252 | `if p["alive"] and p["in_tank"] < 0 …` | a frogman comment |

Three for three, unrelated code. The coder receiving that plan edits the wrong lines or hunts
blind, and every downstream stage inherits the error with full confidence.

`ROOT_NOTE` is now prepended to the plan, code, gate, confirm and behaviour prompts: cd to ROOT
as the FIRST command, and print `git rev-parse --abbrev-ref HEAD` before citing any line number.
The self-catch is the useful part — **"if you find yourself naming another branch as the thing
you verified against, you have already made this mistake."** The plan agent did name it, in
writing, and no one was reading.

**The general rule:** when a prompt hands an agent a path, it must also tell it where the shell
actually is. A path in a prompt is a fact about the filesystem, not an instruction to the shell.

## Working alongside a long run

While a multi-cycle run owns the repo, agents that launch Godot compete for CPU *and* rotate
each other's logs. Two things that work: give implementation agents their own worktrees plus the
private-`user://` wrapper, and give audit agents an explicit **"read-only, do not run Godot at
all"** instruction. Read-only lenses (camera framing, silent-failure sweeps, collision fairness)
cost nothing in contention and return citations you can act on once the tree is free. Their
negative results are worth as much as the findings — one such pass retired a dozen standing
suspicions with line references, which is a thing a cycle-based loop never produces.

### Flag the adjacent findings, do not sweep them into your commit

When you fix something by hand next to a running loop, the tempting move is to fold every adjacent
defect you noticed into the same commit. Don't — name them in the commit body as explicitly *not
fixed* and let a later cycle take them. Measured 2026-07-26: a hand fix corrected three authored
coordinates that sat inside a hazard volume, and explicitly flagged "the rng-streamed beats can
still land in it on ~19% of seeds" as out of scope. A later cycle picked exactly that up, fixed it
with two new helpers, a census tool, +151 lines of mechanics tests, +63 of view-honesty tests and
its own reasoned golden re-record — a far better job than the hand fix would have done inline.
It also caught what the human missed entirely: those streamed beats used gate 2's x-coordinates
for BOTH fork gates, so one gate's lanes were positioned with the other's numbers.

The flag is what makes this work. An unflagged adjacent defect is invisible; a flagged one is a
backlog entry with a known shape.

### Do not put the runtime-owning agent behind a barrier

If you fan out audit lenses alongside one agent that actually RUNS the engine, do not collect
them with a barrier (`parallel()` and then use the results). Measured this session on a 6-lens
sweep: the five read-only code-reading lenses all returned in ~8 minutes; the single lens that
had to build and run a headless probe took **~25**, and the barrier held every downstream phase
for the slowest one. Pipeline instead, or let the runtime lens report separately and fold its
numbers in when they land — the read-only lenses' findings are actionable without it.

Related: the runtime lens is also the only one that can starve the others, so give exactly ONE
agent per run permission to launch the engine and tell the rest "read-only, do not run Godot at
all." A healthy headless sim is CPU-BOUND; if that one agent sits at ~1% CPU it is broken, not
slow, and no amount of waiting fixes it.

## The defect class this loop keeps finding: the view asserts what the sim does not do

In one session, seven independent passes found the same shape — a 15-site "honesty sweep", an MG
nest that drew a locked aim lane and then re-aimed on the firing tick, a vent whose warn ring was
drawn at 10px over a 24px kill radius, an elite that fired off the line it telegraphed, a boss
grade / crate / colossus trio all reporting states the sim never entered, and two separate cases of
**import-scale drift** (a texture import gained `size_limit` without its `SCALE` being retuned, so
a bunker drew at 14px while colliding at 48px, a reward pickup shrank to 3px, and a courier became
effectively bullet-proof).

Treat it as a first-class lens, not something to stumble into. It is worth an explicit pass that
diffs **what the view draws** against **what the sim computes**: every telegraph radius against the
constant that actually kills, every aim line against the vector actually fired, every drawn sprite
extent against the collision box it implies, every HUD claim against the field it reads. It is
also the class most worth a ratchet, because each instance is individually invisible — the game
looks fine and simply lies.

Two reasons it breeds here specifically: the sim/view split means a constant can move on one side
alone, and asset-pipeline changes alter drawn size without touching gameplay numbers.

## The same lie class lives in prose: the artifact asserts what the code does not do

The honesty lens above generalises to every WORD the loop writes. One docs session (8 community
files, each drafted then adversarially verified) ran a **50% lie rate**: 4 of 8 artifacts held at
least one claim the code refuted — an issue template saying the version is "shown on the main
menu" (nothing in `src/` renders it), a guide saying `ERROR_ALLOW` "is deliberately empty" (one
live entry, with its own justification comment), a dedup pointer to `Backlog.md` whose own header
declares itself STALE and redirects to FINDINGS.md, and a "count it yourself" grep printing 973
next to prose claiming ~971. Same shape as the drawn-lane lie: individually invisible, everything
*reads* fine, and the prose simply lies. The dossier rule pins visual claims to screenshots;
nothing pinned CODE claims to code. And the loop emits prose constantly — dossiers, backlog
titles, FINDINGS entries, ledger `corrected_detail`s — while every lens checks the game.

The pass that caught these is cheap: one adversarial verifier per shipped artifact, instructed to
REFUTE ("assume it lies until proven otherwise"), returning `{ok, issues: [{claim, problem,
fix}]}` — quote the exact claim, name the contradicting evidence (file:line), hand over the
concrete replacement. The `fix` field is what makes the repair one-shot, and the fixer re-runs
whatever check the verifier ran (parse, grep, count) before declaring done.

**Wired into `wf_aaa.js` 2026-07-29 as the `prose-verify` stage.** It audits exactly one
artifact: `confirm.corrected_detail` — the one document plan, code and gate all build against
precisely because it claims to be measured. Runs per *surviving* candidate only (a retired
candidate's detail never reaches the planner, so it cannot poison anything; an empty
corrected_detail means Confirm endorsed every specific, so there is nothing to audit). Fails
OPEN on a dead verifier or an empty rewrite — the original already survived Confirm's own
measurement pass, and this stage tightens a verified artifact rather than being the only gate.
Everything else the loop emits was deliberately left uncovered, each for a named reason: the
dossier is already pinned to screenshots and forbidden code claims; gate-banked
`found_not_fixed` entries and raw review findings get Confirmed when a later cycle attacks
them, so banking them unverified is by design; the plan is gated by the gate itself;
`Backlog.md` is re-triaged against HEAD by the backlog-triage pre-flight.

**First live fire, same day — and it caught the inheritance vector.** Confirm's restatement
carried a "uniform ~46px opaque zone" figure IN from the finding, unmeasured; the audit measured
the actual PNG per axis at 29-50px. The corrected conclusion survived (the masking genuinely was
fine), but the plan now builds on executed numbers instead of inherited ones. Name the vector:
when Confirm ENDORSES part of a finding, the endorsed specifics ride along unmeasured — 2b's
disease surviving inside 2b's own remedy, the lie wearing a lab coat. Confirm's prompt now
states the rule: every number in corrected_detail exists because Confirm executed it, or it does
not go in.

Three checks did all the catching; bake them into any prose-emitting stage:

1. **Every claim about code gets grepped against the code.** "X is shown / Y does Z" → find the
   draw/read site or drop the claim. A claim contradicting the verified ground-truth block in
   your prompt IS an issue, full stop.
2. **A citation is a claim — read the target's header first.** Linking to a file that declares
   itself stale, deprecated, or superseded re-points readers at the dead thing. Cite the live
   successor, demote the stale one to "historical context".
3. **If you tell the reader how to verify a number, run it and reconcile.** A check-yourself
   command whose output contradicts the adjacent figure teaches the reader the doc lies. Execute
   every "count it with X" instruction and make the two agree — or annotate the difference
   (here: "excluding the opt-in perf suite").

## A finding can be wrong in its literal claim and right about the symptom

Do not treat "the stated mechanism does not reproduce" as "there is no bug." Observed live: the
reviewer said the MG nest's aim lane "is never fired down." Literally false — the nest fires. But
the real defect was worse: it locked the aim vector, drew it for a 30-tick windup, then re-acquired
on the firing tick, so reading the telegraph and stepping off the line did not clear the burst. A
verifier that stopped at "it does fire, finding rejected" would have dismissed a genuine bug.

The reviewer is a consumer. It reports what it EXPERIENCED accurately and explains the cause badly.
So when the literal claim fails, ask what else could produce the same experience before dismissing
it — and when you dismiss, say which part reproduced and which did not (one pass correctly reported
that the nest's "the HUD tells you to dodge it" clause had no basis in code while the drawn-lane
lie was entirely real).

## Severity is consequence × RATE, and the rate is the half everyone omits

Four severity misjudgments in one session, in **both** directions, and every single time the
missing input was *how often the path executes* — never the mechanism, which the reporter always
described correctly. Two reported softlocks ("the player is walled at sector 4", "the fork pins
you forever") measured out as MINOR once someone counted the executions; a claymore filed as a
cosmetic nuisance was killing the planter in **~4 ticks** on the direction the tutorial teaches,
which is every run.

So a finding is not triaged until its report carries a denominator. Not "the crate pays more" —
*"the crate pays 67% more, and the crate is 1 of 2 buy surfaces, hit on every gate."* Not "mines
can bury" — *"83 mines buried unreachable across 40 gate-4 forks."* The planner ranks on the
product; a rare catastrophe and a constant papercut can outrank each other and the mechanism
alone will not tell you which.

Corollary for the loop: the reviewer is a consumer and cannot measure rate — it saw one run. The
**confirm** step owns the denominator, and a confirm that returns `real:true` with no count has
done half its job.

## Two entries that disagree on a number are both untrusted

The backlog held the same defect measured twice: the fork telegraph filed as *"1.1 s after the
lane is locked"* and as *"1.7–10.6 s after"*. Nothing reconciles them, so at least one cycle
measured wrong — and there is no way to tell which from the prose. Neither number may be carried
into a plan.

This is a specific hazard of a loop that banks model-written prose across cycles: the second
measurement does not overwrite the first, it sits **next to** it, and both read as authoritative.
When a confirm meets a contradiction, it re-measures with a committed probe and rewrites both
entries with the arithmetic — otherwise the coder picks whichever number is listed first.

## Check whether a test is defending the bug

Three times in one session, the fix was blocked by an existing test that had written the defect
down as a contract: `a useful priced crate still credits cost*10` (the exact 67% scoring gap being
fixed), `player bullet dies in the bag` (the sandbag eating the buyer's own fire), and a determinism
comment asserting "the endless torture never prices a crate" that a sibling's change had made false.

So before assuming a red test means your fix is wrong, read what it actually asserts. A test that
pins the buggy behaviour is part of the bug and must be updated with a note saying why. This cuts
both ways: it is also the strongest argument for the plan's mandatory "the check must FAIL on
current HEAD" rule — a check written against already-broken behaviour is how these got in.

## An agent that does not know what tooling EXISTS will weaken its own ratchet to fit

The rule below stops a cycle *rebuilding* a tool that exists. This is the other half, and it is
more dangerous, because it degrades a test instead of duplicating a file — silently, with a
reasonable-sounding justification attached.

Observed 2026-07-26, cycle 1 of a 20-cycle run. The gate shipped
`test_no_hostile_stalls_an_endless_wave`, which force-clears the field every 800 ticks, and filed
this as an owner decision: *"force-clears the field every 800 ticks by fiat **because there is no
combat-capable headless bot**… That means it pins 'no wedge within any 800-tick window' rather than
'no wedge, ever' — the mutation run reported a 764-tick streak, comfortably inside one window."*

A combat-capable endless bot had been committed to that worktree's own base **an hour earlier**
(`demo_input`'s endless targeting branch: wave 1 → 11, 4 → 22 live hostiles). The agent never looked.
So the ratchet's window is 7.5x too short to catch the very streak its own mutation run produced —
a check that fails-first, passes after, and would still miss the next regression.

**The failure is not laziness, it is that nothing in the loop tells an agent what the tree can
already do.** Fresh agents know the code they grep and nothing about capability. So:

- **Pre-flight must inventory the drivers and probes** — `ls tools/` plus a one-line purpose for
  anything that drives, measures, or replays the game — and that inventory must be threaded into
  the PLAN, CODE and GATE prompts. It is a dozen lines of context that prevents a weakened gate.
- **Never let "there is no tool for X" justify a weaker assertion.** It is a claim about the
  repository, so it needs the same evidence as any other: name the grep you ran. If the tool
  genuinely is missing, that is a finding to bank, not a licence to lower the bar.
- **A ratchet whose window is shorter than the defect it pins is not a ratchet.** When a check
  samples, compare the sampling window against the longest instance the run actually measured, and
  put both numbers in the commit body.

## `already_fixed` only looks at HEAD — in a multi-agent repo the fix is often on a branch

Confirm's cheapest and most valuable outcome is `already_fixed`: "a sibling already did this." It
answers that question against HEAD, and only HEAD. That was fine when one loop owned one checkout.
It is wrong the moment anything else in the session is working in a worktree — which is the
recommended setup, and which this file elsewhere actively recommends.

Measured live 2026-08-20, mid-run:

- `grep -ci "branch --contains|unmerged|sibling branch" wf_aaa.js` -> **0**. The loop has no
  concept of a branch it is not standing on.
- The repo held **21 unmerged branches** (`fix/*`, `overnight/*`, `todo/*`).
- Cycle 2's reviewer re-reported three tells verbatim from cycle 1 — *Truncated Tutorial Text*,
  *HUD Keybind String Clipping*, *Overlapping MAXED Labels*. **All three were already fixed on
  `fix/aaa-text-fitting`**, a branch created from the run's own baseline sha an hour earlier
  (`git log 7bed222..fix/aaa-text-fitting -S<symbol>` returns a commit for each). Two of the three
  were not even defects; the branch's verification had established that and the loop could not
  know it.

So cycles 3-5 were queued to spend opus plan/code/gate budget on problems solved one branch over.
Nothing in the loop can detect that, and `already_fixed` will keep answering "no" correctly and
uselessly.

**The pre-flight already solves the isomorphic problem for tooling** — it inventories `tools/` into
`toolbox` precisely because "fresh agents know the code they grep and NOTHING about capability."
Unmerged branches are the same class of invisible context, and the same remedy applies: list them
once up front (`git branch --format='%(refname:short)' --no-merged HEAD`, plus a one-line subject
per branch) and thread that list into Confirm. Then `already_fixed` can ask the question that
actually matters — *does a fix for this exist anywhere in this repository* — with
`git log HEAD..<branch> -S<symbol>` rather than only *is it at HEAD*.

Corollary for the human driving it: **if you fix something by hand while a run is in flight, the
run cannot see it.** Either merge before the next cycle selects targets, or expect to reconcile
duplicate fixes at merge time. Do not assume a loop that is "attacking the same list" knows the
list has moved.

## A false positive is not wasted work — it audits the ratchet that should have caught it

This file prices `real:false` / `already_fixed` as pure loss: *"Four of five verifications bought
nothing."* That is true of the FIX budget and false of the total return, and the difference is
worth banking.

Measured 2026-08-20 on four cycle-1 tells taken to implementation:

| tell | verdict | byproduct |
|---|---|---|
| Boss HUD overlap | ALREADY_FIXED | **the ratchet was vacuous** |
| Field Manual truncation | WRONG_ABOUT_CODE | **the ratchet was vacuous** |
| Overlapping MAXED | REAL (severity inflated 'dozens' -> 3 measured) | fixed |
| REVIVE keycap clipping | REAL (neither suspected cause) | fixed |

Both non-defects had tests that **could not fail**:

- Deleting `- bottom_band_lift(main.get("sim"))` from `hud.gd` left `SUITE=hud` at
  `PASS — 112 methods, 2103 assertions` with the verb chip nailed back over the boss name. The
  tests asserted `bottom_band_lift()` returned the right NUMBER, then re-did the subtraction
  themselves, never reading what `_verb_legend()` draws.
- Deleting the `_body_block` wrap branch from `menu.gd` left `SUITE=menu_layout` at
  `PASS — 214 methods, 8661 assertions` with four sentences hanging **247px past the frame**. The
  existing test overrode `_verb_line` WHOLESALE, so the real wrap never executed headless.

Neither hole was findable by looking for holes. Both surfaced because someone tried to *reproduce a
defect that wasn't there* and had to ask "then what is currently stopping this?" — and the honest
answer was "nothing."

**So when Confirm returns not-real, ask the follow-up before closing it out:** what test would have
caught this if it HAD been real, and does that test actually bite? Revert the relevant production
line and watch. It costs one suite run against a cycle you have already paid for, and it converts
the loop's most common disappointing verdict into its cheapest source of genuine defects.

Note the shape: the pixel reviewer's WEAKNESS (it reports what it experienced and explains the
cause badly, per the section above) is what produces these. A reviewer that only ever reported real
bugs would never have pointed at either of those two files.

## A committed probe that STILL REPRODUCES is an unfixed bug wearing a tool's clothes

The two rules below cover a probe that lies and a probe built twice. This is the third and it cost
the most: a probe that told the exact truth about a live defect and was read, every cycle, as a
capability.

Measured 2026-08-02 on Commander In Chief. An outside reviewer (a separate model, no access to this
loop's state) audited the game and its top-10 do-now list included defects the repo **already
carried committed probes for**. Running them at HEAD, unchanged, that same day:

```
$ tools/run_tests.sh -s res://tools/probe_tank_revive.gd
revive_context(P1)=true  (what main.gd would route E to)
after 120 ticks of E held: p2 alive=false  revived=false  cannon_fired=false
revive-related events seen: []
CONTROL on foot: p2 alive after 1 tick of E = true
```

That prints the defect in plain English, with a control line, in under ten seconds — the view routes
a key the sim discards. It was never fixed. The cause is not neglect — it is a category error baked
into the pre-flight: the baseline
agent inventories `tools/` into `toolbox` and describes each script by its header, so
`probe_tank_revive.gd` entered every single cycle's prompt as *"measures whether a tank driver's
revive press is swallowed"* — phrasing that reads as an available instrument. It is not an
instrument. It is a bug report with a `main()`. The loop had the evidence in its own context window
for cycles and spent that context re-deriving fresh visual findings instead.

**A probe's header describes a SYMPTOM, not a measurement, when it names a specific failing
scenario rather than a quantity.** "Does planting a claymore kill the planter, and in how many
ticks" is a symptom. "Dumps every sprite's imported size and opaque bbox" is a measurement. The
first kind is a candidate; the second kind is a tool.

Wired into `wf_aaa.js` 2026-08-02: the baseline agent now **runs** every `tools/probe_*.gd` and
returns `open_probes[{script,title,detail}]` for each whose output still demonstrates a defect,
which is seeded into the backlog at cycle 0 and competes for the primary slot. Four rules in that
prompt, each earned:

1. **Run it, never infer from the header.** A probe written for a bug that later got fixed now
   prints the *passing* case. Banking that spends a whole cycle confirming a non-defect.
2. **The printed output IS the detail** — quote it verbatim, then grep the responsible predicate and
   add its `file:line`. That pairing is what makes the fix one-shot.
3. **Still passes through Confirm.** A probe proves a behaviour exists, not that it is wrong; a
   sibling cycle may have shipped the fix without deleting the rig.
4. **Contradicting a green test is the OTHER failure mode** (the lying rig, below) — that is a
   broken tool, not an open defect. Keep it out of `open_probes`.
5. **Read the output against the code's STATED INTENT, not against your instinct.** Running it is
   necessary and not sufficient. This rule was written the hard way, in this very section: the
   first draft also banked `probe_salvage.gd`, which prints `hulk burn_ticks after salvage: 0 (100
   = cover kept, 0 = cover stripped)` — unmistakably a bug report. It is not. `_try_salvage_hulk`'s
   own docstring reads *"the strip ENDS the cover. That is the decision: keep the wall or take the
   ammo"*, `tests/test_mechanics.gd:1306` pins it, and the HUD lie the probe was originally written
   for was fixed in place three lines below. A skeptic pass killed it, and killed the fix a
   reviewer had proposed for it: players spawn at `GRENADE_AMMO_MAX` and hulks are solid to boots,
   so "refuse the strip at cap" would have made a hulk wall permanently unclearable for a fresh
   player — a golden re-record spent buying a regression. **Before banking a probe, grep the
   function it exercises for a docstring or a test that declares the behaviour intentional.** A
   probe cannot tell a bug from a decision; only the code's own stated intent can.

Why this is the cheapest finding in the run: every other candidate arrives needing reproduction and
a ratchet designed from scratch. These arrive with a deterministic repro already committed and a
ready-made failing-then-passing check — the probe itself is the gate's evidence. The generalisation
for any long-running loop: **inventory your own artefacts as claims, not as assets.** Anything the
loop left behind that asserts a defect is an open item until something re-runs it and says
otherwise.

## A committed probe that disagrees with a green test is a trap, not a leftover

The rule below stops a cycle rebuilding a tool that exists. This stops it committing one that
LIES, which is worse, because the tool outlives the cycle and nobody re-derives its accuracy.

Observed 2026-07-26 on this loop's own cycle 1. It shipped `tools/probe_frame_bounds.gd` after
its gate had already measured the problem and written it down verbatim:

> "Ran it post-fix: 44 [OVER] lines, and `grep -v 'y345..353'` returns zero — every one is the
> footer legend strip, which is drawn on the scrim below the frame by design and which the test
> correctly excludes. **The probe lacks that exclusion, so its output contradicts the green test.**"

The gate filed that in `found_not_fixed`, scored the cycle 95/100, and committed. So the repo now
carries a measuring rig that reports 44 failures against code its own suite calls correct. The
next person to run it either wastes an hour or — worse — "fixes" something that was never broken,
which is the exact failure mode the Confirm phase exists to prevent, reintroduced through tooling.

The gate now treats this as **blocking**: if a diff touches `tools/`, run it, and a tool whose
output contradicts the tests it supports fails the gate. Either fix the tool or drop it from the
diff — a cycle owes a passing check, not a probe. Same bar for the `.gd.uid` sidecar and for
duplicating a tool that already exists.

**The generalisation is uncomfortable and worth stating:** every quality bar this loop applies to
game code, it should apply to the artefacts it leaves behind. A fix is gated, measured, ratcheted
and mutation-tested; the probe shipped alongside it was none of those. Unvalidated tooling is
still output.

## "Check first" applies to tooling, not just fixes

The loop already refuses to rebuild a fix that exists at HEAD. Extend the same check to the
measuring tools and helpers a cycle writes for itself. Observed live: a collision-fairness pass and
an import-drift pass, running in parallel, each wrote a dev tool that independently computed the
opaque alpha bbox of every sprite — the same primitive, twice, and the second pass then appended
assertions to the first pass's test file without noticing whose it was.

That is the same defect this loop keeps finding in the game: two sites computing one value drift
apart (a crate and a wheel awarding different score for one item; two copies of one chest bonus; a
camera leash and an actor clamp reading the same literal `344`). Every one of those was fixed by
routing through a single shared constant. A loop that reproduces that shape in its own tooling has
no standing to lecture the codebase about it.

Practical rule for the coder and gate prompts: before adding a `tools/` script or a measurement
helper, grep for one that already does it, and prefer extending it. When two are genuinely
warranted, extract the shared measurement into one static both call.
