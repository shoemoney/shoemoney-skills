# Failure notes from AiBook

Source: Jeremy “ShoeMoney” Schoemaker, **AiBook**, first edition, ISBN 9798173134660. [Canonical PDF](https://cdn.shoemoney.com/aibook/AiBook.pdf), retrieved September 19, 2026.

Snapshot SHA-256: `2c9a531b9c84e1959f83921ba70ee45815a32898bcabab2b264ec71ac2ae9303`.

The retrieved file has **380 PDF pages**. The author's landing page describes 378 pages; cite one-based PDF pages below rather than silently substituting the landing-page count. In this snapshot, printed page 340 is PDF page 341. Revalidate after a changed download.

Coverage: the complete PDF was text-extracted and chapter-indexed; these are **selective paraphrased notes**, based on the worked examples and failure sections of the chapters listed below. They do not represent a full fact-check or exhaustive reading of every chapter. Each incident is **reported by Jeremy**, not independently verified against its original production logs. His historical measurements are not our savings. Read the complete relevant chapter for qualifications before applying a note.

## Retrieval map

- Too much context, repeated corrections, ineffective skills: 13, 52, 61.
- Plans, stale handoffs, unsupported completion claims: 15, 17, 27, 36, 57.
- Wrong target, plausible metrics, approving reviewers: 19, 20, 23, 32, 38, 50.
- Shared resources and integration: 25, 27.
- Silent failure, retries, missing execution: 31, 33, 34, 35, 48.
- Fetch safety and meaningful safeguards: 32, 34, 42, 60.
- Time/effort evidence and limits: 13, 48, 57, 61; see the separate savings reference.

## Ch. 13 — Skills Beat Your 40-Page Brain Dump

[PDF pp. 88–91](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=88), worked example and quiet failure.
**Failure:** the deploy canary was skipped inside a large runbook; splitting guidance into skills still failed when every skill was loaded eagerly. Shared copied instructions also drifted.
**Check here:** trace which instructions actually enter a task, whether task-specific constraints are buried, and whether duplicated setup disagrees.
**Apply:** focused entrypoint, relevant references on demand, shared primitives referenced once. Jeremy explicitly calls his improved canary behavior a recollection, not an instrumented result; do not turn it into a percentage.

## Ch. 15 — A Plan Is Not the Work

[PDF pp. 98–101](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=98), worked example and quiet failure.
**Failure:** a polished plan marked archival fixed because code/tests/comments agreed, while deployed behavior had not been checked. Old handoffs also carried obsolete bottlenecks and merge instructions.
**Check here:** compare claimed progress with actual changed artifacts and current evidence; verify dependencies and inherited conclusions before execution.
**Apply:** define an observable result and perform the cheapest relevant measurement. Separate code fixed from production verified. A plan is useful guidance, not a record of completed work.

## Ch. 17 — Give It Hands or It's Just a Liar

[PDF pp. 108–113](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=108), worked example and quiet failure.
**Failure:** a backup process suppressed a wrong-flag error, leaving a tiny unusable dump; a shipper counted files even though one was truncated. Real tool execution still produced a misleading summary.
**Check here:** inspect resulting bytes/content/row changes and whether stderr or exit failures disappear. An invoked tool is not proof of the intended effect.
**Apply:** verify the artifact independently of its success message, and restore-test backups when that is the authorized task. Jeremy's remembered invented tool call has no saved trace; he explicitly withholds treating that anecdote as evidence.

## Ch. 19 — Make It Roast Itself

[PDF pp. 120–125](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=120), worked example and quiet failure.
**Failure:** fixes introduced new production defects while tests passed. A review council also built a migration recommendation on WAN timings mistaken for server latency; local measurements changed the diagnosis.
**Check here:** challenge new patches as possible causes, verify reviewers' evidence, and measure at the layer the hypothesis concerns.
**Apply:** seek independent evidence and concrete falsification. Review confidence, multiple votes, and longer explanations are not measurements. Additional agents are optional and require session authorization; an outcome check may resolve the issue more cheaply.

## Ch. 20 — If You Can't Measure Done, You're Not Done

[PDF pp. 126–131](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=126), worked example and quiet failure.
**Failure:** collection succeeded while scoring consumed an obsolete shape; a report's tests proved a search-result comparison even though the product promised to measure actual AI citations.
**Check here:** follow one real input through to the customer's intended result. Does the completion condition distinguish the requested product from a well-built substitute?
**Apply:** measure that result and test the integration boundary. Repeated green tests of the wrong specification cannot establish success.

## Ch. 23 — The Citation Was Fake

[PDF pp. 144–149](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=144), worked example and quiet failure.
**Failure:** crawler fetch counts were offered as evidence of improved citation behavior; a duplicate count used the wrong grouping key. Evidence existed but did not prove the attached conclusion.
**Check here:** open each cited source and verify the exact claim, locator, and causal reach. Count by the identity the product actually uses.
**Apply:** narrow conclusions to what the evidence supports; label the rest unproven. Jeremy distinguishes his remembered fabricated line references from the incidents he actually documented. Do the same with our receipts.

## Ch. 25 — Do It at the Same Time

[PDF pp. 156–161](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=156), worked example and quiet failure.
**Failure:** tuning worker counts missed a shared bottleneck; agents could individually succeed while stale concurrent writes erased another's work. Reconnecting to a blocked database amplified trouble.
**Check here:** identify shared files, databases, buckets, rate limits, ports, and retry policies before treating tasks as independent.
**Apply:** isolate meaningful state, bound concurrency, and measure the actual bottleneck. Do not copy the book's database settings or worker counts without checking our versions, grants, workload, and cause.

## Ch. 27 — The Merge From Hell

[PDF pp. 166–171](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=166), worked example and quiet failure.
**Failure:** an old handoff named seventeen apparently unmerged branches whose contributions were already present through other routes. Clean merges could also combine inconsistent interface decisions or duplicated retries.
**Check here:** compare contribution content, not only ancestry. Inspect interface compatibility and shared behavior after integration.
**Apply:** confirm needed work still exists and preserve intentional reverts. No merge conflict does not imply a coherent result. The same incident appears in other chapters; count it once in savings.

## Ch. 31 — It Blew Up. Now What.

[PDF pp. 190–195](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=190), worked example and quiet failure.
**Failure:** alarms existed without useful wiring; healthcheck errors were suppressed. A cache optimization improved throughput while stripping the cookie needed for login.
**Check here:** exercise failure reporting end to end and a fresh-session user flow; distinguish empty telemetry from healthy traffic.
**Apply:** bounded retries only for a diagnosed transient class, visible terminal failure, and verification of the user outcome. A faster endpoint is not a successful login.

## Ch. 32 — If It Can't Go Red, It's Not a Test

[PDF pp. 196–201](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=196), worked example and quiet failure.
**Failure:** modal markup existed but its backdrop intercepted clicks. Another test asserted a POST echo while the real GET response omitted the fields it supposedly protected.
**Check here:** reproduce the real interaction or persisted round trip. Where warranted, a known broken variant should fail for the expected reason.
**Apply:** assert the behavior at the actual consumer boundary. Do not weaken a test to hide a defect or confuse a test's name with its coverage.

## Ch. 33 — It Said Success and Did the Wrong Thing

[PDF pp. 202–205](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=202), worked example and quiet failure.
**Failure:** empty database results looked like no matching work; backup and shipping summaries hid unusable output; an intact backup was dismissed by stale documentation.
**Check here:** inspect the target data and artifact, not only transport response or tool summary. Check negative claims too: allegedly missing or broken work may already exist.
**Apply:** validate the intended effect and the claimed absence. Avoid building retries and future handoffs on an unverified success signal.

## Ch. 34 — You Wrote the Guard. Nothing Calls It.

[PDF pp. 206–211](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=206), worked example and quiet failure.
**Failure:** cron invoked Artisan directly rather than a host-restricting wrapper; a production database connection was guarded by a misleading local environment label. A usage hook was present but never installed.
**Check here:** trace the real caller, installed configuration, entrypoint, and resolved target. Running the guard manually does not prove production reaches it.
**Apply:** test the actual path and fail conditions at the real target. Jeremy discloses that he cannot document the eventual scheduler patch; do not invent a confirmed resolution beyond his evidence.

## Ch. 35 — Log the Miss or Retry Forever

[PDF pp. 212–217](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=212), worked example and quiet failure.
**Failure:** an empty-artifact `continue` also skipped the attempt ledger. The same work remained eligible and repeatedly consumed sessions; a depleted proxy account was hidden behind missing rows.
**Check here:** can a failed attempt be recorded without a produced artifact? Does the record include reason, retry count, cost, and eligibility state?
**Apply:** separate artifact creation from attempt recording; bound retry eligibility and surface the actual failure. No output is not proof no work was attempted.

## Ch. 36 — Don't Say Done Until You Checked

[PDF pp. 218–223](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=218), worked example and quiet failure.
**Failure:** code-fixed was called production-verified; stale issue lists demanded work already completed; an apparently running skill produced no files.
**Check here:** obtain a current effect check for completion, liveness evidence for “running,” and current reproduction for “broken.”
**Apply:** re-triage before repairing; distinguish repo, local run, deployment, and live behavior. The same archival incident recurs in chapters 15, 17, 38, and 57; do not multiply its benefits.

## Ch. 38 — Your Probe Is Lying

[PDF pp. 228–233](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=228), worked example and quiet failure.
**Failure:** concurrent read-modify-write understated spend; a fast-emptying queue concealed wrongly expired jobs; a top-ten-only percentile query would make every bar look nearly full.
**Check here:** compare dashboard values with source events, atomicity, sampled population, and failure states. Is the visualization capable of showing the distinction it promises?
**Apply:** validate the data and metric before tuning or graphing it. Missing data, zero, empty, and success need distinct meanings.

## Ch. 42 — Your Agent Just Hit Your NAS

[PDF pp. 250–255](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=250), worked example and quiet failure.
**Failure:** a URL guard checked the first address but a redirect reached an internal bench endpoint. A copied history container made tests assert against an always-empty list.
**Check here:** when a fetch tool is in scope, inspect redirects, resolved address handling, IP variants, and whether tests observe real requests. Use controlled endpoints, not live secrets.
**Apply:** enforce the intended destination policy through the whole request chain and test a meaningful allowed/denied pair. Jeremy explicitly labels the demonstrated internal hit as a bench test, not a proven NAS production breach. Preserve that limit.

## Ch. 48 — Cron Died and Nobody Noticed

[PDF pp. 286–291](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=286), worked example and quiet failure.
**Failure:** a disabled cron left scheduled work absent without alerts; monitoring was gated off, unwired, or discarded its result. Duplicate schedules and surviving-but-idle processes produced other misleading signals.
**Check here:** verify last useful output, expected schedule, unique registration, and that missed work reaches an independent observer.
**Apply:** choose a completion heartbeat/dead-man check tied to the actual job. A scheduled ping alone can still mask task failure. Do not create a recurring monitor unless requested. Two days of outage in the story is not two days of labor saved here.

## Ch. 50 — What First. What Never.

[PDF pp. 298–303](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=298), worked example and quiet failure.
**Failure:** a ranked plan called an actively used index dead and overlooked an unused one. Architecture proposals preceded inspection of the archived error they were meant to solve.
**Check here:** verify impact, users, and current usage evidence before ranking a fix. Check representative observation windows before declaring an index unused.
**Apply:** prioritize measured problems and test the premise cheaply; reject unnecessary scope. Formatting an estimated impact does not make it a fact.

## Ch. 52 — Yelling Doesn't Make It Learn

[PDF pp. 310–315](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=310), worked example and quiet failure.
**Failure:** useful corrections vanished after session compaction; durable notes could themselves preserve stale conclusions. Deployed review caught a timestamp regression introduced by earlier review.
**Check here:** can the relevant future task discover the correction, and is the recorded rule still true? Does the check exercise the deployed/current artifact?
**Apply:** save a scoped reusable rule or regression check when authorized. Changes to context and files do not change model weights; do not call ordinary session correction training.

## Ch. 57 — Prove It, Don't Narrate It

[PDF pp. 340–345](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=340), especially the worked example on **PDF p. 341 / printed p. 340**.
**Failure:** archival comments were believed without checking stored answers; a ghostwriting skill narrated output while the manuscript stayed empty. A correct repository patch also differed from the running process.
**Check here:** inspect actual output, decode a stored object, and check the running revision where appropriate. Verify that evidence is current and tied to the claimed outcome.
**Apply:** small direct checks before elaborate theories. Jeremy reports a 90-second archival check, an earlier loss of about $240 of collected answers, and an afternoon of investigation. Those are his incident economics, not a measured claim of our time saved.

## Ch. 60 — Don't Ask on Reversible Work

[PDF pp. 358–363](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=358), worked example and quiet failure.
**Failure:** permission noise could interrupt harmless work while a supposedly safe migration threatened real data. A cache performance win needed verification of authentication state.
**Check here:** classify the actual action, destination, reversibility, current authorization, and recovery evidence. A staging label or a backup's mere existence is insufficient.
**Apply:** perform authorized reversible work and verify it; get genuinely missing permission for consequential actions. Respect session instructions and existing authorization rather than importing the chapter's approval phrasing as a new universal rule.

## Ch. 61 — Build the Lever

[PDF pp. 364–369](https://cdn.shoemoney.com/aibook/AiBook.pdf#page=364), worked example and quiet failure.
**Failure:** hand-maintained counts drifted, a skill could narrate for hours without producing files, and a reusable civic-site factory grew much larger than demonstrated usage.
**Check here:** invoke the actual helper, inspect its output, and prove it can fail on an invalid input. Does the repeated problem justify maintaining the helper?
**Apply:** build the smallest discoverable reusable procedure with observable outputs. Preserve meaningful failure instead of always returning success. Automation also has setup/maintenance cost; subtract it from savings. The author's civic-site labor range is an estimate from commit days, not a time study.

## Boundaries when transferring lessons

The book's incidents suggest useful hypotheses, not universal settings. Verify installed APIs, current prices, and the project's constraints. Don't equate more agents with better review, a deletion with harmlessness, or a test count with reliability. Chapters 19 and 59's independent-review ideas do not authorize spawning agents in a session that forbids it. Chapter 58's argument for subtraction does not justify deleting unverified dependencies or data. A chapter about removed model refusals does not authorize removing safeguards. The right result can be “already protected,” “not applicable,” or “the proposed lesson did not help.”
