export const meta = {
  name: 'tripple-a-gamedev',
  description: 'A multimodal reviewer SEES the screenshots and guesses if the game is AAA; opus plans, sonnet codes, opus reviews. Loops N times.',
  phases: [
    { title: 'Dossier' },
    { title: 'Review', detail: 'multimodal consumer verdict' },
    { title: 'Confirm', detail: 'real flaw, or screenshot-staging artifact?' },
    { title: 'Plan', detail: 'opus' },
    { title: 'Implement', detail: 'sonnet codes, opus gates' },
  ],
}

// args sometimes arrives as a JSON *string* instead of an object; parsing it is the
// difference between running 12 cycles and silently running 1 against `undefined/`.
const A = (typeof args === 'string' ? JSON.parse(args) : (args || {}))
const ROOT = A.root
// macOS default. On Linux/Windows pass args.godot — the pkill in the pre-flight matches on this
// exact string, so a wrong value here makes the orphan-killer a silent no-op.
const GODOT = A.godot || '/Applications/Godot.app/Contents/MacOS/Godot'
const TEST = A.test || `${GODOT} --headless --path ${ROOT} -s res://tests/run_tests.gd`
const N = A.cycles || 1
// ~ rather than an absolute home dir: these are interpolated into shell commands, so the shell
// expands them for whoever cloned the skill.
const SCRIPT = A.script || '~/.claude/skills/tripple-a-gamedev/scripts/aaa_review.py'
const VERIFY = A.verify || '~/.claude/skills/tripple-a-gamedev/scripts/verify_shots.py'
const MIN_SHOTS = A.minShots || 1
const REVIEW_MODEL = A.reviewModel || ''   // '' = script default (google/gemini-3.6-flash)
// 4, not 3: observed rejections were repeatedly ~80% right, and the 3rd attempt now starts from
// a verified-good list instead of from scratch, so the extra round is cheap and often decisive.
const MAX_TRIES = A.maxTries || 4
const BATCH = Math.max(1, A.batch || 2)        // targets attacked per cycle
const LIVE = A.live !== false                  // capture real play, not posed states
const LEDGER = `${ROOT}/.aaa/ledger.json`      // survives across RUNS, not just cycles
// The command that PLAYS the game and prints per-stage difficulty telemetry. ON BY DEFAULT —
// it used to be opt-in and empty, which meant the loop's normal mode was guessing at the
// difficulty curve from still frames. difficulty_probe.gd STEPS the sim rather than awaiting
// frames (~7,000 ticks/s vs 60), so measuring both modes across 3 seeds costs ~20 s.
// Override with args.pacing; pass args.pacing='' explicitly to skip measuring entirely.
const SKILL_DIR = A.skillDir || '~/.claude/skills/tripple-a-gamedev/scripts'
const PROBE = `${SKILL_DIR}/difficulty_probe.gd`
const PACING = A.pacing !== undefined ? A.pacing
  : `SEEDS=0xC0FFEE,1,2,3 MAXT=40000 MODES=campaign,endless CALIB=${ROOT}/.aaa/calibration.json ` +
    `${GODOT} --headless --path ${ROOT} -s res://.aaa/difficulty_probe.gd`
const PACING_JSON = `${ROOT}/.aaa/pacing.json`          // this run
const PACING_BASE = `${ROOT}/.aaa/pacing_baseline.json` // the previous run, for the DIFF
// The calibration the difficulty stage LOADS and then updates: measured per-stage baselines,
// versioned and diffable. Deliberately NOT SKILL.md — numbers self-improve here, prose stays
// hand-edited, because unattended prose rewriting is what got the last loop's cron deleted.
const CALIB = `${ROOT}/.aaa/calibration.json`
const CAPTURE = `${SKILL_DIR}/live_capture.gd`
if (!ROOT) throw new Error('wf_aaa: args.root missing — refusing to run against an undefined project root')

// The dossier stage must PROVE the screenshots are real before anything is allowed to judge
// them. A capture that writes 12 byte-identical black PNGs still prints "SAVED" for each one,
// and the whole pipeline downstream then runs on a description that cannot have come from the
// images — silently, and with completely plausible-looking output.
const BASELINE_SCHEMA = {
  type: 'object',
  required: ['green', 'detail'],
  properties: {
    green: { type: 'boolean', description: 'true only if the suite PASSES with 0 failures' },
    failures: { type: 'number' },
    script_errors: { type: 'number', description: 'count of SCRIPT ERROR lines, pre-existing' },
    baseline_secs: { type: 'number', description: 'wall-clock seconds for one full suite run' },
    toolbox: { type: 'string',
      description: 'one line per tools/ script that drives, measures or replays the game, taken from its header comment — plus, explicitly, which scripted driver exists and which MODES it can play. Threaded into plan/code/gate so no agent weakens a check believing a capability is absent.' },
    open_probes: {
      type: 'array',
      description: 'Committed probes that STILL DEMONSTRATE A LIVE DEFECT at HEAD. Empty is a fine answer; a wrong entry costs a whole cycle.',
      items: {
        type: 'object',
        required: ['script', 'title', 'detail'],
        properties: {
          script: { type: 'string', description: 'repo-relative path, e.g. tools/probe_tank_revive.gd' },
          title: { type: 'string', description: 'the defect in reviewer-title form, e.g. "tank crew revive input is swallowed by the sim"' },
          detail: { type: 'string', description: 'the probe output that proves it, verbatim, plus the file:line of the predicate responsible' },
        },
      },
    },
    branches: { type: 'string',
      description: "Unmerged branches (name + newest subject, one per line), so Confirm's already_fixed can ask whether a fix exists ANYWHERE in the repo rather than only at HEAD. 'none' is a valid answer." },
    ci: { type: 'string',
      description: 'CI status for the current HEAD: the workflow name, status/conclusion, and — if red — which JOB and which STEP failed. "no remote"/"gh unavailable" are valid answers. Does not abort the run; it tells the reader whether a later push can be attributed to this run at all.' },
    detail: { type: 'string' },
  },
}

// One pass over the seeded backlog instead of one full Confirm per stale entry mid-run.
const TRIAGE_SCHEMA = {
  type: 'object',
  required: ['fixed', 'unreal', 'open'],
  properties: {
    fixed: { type: 'array', items: { type: 'string' },
      description: 'EXACT titles, byte-for-byte, of entries the code at HEAD already fixes. Only when you SAW the fix.' },
    unreal: { type: 'array', items: { type: 'string' },
      description: 'EXACT titles whose premise is false against HEAD — the described behaviour does not exist.' },
    open: { type: 'array', items: { type: 'string' },
      description: 'EXACT titles still open, INCLUDING every one you were not sure about. This is the default.' },
    notes: { type: 'string', description: 'one line per reclassified entry: title + the file:line that decided it' },
  },
}

const LEDGER_SCHEMA = {
  type: 'object',
  required: ['shipped', 'dismissed'],
  properties: {
    shipped: { type: 'array', items: { type: 'string' } },
    dismissed: { type: 'array', items: { type: 'string' } },
    backlog: { type: 'array', description: 'real findings seen but never attacked',
      items: { type: 'object', properties: { title: { type: 'string' }, detail: { type: 'string' }, cycle: { type: 'number' } } } },
    decisions: { type: 'array', items: { type: 'string' },
      description: 'owner decisions carried forward from earlier runs' },
  },
}

// Difficulty feedback is only trustworthy in two forms: a DELTA against the last measurement, and
// an instrument check. An absolute "too hard" from a scripted bot is unanchored — the bot's own
// skill sets the number. So this asks for both, and for the instrument verdict to be stated.
const PACING_SCHEMA = {
  type: 'object',
  required: ['table', 'trustworthy'],
  properties: {
    table: { type: 'string', description: 'the per-stage table verbatim from the tool, plus a DELTA column vs the baseline if one existed' },
    outliers: { type: 'array', items: { type: 'string' },
      description: 'stages that are genuine difficulty outliers: costly AND fighting normally' },
    instrument_suspect: { type: 'array', items: { type: 'string' },
      description: 'stages whose cost comes with COLLAPSED offense — the driver cannot fight there, so the number is about the bot. Never tune on these.' },
    regressions: { type: 'array', items: { type: 'string' },
      description: 'stages that got materially harder or easier SINCE THE BASELINE, with both numbers. This is the only difficulty signal that does not depend on how good the driver is.' },
    trustworthy: { type: 'boolean',
      description: 'false if the run was truncated, the seed count was too small, or the tool errored. Say so rather than reporting a number nobody should act on.' },
    baseline_valid: { type: 'boolean',
      description: 'false when the calibration was recorded against a DIFFERENT game or a DIFFERENT driver — i.e. HEAD moved, or the bot/probe changed — which makes every delta a re-baseline rather than a regression. Say false rather than reporting movement nobody should act on.' },
    tunable: { type: 'array',
      description: 'the ONLY stages downstream may treat as a difficulty finding. A stage qualifies solely by being a real outlier (costly AND fighting normally) that ALSO moved against the recorded calibration, or by carrying an explicit human anchor. A bot cannot establish that a HUMAN finds something too hard, so an unanchored absolute belongs in outliers and stops there.',
      items: { type: 'object', required: ['stage', 'anchor'],
        properties: {
          stage: { type: 'string' },
          anchor: { type: 'string', description: 'what makes this more than the bot\'s own skill: a calibration DELTA with both numbers, or a human observation quoted from owner_decisions / the ledger. "the bot died a lot" is not an anchor.' },
        } } },
    calibration_written: { type: 'boolean',
      description: 'true once this run\'s measurement has been written to the calibration file, so the NEXT run has a baseline to diff against. That diff is the only driver-independent difficulty signal there is.' },
    caveats: { type: 'string' },
  },
}

const DOSSIER_SCHEMA = {
  type: 'object',
  required: ['shots_ok', 'path'],
  properties: {
    shots_ok: { type: 'boolean', description: 'true ONLY if verify_shots.py exited 0. Never guess.' },
    shots_report: { type: 'string', description: 'verify_shots.py output, verbatim' },
    path: { type: 'string' },
  },
}

const REVIEW_SCHEMA = {
  type: 'object',
  required: ['verdict', 'giveaways'],
  properties: {
    verdict: { type: 'string' },
    confidence: { type: 'number' },
    first_impression: { type: 'string' },
    giveaways: {
      type: 'array',
      description: 'every giveaway the reviewer listed, in its ranked order, none dropped',
      items: {
        type: 'object',
        required: ['title', 'structural', 'detail'],
        properties: {
          rank: { type: 'number' },
          title: { type: 'string' },
          structural: { type: 'boolean' },
          detail: { type: 'string', description: 'where + what_i_see + why_it_outs_it + aaa_version, VERBATIM' },
        },
      },
    },
  },
}
// The gate used to be binary, and that threw away a lot of correct work: real rejections
// opened with "VERIFIED GOOD (don't touch, don't redo)" and then named ONE blocker, and the
// whole cycle got reverted anyway. So the gate now says what is already right (fed forward so
// retries stop re-litigating settled work) and, when it fails, whether the good part can be
// salvaged by reverting specific files.
const GATE_SCHEMA = {
  type: 'object',
  required: ['perfect', 'feedback'],
  properties: {
    perfect: { type: 'boolean' },
    feedback: { type: 'string', description: 'precise, actionable list of what to fix' },
    summary: { type: 'string' },
    verified_good: {
      type: 'string',
      description: 'what you CONFIRMED is correct and must not be redone or undone. Be specific ' +
                   '(file + what about it). This is fed verbatim to the next attempt.',
    },
    closeness: {
      type: 'number',
      description: '0-100: how close THIS attempt is to shippable. 100 = perfect. Judge the tree ' +
                   'as it stands now, independent of earlier attempts. Used to pick which attempt ' +
                   'to keep if every one gets rejected, so be honest and comparable across rounds.',
    },
    salvageable: {
      type: 'boolean',
      description: 'true ONLY if reverting whole files listed in revert_paths would leave a ' +
                   'coherent, working, strictly-better-than-HEAD tree. false if the good and bad ' +
                   'changes are tangled inside the same file.',
    },
    revert_paths: {
      type: 'array',
      items: { type: 'string' },
      description: 'repo-relative paths to discard when salvageable is true. Everything else is kept.',
    },
    found_not_fixed: {
      type: 'array',
      items: { type: 'object', properties: { title: { type: 'string' }, detail: { type: 'string' } } },
      description: 'DEFECTS you found while gating but did NOT fix, including ones that predate this ' +
                   'diff (say so, and say how you verified it — "identical on HEAD, checked by ' +
                   'capture"). These are BANKED INTO THE BACKLOG and a later cycle will attack them, ' +
                   'so they must be real and specific: title + where + what is wrong + how you ' +
                   'measured it. This is the right home for "X renders broken", "Y overlaps Z", ' +
                   '"the digit is clipped" — anything with a determinable right answer. Do NOT put ' +
                   'those in owner_decisions: that field is not persisted as work and nothing will ' +
                   'ever build from it. Empty is fine; invented is not.',
    },
    owner_decisions: {
      type: 'array',
      items: { type: 'string' },
      description: 'ONLY things that are PRODUCT CALLS, not defects — where the honest fix ' +
                   'depends on intent only the owner has, so you correctly did NOT guess. One line ' +
                   'each, WITH the measurement that makes it decidable. Real examples from one run: ' +
                   '"miniboss tiers freeze at wave 20 (no BOSS_MORTAR_TICKS_T4) while the README ' +
                   'promises escalation by tier"; "the VP meta has a 295 VP total sink vs per-run ' +
                   'income, so it is spent in ~10 runs while the banner keeps celebrating it"; ' +
                   '"each lane of fork gate 4 strands one of the two bunkers you must destroy". ' +
                   'These are the highest-value thing a review produces and they are worthless if ' +
                   'they die in an agent transcript — empty is fine, invented is not.',
    },
  },
}

const CONFIRM_SCHEMA = {
  type: 'object',
  required: ['real', 'why'],
  properties: {
    real: { type: 'boolean', description: 'true only if a real player would hit this in a real run' },
    why: { type: 'string', description: 'the evidence; if false, name the staged field that causes it' },
    already_fixed: {
      type: 'boolean',
      description: 'true if the defect no longer reproduces because it has ALREADY been fixed in ' +
                   'the current tree. Cheap, correct outcome - not a failure.',
    },
    corrected_detail: {
      type: 'string',
      description: 'The finding restated to match what the code ACTUALLY does - real file:line, real ' +
                   'numbers you measured, wrong claims dropped. Fed to the planner INSTEAD of the ' +
                   "reviewer's version. Leave empty only if every specific checked out exactly.",
    },
  },
}

// The confirm stage's corrected_detail is the loop's most trusted prose: plan, code and gate all
// build against it precisely BECAUSE it claims to be measured. A docs session measured the lie
// rate of unverified prose-about-code at 50% of artifacts — a "version shown on the main menu"
// nothing renders, an "ERROR_ALLOW is empty" that had a live entry. Same lie class as the
// view/sim seam, one level up: the artifact asserts what the code does not do. So the verified
// document gets a verifier of its own, in the shape that caught those: refute-first, and every
// issue carries its own concrete fix so the repair is one shot.
const PROSE_VERIFY_SCHEMA = {
  type: 'object',
  required: ['ok', 'issues'],
  properties: {
    ok: { type: 'boolean', description: 'true ONLY if every claim survived refutation' },
    issues: {
      type: 'array',
      items: {
        type: 'object',
        required: ['claim', 'problem', 'fix'],
        properties: {
          claim: { type: 'string', description: 'the exact quoted claim being refuted' },
          problem: { type: 'string', description: 'the contradicting evidence: file:line or the measured value' },
          fix: { type: 'string', description: 'the concrete replacement text' },
        },
      },
    },
  },
}

// Cross-cycle memory. The reviewer is stateless and re-derives its list from scratch every cycle,
// so without this the same tell gets re-attacked after it has already been fixed (or re-proposed
// after being dismissed as a staging artifact), and long runs spin on one item.
// The ledger is written the INSTANT shipped/dismissed changes, never deferred. A deferred flush
// (flag now, write at the next top-of-loop) loses the whole record when the process dies
// mid-cycle — observed for real: a run's review, dossier and 27 shots were all on disk and the
// ledger indexing them was never written, so the next run would have re-paid for all of it.
const shipped = new Set()    // titles an earlier cycle fixed and committed
const dismissed = new Set()  // titles rejected as unreal / not worth building
// Real findings the cycle SAW but did not attack (only BATCH targets get built per round).
// These used to evaporate: one live cycle returned 5 giveaways, fixed 1, and silently dropped
// "the bark box never clears" and "five HUD elements stack during the boss fight" — both real,
// both re-derived from scratch on later runs at full reviewer cost. Backlog is NOT `seen`:
// these are still open, still fair game to attack, and they are reported at the end of the run
// so a finding is never lost just because its cycle spent its budget elsewhere.
const backlog = new Map()    // norm(title) -> {title, detail, cycle}
// norm(title) -> the ORIGINAL wording. shipped/dismissed keep only normalised keys, but the
// reviewer needs the exact string it used last time or it cannot reuse it verbatim.
const titleOf = new Map()
// --known: the exact titles this game's earlier cycles used. The reviewer has no memory
// between cycles, so it re-describes the same tell with a fresh title every time and the
// title-keyed dedupe never fires. Observed over two consecutive cycles: three identical
// tells, three new titles, zero matches — so the primary slot re-derives them forever.
// This asks for title REUSE, never silence: a still-visible tell must still be reported.
// Shell-quoted as one argument; titles are newline-joined and single quotes are escaped.
function knownFlag() {
  // STILL-OPEN entries ONLY. Feeding it shipped/dismissed titles was actively harmful and
  // measured so: cycle 1 of the 17:12 run returned 5 giveaways and FOUR matched
  // shipped/dismissed, so the whole visual lens filtered to nothing. The real hazard is
  // worse than the waste — `seen()` drops anything matching a shipped title, so asking the
  // reviewer to reuse those titles means a REGRESSION of an already-shipped fix gets
  // reported, matches, and is silently discarded as "already done". The loop would go blind
  // to exactly the failures it most needs to catch. That hazard pre-dates this flag but only
  // fired by luck, because reviewers reworded titles; making reuse reliable made the
  // blindness reliable too. Open items still need stable titles (they are counted, not
  // filtered), so they stay — a regressed fix now has to be described fresh, and gets through.
  // VISUAL-ORIGIN titles only. Sending the whole open backlog turned the consumer reviewer
  // into a parrot: measured on the 17:43 run, FOUR of its five findings came verbatim from
  // the list and only one was genuinely new — and two of the four were BEHAVIOUR-lens
  // findings ("the camera is clamped so you cannot push north", "HOW TO PLAY mis-sells the
  // armor") that no screenshot can possibly show. A pixels-only reviewer echoing sim-derived
  // titles is worse than noise: downstream it reads as two independent lenses agreeing, when
  // it is one lens reciting a list it was handed. Untagged legacy entries are NOT sent —
  // failing closed just means the reviewer rewords, which is only the old behaviour.
  const open = [...backlog.values()]
    .filter(b => b && b.lens === 'visual' && b.title)
    .map(b => b.title)
  if (!open.length) return ''
  const joined = open.slice(0, 60).map(t => `- ${t}`).join('\n').replace(/'/g, `'\\''`)
  return ` --known='${joined}'`
}
// Owner decisions must OUTLIVE the run: they used to exist only in the returned object, so every
// one of them evaporated when the workflow finished. They are now persisted in the ledger.
const decisions = []
// Product calls the run deliberately refused to guess at. Surfacing these IS the deliverable —
// in one session every item that mattered most to the owner (a fork gate stranding a required
// bunker, a meta currency exhausted in ~10 runs, tiers that stop escalating against a README that
// promises they do not) was found by an agent, mentioned once, and would have died in a transcript.
const norm = t => (t || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()

// ---------------------------------------------------------------------------
// Pre-flight. Two things must be true before spending a single cycle.
// ---------------------------------------------------------------------------
phase('Preflight')

// 1. BASELINE. The most expensive failure observed: project.godot picked up a dev-only
//    autoload, the suite went red, and every gate rejected work for a reason that had
//    nothing to do with the code under review — 6 cycles and ~3 hours for zero output,
//    because a gate cannot tell "my change broke it" from "it was already broken".
const baseline = await agent(
  `In ${ROOT}, establish the starting state. Change nothing.\n\n` +
  `FIRST kill orphaned engine processes — a previous run's Godot can sit for an HOUR at 0.4% CPU\n` +
  `holding things up, and it is invisible unless you look:\n` +
  `  pkill -f '${GODOT}' ; sleep 2\n` +
  `Count with the FULL BINARY PATH, never \`grep godot\` — that also matches the godot-mcp npm\n` +
  `servers and inflates the number, which sends you hunting contention that is not there.\n\n` +
  `NEXT refresh the import cache — one cheap command that guards the whole run:\n` +
  `  ${GODOT} --headless --path ${ROOT} --import\n` +
  `A warm-but-STALE .godot/ serves the PREVIOUSLY imported textures (Art.tex() reads ` +
  `.godot/imported/*.ctex, never the PNG on disk), so without this every captured frame and ` +
  `every art test in the run judges OLD PIXELS — and a worktree warmed by copying .godot in ` +
  `is stale by construction. --import only re-imports what changed; on a current cache it ` +
  `costs seconds.\n\n` +
  `Then run the suite ONCE and TIME it:\n\n` +
  `  time ${TEST}\n\n` +
  `Report seconds in baseline_secs. This number is load-bearing: this suite runs in ~10s, and a\n` +
  `run that takes MINUTES is not slow, it is a script that failed to parse and left the runner\n` +
  `spinning. Later cycles compare against it.\n\n` +
  `Report green=true only if it prints PASS with 0 failures. Also count the SCRIPT ERROR ` +
  `lines (some may be pre-existing and that is fine — we just need the number, so later ` +
  `gates can judge NEW errors instead of absolute silence). If the suite is red, say ` +
  `exactly which assertions fail.\n\n` +
  `FINALLY, INVENTORY THE TOOLING and put it in \`toolbox\`. Run \`ls tools/\` and give a ONE-LINE ` +
  `purpose for everything that DRIVES, MEASURES or REPLAYS the game (scripted bots/drivers, probes, ` +
  `census tools, replay validators, capture harnesses) — read each file's header comment, do not ` +
  `guess from the filename. Name the scripted driver explicitly if one exists, and say which MODES ` +
  `it can actually play.\n` +
  `This exists because a gate shipped a weakened ratchet on the false premise that "there is no ` +
  `combat-capable headless bot" while one sat in that very worktree, committed an hour earlier. Its ` +
  `test sampled every 800 ticks against a defect its own mutation run measured at 764 — 7.5x too ` +
  `short to catch. Fresh agents know the code they grep and NOTHING about capability, so this list ` +
  `is threaded into every later stage. Be accurate: an overstated toolbox is worse than none.\n\n` +
  `ALSO INVENTORY UNMERGED BRANCHES into \`branches\`. Run:\n` +
  `    git branch --no-merged HEAD --format='%(refname:short)' | head -40\n` +
  `and for each, one line: name + its newest subject (\`git log -1 --format=%s <branch>\`).\n` +
  `WHY: Confirm's \`already_fixed\` check only looks at HEAD, so a fix sitting on a sibling \n` +
  `branch is invisible and the loop will happily spend a full plan/code/gate cycle rebuilding \n` +
  `it. MEASURED 2026-08-20 mid-run: the repo held 21 unmerged branches, and cycle 2's reviewer \n` +
  `re-reported three tells verbatim from cycle 1 that were ALL already fixed on a branch cut \n` +
  `from this run's own baseline sha — two of which were not even real defects. This is the same \n` +
  `class as the toolbox inventory above: context a fresh agent cannot grep its way to.\n` +
  `Empty is a fine answer. Keep it to names + subjects; do NOT read the diffs.\n\n` +
  `FINALLY, CHECK CI — a green LOCAL suite does not mean a green pipeline. Report it in \`ci\`.\n` +
  `If the repo has a GitHub remote and \`gh\` is installed:\n` +
  `    gh run list --limit 3 --json headSha,workflowName,status,conclusion\n` +
  `CI runs GATES THE SUITE DOES NOT. Measured 2026-08-20 on this repo: the last two completed runs ` +
  `on main were FAILING while the local suite passed 1116/26644 clean — the red was ` +
  `\`python3 tools/i18n_check.py\`, which no test invokes, catching two hint strings that shipped ` +
  `without .po entries. Two sessions in a row had ended at "pushed" and never looked.\n` +
  `⚠️ \`gh run view --log-failed\` frequently returns only post-job CLEANUP noise (credential ` +
  `teardown, orphan-process reaping) and NOT the failing step. Get the job id from ` +
  `\`gh run view <run> --json jobs\` and read \`gh run view --job <id> --log\`, grepping for the ` +
  `step's own command. Concluding from the cleanup tail is a confidently wrong answer.\n` +
  `This does NOT abort the run — a red CI on someone else's commit is context, not your failure. ` +
  `But say so plainly, because every cycle here commits, and a run that pushes onto an already-red ` +
  `pipeline cannot tell you whether IT broke anything.\n\n` +
  `THEN RUN THE PROBES — do not merely list them. A probe is not only a capability, it is often a ` +
  `DEFECT MARKER: some earlier cycle reproduced a bug, wrote a rig that prints it in plain English, ` +
  `committed the rig, and never landed the fix. The inventory above reads those files as tools and ` +
  `walks straight past the bug. MEASURED 2026-08-02 on Commander In Chief: an outside reviewer ` +
  `independently rediscovered three defects this repo already carried committed probes for — ` +
  `\`probe_tank_revive.gd\` printing "after 120 ticks of E held: revived=false ... revive-related ` +
  `events seen: []" against a control line proving it works on foot, and \`probe_salvage.gd\` ` +
  `printing "grenades before/after: 12 -> 12 ... cover stripped". Both still reproduced at HEAD. ` +
  `The evidence had been sitting in the tree, in the pre-flight's own toolbox list, for cycles.\n` +
  `So: for every \`tools/probe_*.gd\` (and any other rig whose header describes a SYMPTOM rather ` +
  `than a measurement), execute it and read the output. Populate \`open_probes\` with each one whose ` +
  `output still demonstrates a live defect. Rules:\n` +
  `- Run it, do not infer from the header — a probe written for a bug that was later fixed now ` +
  `prints the PASSING case, and banking that wastes a full cycle on a non-defect.\n` +
  `- The probe's own printed output IS the detail. Quote it verbatim; then grep for the predicate ` +
  `responsible and add its file:line. That combination makes the finding one-shot fixable.\n` +
  `- A probe whose output contradicts a GREEN test is the other failure mode (a lying rig) — that ` +
  `is not an open defect, it is a broken tool. Say so in \`detail\` and leave it OUT of open_probes.\n` +
  `- READ THE OUTPUT AGAINST THE CODE'S STATED INTENT, not against your instinct. Running it is ` +
  `necessary, not sufficient. \`probe_salvage.gd\` prints "hulk burn_ticks after salvage: 0 (100 = ` +
  `cover kept, 0 = cover stripped)" — unmistakably a bug report, and it is not one: the function's ` +
  `own docstring says "the strip ENDS the cover. That is the decision: keep the wall or take the ` +
  `ammo", a test pins it, and the HUD lie the probe was written for was fixed three lines below. ` +
  `Banking it would have spent a golden re-record on a REGRESSION (players spawn at max grenades ` +
  `and hulks block movement, so refusing the strip at cap makes a hulk wall unclearable). So for ` +
  `each candidate, grep the exercised function for a docstring or a test declaring the behaviour ` +
  `INTENTIONAL, and drop it if you find one. A probe cannot tell a bug from a decision.\n` +
  `- Empty is a legitimate result. Do not manufacture entries.`,
  { label: 'baseline', phase: 'Preflight', model: 'opus', effort: 'high', schema: BASELINE_SCHEMA })

if (!baseline || !baseline.green) {
  const why = (baseline && baseline.detail) || 'baseline agent returned nothing'
  log(`ABORTING: the suite is ALREADY RED before any cycle ran. Every gate would reject ` +
      `work for a pre-existing failure. Fix this first.\n${why}`)
  return { aborted: 'baseline red', detail: why, cycles: [] }
}
const baseErrors = (typeof baseline.script_errors === 'number') ? baseline.script_errors : 0
const baseSecs = (typeof baseline.baseline_secs === 'number' && baseline.baseline_secs > 0)
  ? baseline.baseline_secs : 0
// A suite that "hangs" is almost never slow — it is a script that failed to PARSE, leaving the
// runner unable to instantiate it and spinning. Cost an hour of misdiagnosis as CPU contention.
// What the repo can ALREADY do. Threaded into plan/code/gate because a fresh agent knows the code
// it greps and nothing about capability — and one that believes a capability is missing will lower
// its own bar to fit. A gate shipped an 800-tick sampling window against a 764-tick defect on
// exactly that mistake, while the driver it wanted was committed in its own tree an hour earlier.
// Confirm's `already_fixed` asks about HEAD only. Measured 2026-08-20 mid-run: 21 unmerged
// branches, and cycle 2 re-reported three tells verbatim that were ALL fixed on a branch cut from
// this run's own baseline sha. Same invisible-context class as TOOLBOX_NOTE.
const BRANCH_NOTE = (baseline && baseline.branches && !/^\s*none\s*$/i.test(baseline.branches))
  ? `\nUNMERGED BRANCHES IN THIS REPO (from pre-flight). A fix for the tell you are confirming may ` +
    `already exist on one of these, and \`already_fixed\` is the cheapest correct verdict there is:\n` +
    `${baseline.branches}\n` +
    `Before concluding a defect is real, check whether it is fixed OFF HEAD — e.g. ` +
    `\`git log HEAD..<branch> -S<symbol>\` or \`git diff HEAD..<branch> -- <file>\` on the file the ` +
    `finding names. If it is fixed on a branch, say so and name the branch: that is still ` +
    `already_fixed for planning purposes, and rebuilding it wastes a full plan/code/gate cycle.\n`
  : ''
const TOOLBOX_NOTE = (baseline && baseline.toolbox)
  ? `\nTOOLING THAT ALREADY EXISTS IN THIS REPO (from pre-flight — use it, do not rebuild it, and ` +
    `do NOT weaken a check on the belief that some capability is absent):\n${baseline.toolbox}\n` +
    `If you are about to justify a weaker assertion with "there is no tool for X", that is a claim ` +
    `about the repository: run the grep first and name it. A missing tool is a finding to bank, not ` +
    `permission to lower the bar. And if a check SAMPLES, compare its window against the longest ` +
    `instance actually measured — a ratchet whose window is shorter than the defect it pins is not ` +
    `a ratchet. Put both numbers in the commit body.\n`
  : ''
// EVERY agent's shell starts in the SESSION's cwd, which is NOT ${ROOT}. On a repo driven from
// a worktree that is a different branch with different line numbers — and often another
// session's dirty tree. Measured 2026-07-26: the plan agent announced "Verified on
// `aaa/polish-run-10` (working tree)" — the main checkout, a stale branch with 13 uncommitted
// files — and enumerated 8 lethal predicates by line number. Checked against ROOT, all three
// spot-checked lines held UNRELATED code (:1256 tank-boarding vs an in_tank guard, :2542
// grenade-hold, :3252 a frogman comment). The plan's central finding was line-numbered against
// a tree nobody was editing, and nothing in the run would have caught it.
const ROOT_NOTE =
  `\n⚠️ WORK ONLY IN ${ROOT}. Your shell does NOT start there — it starts in the session's cwd, ` +
  `which on this machine is a DIFFERENT worktree on a DIFFERENT branch, frequently with another ` +
  `session's uncommitted changes. \`cd ${ROOT}\` as your FIRST command and keep every path ` +
  `relative to it (or absolute under it). Before you cite a single line number, run\n` +
  `    cd ${ROOT} && git rev-parse --abbrev-ref HEAD && git log --oneline -1\n` +
  `and state that branch in your output. A file path with no cd is read from the WRONG TREE and ` +
  `looks completely plausible: same filenames, same functions, different line numbers, different ` +
  `code. If you ever find yourself naming another branch as the thing you verified against, you ` +
  `have already made this mistake — redo the measurement in ${ROOT}.\n`
const HANG_NOTE = baseSecs
  ? `The suite takes ~${Math.ceil(baseSecs)}s. If yours runs MUCH longer, do NOT wait it out and do ` +
    `NOT blame CPU contention: it is a PARSE ERROR. Kill it and run --check-only on every file you ` +
    `touched (a syntax check passes on semantic breakage — a symbol used before its declaration, a ` +
    `duplicated func, a class whose definition you dropped while keeping its call sites).\n` +
    `A HEADLESS RUN SITTING AT ~1% CPU IS BROKEN, NEVER SLOW. A healthy headless sim is CPU-BOUND ` +
    `(measured: 4,000 ticks in 1.87s at 97% CPU). Low CPU + indefinite runtime + no output means the ` +
    `script ABORTED before installing a main loop — an error inside _init leaves the engine spinning ` +
    `with nothing to do, forever. Read the process's own stdout/stderr for that error instead of ` +
    `waiting, and do not diagnose it as "a slow probe" or "contention".\n` +
    `AND IF A TEST FAILS ON ART YOU JUST CHANGED, SUSPECT THE IMPORT CACHE FIRST. Godot serves ` +
    `.godot/imported/*.ctex, not the file on disk; a worktree warmed by copying .godot holds a ` +
    `SNAPSHOT, so regenerated art fails its own test on stale pixels while the tree is correct. ` +
    `Compare the cache mtime against the asset, re-run --import, and only then believe the red — ` +
    `otherwise you will "fix" a working asset.\n`
  : ''

// Two reporting habits that separated the trustworthy agent reports from the plausible ones in a
// session where EIGHT OF EIGHT briefs turned out to be wrong in some specific. Both are cheap and
// both are things a confident-sounding summary silently omits.
const MEASURE_NOTE =
  `REPORT NUMBERS YOU MEASURED, BEFORE AND AFTER. Not "the cursor is smaller" but "128px -> 48px ` +
  `at the default 2x window"; not "ammo is fine" but "306 rounds/min vs 213, dry 0.8% of ticks". ` +
  `A fix whose effect you cannot state as a measurement is a fix you are guessing about. Where the ` +
  `claim is statistical, use the MEDIAN and say your sample: one pathological seed owns the mean, ` +
  `and that is exactly how a real run produced a bogus "one sector causes 48% of all deaths" ` +
  `headline that sent a whole investigation at the wrong sector. Name your instrument's limits too ` +
  `— a scripted bot's deaths are not a player's.\n` +
  `REPORT WHAT YOU CHECKED AND FOUND CORRECT, not only what you changed. Negative results stop the ` +
  `next cycle re-deriving them at full cost, and they are the evidence that a sweep was actually a ` +
  `sweep: one pass reported 15 confirmed defects AND the list of indicators it verified were honest, ` +
  `which is what made the 15 believable. If a claim in the brief did not reproduce, say so plainly ` +
  `— "already fixed" and "this premise is wrong" are correct, valuable outcomes, not failures.\n`

// The engine-error gate reads its own log back out of a user:// dir that is shared by EVERY
// concurrent Godot on this machine, so a sibling run can rotate the log away and the gate
// reports "no log carried this run's marker" — a FALSE NEGATIVE that is not about your edit.
// Observed on 3 of 6 parallel agents in one afternoon; each burned an attempt re-litigating a
// clean change. It fails closed (correct), so the answer is one serial retry, never weakening it.
const GATE_NOTE =
  `If the suite fails with "no log carried this run's marker", that is NOT your change: parallel ` +
  `Godot processes share one user:// log dir and rotate each other's logs away. Re-run the suite ` +
  `ONCE, alone (pkill any stray Godot by FULL binary path first — "grep godot" also matches the ` +
  `godot-mcp npm servers and will lie to you). Treat it as a real failure only if it repeats on ` +
  `the serial re-run. Never add it to ERROR_ALLOW to make it go away.\n`
log(`baseline green (${baseErrors} pre-existing SCRIPT ERROR lines) - starting cycles`)

// 2. LEDGER. shipped/dismissed used to live only in memory, so every RUN re-derived the
//    same findings from scratch — six runs independently re-reported the terrain tiling,
//    the banner overlaps and the shop clutter. Persist it and feed it back to the reviewer.
const prior = await agent(
  `Read ${LEDGER} in ${ROOT} if it exists and return its {shipped:[], dismissed:[], backlog:[], decisions:[]} arrays. ` +
  `If the file does not exist, return two empty arrays — do NOT create it, and do not fail.`,
  { label: 'ledger-load', phase: 'Preflight', model: 'opus', effort: 'high', schema: LEDGER_SCHEMA })
for (const t of ((prior && prior.shipped) || [])) { shipped.add(norm(t)); if (norm(t)) titleOf.set(norm(t), t) }
for (const t of ((prior && prior.dismissed) || [])) { dismissed.add(norm(t)); if (norm(t)) titleOf.set(norm(t), t) }
for (const d of ((prior && prior.decisions) || [])) if (d && !decisions.includes(d)) decisions.push(d)
for (const b of ((prior && prior.backlog) || [])) {
  if (b && b.title && norm(b.title) && !shipped.has(norm(b.title)) && !dismissed.has(norm(b.title))) { backlog.set(norm(b.title), b); titleOf.set(norm(b.title), b.title) }
}
if (shipped.size || dismissed.size) {
  log(`ledger: ${shipped.size} already shipped, ${dismissed.size} already dismissed - ` +
      `the reviewer is told to find something new`)
}

// PROBES THE PRE-FLIGHT RAN THAT STILL REPRODUCE ARE THE CHEAPEST FINDINGS IN THE RUN, so they
// join the backlog before cycle 1 and compete for the primary slot like any other open entry.
// Uniquely among candidates they arrive with the two expensive halves already done: a deterministic
// repro and a ready-made ratchet (the probe becomes the failing-then-passing check the gate wants).
// They are NOT auto-trusted — Confirm still runs, and can retire one as already_fixed — because a
// probe proves a behaviour, not that the behaviour is wrong. Tagged behaviour so the `--known` list
// never feeds a symptom back to the pixel reviewer that no frame could have shown.
for (const p of ((baseline && baseline.open_probes) || [])) {
  const k = p && p.title && norm(p.title)
  if (!k || shipped.has(k) || dismissed.has(k) || backlog.has(k)) continue
  backlog.set(k, { title: p.title, detail: `${p.detail}\n\nREPRO (committed, run it): ${p.script}`,
                   cycle: 0, lens: 'behaviour' })
  titleOf.set(k, p.title)
}
const probeCount = ((baseline && baseline.open_probes) || []).length
if (probeCount) log(`pre-flight: ${probeCount} committed probe(s) STILL reproduce a defect at HEAD - ` +
    `seeded into the backlog with their own output as evidence`)

// The ledger is the CROSS-RUN carry, and it rides inside a prompt every single cycle. Measured
// 2026-07-26 on a live run: ledger.json was 45,996 chars, of which 36,547 were backlog `detail`
// (mean 1,142, max 3,807) — a 12,272-char prompt handed to a model whose only job is byte-for-byte
// reproduction, which is precisely the setup that produced the documented title-drift corruption.
// Capping detail at 400 cuts that payload 69%.
//
// CAPPED AT SERIALISATION ONLY, and the distinction is load-bearing. The in-memory `backlog` map
// keeps FULL detail, so this run's Report phase still writes the complete measurements into the
// committed Backlog.md. Capping at bank time instead would truncate the numbers everywhere, and
// the numbers are the entire reason an entry is actionable rather than an opinion. What a LATER
// run inherits is the first 400 chars plus a pointer to where the full text lives.
const LEDGER_DETAIL_CAP = 400
const LEDGER_DETAIL_CYCLES = 3   // entries older than this carry title only
const forLedger = (b, nowCycle) => {
  // TITLES ARE NEVER DROPPED. They are the dedupe keys, they are ~80 chars, and losing one makes
  // the loop re-attack something it already settled. DETAIL is the bulk and it is what gets bounded.
  const age = nowCycle - (Number(b.cycle) || 0)
  if (age > LEDGER_DETAIL_CYCLES) {
    return Object.assign({}, b, { detail: `[see Backlog.md — detail aged out of the ledger]` })
  }
  const d = String(b.detail || '')
  if (d.length <= LEDGER_DETAIL_CAP) return b
  return Object.assign({}, b, {
    detail: d.slice(0, LEDGER_DETAIL_CAP).trimEnd() + ` […truncated for the ledger; full text in Backlog.md]`,
  })
}

const flushLedger = async (n) => await agent(
  `Write ${LEDGER} in ${ROOT} as JSON with exactly these keys:\n` +
  `  {"shipped": ${JSON.stringify([...shipped])}, "dismissed": ${JSON.stringify([...dismissed])},\n` +
  `   "backlog": ${JSON.stringify([...backlog.values()].map(b => forLedger(b, n)))},\n` +
  `   "decisions": ${JSON.stringify(decisions)}}\n` +
  `Overwrite it wholesale, create parent dirs if needed, and do NOT git add it (.aaa/ is ignored).\n\n` +
  `⚠️ COPY THE JSON ABOVE BYTE-FOR-BYTE. Do not re-title, shorten, summarise, re-word, re-order or ` +
  `"tidy" ANY string — not a title, not a detail, not a decision. Write the bytes you were given.\n` +
  `WHY THIS IS NOT PEDANTRY: the TITLE is the deduplication key. Every later cycle asks "have I ` +
  `already shipped or dismissed this?" by normalising the title and comparing it. Paraphrase a ` +
  `title and that comparison silently stops matching, so a defect that was already fixed reads as ` +
  `still-open and the loop pays to attack it again. Measured 2026-07-26: this exact drift happened ` +
  `("The MG nest's 30-tick aim lane is drawn but never fired down — and the HUD tells you to dodge ` +
  `it" came back as "MG nest telegraph never fires down drawn lane"), and a route-fork defect ` +
  `ended up in BOTH shipped and backlog under two different wordings. Some titles survived exact ` +
  `and some drifted, which is worse than total corruption because the breakage is intermittent.\n` +
  `If the JSON is large, write it in chunks — but never regenerate it from memory or from your own ` +
  `summary of it. If you cannot reproduce it exactly, say so instead of writing an approximation.`,
  { label: `ledger:${n}`, phase: 'Preflight', model: 'opus', effort: 'high' })

// PLAY THE GAME AND MEASURE THE CURVE. Runs once per run, not per cycle: it is the sim that moves
// the curve, and a 4-seed campaign is minutes. The output is fed to the behaviour lens every cycle.
let pacing = null
if (PACING) {
  phase('Pacing')
  pacing = await agent(
    `MEASURE THE DIFFICULTY CURVE of the game at ${ROOT} by PLAYING it, then compare against the ` +
    `previous measurement.\n\n` +
    `0. Stage the probe:  mkdir -p ${ROOT}/.aaa && cp ${PROBE} ${ROOT}/.aaa/difficulty_probe.gd\n` +
    `   It STEPS the sim; it must never await frames (60 ticks/s vs ~7,000). Both modes across ` +
    `4 seeds is ~30 s. It runs god mode so a hard stage cannot truncate its own evidence, and it ` +
    `reports MEDIANS because one trapped seed once owned a mean and invented a "wall".\n` +
    `1. Run exactly:  JSON_OUT=${PACING_JSON} ${PACING}\n` +
    `   Redirect to a file — Godot BLOCKS on a full 16KB stdout pipe, so \`cmd | grep\` looks ` +
    `exactly like a hang. A healthy headless sim is CPU-BOUND; low CPU means broken, never slow.\n` +
    `1b. FIRST CHECK THE BASELINE IS COMPARABLE. Read the \`head\` and \`driver\` fields in ` +
    `${CALIB} (missing = NOT comparable) and compare \`head\` to \`git -C ${ROOT} rev-parse HEAD\`. ` +
    `If they differ, the calibration measured a DIFFERENT GAME and every delta is a RE-BASELINE, ` +
    `not a regression: set baseline_valid=false, report movement as context only, and leave ` +
    `\`tunable\` EMPTY. Same if the scripted driver changed — a bot that gained a behaviour is a ` +
    `different instrument and its offense numbers are not comparable at all.\n` +
    `WHY THIS IS A HARD GATE: \`tunable\` REQUIRES a delta as its anchor, so after a balance change ` +
    `EVERY stage shows a large delta and EVERY stage looks anchored — the safeguard inverts into a ` +
    `false-positive generator exactly when the game is moving fastest. Observed 2026-07-26: a ` +
    `calibration written at 17:48 was still being diffed against after six shipped gameplay changes ` +
    `AND a driver change that moved on-foot kills/1000t from 34.23 to 30.75.\n` +
    `2. The probe reads ${CALIB} itself and prints a DELTA section against it. Read that section — ` +
    `it is the ONLY difficulty signal independent of how good the driver is (same bot, same seeds, ` +
    `different number means the GAME moved). Then copy ${PACING_JSON} over ${CALIB}, adding a ` +
    `"recorded" date field, the CURRENT \`head\` sha, and a one-line \`driver\` fingerprint (which scripted bot, which behaviours), so the next run can tell a regression from a re-baseline. Also copy it to ${PACING_BASE}. ` +
    `Set calibration_written=true only once that write actually succeeded.\n` +
    `3. Report the table, and classify every costly stage.\n` +
    `4. Fill \`tunable\` with ONLY the stages that cleared the anchor bar, and leave it EMPTY if ` +
    `none did. An empty tunable list on a run full of dramatic knockdown counts is the correct ` +
    `and expected output the first time this ever runs, because there is no baseline to move ` +
    `against yet. Do not manufacture an anchor to fill the field.\n\n` +
    `THE ONE THING TO GET RIGHT: a knockdown count from a scripted bot measures THE BOT, not the ` +
    `difficulty. This project has already lost a full session to that exact error — a sector was ` +
    `"too hard" for 45 cycles and turned out to be a bot that could not track a 20px disc drifting ` +
    `at 2px/tick, absorbing 6,200 ticks against a design budget of 150-320. The tool now prints an ` +
    `\`offense\` figure (player kills per 1000 ticks) precisely so you can tell them apart:\n` +
    `  costly + offense near the median  -> real pressure. A genuine outlier.\n` +
    `  costly + offense COLLAPSED        -> the driver cannot fight there. instrument_suspect.\n` +
    `Put every stage in exactly one of those buckets and never move a collapsed-offense stage into ` +
    `outliers because its raw numbers look dramatic.\n\n` +
    `Report trustworthy=false if the run truncated (a stage whose ticks sit near MAXT is cut off, ` +
    `so its total is a floor not a measurement), if too few seeds ran to median honestly, or if the ` +
    `tool errored. A number nobody should act on is worse than no number.\n` +
    `Do NOT change any game code. You are measuring.`,
    { label: 'pacing', phase: 'Pacing', model: 'opus', effort: 'high', schema: PACING_SCHEMA })
  if (pacing) {
    log(`pacing: ${(pacing.outliers || []).length} real outlier(s), ` +
        `${(pacing.instrument_suspect || []).length} instrument-suspect, ` +
        `${(pacing.regressions || []).length} change(s) since baseline, ` +
        `${(pacing.tunable || []).length} anchored as tunable` +
        `${pacing.calibration_written ? '' : ' — CALIBRATION NOT WRITTEN, next run has no baseline'}` +
        `${pacing.trustworthy ? '' : ' — NOT TRUSTWORTHY, see caveats'}`)
  }
}


// 2b. TRIAGE THE SEEDED BACKLOG, ONCE, BEFORE ANY CYCLE PAYS FOR IT.
// A backlog persists across runs, so its oldest entries are exactly the ones a sibling session
// or an earlier run has since fixed — and the loop only discovers that by spending a full
// Confirm (opus, reads code, runs the sim) per entry, mid-cycle, after already paying for a
// dossier capture and two reviews. MEASURED on the run that motivated this: Confirm outcomes
// were real:1, not-real:1, already_fixed:3 — four of five verifications bought nothing, and
// three consecutive cycles of an earlier run died the same way, producing zero fixes in 2.5h.
// One batched pass costs a single agent and reclassifies the whole queue up front.
// Deliberately conservative: `dismissed` means NEVER LOOK AGAIN, so an over-eager "fixed"
// permanently buries a live defect. Unsure MUST return open.
if (backlog.size >= 3) {
  phase('Preflight')
  const entries = [...backlog.values()].map(b => `- ${b.title}\n    ${(b.detail || '').slice(0, 400)}`).join('\n')
  const triage = await agent(
    `Triage a stale defect backlog for the project at ${ROOT}. Change NOTHING — you are reading.\n\n` +
    `Each entry below was a REAL defect when it was filed. Since then other cycles, other runs and ` +
    `other sessions have committed to this tree, so some are already fixed and some describe code ` +
    `that has moved. Decide, per entry, against the CODE AT HEAD.\n\n` +
    `${entries}\n\n` +
    `For each: open the file it names, read what is there NOW, and put its title in exactly one of ` +
    `fixed / unreal / open.\n` +
    `- fixed  = you SAW the corrected code. Name the file:line in notes.\n` +
    `- unreal = the described behaviour does not exist at HEAD (the premise was wrong or the code ` +
    `moved so far the entry no longer means anything).\n` +
    `- open   = still there, OR you could not settle it cheaply. **THIS IS THE DEFAULT.**\n\n` +
    `BE CONSERVATIVE, and understand the asymmetry: a wrong "open" costs one Confirm later, which ` +
    `is exactly what happens today. A wrong "fixed" or "unreal" is PERMANENT — those titles are ` +
    `never looked at again, so a live defect is buried forever. When the two are close, choose open.\n` +
    `Do not run the game and do not run the suite; this is a read. Copy every title BYTE-FOR-BYTE ` +
    `— they are dedupe keys, and a re-worded title silently matches nothing.`,
    { label: 'backlog-triage', phase: 'Preflight', model: 'opus', effort: 'high', schema: TRIAGE_SCHEMA })
  if (triage) {
    let moved = 0
    for (const t of (triage.fixed || [])) {
      const k = norm(t); if (k && backlog.has(k)) { backlog.delete(k); shipped.add(k); titleOf.set(k, t); moved++ }
    }
    for (const t of (triage.unreal || [])) {
      const k = norm(t); if (k && backlog.has(k)) { backlog.delete(k); dismissed.add(k); titleOf.set(k, t); moved++ }
    }
    log(`backlog triage: ${moved} of ${moved + backlog.size} entries retired up front ` +
        `(${(triage.fixed || []).length} already fixed, ${(triage.unreal || []).length} no longer real); ` +
        `${backlog.size} still open`)
    if (moved) await flushLedger(0)
  }
}

const cycles = []
for (let i = 1; i <= N; i++) {
  const tag = `cycle ${i}/${N}`
  const dossierPath = `${ROOT}/.aaa/dossier-${i}.md`
  const reviewPath = `${ROOT}/.aaa/review-${i}.json`

  phase('Dossier')
  const dossier = await agent(
    `You are preparing a PLAYER-EXPERIENCE DOSSIER for the Godot game at ${ROOT} (${tag}).\n` +
    `Do NOT change any game code.\n\n` +
    `1. mkdir -p ${ROOT}/.aaa/shots-${i} (the capture tool cannot create it and will silently write ` +
    `nothing) and make sure .aaa/ is in ${ROOT}/.gitignore.\n` +
    (LIVE
      ? `2. Capture frames from a REAL RUN (preferred - a posed state that forgets to set a field\n` +
        `   renders as a bug, and the reviewer correctly reports it; observed live with a victory\n` +
        `   card showing 0 KILLS because the shot builder never posed the counter):\n` +
        `     mkdir -p ${ROOT}/.aaa && cp ${CAPTURE} ${ROOT}/.aaa/live_capture.gd\n` +
        `     SHOT_DIR=${ROOT}/.aaa/shots-${i} LIVE_FRAMES=19000 LIVE_EVERY=1200 LIVE_GOD=1 \\\n` +
        `       ${GODOT} --path ${ROOT} --rendering-method gl_compatibility -s res://.aaa/live_capture.gd\n` +
        `   LIVE_GOD=1 arms the debug auto-restore so the run CANNOT end, and the spread frame\n` +
        `   interval samples the WHOLE campaign instead of its first 15 seconds. This matters more\n` +
        `   than it sounds: before this existed, every review cycle ever run judged sector 1 of 6,\n` +
        `   because the scripted bot dies at the Colossus every time and Last Stand is dead-is-dead.\n` +
        `   Sectors 2-6, the Colossus and the victory card had NEVER been seen by a reviewer.\n` +
        `   The capture prints KNOCKDOWNS (per sector) and ENDSTATE when it finishes.\n` +
        `   *** PUT THE KNOCKDOWN TELEMETRY AND "difficulty was neutralised" IN THE DOSSIER. ***\n` +
        `   A god-mode run shows the whole game but LIES about difficulty - the player never loses.\n` +
        `   If you hand that to the reviewer unlabelled it will conclude the pacing is fine, which is\n` +
        `   a false signal worse than no signal. State plainly that auto-restore was on, and give the\n` +
        `   per-sector knockdown counts as the difficulty evidence instead (one real run reported\n` +
        `   s4=41 of 85 total - nearly half the deaths in a single sector, and 2.3 min to cross vs\n` +
        `   12-45s elsewhere; that is a pacing finding a screenshot cannot carry).\n` +
        `   IF THE RENDER LOOP IS STARVED, SAY SO - do not silently ship a sector-1 dossier. An\n` +
        `   occluded/background macOS window throttles frame_post_draw to ~1fps (3 frames in 90s),\n` +
        `   so a deep run needs a foregrounded window. If you got far fewer shots than\n` +
        `   LIVE_FRAMES/LIVE_EVERY implies, report how far the run ACTUALLY got, then fall back to\n` +
        `   the short run (LIVE_FRAMES=900 LIVE_EVERY=60) plus the posed harness and say the deep\n` +
        `   content is missing from this cycle.\n` +
        `   THEN also run the posed harness into the SAME dir for the menu/debrief screens the run\n` +
        `   still never reaches (tools/screenshots.gd, same SHOT_DIR).\n`
      : `2. Capture fresh screenshots with the project's own harness (check CLAUDE.md / tools/screenshots.gd; ` +
        `SHOT_DIR=${ROOT}/.aaa/shots-${i} and the gl_compatibility rendering method).\n`) +
    `3. VERIFY the capture actually worked — this is mandatory and you may not skip or fake it:\n` +
    `     python3 ${VERIFY} ${ROOT}/.aaa/shots-${i} --min-shots ${MIN_SHOTS}\n` +
    `   "SAVED" lines and files on disk prove NOTHING: a broken harness writes byte-identical black\n` +
    `   PNGs and still reports success. If this exits non-zero, set shots_ok=false, put its output in\n` +
    `   shots_report, and STOP — do not write a dossier, do not describe the game from memory or from\n` +
    `   source code. A fabricated dossier is worse than no cycle at all.\n` +
    `4. Only if it exits 0: VIEW every captured PNG with the Read tool and describe what you actually\n` +
    `   see in them. Every visual claim in the dossier must be something you observed in an image.\n` +
    `5. You MAY read view/UI/audio source ONLY for things a screenshot cannot show (audio, timing,\n` +
    `   transitions). Never use code to describe how something LOOKS — if it is not in a shot, leave\n` +
    `   it out. The reviewer SEES these same screenshots itself, so a claim that contradicts them\n` +
    `   actively misleads it — the dossier's job is the non-visual half (audio, timing, feel).\n\n` +
    `Write ${dossierPath}: a purely CONSUMER-FACING description - what it looks like, sounds like, and feels ` +
    `like to play, screen by screen and moment by moment. Describe flaws as neutrally as strengths; do not ` +
    `sell the game. No file paths, no code, no engine talk, no mention ` +
    `of who made it or that it is a hobby/indie/AI project. Be concrete and detailed (aim 800-1500 words).\n` +
    `Return shots_ok, the verify output, and the dossier path.`,
    { label: `dossier:${i}`, phase: 'Dossier', model: 'opus', effort: 'high', schema: DOSSIER_SCHEMA })

  if (!dossier || !dossier.shots_ok) {
    const why = (dossier && dossier.shots_report) || 'dossier agent returned nothing'
    log(`${tag}: SCREENSHOTS UNUSABLE — skipping cycle rather than reviewing a fabricated dossier\n${why}`)
    cycles.push({ cycle: i, accepted: false, blocked: 'screenshot capture failed verification',
                  shots_report: why })
    continue
  }

  phase('Review')
  const review = await agent(
    `Run the AAA consumer reviewer and report its verdict (${tag}).\n\n` +
    `Run exactly: python3 ${SCRIPT} ${dossierPath} ${reviewPath} --shots=${ROOT}/.aaa/shots-${i}` +
    (REVIEW_MODEL ? ` --model=${REVIEW_MODEL}` : '') + knownFlag() + `\n` +
    `(--shots makes the reviewer SEE the screenshots; it takes up to 4 minutes, do not re-run on ` +
    `slowness). Then read ${reviewPath} and return its content ` +
    `as structured output: return EVERY giveaway in its ranked order, and each detail field must ` +
    `concatenate that giveaway's where / what_i_see / why_it_outs_it / aaa_version fields VERBATIM - ` +
    `do not summarize, shorten, or soften them.`,
    { label: `verdict:${i}`, phase: 'Review', model: 'sonnet', effort: 'low', schema: REVIEW_SCHEMA })

  if (!review) { log(`${tag}: reviewer failed, skipping cycle`); continue }

  // A SECOND, BLIND-TO-PIXELS reviewer. The consumer above only ever sees still frames, so every
  // giveaway it is CAPABLE of producing is cosmetic - across 45 recorded cycles it never once
  // named a gameplay defect, while five code-reading agents found five in a single pass (a rescue
  // target that feeds your kill streak, one grenade that disables both bosses, a victory card
  // naming the wrong biome, an arena that stops rearranging, a supply drop that silently vanishes).
  // Those out a game as non-AAA harder than any contrast ratio, and no screenshot can show them.
  // Same output shape as the visual review, so dedupe/batch/confirm/gate carry it unchanged.
  // Built with an array join, deliberately: the first version chained `+` and `?:` together, and
  // since `+` binds tighter the whole concatenation became the CONDITION — so it always emitted the
  // outliers line and silently dropped the table itself.
  let pacingBrief = ''
  if (pacing) {
    const parts = [
      `\n=== MEASURED DIFFICULTY CURVE (this run PLAYED the game — do not re-derive it) ===`,
      pacing.table || '(no table returned)',
    ]
    if ((pacing.outliers || []).length) {
      parts.push(`GENUINE OUTLIERS (costly AND fighting normally): ${pacing.outliers.join(' | ')}`)
    }
    if ((pacing.instrument_suspect || []).length) {
      parts.push(`⚠️ INSTRUMENT-SUSPECT — cost with COLLAPSED offense, i.e. the driver cannot fight ` +
        `there, so the number is about the bot and not the game. Do NOT report these as difficulty ` +
        `problems and do NOT propose tuning them: ${pacing.instrument_suspect.join(' | ')}`)
    }
    if ((pacing.regressions || []).length) {
      parts.push(`CHANGED SINCE THE LAST MEASUREMENT (the only signal that does not depend on how ` +
        `good the driver is): ${pacing.regressions.join(' | ')}`)
    }
    if (!pacing.trustworthy) {
      parts.push(`⚠️ THIS MEASUREMENT IS NOT TRUSTWORTHY: ${pacing.caveats || 'unstated'} — treat ` +
        `pacing as unmeasured this run rather than acting on it.`)
    }
    if ((pacing.tunable || []).length) {
      parts.push(`ANCHORED AS TUNABLE — these cleared the bar for being about the GAME rather than ` +
        `about the driver, each with the anchor that got it there. A difficulty finding may only ` +
        `name a stage from THIS list:\n` +
        pacing.tunable.map(t => `  · ${t.stage} — anchor: ${t.anchor}`).join('\n'))
    } else {
      parts.push(`NOTHING IS ANCHORED AS TUNABLE THIS RUN. A scripted bot cannot establish that a ` +
        `HUMAN finds a stage too hard or too easy — only that IT did, which is a fact about the ` +
        `bot. Absent a calibration delta or a human observation, you may report the numbers as ` +
        `context but you may NOT file "sector N is too hard / too easy" as a finding. This project ` +
        `spent a full session tuning a sector that was never the problem; the empty list is the ` +
        `guard against doing it again, not an oversight to work around.`)
    }
    parts.push(`Use these numbers instead of guessing at pacing. If you disagree with a ` +
      `classification, say which NUMBER changes your mind rather than asserting a different feel.`)
    pacingBrief = parts.join('\n') + '\n'
  }
  const behaviour = await agent(
    pacingBrief +
    `You are a veteran game-feel critic playing Commander In Chief (${tag}) - a deterministic ` +
    `top-down run-and-gun in ${ROOT}. You CANNOT see the screen. Judge only what the game DOES.\n\n` +
    `Read src/sim/ (the deterministic core - it is the source of truth for behaviour) and run the ` +
    `sim headlessly to check what you suspect. Hunt the things that make a player say "this is not ` +
    `a real studio game" while PLAYING, not while looking:\n` +
    `- rules that contradict what the game TELLS the player (a telegraph that lies, a reward that ` +
    `punishes, an objective that scores like a threat)\n` +
    `- a dominant or dominated option that makes a choice fake\n` +
    `- a system advertised in copy or UI that quietly stops working, or never started\n` +
    `- feedback the player never gets for something that actually happened to them\n` +
    `- PACING OUTLIERS, measured. Difficulty curve is a top-tier quality signal and a still frame ` +
    `cannot carry it, so nothing in a screenshot review has ever assessed it. You can: run the game ` +
    `headlessly with the debug auto-restore armed (it exists precisely so a run cannot end) and ` +
    `COUNT per stage - deaths/knockdowns, ticks to cross, ammo dry time, income. Then look for the ` +
    `outlier, not the average. A real run reported one sector owning 41 of 85 knockdowns (~48% of ` +
    `every death in the game) and taking 2.3 minutes to cross against 12-45 seconds for every other ` +
    `sector - three separate decisions (length x a half-speed modifier x its enemy roster) stacking ` +
    `into a wall nobody had evaluated together, invisible for the game's whole life because no run ` +
    `had ever survived to compare stages. A rising ramp is good design; one stage owning half the ` +
    `deaths is a defect. Report the TABLE, and beware the instrument: a scripted bot's deaths are ` +
    `not a player's, so distinguish "lethal" from "the bot cannot traverse it" before calling it ` +
    `a difficulty problem.\n` +
    `  MEASURE BY STEPPING THE SIM, NOT BY WATCHING IT. If the project separates a render-free ` +
    `deterministic core from its view (this one does), drive that core directly in a loop - never ` +
    `await frames in a headless probe. Frame-pacing throttles a simulation that could run flat out ` +
    `to WALL-CLOCK time: one observed probe took 5.3 real minutes per campaign at 1.5% CPU, idling ` +
    `between ticks, which turns a multi-seed study into a 25-minute job. The same repo's test suite ` +
    `runs 860+ methods INCLUDING a 60-second two-player torture in ~11 seconds, because the tests ` +
    `step the sim directly. That is ~100x, and it is the difference between a measurement you run ` +
    `every cycle and one you only run once. Await frames ONLY when you need pixels.\n` +
    `- difficulty that comes from concealment rather than challenge (unreactable windups, ` +
    `offscreen damage, a death with no visible cause)\n\n` +
    `MEASURE before claiming. Run the sim, count the beats, compare against the thresholds the ` +
    `code itself documents. Report only what you verified; say so if a suspicion did not hold.\n` +
    `Mark structural:true ONLY for things needing an engine/art-pipeline change - a behaviour fix ` +
    `is almost never structural. Each detail: where (file:line) + what happens + why it outs the ` +
    `game + what a real studio does instead.` + ROOT_NOTE + ``,
    { label: `behaviour:${i}`, phase: 'Review', model: 'opus', effort: 'high', schema: REVIEW_SCHEMA })

  const behaviourFindings = (behaviour && behaviour.giveaways) || []
  if (behaviourFindings.length) log(`${tag}: behaviour lens added ${behaviourFindings.length}: ` +
      behaviourFindings.map(g => g.title).join(' | '))
  // `all` is the full finding set for banking + reporting; ORDER HERE IS NOT PRIORITY
  // (see freshOrdered below, which is what target selection actually reads).
  const all = (review.giveaways || []).concat(behaviourFindings)
  // BEHAVIOUR LEADS. It used to be visual-first, with behaviour getting one reserved slot --
  // and measured over two cycles of one 20-cycle run that ordering was backwards. The visual
  // reviewer is REQUIRED by its own prompt to return >=3 fixable craft items, so it always
  // filled the primary slot; and it returns the SAME tells re-worded every cycle ("Text Contrast
  // and Screen Cluttering" -> "Text Contrast and Background Collision", "Generic Box-Border Menu
  // Framing" -> "Developer-Art Menu Container Layouts"), which the title-keyed dedupe cannot
  // catch. Meanwhile the behaviour lens returned, in those same two cycles: a wedged mover that
  // holds an Endless wave open forever (isolated repro: 0.0px in 600 ticks; census: 5 of 6 runs),
  // an anti-camp mortar that fires while the camera clamp forbids the advance it demands (46-58%
  // of every campaign measured as pinned), and an advertised counterplay that is geometrically
  // impossible (5,040 trials, 774 rounds on target, 774 blocked, zero kills).
  // So the priority is inverted and the RESERVED slot flips to visual -- symmetric, because
  // behaviour-only slots would reproduce this exact bug mirrored, and a sim fix plus a view fix
  // are still maximally different surfaces (which the extras rule wants anyway).
  // Which lens produced a finding. Load-bearing for --known: a pixels-only reviewer must
  // never be handed a sim-derived title to "reuse", or it will claim to see it.
  const lensOf = g => (behaviourFindings.includes(g) ? 'behaviour' : 'visual')
  const freshOrdered = behaviourFindings.concat(review.giveaways || [])
  log(`${tag}: ${review.verdict} (${review.confidence}%) - ${all.length} giveaways: ` +
      all.map(g => `${g.title}${g.structural ? ' [structural]' : ''}`).join(' | '))
  if (review.verdict === 'AAA' || all.length === 0) {
    cycles.push({ cycle: i, verdict: review.verdict, giveaways: all, note: 'nothing actionable to fix' })
    continue
  }
  // Attack the hardest tell that is actually fixable; structural ones are reported, never built.
  // Also skip anything an earlier cycle already shipped or already dismissed as unreal — the
  // reviewer has no memory between cycles and will happily re-report the same tell forever.
  const seen = t => norm(t) && (shipped.has(norm(t)) || dismissed.has(norm(t)))
  const fixable = g => !g.structural && !seen(g.title)
  // DRAIN THE BACKLOG, or it is a graveyard. `backlog` was written to, persisted across runs and
  // returned in the result — but never read as a target source, so nothing could ever build from
  // it. The docs already promised otherwise ("Backlog is deliberately NOT `seen`: these are still
  // open and still fair game to attack"), so the code contradicted its own stated intent. Found
  // 2026-07-26 with 12 entries rotting in it, SEVEN of them gameplay defects a player would feel
  // (an MG nest drawing an aim lane it never fires down, a claymore that kills you 4 ticks after
  // you plant it, a 40-coin sandbag that eats 100% of your own outgoing rounds, buying off the
  // ground paying 67% more than the shop wheel). They survived multiple full runs precisely
  // because every cycle re-derived a fresh visual list and spent its whole batch there.
  // Backlog entries are already confirmed-real, so they still pass through Confirm (which can
  // retire one cheaply as already_fixed if a sibling shipped it). Fresh review leads on even
  // cycles; the oldest backlog entry takes the primary slot on odd ones, so a 20-cycle run drains
  // ~10 known defects instead of 0 while still answering what the reviewer sees right now.
  const backlogQueue = [...backlog.values()].filter(fixable)
  const preferBacklog = (i % 2 === 1) && backlogQueue.length > 0
  const candidates = preferBacklog ? backlogQueue.concat(freshOrdered) : freshOrdered.concat(backlogQueue)
  // PROMOTE ON RETIRE, do not abandon the cycle. Confirm returning `real:false` or
  // `already_fixed` used to `continue`, throwing away every other slot in the batch -- including
  // the reserved behaviour finding. MEASURED 2026-07-26: with a 56-entry backlog (old entries are
  // exactly the ones most likely to be stale), THREE CONSECUTIVE CYCLES died at the first confirm
  // and the run produced zero fixes in 2.5 hours, each cycle having already paid for a dossier
  // capture and two full reviews. Retiring a candidate is correct and permanent, but it is not a
  // reason to drop 4-7 fresh findings that were already selected. So retire it and PROMOTE the
  // next candidate: `fixable()` re-reads shipped/dismissed, so re-running `candidates.find` after
  // the retirement advances by itself. `batchList` is deliberately computed AFTER this loop -- if
  // it is built from a target that then gets retired, it is read while stale (and `node --check`
  // will not catch it).
  let target = null, review_target = null, batchList = null, confirm = null
  const retired = []
  while (true) {
    target = candidates.find(fixable)
    if (!target) break
    if (preferBacklog) log(`${tag}: draining backlog (${backlogQueue.length} open): ${target.title}`)
    review_target = { giveaway_title: target.title, giveaway_detail: target.detail }
  phase('Confirm')
  confirm = await agent(
    `A blind reviewer looked at POSED screenshots of the game at ${ROOT} and named this tell (${tag}):\n\n` +
    `TITLE: ${review_target.giveaway_title}\n\nDETAIL:\n${review_target.giveaway_detail}\n\n` +
    `Answer TWO things.\n\n` +
    `(A) Would a real player actually hit this, or is it an artifact of how the screenshot harness ` +
    `stages its scenes? Those shots come from a tool that hand-poses sim state (read the capture ` +
    `tool - see CLAUDE.md - and the code that draws the affected screen). A field the harness never ` +
    `populates will look broken in a shot while being perfectly correct in a real run. Check what ` +
    `the LIVE game does: trace where the values/visuals in question come from during actual play.\n` +
    `real=true only if a player hitting this screen in a real run would genuinely see it. ` +
    `real=false if it only appears because of the posing - then say exactly which staged field or ` +
    `setup causes it, so the harness can be corrected instead of the game.\n\n` +
    `(B) VERIFY THE SPECIFICS, and correct them. This is the half that saves the cycle. A reviewer ` +
    `is reliably right about the SMELL and wrong about the DETAILS: measured ratios that do not ` +
    `reproduce, the wrong file, a magnitude off by 8x, a rule that moved, a defect a sibling already ` +
    `fixed. Every claim built on an unchecked specific is a coding attempt spent on fiction, and ` +
    `worse, one that can "fix" something that was already correct.\n` +
    `So: open the code. MEASURE the numbers - run the sim headlessly if that is what it takes; a ` +
    `value you did not execute is a hypothesis. That includes numbers that arrived INSIDE the ` +
    `finding: an endorsed-but-unmeasured specific is the same lie by inheritance, and the audit ` +
    `pass caught one live 2026-07-29 (a "uniform ~46px opaque zone" figure carried in from the ` +
    `finding that measured 29-50px by axis). Every number in your corrected_detail exists because ` +
    `YOU executed it, or it does not go in. Then write corrected_detail: the finding restated ` +
    `to match what the code actually does, with real file:line and real numbers, wrong claims ` +
    `dropped. It replaces the reviewer's version downstream, so it must stand alone.\n` +
    `If the defect does not reproduce because it is ALREADY FIXED, set already_fixed=true and say ` +
    `where it was fixed. That is a correct, cheap outcome - never force a change to look productive.\n\n` +
    `Do NOT change any code.` + ROOT_NOTE + ``,
    { label: `confirm:${i}`, phase: 'Confirm', model: 'opus', effort: 'high', schema: CONFIRM_SCHEMA })

  // `already_fixed` WINS over `real:false`. Observed live 2026-07-26: a confirm returned
  // real=false AND already_fixed=true — meaning "it does not reproduce because it is already
  // fixed" — and because this branch was tested first it got filed as a STAGING ARTIFACT, i.e.
  // permanently recorded as never-having-been-real. That loses the truth (it was real, and it is
  // done) and the two outcomes are not interchangeable: dismissed says "never investigate again",
  // shipped says "this is handled".
    if (confirm && confirm.real && !confirm.already_fixed) break

    // Both verdicts are cheap, correct and PERMANENT (flushed at once so no later run re-derives
    // them). `already_fixed` WINS over `real:false`: a confirm can legitimately return both,
    // meaning "it does not reproduce BECAUSE it is fixed", and filing that as a staging artifact
    // would record a real, finished defect as never-having-been-real. dismissed says "never
    // investigate again"; shipped says "handled". They are not interchangeable.
    const rwhy = (confirm && confirm.why) || 'confirmation agent returned nothing'
    if (confirm && confirm.already_fixed) {
      log(`${tag}: "${review_target.giveaway_title}" is ALREADY FIXED - retiring it\n${rwhy}`)
      shipped.add(norm(review_target.giveaway_title))
      retired.push({ title: review_target.giveaway_title, outcome: 'already fixed', why: rwhy })
    } else {
      log(`${tag}: "${review_target.giveaway_title}" is NOT REAL (staging artifact) - retiring it\n${rwhy}`)
      dismissed.add(norm(review_target.giveaway_title))
      retired.push({ title: review_target.giveaway_title, outcome: 'not real', why: rwhy })
    }
    backlog.delete(norm(review_target.giveaway_title))   // it is no longer open
    await flushLedger(i)
    target = null
  }

  if (!target) {
    // Bank this round's fresh findings BEFORE bailing. Moving the confirm into a loop moved the
    // banking below it, which quietly made this path lossy: the OLD code banked before Confirm ran,
    // so an abandoned cycle still kept its 4-7 new findings. Losing them here would be worst
    // possible timing — nothing shipped AND the round's discovery thrown away.
    for (const g of all) {
      if (g.structural || seen(g.title) || !norm(g.title) || backlog.has(norm(g.title))) continue
      backlog.set(norm(g.title), { title: g.title, detail: g.detail, cycle: i, lens: lensOf(g) }); titleOf.set(norm(g.title), g.title)
    }
    await flushLedger(i)
    log(`${tag}: every candidate retired as not-real or already-fixed (${retired.length}); ` +
        `${backlog.size} finding(s) banked`)
    cycles.push({ cycle: i, verdict: review.verdict, giveaways: all, accepted: false,
                  note: 'all candidates retired (not real / already fixed)', retired })
    continue
  }
  if (retired.length) log(`${tag}: promoted past ${retired.length} retired candidate(s) to: ${target.title}`)

  // The batch describes the SURVIVING target, so it is built only once something confirms real.
  const rest = candidates.filter(g => g !== target && fixable(g))
  // Reserved slot is now the VISUAL one (behaviour leads above). Without this, a cycle whose
  // behaviour lens returned several findings would spend the whole batch on sim work and the
  // consumer-visible tells would only ever be banked -- the same starvation, mirrored.
  const vTop = (review.giveaways || []).find(g => g !== target && fixable(g))
  const extras = (vTop ? [vTop].concat(rest.filter(g => g !== vTop)) : rest).slice(0, BATCH - 1)
  if (vTop && extras.includes(vTop)) log(`${tag}: visual finding reserved a slot: ${vTop.title}`)
  batchList = [target].concat(extras)
  if (extras.length) log(`${tag}: batching ${batchList.length} targets this cycle`)

  // Bank every real finding this round could not get to, so it survives the cycle.
  for (const g of all) {
    if (g.structural || seen(g.title) || batchList.includes(g) || !norm(g.title)) continue
    if (!backlog.has(norm(g.title))) { backlog.set(norm(g.title), { title: g.title, detail: g.detail, cycle: i, lens: lensOf(g) }); titleOf.set(norm(g.title), g.title) }
  }
  if (backlog.size) log(`${tag}: ${backlog.size} finding(s) banked, unattacked`)

  // The reviewer is right about the smell and wrong about the details. Everything downstream now
  // builds against the VERIFIED restatement, not the reviewer's guess at file/line/magnitude.
  if (confirm.corrected_detail) {
    review_target.giveaway_detail = confirm.corrected_detail
    batchList[0] = { title: target.title, detail: confirm.corrected_detail, structural: false }
    log(`${tag}: specifics corrected by verification - building against measured detail, not the review`)

    // ...and the verified restatement gets refuted before the plan trusts it. This runs ONLY on
    // a surviving candidate: a corrected_detail never written (confirm endorsed every specific)
    // has nothing to audit, and one from a retired candidate never reaches the planner, so it
    // cannot poison anything. Fails OPEN on a dead verifier or an empty rewrite — the original
    // already survived Confirm's own measurement pass, so it stays the best available; this
    // stage tightens a verified artifact and is not the only gate.
    const pv = await agent(
      `A verification pass restated a defect against the code at ${ROOT}, and a planner is about ` +
      `to build against it. REFUTE the restatement — assume it lies until it proves otherwise.\n\n` +
      `TITLE: ${review_target.giveaway_title}\n\nRESTATEMENT UNDER AUDIT:\n${confirm.corrected_detail}\n\n` +
      `Checks, each one non-optional:\n` +
      `1. Every file:line citation — open it; the code there must do what the text claims it does.\n` +
      `2. Every number — reproduce it: grep the constant, or run the sim headlessly if the value ` +
      `only exists at runtime. A number you did not execute is unverified.\n` +
      `3. Every "count/check it yourself with X" instruction — RUN X and reconcile its output with ` +
      `the adjacent claim.\n` +
      `4. Every citation of another doc or file — read the target's header; citing a file that ` +
      `declares itself stale or superseded is an issue.\n` +
      `ok=true ONLY if zero real issues survive. Per issue: quote the exact claim, name the ` +
      `contradicting evidence (file:line or the measured value), and give the concrete ` +
      `replacement text. Do NOT change any code.` + ROOT_NOTE,
      { label: `prose-verify:${i}`, phase: 'Confirm', model: 'opus', effort: 'high', schema: PROSE_VERIFY_SCHEMA })
    if (pv && !pv.ok && (pv.issues || []).length) {
      log(`${tag}: prose-verify caught ${pv.issues.length} false claim(s) in the confirmed detail ` +
          `- correcting before the plan builds on them`)
      const fixed = await agent(
        `Rewrite this defect restatement for the project at ${ROOT}, applying every correction ` +
        `listed — and nothing else. Keep it standalone: real file:line, real measured numbers, ` +
        `refuted claims dropped, no new claims added. Re-run any check the rewrite cites.\n\n` +
        `ORIGINAL:\n${confirm.corrected_detail}\n\nCORRECTIONS TO APPLY:\n` +
        pv.issues.map((it, k) => `${k + 1}. CLAIM: ${it.claim}\n   EVIDENCE: ${it.problem}\n   FIX: ${it.fix}`).join('\n') +
        `\n\nReturn ONLY the rewritten restatement.` + ROOT_NOTE,
        { label: `prose-fix:${i}`, phase: 'Confirm', model: 'opus', effort: 'high',
          schema: { type: 'object', required: ['detail'], properties: { detail: { type: 'string' } } } })
      if (fixed && (fixed.detail || '').trim()) {
        confirm.corrected_detail = fixed.detail
        review_target.giveaway_detail = fixed.detail
        batchList[0] = { title: target.title, detail: fixed.detail, structural: false }
      } else {
        log(`${tag}: prose-fix returned nothing usable - keeping the original confirmed detail`)
      }
    }
  }

  phase('Plan')
  const plan = await agent(
    `A consumer reviewer played the game at ${ROOT} and said it is NOT triple-A. Fix these ` +
    `${batchList.length} tell(s) this cycle - the first is the hardest one they named:\n\n` +
    batchList.map((g, k) => `[${k + 1}] ${g.title}\n${g.detail}`).join('\n\n') + `\n\n` +
    `Write a concrete implementation plan that kills THESE specifically - nothing else, no scope ` +
    `creep. If two of them turn out to fight each other (same file, same layout band), say so and ` +
    `plan only the first; a smaller correct plan beats a tangled one.\n\n` +
    `FIRST DECIDE: INSTANCE, OR CLASS? A reviewer reports the one instance it happened to SEE. ` +
    `If the root cause is a shared mechanism - a constant tuned against something that changed, a ` +
    `helper every caller routes through, a pipeline/import step, a layout rail, a formula - then ` +
    `the class IS the finding and the other instances are already shipped, unreported. ENUMERATE ` +
    `THE FULL SET before planning, and fix it at the seam. This is NOT scope creep: scope creep is ` +
    `wandering into unrelated improvements; this is fixing the reported defect everywhere it ` +
    `actually occurs. Measured, every time this came up in one session:\n` +
    `  1 oversized hitbox  -> 8 sprites, one import size_limit sweep nobody re-tuned SCALE for\n` +
    `  1 enormous cursor   -> 3 defects (size, a hotspot off the art's tip, an in-place resize)\n` +
    `  3 colliding banners -> ~50 producers could paint that rail; 16 bypassed the arbiter\n` +
    `  7 stale UI strings  -> 15 verified lies once the sim/view seam was swept deliberately\n` +
    `In every case the observed instance was a small fraction of the real set, and patching just ` +
    `it would have left the rest shipped and the next cycle re-finding a sibling. If it IS a lone ` +
    `instance, say so in one line and move on - do not invent a class that is not there.\n\n` +
    `If the tell traces to a DELIBERATE recent decision, that does not excuse it — it is the ` +
    `strongest signal in the run. Observed live: a commit whose stated purpose was "AAA polish" ` +
    `made the commander bark persistent, and the very next blind reviewer called that same ` +
    `persistence "missing display timers and neglected UI lifecycle management" AND shipped a ` +
    `doubled speaker prefix in the same change. Intent is invisible to a player; only the screen ` +
    `is real. Plan the fix on what the screen shows, and say in one line that you are overturning ` +
    `an intentional choice so the reviewer at the gate knows it was not an accident.\n\n` +
    `Explore the repo first (read CLAUDE.md; respect the sim/view split and determinism rules if present). ` +
    `The plan must name exact files, exact changes, the risk to determinism goldens, and how to verify it. ` +
    `Prefer view-layer changes when they achieve the same player-visible result.\n\n` +
    `MANDATORY - every item needs an automated check that FAILS ON CURRENT HEAD:\n` +
    `Name the assertion you will add (file + what it asserts) and the value it currently produces ` +
    `versus what it must produce. A rect overlap, a contrast ratio, a colour count, a measured\n` +
    `y-gap - whatever pins THIS giveaway. Look at how the suite already does this before inventing\n` +
    `anything: it has render-bounds capture and a WCAG contrast helper.\n` +
    `WHERE A CLASS EXISTS, PIN THE CLASS, NOT THE INSTANCE. A check that asserts "this one banner ` +
    `sits at this one y" passes forever while the next producer collides. Assert the invariant over ` +
    `the whole set, and derive the set FROM THE SOURCE so copy added tomorrow is covered the day it ` +
    `lands - e.g. scrape every show_banner()/_hint() call site and cross-product them (~33k overlap ` +
    `checks, run at 100% AND 200% text size), or record the canvas every art-derived constant was ` +
    `tuned against so a re-bake fails loudly instead of silently resizing the game. Then MUTATION-` +
    `TEST it: break the fix on purpose, confirm the check goes red, restore. A ratchet nobody proved ` +
    `can fail is decoration - and it is the only part of this cycle that outlives the next edit.\n` +
    `Why this is mandatory: without it the gate has to re-judge "is it gone?" from screenshots every ` +
    `round, and a fixed giveaway comes straight back the next time someone edits that file. The ` +
    `check is the deliverable as much as the fix is. If a giveaway genuinely cannot be pinned by ` +
    `an assertion, say so explicitly and explain why.\n\n` +
    TOOLBOX_NOTE + BRANCH_NOTE + ROOT_NOTE +
    `Return the plan as markdown.`,
    { label: `plan:${i}`, phase: 'Plan', model: 'opus', effort: 'high' })

  phase('Implement')
  let feedback = '', keep = '', gate = null, tries = 0
  // The coder used to be told WHAT to fix but never HOW CLOSE it already was, so an attempt one
  // item from shippable got the same "implement the plan" framing as an attempt that was half
  // wrong — and would go wide when it should have made a one-line touch-up. Measured twice:
  // closeness 93 -> 82 on this loop, and an earlier session logged the same shape (attempt 3
  // one-away, attempt 4 regressed). restore-best keeps the 93, so the cost is a burnt attempt out
  // of MAX_TRIES rather than lost work — still the most expensive attempt to waste.
  let lastScore = -1
  let bestSha = '', bestScore = -1, bestKeep = ''
  while (tries < MAX_TRIES) {
    tries++
    await agent(
      `Implement this plan in ${ROOT} (${tag}, attempt ${tries}).\n\n=== PLAN ===\n${plan}\n\n` +
      (feedback ? `=== REVIEWER FEEDBACK ON YOUR PREVIOUS ATTEMPT - fix all of it ===\n${feedback}\n\n` : '') +
      (lastScore >= 85
        ? `=== YOU ARE ONE SMALL STEP AWAY: the previous attempt scored ${lastScore}/100 ===\n` +
          `Make the SMALLEST change that clears the feedback above and nothing else. Do not refactor, ` +
          `do not touch a file the feedback does not name, do not "while I'm here" anything, do not ` +
          `re-tune a constant that was not objected to. At this score the only way to lose is to ` +
          `introduce a NEW problem, and a regression costs the whole attempt — the run keeps the ` +
          `best-scoring attempt, so going backwards from ${lastScore} wastes one of your ${MAX_TRIES}.\n\n`
        : lastScore >= 0
          ? `=== The previous attempt scored ${lastScore}/100 ===\n` +
            `Treat that as the distance left to cover: it is not nearly there, so re-read the plan's ` +
            `own success criteria before editing rather than patching only what the feedback names.\n\n`
          : '') +
      (keep ? `=== ALREADY VERIFIED CORRECT BY REVIEW - DO NOT redo, rewrite, or undo any of this; ` +
              `it is settled. Change ONLY what the feedback asks for ===\n${keep}\n\n` : '') +
      `Write the plan's CHECK FIRST, before the fix. Run it, and confirm it FAILS for the stated ` +
      `reason — a check that passes before you have fixed anything is pinning the wrong thing and is ` +
      `worse than no check, because it will read as green forever. Then make it pass.\n\n` +
      `CONFIRM WHAT MADE IT RED BEFORE YOU CHANGE ANYTHING. A failure names a SYMPTOM, not a culprit, ` +
      `and acting on the accusation instead of the cause edits working code. All observed in one ` +
      `session: a regenerated sprite's own test failed on OLD PIXELS because the import cache was ` +
      `stale (the file on disk was byte-identical to the branch that passed — "fixing" the art would ` +
      `have broken it); one duplicated func reported as 250+ parse errors across four INNOCENT files; ` +
      `an engine-error gate failed with "no log carried this run's marker", which was parallel ` +
      `processes rotating the log, not a defect. So: read the failure TEXT, not the count; check ` +
      `whether the input the check actually consumed is the input you think it consumed (cache, ` +
      `stale build, wrong path, another process); and reproduce the cause before editing. If the red ` +
      `turns out to be environmental, say so and fix the environment — do not "fix" correct code to ` +
      `chase a green.\n\n` +
      ROOT_NOTE + HANG_NOTE + TOOLBOX_NOTE + GATE_NOTE + MEASURE_NOTE +
      `Then run the test suite: ${TEST}\nIt must PASS with 0 failures, and introduce no SCRIPT ERROR ` +
      `beyond the ${baseErrors} that were ALREADY THERE before this run started (that count is the ` +
      `baseline; do not chase pre-existing ones, and do not hide new ones). If determinism ` +
      `goldens move, only re-record them if the change legitimately alters sim logic, and note why in the comment. ` +
      `Do not commit. Return a short summary of what you changed and the test result.`,
      { label: `code:${i}.${tries}`, phase: 'Implement', model: 'opus', effort: 'high' })

    gate = await agent(
      `Review the uncommitted changes in ${ROOT} (git diff + git status) against this goal (${tag}).\n\n` +
      `GOAL: eliminate this consumer-visible giveaway:\n${review_target.giveaway_title}\n${review_target.giveaway_detail}\n\n` +
      `=== PLAN THAT WAS SUPPOSED TO BE FOLLOWED ===\n${plan}\n\n` +
      `Verify by reading the code AND by running the test suite yourself: ${TEST}\n` + ROOT_NOTE + HANG_NOTE + TOOLBOX_NOTE + GATE_NOTE + MEASURE_NOTE +
      `The suite had ${baseErrors} SCRIPT ERROR lines BEFORE this run began — judge NEW ones only.\n` +
      `Also verify the plan's automated check actually exists, actually asserts the giveaway (not ` +
      `something adjacent), and would FAIL without the fix — stash the diff and run it if you want ` +
      `proof. A fix with no check, or with a check that passes on unfixed code, is not done.\n` +
      `perfect = true ONLY if the giveaway is genuinely gone from the player's perspective, the plan was fully ` +
      `executed, tests pass clean, and nothing was broken or half-done. Otherwise perfect = false and feedback ` +
      `must be a precise, actionable list of what to fix. Be strict.\n` +
      `BEFORE YOU SET perfect=true ON A VISUAL GIVEAWAY, LOOK AT THE SCREEN AGAIN. It was found by ` +
      `SEEING a frame; a diff and a green suite are not the same evidence, and this loop has never ` +
      `once re-rendered before declaring something fixed. Re-capture the affected screen and VIEW ` +
      `the PNG with the Read tool — the capture harness drives a real run and can reach deep content ` +
      `(set LIVE_GOD=1 so the run cannot end), so the screen that carried the defect is reachable. ` +
      `Confirm with your own eyes that the tell is gone AND that the fix did not introduce a new one ` +
      `next to it — a plate that now overlaps its neighbour, a resized sprite that no longer matches ` +
      `its hitbox, a colour that fixed contrast here and broke it there. If you cannot re-capture ` +
      `that screen, say so in feedback and judge on the evidence you DO have rather than pretending ` +
      `you looked. For a BEHAVIOUR giveaway (a rule, a telegraph, an economy) the failing-then-` +
      `passing check IS the evidence and no capture is required — do not burn a capture proving ` +
      `something a screenshot cannot show.\n\n` +
      `IF THIS DIFF ADDS OR CHANGES ANYTHING UNDER tools/, RUN IT, and treat a tool whose output ` +
      `contradicts the tests it supports as BLOCKING — not as a note. A measuring rig that disagrees ` +
      `with a green test is worse than no rig: it is committed, the next person runs it, and it tells ` +
      `them the codebase is broken when it is not. Observed 2026-07-26 on this loop's own cycle 1 — ` +
      `it committed tools/probe_frame_bounds.gd having already established the probe emits 44 false ` +
      `[OVER] lines (every one the footer legend strip, which the real test correctly excludes and ` +
      `the probe does not). That went into found_not_fixed and shipped anyway. Either fix the tool, ` +
      `or delete it from the diff and keep the fix — a cycle is not required to leave a probe behind, ` +
      `only a passing check. The same bar applies to its .gd.uid sidecar (repo convention) and to any ` +
      `tool that duplicates one already in tools/.\n\n` +
      `ALSO fill in, every time:\n` +
      `- closeness (0-100): how close THIS attempt is to shippable, judged on its own. Be honest and\n` +
      `  comparable between rounds — if every attempt fails, the highest-scoring one is restored and\n` +
      `  the others are discarded, so a flattering score on a bad attempt destroys better work.\n` +
      `- verified_good: what you CONFIRMED is correct. The next attempt is told not to touch it, so ` +
      `  being specific here is what stops the coder churning work you already approved.\n` +
      `- salvageable / revert_paths: if this is the LAST attempt, could discarding whole files leave a ` +
      `  coherent, working tree that is strictly better than HEAD? If the good and bad changes are ` +
      `  tangled inside one file, say salvageable=false — a half-reverted file is worse than none.`,
      { label: `gate:${i}.${tries}`, phase: 'Implement', model: 'opus', effort: 'high', schema: GATE_SCHEMA })

    if (gate && Array.isArray(gate.owner_decisions)) {
      for (const d of gate.owner_decisions) if (d && !decisions.includes(d)) decisions.push(d)
    }
    // Defects the gate found but did not fix go to the BACKLOG, where a later cycle can attack
    // them. Before this they were being dumped into owner_decisions — which is neither banked nor
    // (until now) persisted — so genuine bugs like "the HOW TO PLAY title is clipped off the top"
    // and "REBIND's P1|P2 selector renders two identical plates both reading PLAYER" were named
    // precisely and then dropped. Unlike a lens finding these are NOT re-derived next cycle: they
    // come from gating one specific diff, so if they are not banked, nothing rediscovers them.
    if (gate && Array.isArray(gate.found_not_fixed)) {
      for (const f of gate.found_not_fixed) {
        if (!f || !f.title || !norm(f.title) || seen(f.title) || backlog.has(norm(f.title))) continue
        backlog.set(norm(f.title), { title: f.title, detail: f.detail || '', cycle: i })
        log(`${tag}: gate banked a defect it did not fix: ${f.title}`)
      }
    }
    if (gate && gate.perfect) break
    // Snapshot THIS attempt before the next one overwrites it. Observed live: attempt 3 came back
    // "one item, everything else is approved" and attempt 4 undid approved work and regressed to a
    // four-item list — the loop had no memory of its own best state, so the near-miss was lost.
    // `git stash create` writes a dangling commit WITHOUT touching the working tree.
    const snap = await agent(
      `In ${ROOT} run this as ONE shell command, exactly as written:\n` +
      `    git add -A -- . ':!.aaa' 2>/dev/null || git add -A -- . ; SNAP_SHA=$(git stash create) ; echo "SNAP_SHA=$SNAP_SHA"\n` +
      `then return ONLY the 40-char hex after \`SNAP_SHA=\` (empty string if it printed nothing, ` +
      `which just means there were no changes — that is a valid answer, return it and stop).\n` +
      `\n` +
      `⚠️ RUN IT IN THAT SHAPE — do NOT "simplify" it to a bare \`git stash create\`. Some shells ` +
      `here sit behind an output-filtering proxy that rewrites a lone git invocation and prints a ` +
      `SUMMARY instead of the command's real stdout: a bare \`git stash create\` comes back as the ` +
      `literal text \`ok stash create\` with the SHA DISCARDED. The command is fine; the SHA is ` +
      `simply not in the output you get to see. Assigning to a variable and echoing it defeats ` +
      `that, and so does piping to \`cat\`. If what you get back is not 40 hex characters, do not ` +
      `improvise around it — re-run the echo form above, and if it still will not yield a SHA, ` +
      `return an EMPTY string rather than inventing or reconstructing one.\n` +
      `\n` +
      `Whatever happens, your LAST action must be the StructuredOutput tool CALL. Writing ` +
      `\`<StructuredOutput>\` as text in a message does not count and fails the whole run — that ` +
      `has now killed two multi-hour runs at this exact stage, both times after the agent had ` +
      `already recovered the right SHA.\n` +
      `\n` +
      `The \`||\` fallback is ` +
      `LOAD-BEARING, not defensive noise: when .aaa/ is gitignored — which this skill REQUIRES — ` +
      `naming it in a pathspec makes \`git add\` exit 1 with "the following paths are ignored", so ` +
      `the first form fails in every correctly-configured repo. The fallback needs no exclude ` +
      `because gitignore already omits .aaa. Verified in a scratch repo both ways: with .aaa ` +
      `ignored and not ignored, the snapshot captures tracked AND untracked work and never ` +
      `captures .aaa. Do NOT stash, reset, checkout or otherwise alter the working tree — ` +
      `stash create just records a snapshot commit and leaves everything in place.`,
      { label: `snap:${i}.${tries}`, phase: 'Implement', model: 'haiku', effort: 'low',
        schema: { type: 'object', required: ['sha'], properties: { sha: { type: 'string' } } } })
    const score = (gate && typeof gate.closeness === 'number') ? gate.closeness : 0
    if (snap && /^[0-9a-f]{7,40}$/.test((snap.sha || '').trim()) && score > bestScore) {
      bestScore = score; bestSha = snap.sha.trim(); bestKeep = (gate && gate.verified_good) || ''
      log(`${tag}: attempt ${tries} is the best so far (closeness ${score})`)
    }
    lastScore = score
    feedback = (gate && gate.feedback) || 'reviewer returned no verdict; re-check the plan end to end'
    if (gate && gate.verified_good) keep = gate.verified_good
    log(`${tag}: gate rejected attempt ${tries}${gate && gate.salvageable ? ' (says salvageable)' : ''}`)
  }

  let salvaged = false, restored = false
  // Restore-best: every attempt was rejected, but they were not equally bad. The LAST attempt is
  // whatever the coder happened to leave behind — often a regression of a better earlier one. Roll
  // the tree back to the highest-scoring snapshot before deciding what to salvage, so the salvage
  // pass judges the best work this cycle produced instead of its final flailing.
  if (gate && !gate.perfect && bestSha && bestScore >= (A.minCloseness || 60)) {
    const rb = await agent(
      `In ${ROOT}, an earlier attempt this cycle scored better than the current tree (${tag}).\n\n` +
      `Restore snapshot ${bestSha} over the working tree:\n` +
      `  git checkout ${bestSha} -- . && git checkout HEAD -- .aaa 2>/dev/null || true\n` +
      `(the snapshot is a dangling commit from \`git stash create\`; it holds that attempt's exact ` +
      `tree). Do NOT reset HEAD, do not commit, do not touch .aaa/.\n` +
      `Then run ${TEST} and report ok=true only if it PASSES with 0 failures and no new SCRIPT ERROR.`,
      { label: `restore-best:${i}`, phase: 'Implement', model: 'opus', effort: 'high',
        schema: { type: 'object', required: ['ok', 'detail'],
                  properties: { ok: { type: 'boolean' }, detail: { type: 'string' } } } })
    if (rb && rb.ok) {
      // The restored tree is a real, suite-green improvement that the gate scored at
      // >= minCloseness. Earlier this only chose WHICH version to throw away: acceptance
      // required gate.salvageable, and a gate whose good/bad changes are tangled in one
      // file correctly answers false every time — so a rolled-back, verified, 82/100 tree
      // was deleted by the full-revert path. A restore that passes IS the partial accept.
      restored = true
      log(`${tag}: rolled back to the best attempt (closeness ${bestScore}), suite green - accepting as PARTIAL`)
      if (bestKeep) gate = Object.assign({}, gate, { verified_good: bestKeep })
    } else {
      log(`${tag}: restore-best FAILED - staying on the last attempt :: ${rb && rb.detail ? String(rb.detail).slice(0,140) : 'no detail'}`)
    }
  }

  // Salvage pass: the gate exhausted its attempts but says the tree minus a few files is
  // still a real improvement. Revert exactly those files and re-verify — a partial win that
  // PASSES is worth more than discarding work the gate itself called correct. The re-check is
  // non-negotiable: reverting files can break what remains, and "probably fine" is how a red
  // suite gets committed.
  if (gate && !gate.perfect && gate.salvageable && (gate.revert_paths || []).length) {
    const paths = gate.revert_paths.join(' ')
    const sv = await agent(
      `In ${ROOT} a change was rejected as a whole, but review says the rest is worth keeping (${tag}).\n\n` +
      `1. Discard ONLY these paths: \`git checkout HEAD -- ${paths}\` (also \`git clean -fd\` any of them ` +
      `that are untracked new files). Touch nothing else.\n` +
      `2. Re-verify what remains: run ${TEST}. It MUST print PASS with 0 failures and introduce no new ` +
      `SCRIPT ERROR, and determinism goldens must be untouched.\n` +
      `3. Report ok=true ONLY if the suite is genuinely green after the revert. If it is red, or the ` +
      `remainder no longer makes sense on its own, report ok=false — do NOT try to fix it.\n\n` +
      `WHAT REVIEW CONFIRMED IS GOOD (this is what you are preserving):\n${gate.verified_good || '(unstated)'}`,
      { label: `salvage:${i}`, phase: 'Implement', model: 'opus', effort: 'high',
        schema: { type: 'object', required: ['ok', 'detail'],
                  properties: { ok: { type: 'boolean' }, detail: { type: 'string' } } } })
    salvaged = !!(sv && sv.ok)
    log(`${tag}: salvage ${salvaged ? 'SUCCEEDED - committing the verified-good remainder' : 'failed - full revert'}` +
        `${sv && sv.detail ? ' :: ' + String(sv.detail).slice(0, 160) : ''}`)
  }

  const partial = salvaged || restored
  const accepted = !!(gate && gate.perfect) || partial
  // Remember the outcome: a fully-fixed tell must not be re-attacked, and one that survived every
  // coding attempt will not fall to another round on the very next cycle either. A SALVAGE goes in
  // neither set on purpose — only part of it shipped, so the tell may well still be on screen and
  // a later cycle should be free to finish the job.
  if (!partial) {
    // A batched cycle ships (or burns) every target it planned, not just the primary.
    for (const g of batchList) {
      (accepted ? shipped : dismissed).add(norm(g.title))
      // ...and it leaves the map, or the SHIPPED title persists as an open backlog entry with
      // PRE-fix detail. Measured 2026-07-29: the run shipped "Unmasked Radial Shop Menu Overlay",
      // "Unaligned Leaderboard Column Formatting" and "Full-Screen Low-Pass Distortion" and all
      // three still sat in result.backlog (the cycle-1 banked copy survives an attack from
      // backlogQueue, because only the retire path deleted). The next run's ledger-load filters
      // shipped titles, so this was cosmetic — but the Report writer had to reconcile the
      // overlap by hand ("lens still flags a remainder") to keep Backlog.md honest. A remainder
      // the lens genuinely still sees must come back as a FRESH title, not ride a stale copy.
      backlog.delete(norm(g.title))
    }
    await flushLedger(i)
  }
  if (accepted) {
    await agent(
      `In ${ROOT}, commit the current changes (exclude .aaa/). One commit, conventional style with an emoji, ` +
      `subject referencing the AAA-polish fix "${review_target.giveaway_title}"${partial ? ' — and say in the body that this is a PARTIAL fix: review rejected part of the work, which was reverted, so the giveaway may not be fully gone.' : ''}. Do not push.\n\n` +
      ROOT_NOTE +
      `⚠️ PROVE THE COMMIT HAPPENED, and do not report success on a no-op. Capture HEAD BEFORE and ` +
      `AFTER:\n` +
      `    before=$(git rev-parse HEAD); <stage + commit>; after=$(git rev-parse HEAD)\n` +
      `If \`after\` equals \`before\`, the commit DID NOT HAPPEN — say so loudly and report the ` +
      `failure rather than returning the old sha. Then run \`git status --porcelain\` and include ` +
      `it: work that is still modified/staged after a "successful" commit is an ACCEPTED CYCLE ` +
      `ABOUT TO BE LOST.\n` +
      `Why this is a hard check and not a nicety — observed 2026-07-26, cycle 3 of a live run: the ` +
      `gate passed at closeness 96, this stage returned the PREVIOUS cycle's sha, and 781 insertions ` +
      `across 7 files sat staged-but-uncommitted. The next cycle then either sweeps that work into ` +
      `its own commit under the wrong message, or — if IT is rejected — destroys an ACCEPTED cycle ` +
      `outright, because the reject path is \`reset --hard\` + \`clean -fd\`. A silent no-op here is ` +
      `the most expensive failure in the whole loop: the work was already reviewed and paid for.\n` +
      `Return the NEW sha, and only a new sha.`,
      { label: `commit:${i}`, phase: 'Implement', model: 'opus', effort: 'high' })
  } else {
    // A rejected cycle MUST leave the tree exactly as it found it. Otherwise the next
    // cycle inherits work the gate already refused, builds on top of it, and sweeps it
    // into ITS commit - so rejected code ships anyway, attributed to the wrong fix.
    // .aaa/ is gitignored, so plain `clean -fd` (no -x) leaves the run's artifacts alone.
    await agent(
      `In ${ROOT}, discard ALL uncommitted work — but SNAPSHOT IT FIRST so nothing is ever ` +
      `unrecoverable:\n` +
      `    git add -A -- . ':!.aaa' 2>/dev/null || git add -A -- .\n` +
      `    snap=$(git stash create) && [ -n "$snap" ] && git tag -f rescue/cycle-${i} "$snap"\n` +
      `The \`||\` fallback is required, not defensive noise: when .aaa/ is gitignored (which this ` +
      `skill requires) naming it in a pathspec makes \`git add\` exit 1, and the \`&&\` chain then ` +
      `skips the snapshot entirely — the rescue would be empty at exactly the moment it matters. ` +
      `The fallback needs no exclude because gitignore already omits .aaa.\n` +
      `The \`git add -A\` is LOAD-BEARING and was missing until 2026-08-20. A bare ` +
      `\`git stash create\` snapshots TRACKED modifications only — so the rescue tag could not ` +
      `restore the one category the \`git clean -fd\` below actually deletes. Proven in a scratch ` +
      `repo: bare stash captured 1 tracked file, clean -fd removed an untracked directory, and the ` +
      `snapshot held 0 of its files. Staging first is what makes the promise above true.\n` +
      `\`git stash create\` writes a dangling commit WITHOUT touching the tree, and the tag keeps it ` +
      `alive through both commands below. This costs nothing and it has already mattered: a cycle ` +
      `whose commit silently no-opped left 781 insertions of ACCEPTED, gate-passed work sitting ` +
      `uncommitted, one rejection away from being erased by exactly this step. Report the tag.\n` +
      `THEN discard: \`git reset --hard HEAD\` then \`git clean -fd\` ` +
      `(NO -x — the gitignored .aaa/ directory must survive).\n` +
      `This is deliberate: the changes were rejected by review and must not leak into the next ` +
      `cycle. Do not try to preserve, stash, or salvage any of it.\n` +
      `Then confirm with \`git status --porcelain\` that nothing tracked remains modified, and ` +
      `report the HEAD sha you reset to.`,
      { label: `revert:${i}`, phase: 'Implement', model: 'opus', effort: 'high' })
    log(`${tag}: NOT accepted after 3 attempts - working tree reverted to HEAD`)
  }
  cycles.push({
    cycle: i, verdict: review.verdict, confidence: review.confidence,
    first_impression: review.first_impression,
    attacked: review_target.giveaway_title, giveaways: all,
    attempts: tries, accepted, gate_summary: gate && (gate.summary || gate.feedback),
  })
}

await flushLedger(N)   // cheap, and covers a run whose last cycle exited by a path that wrote nothing

// PERSIST THE DISCOVERY, IN THE REPO. The ledger lives in .aaa/, which is gitignored — so a run's
// entire output (32 findings and 7 owner decisions, on the run that motivated this) died with its
// worktree, and the only durable trace was whatever a human happened to copy out of the return
// value. This file already argued that decisions "are worth nothing if they stay in the return
// value" and then fixed only the PRINTING. Measured 2026-07-26: reconstructing one run's backlog
// by hand from ledger JSON plus gate output took a full pass and would not have survived a
// `git worktree remove`. A committed markdown file is the cheapest durable form.
if (backlog.size || decisions.length) {
  phase('Report')
  const rows = [...backlog.values()].map(b =>
    `- [${b.lens || 'lens?'}] ${b.title}\n      ${(b.detail || '').replace(/\n/g, ' ').slice(0, 700)}`).join('\n')
  await agent(
    `Write ${ROOT}/Backlog.md — the durable record of what this run FOUND and did not fix.\n\n` +
    ROOT_NOTE +
    `If the file already exists, MERGE: keep entries still open, mark anything now shipped as ` +
    `RESOLVED with its commit sha rather than deleting it (a decision and its outcome belong next ` +
    `to each other), and do not drop entries you cannot categorise.\n\n` +
    `OWNER DECISIONS — these lead the file. They need a human, not a fix, and they are the highest-` +
    `value thing a review produces:\n${decisions.map((d, n) => `${n + 1}. ${d}`).join('\n\n')}\n\n` +
    `OPEN FINDINGS (${backlog.size}):\n${rows}\n\n` +
    `SHIPPED THIS RUN: ${[...shipped].join(' | ') || '(none)'}\n\n` +
    `Group by what a reader would DO with each entry — owner decisions, sim/gameplay defects, ` +
    `teaching honesty, UI polish, test and tooling debt, process — not by which cycle found them.\n` +
    `COPY THE MEASURED NUMBERS VERBATIM. They are the whole reason these are actionable, and a ` +
    `paraphrased measurement is just an opinion. Where an entry was reasoned about rather than ` +
    `measured, say so in the entry.\n` +
    `Open with the standing warning: read severities sceptically and enumerate the predicate's ` +
    `call sites before designing a fix — reports here have named a real smell and missed the ` +
    `consequence by a whole class more than once.\n` +
    `Then commit ONLY Backlog.md (conventional style, emoji, a body that says what moved). Do not ` +
    `touch anything else and do not push.`,
    { label: 'backlog-report', phase: 'Report', model: 'opus', effort: 'high' })
  log(`Backlog.md written: ${backlog.size} open finding(s), ${decisions.length} owner decision(s)`)
}

// The backlog is part of the deliverable, not bookkeeping: these are real, confirmed-visible
// tells the run SAW and consciously did not spend its budget on. Returning them means a run that
// fixes 3 things still hands back the other 7 instead of quietly implying the game is now clean.
return { cycles, backlog: [...backlog.values()], shipped: [...shipped], dismissed: [...dismissed], decisions }
