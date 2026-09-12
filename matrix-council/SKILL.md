---
name: matrix-council
description: Convene a seven-member council of software engineers and computer scientists — six frontier models debating via OpenRouter, chaired by Fable ("Neo") inside this harness — to settle a hard technical question with evidence rather than opinion. They label every claim VERIFIED / CONTESTED / THEORY / UNMEASURED, may argue a theory but must supply the test that would settle it, dispatch Haiku research agents ("Operators") for anything they lack first-hand, and explicitly retract when shown proof they had not considered. Produces an HTML meeting record in council_meetings/ and a blog post. Use when the user says "/matrix-council", "convene the council", "ask the council", "matrix council", "council of SWE", or wants a hard architecture/debugging/design question settled by adversarial multi-model review rather than one model's guess. Also reach for it when a decision keeps getting relitigated, when a plausible-sounding theory needs a test rather than another argument, or when the cost of being confidently wrong is high.
---

# The Matrix Council

Seven computer scientists. Six seated, one in the chair.

They exist because a single model — including this one — produces confident theory and calls it
knowledge. The council's entire purpose is to make that expensive: every claim is labelled, every
theory arrives with its falsifying test, and every member is read by six others who are rewarded
for finding the hole.

**The one rule that outranks the rest: a theory is never the answer until it is reliably
reproducible and proven.**

## The crew

| Nickname | Model | Temperament |
|---|---|---|
| **Neo** ⭐ | Fable, **in this harness** | **Chairman.** Questions the frame, verifies claims against the actual repo/DB, rules on whether consensus is real |
| **Morpheus** | `openai/gpt-5.6-luna-pro` | Systems thinker — what does this claim imply for the whole? |
| **Trinity** | `google/gemini-3.6-flash` | Fast and exact — reaches for the number, the measurement, the citation |
| **Mouse** | `x-ai/grok-4.5` | Irreverent — attacks the assumption everyone is treating as furniture |
| **Tank** | `deepseek/deepseek-v4-flash` | Operator — mechanism and implementation detail, what the code actually does |
| **Seraph** | `moonshotai/kimi-k3` | The verifier — "I protect that which matters most." Trusts nothing untested |
| **Niobe** | `qwen/qwen3.8-max` | Pragmatic captain — cost, risk, reversibility, what we do Monday |
| **Operators** | Haiku subagents | Dispatched on demand to research what the council lacks first-hand |

**Neo chairs, does not hold a seat, and decides all ties.** A chair who is also a seat cannot
referee its own claim. More importantly, Neo is the only member with *tools* — it can read the repo,
query the database, open the stored artifact and settle a dispute the others can only argue about.
That asymmetry is the design, not an accident.

### The chair's casting vote

When the seated members deadlock, **Neo rules and the ruling stands.** But the gavel comes with
three obligations, because an unchecked casting vote is just one model's opinion wearing a robe:

1. **A tie is broken with evidence, not preference.** Before ruling, the chair must produce
   something the seated members could not: run the command, open the artifact, query the table. The
   ruling cites what it found. *"I find Trinity more persuasive"* is not a ruling.
2. **If the chair cannot break the tie with evidence, it must not break it at all.** The correct
   ruling is then **productive deadlock** — name the single experiment that separates the positions
   and stop. A deadlock reduced to one experiment is a better outcome than a coin-flip dressed as
   authority.
3. **The ruling is recorded with its own status label**, like everyone else's claims. A chair's
   decision made on partial evidence is `THEORY` and says so, and the losing position stays in the
   record with the test that would revive it.

The chair may also **overrule unanimity.** Six members agreeing is not proof — if the chair opens
the artifact and finds all six were reasoning over a label rather than the thing itself, the chair
says so and the round continues. *(That exact failure happened on 2026-08-08: three planners agreed
on a diagnosis for six hours; the answer was in an archived page none of them had opened.)*

**Known substitution, stated rather than hidden:** `gpt-5.6-sol` is not exposed on OpenRouter (Sol
appears to be a ChatGPT product routing tier; the API offers `luna` / `luna-pro`). Morpheus rides
`luna-pro`.

## Running it

### 1. Write the brief

A markdown file stating the question, the measured facts already in hand, and what is explicitly
unknown. **Include the artifacts** — file paths, error strings, table counts, log excerpts. The
council is only as good as its evidence, and a brief of pure narrative produces pure narrative back.

Save to `council_meetings/<slug>/brief.md`.

### 2. Round 1 — opening positions

```bash
python3 ~/.claude/skills/matrix-council/scripts/council.py \
  council_meetings/<slug>/brief.md \
  --round 1-opening --out-dir council_meetings/<slug>
```

Each seated member returns strict JSON: `position`, `claims[]` (each labelled, with evidence and —
for THEORY/CONTESTED — a test), `challenges[]`, `retractions[]`, `needs_research[]`,
`consensus_ready`, `dissent`.

`council.py --dry-run` (accepts the same flags) validates args, reads the brief, resolves the
member list, and prints the plan (`brief_chars`, `round`, `members`, `out_dir`, `prior`,
`research`, `max_tokens`) as JSON — no key lookup, no network call, no out-dir writes.

### 3. Dispatch the Operators

Read `round-1-opening.json` → `open_research`. For each distinct question, dispatch a **Haiku**
subagent via the Agent tool. Run them **in parallel, in one message**.

Every Operator prompt MUST say: *"All web search goes through `mcp__searxng__searxng_web_search` /
`mcp__searxng__web_url_read`. Never the generic WebSearch tool."* Require source URLs and
publication dates, and require them to separate VERIFIED from COMMUNITY-REPORTED from COULD NOT
DETERMINE.

Collect their findings into `council_meetings/<slug>/research.md`.

**Neo also researches by doing.** Where a question is answerable from the repo, the database or a
stored artifact, the chair answers it directly — with the command and its output. That evidence
outranks anything a model recalls, and it is the chair's main contribution.

### 4. Round 2 — cross-examination

```bash
python3 ~/.claude/skills/matrix-council/scripts/council.py \
  council_meetings/<slug>/brief.md --round 2-cross \
  --out-dir council_meetings/<slug> \
  --prior council_meetings/<slug>/round-1-opening.json \
  --research council_meetings/<slug>/research.md
```

Every member now sees every other position and is instructed to revise on new proof. **Watch
`retractions[]` — a round with zero retractions across six members usually means the brief was too
agreeable or the members are not reading each other.**

### 5. Chair's verification pass — the part that matters

Neo now does what no seated member can. For each **VERIFIED** claim that is load-bearing:

- **Check it.** Run the command. Open the file. Query the table. Read the stored artifact.
- **A claim's label is a claim.** A member asserting VERIFIED does not make it verified.
- Where the chair's check contradicts a member, that is a finding — feed it into the next round
  explicitly and require the member to retract or defend.

This is where councils earn their keep. It is also where they fail: a chair that accepts six
confident agreements without opening anything has run a poll, not a council.

### 6. Further rounds until consensus, or until the disagreement is *productive*

Re-run with `--prior` pointing at the latest round. **Reconvene whenever new evidence lands**,
including evidence from outside the council entirely — that is a feature, not a restart.

Stop when one of:
- **Consensus:** every reachable member sets `consensus_ready: true`, AND the chair has verified the
  load-bearing claims independently. Unanimity among models that never examined the artifact is six
  copies of one assumption.
- **Chair's ruling:** deadlocked, and Neo broke the tie with evidence the seats did not have — cited
  in the record, labelled with its status.
- **Productive deadlock:** the disagreement has been reduced to a *single named experiment* and the
  chair cannot settle it with evidence either. Legitimate, and often the better outcome — ship the
  experiment, not the argument.

Cap at ~5 rounds. If it has not converged, the question is underspecified — say so and return the
sharpest version of the question instead of a false verdict.

### 7. Publish

**HTML meeting record** → `council_meetings/<slug>/verdict.html`

Self-contained, no external assets except a CDN stylesheet, readable in a browser. Must contain:
- The question, and the verdict with its status label
- A **claims table**: claim / status / evidence / who
- **Retractions** — who changed position, on what evidence, supplied by whom. This is the most
  valuable section; a council that never moves is theatre
- **Dissent**, if any, with the test that would settle it
- **Still open** — everything UNMEASURED, with the experiment named
- Per-member positions
- Chair's verification: what was independently checked, and what that check found

**Blog post** → `blog/<YYYY-MM-DD>-<slug>.md`

Narrative for a human reader later. Keep the wrong turns in — the retracted theories are the
substance, not an embarrassment. Include real numbers with their sample sizes.

## Doctrine (enforced in the system prompt, restated for the chair)

- **We do not theorize and present it as knowledge.** Nothing is fact until reliably reproducible.
- **Label every claim.** VERIFIED / CONTESTED / THEORY / UNMEASURED. Unlabelled is a defect.
- **A theory without a test is an opinion.** Every THEORY carries the experiment that settles it.
- **Cite or downgrade.** No citation means it is not VERIFIED, however obvious it seems.
- **Research the gap, don't reason past it.** No first-hand proof → `needs_research`, not confidence.
- **Retracting on evidence is the highest-status act available.** Reward it in the write-up.
- **Attack the strongest version** of another member's position.
- **A window is not a rate.** Numbers carry their sample size and window.
- **"I have not seen evidence for X" ≠ "X is false."**

## Failure modes this skill exists to prevent

| Failure | Guard |
|---|---|
| Six models agreeing confidently and wrongly | Chair independently verifies load-bearing claims with tools |
| A plausible mechanism treated as a cause | THEORY label + mandatory test |
| Reasoning over a label instead of the artifact | Chair opens the artifact; Operators fetch sources |
| A good sample quoted as a general rate | Numbers carry sample and window |
| Consensus by exhaustion | Productive deadlock is a legal outcome; name the experiment |
| An API failure masquerading as agreement | Quorum of 4/6 reachable required before `unanimous` |

## Gotchas, measured

- **`max_tokens` is the #1 cause of a member "failing", and it lies about itself.** Reasoning
  models spend the entire budget on `reasoning` BEFORE emitting any `content`, so a starved member
  returns nothing and the error reads like an outage or a maxed account. Measured 2026-08-08
  against this exact doctrine prompt:

  | model | reasoning | content | needs |
  |---|---|---|---|
  | `qwen3.8-max` | 23,781 chars | 4,804 | ~12k tokens |
  | `kimi-k3` | 19,543 chars | 7,324 | ~12k tokens |

  At 4,000 both returned `finish_reason=length` with **zero** content. Default is now **12000**.
  Do not lower it to save money — a starved member is an absent member, and it will look like the
  account is out of credit when it is not.
- OpenRouter pads responses with whitespace before the JSON body; the script's `extract_json`
  handles fences, prose and padding.
- The key is read from `OPENROUTER_API_KEY` or `~/.config/openrouter/key`.
- A member that fails all retries is recorded with `_ok: false` and excluded from the consensus
  computation rather than killing the round.
- `kimi` and `muse` CLIs are installed locally if a member needs driving outside OpenRouter.

## Chair patterns, proven over four concurrent councils (2026-08-12/13, airank launch week)

- **Concurrent councils work.** Four ran in parallel (separate out-dirs, background council.py
  runs) with implementations interleaved; the chair's only real serialization point is prod
  surgery. Notifications drive the loop; never foreground-wait a round.
- **"Not consensus_ready until X lands" is a VERDICT, not a dissent** — when every seat's
  condition list names the same items, rule "converged in substance", implement the union, and
  record the ready=False votes as conditions honored. Waiting for a round 3 there burns ~8 min
  to learn nothing.
- **qwen (niobe) starves even at 12k max_tokens on heavy briefs** — twice returned _ok with
  EMPTY position/content. Treat an empty-content member as absent (like _ok:false); do not
  count it toward or against consensus, and do not re-run the round for it.
- **The chair's cheapest unfair advantage is a curl/localhost measurement** — in three separate
  councils, one command (localhost latency vs WAN; Set-Cookie presence; Kuma heartbeat) killed
  the round's dominant framing. Budget chair time for measurement BETWEEN rounds, not prose.
- **Implementation reviews are seats too:** the Opus review pass on a council-verdict workflow
  caught a 337k-row data-clobber BLOCKER (a column serving two masters) that the unanimous
  verdict text had sailed past. Verdict ≠ safe diff; keep the adversarial review stage even
  when the council was unanimous.
