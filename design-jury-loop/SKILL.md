---
name: design-jury-loop
description: >
  Multi-model OpenRouter design jury that reviews an implemented UI/brand surface,
  dedupes findings into improve.md, implements agreed items, commits/pushes, and
  repeats for N iterations until models vote stop or the queue is empty.
  Use when the user says "design jury", "brand jury review", "jury the site",
  "iterate design with models", "/design-jury-loop", "jury loop N", or asks to
  review the live SPA/brand with multiple OpenRouter models and ship improvements
  in a loop. Argument: iterations (default 3). Also triggers after major UI launches
  when user wants adversarial multi-model polish.
---

# Design Jury Loop

Parallel **OpenRouter model jury** → **dedupe `improve.md`** → **implement agrees** →
**build/deploy if needed** → **commit + push** → repeat for `iterations`.

Battle-tested on Cue (Stage Prompt brand, Vue SPA, tone slider, dropzone studio).

## Arguments

| Arg | Default | Meaning |
|---|---|---|
| `iterations` | `3` | Max jury→implement rounds |
| `url` | project primary URL if known | Live URL under review (e.g. `https://cue.shoemoney.ai`) |
| `out` | `<project>/brand/improve.md` or `<project>/improve.md` | Running log |
| `models` | 5 smart defaults | Comma list of OpenRouter model ids |
| `floor_stop` | `3` | Stop early if this many models set `"stop": true` |

Parse from user text:
- `/design-jury-loop 5` → iterations=5
- `jury loop 2 rounds` → iterations=2
- `design jury until clean` → iterations=5 (cap), stop on floor_stop

## Default models (the “smart 5”)

```
anthropic/claude-opus-5
openai/gpt-5.6-sol
google/gemini-3.7-flash
x-ai/grok-4.6
deepseek/deepseek-v4-flash
```

Override when user names models. Prefer non-`:batch` chat endpoints.

## Prerequisites

- `OPENROUTER_API_KEY` **or** working key scrape from `~/.hermes/.env` / aigate vault
  (**models list can 200 with a dead key — chat calls are truth**).
- Project has a frontend (Vue/React/Blade/static). Know the live URL or local preview.
- Git remote optional; still commit locally if no remote.

## Harness scripts (this skill)

```
~/.claude/skills/design-jury-loop/scripts/jury.py     # parallel OpenRouter fan-out
~/.claude/skills/design-jury-loop/scripts/dedupe.py   # summary.json → improve.md + counts
```

```bash
SKILL=~/.claude/skills/design-jury-loop
python3 "$SKILL/scripts/jury.py" /tmp/brief.txt --out-dir /tmp/design-jury-r$N
# prints SUMMARY:/tmp/design-jury-r$N/summary.json
python3 "$SKILL/scripts/dedupe.py" /tmp/design-jury-r$N/summary.json \
  "$OUT/improve.md" --round $N
```

## Loop (per iteration `i = 1..iterations`)

### 1) Snapshot the implemented design

Gather a **brief** (write `/tmp/design-jury-brief-r$i.txt`) including:

- Locked brand decisions (do **not** allow juries to reopen settled direction unless user asks)
- Live URL(s) + what each route does
- Palette tokens, fonts, motion inventory
- Key components / files reviewers should assume exist
- Explicit “product rules” (e.g. human-in-the-loop, no auto-send)
- Ask schema (must match parser):

```json
{
  "model_note": "string",
  "general": ["5 concrete UX/UI items"],
  "transitions": ["5 motion/effects items"],
  "professional": ["5 premium feel items"],
  "font": {
    "primary": "face + why",
    "pair": "optional",
    "react_style": "weights/tracking one-liner"
  },
  "stop": false,
  "top3_must": ["3 highest-ROI items"]
}
```

`stop: true` **only** if they believe shipping quality needs no material UI upgrades.

Pull brief from live `curl` + reading `App.vue` / design tokens / `brand/CHOSEN.md` when present.

### 2) Fan-out jury (parallel)

```bash
python3 "$SKILL/scripts/jury.py" /tmp/design-jury-brief-r$i.txt \
  --out-dir "/tmp/design-jury-r$i" \
  --models "$MODELS"
```

If a model `PARSE_FAIL` / truncated (`finish=length`), **one retry** with:
- shorter brief reminders
- `max_tokens` already 2200 — ask “minified JSON, bullets ≤12 words”

Need **≥3 parsed** votes to continue the round; else retry failed models once.

### 3) Dedupe → improve.md

```bash
python3 "$SKILL/scripts/dedupe.py" /tmp/design-jury-r$i/summary.json \
  "$PROJECT/brand/improve.md" --round $i
```

If no `brand/`, write `$PROJECT/improve.md`.

**Append** round history rather than wiping prior rounds when `i > 1`
(prepend new round section or write `improve-r$i.md` + rollup `improve.md`).

### 4) Agent agreement (you decide)

From auto-YES queue + your judgment:

| Auto-YES signals | Usually skip |
|---|---|
| ≥2 model votes | Brand direction reversals |
| reduced-motion / a11y / contrast | “Replace hero with stock model” |
| palette coherence with locked brand | Rename product core concepts without user OK |
| trust/footer human-in-the-loop | Expensive live LLM-on-slider unless free |
| glass token / type system | Pure copy nits with no UI impact |

Write an **Agent decisions** subsection listing SHIP / SKIP + why.

### 5) Implement (max parallelism)

Fan **Task/subagents** by lane, e.g.:

1. **System CSS** — tokens, fonts, reduced-motion, veil/contrast  
2. **Core components** — slider, dropzone, cards  
3. **Pages** — landing + primary app surface  
4. **Extension** — if same brand/motion tokens mirror chrome extension  
5. **Verify/build/deploy** — `npm run build`, rsync, docker, curl 200 + HTTPS assets  

Hard rules:

- Prefer editing existing components over new frameworks  
- `npm run build` (or project equivalent) must pass  
- No secrets in git  
- Match locked brand (for Cue: Stage Prompt / ember — do not invent a fourth direction)

### 6) Commit + push + cleanup

```bash
git add -A
git commit -m "design-jury r$i: <short summary of shipped items>"
git push   # if remote exists
```

Cleanup:

- Remove scratch `/tmp/design-jury-r$i` **only after** improve.md references key verdicts
  (or keep last round for audit)
- Drop dead code / unused experimental CSS from the round
- Ensure `public/build` stays gitignored if project policy says so

### 7) Stop checks

Stop the outer loop when **any**:

1. `i == iterations`
2. `stop_votes >= floor_stop` (default 3)
3. Auto-agree queue has **zero shippable** UI items (only SKIP/nits)
4. User aborts

On stop: write final section to `improve.md`:

```markdown
## Loop complete
- Rounds run: X
- Final stop votes: Y/N
- Outstanding nits: ...
```

## Brief template (copy)

```markdown
# Design jury brief — <product> — round <i>

## Locked brand (do not reopen)
- Direction, palette hex, tagline, mark name

## Live surfaces
- URL + route map + what user can do

## Implemented UI inventory
- Components, motion list, fonts loaded, known gimmicks

## Constraints
- e.g. human always sends; no category trademark clones

## Required JSON schema
(paste schema above)
```

## Cue-specific defaults (when cwd is cue)

- URL: `https://cue.shoemoney.ai` (+ `/studio`)
- Brand file: `brand/CHOSEN.md`
- Improve: `brand/improve.md`
- Deploy: rsync `backend/` → `<deploy-host>:<deploy-path>/cue/backend` then
  `sudo docker compose build api && up -d --force-recreate api`
- Verify: curl `/` `/studio` `/brand/favicon.svg` — HTTPS asset URLs only

## Anti-patterns

- Letting models vote to abandon a founder-locked brand direction mid-loop  
- Shipping every “cute motion” while ignoring contrast/trust  
- Infinite loop on score-9 nits once stop votes pile up  
- Blocking on one slow model — run all five in parallel (jury.py does)  
- Implementing unsafely invasive “replace the founder’s chosen photo”

## Output to user each round

Keep ADHD-scannable:

1. Round `i` vote table (top agrees)  
2. SHIP list  
3. SKIP list (1 line each)  
4. Deploy/live check  
5. Continue / stopped why  

## Verification gotchas (learned on camera, airank modal + /r/ loops 2026-08)

- **CSS `animation` shorthand resets `animation-delay` to 0.** Setting
  `animation: foo .3s, bar .3s` then `animation-delay: X` in the SAME shorthand silently
  zeroes it — the element fires before its staggered siblings. End-state screenshots look
  perfect; only a mid-stagger frame catches it. Fix: shorthand first, then explicit
  `animation-delay: var(--stagger), calc(var(--stagger) + 350ms);` longhand after.
  Always shoot one MID-animation frame (~40% through the stagger), not just the final state.
- **Playwright MCP screenshots write relative to the playwright SERVER's cwd** (the main
  checkout), not your worktree — even in-page `page.screenshot()`. `find` the file before
  concluding a shot failed.

## Round dynamics, measured (airank public-page sweep, 2026-08-12)

Ten surfaces, five models each, three rounds. The vote counts are worth knowing in advance
because they change how you plan the run.

**Round 1 will score zero stop votes. Plan for it.**

| Round | Stop votes | Note |
|---|---|---|
| R1 | **0/45** | not one model voted stop on any of nine surfaces |
| R2 | **28/45** | 7 of 9 surfaces at or past `floor_stop=3` |
| R3 | +2 surfaces | one surface never converged, hit the iteration cap at 2/5 |

Never present round 1 as a completed loop. Zero stop votes is the *expected* R1 result, not a
signal that the page is bad — models asked to critique a page they have not yet seen improved
will always find five things.

**Round N+1 must review the DEPLOYED state of round N.** This is the single most important
sequencing rule. If you re-jury your local tree, the models re-report round N's findings as if
nothing was done, and you burn a full round confirming work you already shipped. Order:

```
jury -> implement -> build -> test -> commit -> DEPLOY -> verify asset hash moved -> re-jury
```

Verify the hash actually moved (`curl` the page, diff the `/build/assets/<Component>-*.js` name
against the pre-deploy value) before spending the next round's tokens.

**Put the stop question first and make refusal legitimate.** The default framing invites models
to invent work to appear useful. State explicitly, in the brief:

- taste preferences, token swaps and re-litigating locked brand decisions are **not** material
- inventing work to appear diligent is a failure mode, not thoroughness
- `"stop": true` is a respected, expected answer for a page that is genuinely done
- only a real defect — an a11y failure, a dishonest element, a broken state, a usability
  blocker — justifies continuing

R3 on one surface returned **4/5 stop and zero ship items** under this framing. That is what a
clean stop looks like.

**Report a cap as a cap, never as agreement.** A surface that exhausts `iterations` at 2/5 has
*not* converged. Say "terminated by the iteration cap, never reached the stop floor" — the loop's
own second stop condition — and leave the round-4 decision to the owner. Rounding a cap up to
"stopped" is the one outcome that makes the whole vote meaningless.

**The loop's best output may be a regression it caused itself.** R1 on one surface added relative
time formatting to a list whose timestamps came from an uncast `DB::raw` aggregate; it shipped
broken and R3 caught it. Budget for the possibility that a later round's most valuable finding is
an earlier round's mistake — and do not let an agent "fix" it outside its file scope.

**What good juries refuse.** Log the refusals, they are as valuable as the ships: a
"VERIFIED" badge over a null verification column, passive polling plus a pulsing "live" chip on a
page that does no live work, a progress meter on a process whose completion cannot be predicted.
On a measurement product, a jury that declines to decorate is working correctly.

- **Vue SCOPED styles don't travel with class names.** A page reused `class="rise"` + per-section
  `--stagger` vars from a sibling page, but `.rise` was defined in the SIBLING's `<style scoped>`
  — so the entrance animation was dead code that never ran, invisibly (static render looks fine).
  The jury caught it via a deep-link complaint, not visually. When a brief claims "sections
  stagger in", verify the keyframes exist in THAT component's scope (or global CSS) before
  asserting motion inventory — grep the component itself for the @keyframes, not the codebase.
- **The honest-stop framing works round 1.** With "stop:true is respected" + refusal-legitimacy
  language in the brief, r1 scored 2/5 stops and models submitted "retain X, do not decorate"
  items — on airank /d/ the loop converged 5/5 by r3. Without that framing the measured baseline
  was 0/45 r1 stops. Also: models re-report already-true facts (rows "need" to be buttons that
  already are buttons) — audit each claim against the artifact before shipping it.
- **Site-wide consistency round: probe first, jury second.** For "are all N pages consistent"
  asks, don't jury each page — fan out one rendered-DOM probe per page (playwright-core script
  dumping computed font/colors, header/footer presence, canonical, h1 text, overflow, console
  errors as JSON), aggregate into a matrix, and give the JURY the matrix plus the specific
  judgment calls. On airank (17 pages) the probe found the real issues itself (9 missing
  canonicals, one identical logo-h1 sitewide, one chrome-less docs page); the jury's value was
  the two 5/5 verdicts on what to DO, one round, no iteration needed. Probe agents also
  re-report the brand mark's concatenated textContent as "corrupted h1" — expect it.
- **Agent-returned file content: truncate at the last closing tag, don't just strip fences.**
  A drafted .vue arrived as ```vue…``` plus trailing prose; naive fence-stripping left the
  commentary INSIDE the file after </template> — and Vue's SFC compiler silently tolerates
  trailing junk, so the build stayed green and it would have shipped. Cut at
  `s[:s.rindex('</template>')]` (or the format's final closer), then verify the tail.

## OpenRouter failure modes that cost a full round each

Measured 2026-08-19 running a six-model panel four times.

**1. Reasoning models return `content: null` and put everything in `reasoning`.**
Four of six models came back with `message.content == None`. The naive
`open(f,"w").write(msg["content"])` dies with `TypeError: write() argument must be str, not None`,
which reads like a bug in your harness rather than a truncated generation.

```python
msg = d["choices"][0]["message"]
txt = msg.get("content") or msg.get("reasoning") or ""
if not txt:
    raise RuntimeError("empty; finish=" + str(d["choices"][0].get("finish_reason")))
```

**2. The real cause is `max_tokens` too low for a reasoning model.** The fallback above then
"succeeds" and hands you 12KB of chain-of-thought with no final answer — the model spent the whole
budget thinking and never emitted JSON. The tell is a large response that parses to nothing: text
ending mid-sentence, often mid-deliberation ("Actually, let me reconsider #5...").
**3000 was not enough; 16000 was.** Budget for reasoning tokens separately from answer length —
a 5-item JSON answer still needs five figures of headroom on these models.

**3. `str.format()` collides with literal JSON braces in your prompt template.** Asking for
`{"fix_a": "LANDED"}` in a `.format()`-ed brief raises `KeyError: '"fix_a"'`. Double every literal
brace (`{{`/`}}`) or use string concatenation for prompt bodies containing JSON examples.

**Retry only the failures.** All three of these are per-model; re-flying the whole squadron wastes
the models that worked and costs another several minutes of wall-clock.

**4. `max_tokens` alone does not fix a model that will not stop thinking.** Measured 2026-08-19 on
`moonshotai/kimi-k3`: at 24000 it returned 85KB of pure deliberation and never emitted the answer,
twice, ending mid-sentence mid-calculation. The retry that worked set **`"reasoning": {"effort":
"low"}`** alongside a raised ceiling — and `content` came back non-null at 7KB. Same model failed
the same way on the ranking call at 20000. If a model burns its whole budget reasoning, cap the
reasoning explicitly rather than raising the ceiling again; the ceiling is not the lever.

**Give the harness a single-seat re-fly.** `python3 rank.py <model-id>` re-running one juror and
MERGING into the existing `votes.json` turned a 5/6 panel into 6/6 for one call. Any jury script
that can only re-run all N will make you choose between a short panel and paying for the whole
squadron twice.

## Blind ranking: anonymize plans before the panel votes

When the panel produces competing PLANS rather than findings, a second round can pick a winner —
but only if authorship is hidden. Relabel each plan to a letter, keep the mapping locally, and ask
every reviewer to rank all of them including (unknowingly) its own.

Scoring: Borda (N points for 1st down to 1 for last) plus a count of first-place votes. Report
both — they disagree usefully. In one run the Borda winner had 3 first-place votes while a plan
with 2 first-place votes finished third overall, because it was ranked last by two reviewers.

**What blind ranking buys you, concretely:** two of five reviewers voted for a plan other than
their own, and one ranked its own submission DEAD LAST. That is a signal you cannot get from a
non-anonymized vote, and it is what makes the winner credible rather than diplomatic.

Also harvest, in the same call:

- `best_idea_to_graft` — `{from, idea}`. The winner plus 2-3 grafts beats the winner alone; two
  reviewers independently asked to steal the same idea from a losing plan, which is a strong
  signal that idea is separable from the plan that carried it.
- `fatal_risk` — `{plan, risk}`. Three of five independently named the SAME implementation risk in
  one losing plan (a fixed bottom sheet against iOS Safari's collapsing URL bar with `dvh` and
  `safe-area-inset`). Convergent risk-naming is the most reliable output of the whole exercise;
  weight it above the ranking itself.

## Vision juries (screenshots, not prose) — measured 2026-08-27, airank Operation Cleanup

The skill's jury.py is text-only. When the question is "does this look professional", build the
brief around IMAGES: airank now has `design-audit/vjury.py` — copy it forward. The load-bearing
parts: PIL downscale to ≤1100×2200 JPEG q78 before base64 (full-page PNGs blow context),
`msg.content or msg.reasoning` fallback, per-model retry, `--merge` for single-seat re-fly, and
`reasoning: {effort: low}` for kimi. Vision panel that parsed 6/6 twice: gpt-5.6-sol,
gemini-3.7-flash, grok-4.6, kimi-k3, qwen3-vl-235b-a22b-instruct, glm-4.6v. Full-page screenshots
attach fine as one tall image — tell jurors "judge the SHAPE, text will be small."

**Round-2 protocol that produced a clean 2.7→5.9 measurement:** tell the panel WHAT CHANGED as a
list, then "judge the RESULT, not this list", and require a `delta_vs_round1` field plus a
`regressions` array. The regressions array is the highest-signal output: 3 of 6 models
independently flagged ghost-faded content as "worse than a plain page" — it was real (opacity held
at 0/0.2 by a scroll-timeline fill-mode), invisible in my own end-state screenshots, and it was
also a print + reduced-motion content loss. Juries catch mid-scroll states humans skip.

**Two false-positive classes to expect and not act on:**
- **Training-cutoff dates.** Jurors reported "AUG 9, 2026" as a bug ("future-dated evidence",
  "fix year 2026 timestamps") — the session date WAS 2026-08. A model cannot know today's date;
  any "wrong date" finding gets checked against the calendar before it costs a fix.
- **Full-page-capture artifacts.** `fullPage: true` doesn't run scroll timelines, so jurors see
  "a huge blank band" that renders fine for real users. Verify with incremental real scrolling
  (400px steps + waits) before treating an empty-section finding as a page bug — it can be BOTH
  (the airank case was a capture artifact AND a real at-rest invisibility, distinguished only by
  measuring computed opacity after real scrolling).

**Measure decoration before deleting it when the call is contested:** screenshot with/without the
layer (toggle via `addStyleTag display:none`), PIL-diff the pixels. A full-viewport WebGL
background measured 0.181% of pixels changed — the number ended the argument in one line.

## The protected-aesthetic trap — measured 2026-08-27 evening, airank

**A jury score can plateau high while the owner hates the site, and the brief is the reason.**
This skill's own advice ("do not allow juries to reopen settled direction") was in every airank
brief, so five sittings graded execution INSIDE a neo-brutalist ledger aesthetic and reached
8.1/10 — at which point the owner looked at it and said, verbatim, "this site looks horrific."

The gap was the brief, not the panel. A "no sacred cows" sitting — same screenshots, protection
explicitly removed, owner's verdict quoted, reference class named (Stripe/Linear/Vercel/Ahrefs) —
produced a 6/6 unanimous diagnosis naming five offenders (black void ground, 3px borders + hard
offset shadows, mono ALL-CAPS labels, green-on-black chrome bands, uniform loudness), a
token-level prescription, and an 8.5–9.1 estimate if executed. Executed, the next sitting scored
8.77→9.13 with a unanimous stop.

Rules extracted:
- The brand lock is a tool, not a truth. **The owner's displeasure is the unlock signal**: when
  the human stakeholder's read diverges from a plateaued jury score, the first suspect is what
  the brief declared off-limits.
- The unlocked brief must do four things: quote the owner's verdict verbatim, name the reference
  class, state explicitly which prior protection is removed, and ask for a diagnosis-of-the-gap
  ("why did prior panels see 8 where the owner sees horrific") before any prescription.
- Ask for the prescription as TOKENS (ground, borders/shadows, radii, type roles, label casing,
  chrome, color use, density) — six models converged to an implementable spec in one round.
- Harvest the `keep` list as hard as the offenders: it protected the honesty layer, the data
  glyphs, and the one deliberate dark surface from an over-rotation.

## Juror OCR false positives — verify text findings with grep, never fix from the screenshot

Small text in downscaled screenshots gets misread and reported confidently as typos: one juror
filed a hero "mesure" misspelling (source greps zero hits — it was the underlined "measure"),
another filed "udAdswers" and "www.rttings.com" (actual: "adAnswers ÷ answers" and rtings.com,
correct in data). Standing rule: any juror-reported TYPO or micro-text defect gets a source grep
before it costs an edit — the fix bar is "reproducible in source or live DOM", not "in the JPEG".
Companion to the training-cutoff-date false positive above; both are why stop-vote footnotes need
verification rather than reflex fixes.

Current vision panel (2026-08-27, owner-set): gpt-5.6-sol, gemini-3.7-flash, grok-4.6, kimi-k3,
qwen3.8-max, glm-5.3-flash. (qwen3-vl-235b and glm-4.6v retired by owner instruction.)

## Claude-vision jury variant (jerememe Operation Cleanup, 2026-08-27)

When the review target is *screenshots* rather than a live URL brief, Claude subagents that can
Read PNGs beat the OpenRouter text-only jury — they critique what the page actually looks like,
not what the brief claims. Shape that converged in 3 rounds on a full-site declutter:

1. **Probe first** (as above): a playwright-core sweep script shoots every page linked from home
   (desktop + mobile + full-page) AND dumps a DOM probe JSON per page — canvas count, running
   `document.getAnimations().length`, console errors, `innerText.length`, scrollWidth overflow,
   doc height. The probe numbers (23 canvases / 61 animations / 19,000px home) carried more
   authority with the jury than any adjective. macOS binary path tell: the playwright cache ships
   `chromium-1234/chrome-mac-arm64/Google Chrome for Testing.app/...` — NOT `chrome-mac/Chromium.app`;
   glob for the executable before hardcoding.
2. **4 jurors, 4 lenses** (IA/declutter, visual system, core funnel, perf+a11y), each writing a
   plan file; then **cross-review via SendMessage continuation** — every juror ranks all four
   plans (own included) + names grafts + fatal risks. Measured value: one juror's cut list
   deleted the component that WAS the phrase input (`ChaChingRegister`) — only the cross-review
   caught it. Jurors ranked their own plans 2nd/3rd honestly; the diagnostics-heavy plan won 3/4
   first places because it had file:line receipts.
3. **Implement with disjoint file ownership** (one agent per file cluster; tokens locked in the
   master plan doc so waves can run in parallel before the token CSS even lands — code against
   `var(--x, #fallback)`).
4. **Honest-stop framing works here too**: r2 produced a converged 6-item punch list (0/3 stop),
   r3 with "stop is the expected verdict" framing returned 2/2 stop, zero material defects.

**Cleanup deletes delight — keep a restoration path.** After a hard declutter the owner WILL ask
for one deleted flourish back, described from memory ("the spotlight webgpu that was very nice").
Match their word to the *artifact name* in git history first (`useSpotlight` was literally the
thing) before building the fancier neighbor; restore verbatim from the pre-cleanup commit
(`git show <sha>^:path`), then tune. Building a new interpretation first cost a full
implement-deploy round before the correction arrived.

**Redesign trap measured twice this run:** new components reusing OLD class names (`.hero`,
`.composer`) inherit dead global CSS from the pre-redesign stylesheet — a parent
`.maker-view { max-width: 640px }` collapsed a new hero grid's `1fr` column to 132px. Diagnose in
minutes by walking computed styles up the parent chain in the live page
(`getBoundingClientRect().width` + `maxWidth` per ancestor) instead of reading CSS files.

## Single-question layout juries: ranked options + the unmutilated asset (2026-08-28, jerememe)

When the question is one layout defect (not "critique this page"), the one-round shape that
produced a 5/6 first-place landslide with zero retries and zero parse failures:

- **Enumerate 3–4 concrete candidate layouts (A–D), require a full ranking of ALL of them**, and
  explicitly invite "or beat them with your own." Ranking forces engagement with every option;
  Borda + first-place counts then read straight off the ballots. All 6 models ranked the
  caption-cropping option dead last — a unanimity you only see when the constraint ("any crop
  that removes the caption FAILS") is stated as a hard rule in the brief.
- **Attach the UNCROPPED source asset as its own exhibit** alongside the failure screenshot.
  Jurors judging "the circle hides the GIF" need to see what the circle is hiding — the
  failure closeup alone lets them anchor on the mutilated version as the asset's true shape.
  Three exhibits total: failure closeup, full-page context, unmutilated specimen.
- **Demand a per-winner spec object** (frame/size-with-share-of-width/what-happens-to-displaced-
  element/filter-values/mobile) — six models converged to an implementable band (~48-52% of
  container width) and the spec fields disagreed only where taste genuinely differs (drop vs
  tune the filter), which is exactly the residue a human should decide.
- **Harvest grafts by the 2-vote rule:** two jurors independently proposing the same steal from a
  LOSING option (here: keep the retired medallion as a small corner stamp) is a ship signal —
  same convergence logic as fatal risks.

## Print/PDF-artifact juries (airank report polish, 2026-08-28)

When the surface is a PRINT document, not a live page: render HTML → Chrome
`--headless=new --no-pdf-header-footer --print-to-pdf` → `pdftoppm -png -r 110` →
feed per-page PNGs in order to vjury. A US-Letter page at r=110 (~935×1210) fits
vjury's downscale untouched, so text stays legible. **Page-count delta is a free
per-round metric** (16→12pp = orphan fixes landed; 19→22pp = ledger/method pages
added) — report it alongside votes. For Laravel: render blades with UNSAVED
`(new Model)->forceFill([...])` + an in-process
`config(['filesystems.disks.X' => local])` override — zero DB/S3 writes against
prod-shaped donor rows dumped once as JSON.

Lessons that cost a round each:
- **An overbroad locked-rule in the brief manufactures a false-positive cluster.**
  "No third-party provider names" (meant: our internal image/chat suppliers) made
  6/6 jurors demand stripping "ChatGPT" — the measured surface itself. Scope every
  ban precisely in the brief; when a cluster traces to YOUR brief, fix the brief
  between rounds and log the dismissal, don't touch the product.
- **`now()` in a render harness = "future date" juror flags.** UTC evening stamps
  read as tomorrow; jurors (correctly, from their view) call it fabrication. Pin
  fixture timestamps to local daytime.
- **"Leaked internal notes" can be STORED DATA, not code.** Grep of the codebase
  finding nothing does NOT clear the finding — the sentences lived in old rows'
  stored result JSON (a prior copy vintage; current writer emits clean prose).
  Check the data source before dismissing; fix = a bounded exact-string
  modernization map at render time, so every old row prints current voice.
- **Big page sets blow small-context seats.** 22 page-images made glm-5.3-flash
  return "unverifiable — could not inspect pages" while five peers parsed fine.
  That's a juror failure, not a document defect: re-fly the single seat (--merge),
  or halve pages for that model only.
- **Reflow findings are whack-a-mole; require the regressions array to chase them.**
  Round-2's regressions field caught every hole the round-1 pagination fixes moved
  (sparse pages migrated, a collapse concatenated title+status, a new fine-print
  line broke words mid-token). Expect one full round of regression cleanup after
  any pagination wave.
- **Lane-spec seam items:** when speccing implementation lanes by file ownership,
  grep each item's target string FIRST — one item per wave lands in another lane's
  file, both agents correctly refuse, and the orchestrator closes it by hand. A
  deliberately-red test (lane D writing the assertion for the unimplemented spec
  item) keeps the seam visible instead of silently dropped.

## Demanding-juror framing without stop-legitimacy = permanent plateau (aigate/ashtonwoods, 2026-08-28)

A fresh per-round juror script written mid-session WITHOUT this skill's honest-stop framing
("demanding print-design juror… 5 dislikes… remaining_concerns empty ONLY if you'd sign off")
produced a measured flat line: 25 → 25 → 26 concerns over three rounds, 0/15 sign-offs ever,
even though every actionable item from each round was implemented and independently QA-verified.
The category trend was the only real signal: defects → refinements → taste + outright misreads
of the renders. Rules:

- **Category trend, not count, is the convergence metric** under a demanding framing. When a
  round is majority taste + factually-wrong, declare a capped plateau, fix remaining cheap
  factual items on merit, and close honestly — or better, fix the BRIEF and re-run.
- **Before calling plateau, check the brief for the honest-stop block.** The plateau may be
  manufactured by the framing, not the artifact. The repair: stop question first; define
  MATERIAL (a11y / misleading / factual / broken) vs NOT (taste, palette expansion, new
  deliverables, production specs); list owner-LOCKED decisions explicitly so jurors stop
  re-filing declined items; state "inventing work to appear diligent is a failure mode";
  allow dislikes to be non-blocking nits; add numeric scores so movement is measurable.
- **Page ranges drift between rounds.** Polish waves change page counts (12→10→11pp here);
  a juror prompt with hardcoded "images 8-19 = Report 2" ranges silently mislabels every
  finding. Re-derive the ranges (and regenerate the downscale set + its NN- global ordering)
  from disk after EVERY re-render, before every round.
- **Parallel-juror runner: never a compound background one-liner.** `KEY=$(fetch) && juror1 &
  p1=$!; juror2 &` backgrounds the whole && chain with juror1 — jurors 2-N launch WITHOUT the
  key env. Use a run-round.sh (set -u, vault fetch, N jurors &, wait) — also gives round N+1
  a one-argument re-fly.
- **Verify juror "inconsistency" claims against the renders** before implementing: two round-3
  concerns here were flatly wrong ("Report 2 white background breaks dark-mode cohesion" — all
  three reports are dark-cover/white-interior; "section numbering inconsistent" — display
  headers vs reference style, already uniform). Same family as the OCR/typo and
  training-cutoff-date false positives above.

## A blank frame is a stalled load until proven otherwise (learned 2026-09-05, arena r4–r5)

Six jurors unanimously reported "empty stage, dashed headers" as a regression. The frame was a
page captured while its API was still answering: `/api/arena` took **20 s** (see
`sql-table-optimization` → JSON-path predicates), and the capture script had navigated
client-side and shot after 1.5 s. Round 5 then re-flagged a blank price glyph for the same
reason. The most valuable output of five design rounds was a database index.

Before a frame goes to the jury: time every API the page calls (`curl -w '%{time_total}'`), wait
for `networkidle` **and** a data-present probe (a header value that is not `—`), and navigate
directly to the route (a client-side push resets the page). Put the API latency in the brief.
If a juror calls something "empty" or "missing", check the capture before the code.

### Staging state in a production Vue build for screenshots

`el.__vueParentComponent` exists only in dev builds. In production walk the vnode tree from the
container: start at `document.querySelector('#app')._vnode`, recurse `vnode.component.subTree`
and `vnode.children`, and stop at the instance whose `component.exposed` has the method you
need (`spawnChallenger`, `promote`). Then drive it from `page.evaluate` and capture frames at
known offsets. `app._instance` is null in prod; the container's `_vnode` is not.
