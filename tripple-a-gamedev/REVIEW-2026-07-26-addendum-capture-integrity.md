# tripple-a-gamedev — addendum: two holes in the capture gate

**Separate file on purpose.** At 18:08 on 2026-07-26 a sibling session was actively rewriting
`SKILL.md` (58,314 → 68,022 B) and had added `scripts/check_doc_drift.sh` — i.e. it was applying
`REVIEW-2026-07-26.md`. That review's own finding **M** says not to mutate skill prose while a
sibling edits it, so nothing here was written into `SKILL.md`. Findings A and B below are drafted
for whoever merges next.

Verified absent from `SKILL.md` **after** the sibling's edits:
`grep -ci` → `mtime` 0, `timestamp` 0, `freshness` 0, `placeholder` 0, `cwd` 0,
`error channel` 0, `resource load` 0. Neither finding duplicates that pass.

Both come from a non-Godot session (a static site with a photo gallery + YouTube modals). That
is the point: each is a property of *screenshot-judged review*, not of Godot, and each survives
every check the loop currently runs.

---

## A. A stale shot is a perfectly good image — APPLIED to `verify_shots.py`

**Status: code shipped + regression test.** Prose for `SKILL.md` still to merge.

`verify_shots.py` had four checks: exists / distinct / colourful / moving. Every one of them
asks *"is this a real frame of a real game?"* — and last cycle's PNGs answer yes to all four.
Nothing asked *"is this frame from THIS run?"*

The failure needs no exotic bug, just a path divergence: **a capture tool resolves a relative
output path against ITS OWN cwd, not the agent's.** Hit twice in one session — a screenshot tool
reported writing `./site.jpeg` and `./vids.jpeg`; neither existed at that path relative to the
agent's cwd. The second time was sharper and is the one that matters here: the agent had entered
a **worktree** and the tool had not, so the file landed in the original checkout. `wf_aaa.js`
runs agents with `isolation:'worktree'`, which makes those two cwds diverge *by construction*.

Consequence if the expected dir is non-empty: the reviewer receives the **previous** build's
shots, they pass all four checks, and it returns a confident verdict about a build that no
longer exists — including "fixed" verdicts on work it never saw. That is failure mode 1 wearing
clean clothes: `SAVED` proved nothing, and neither does "the PNGs are fine."

**Shipped:**
- `--max-age SECONDS` — fail any shot older than the capture-run start. Error text names the
  real cause (capture tool cwd / worktree divergence) rather than "shots too old".
- `MAX_SPREAD = 3600` — always-on, needs **no reference clock**: if oldest−newest exceeds an
  hour the directory mixes runs. This is the half that works even when the caller forgets.
- `age_s` reported per shot and in the OK line, so age is visible before it is ever fatal.
- `scripts/test_verify_shots_freshness.py` — asserts day-old shots **pass checks 1-4** (proving
  the hole was real) and fail only on check 5, plus the zero-config mixed-vintage case.

**Still to do:** have `wf_aaa.js` pass `--max-age` with the capture start time, and clear
`SHOT_DIR` before capture. Until then only `MAX_SPREAD` is protecting the loop, and it cannot
catch a *uniformly* stale directory.

**Draft, appended to failure mode 1:**
> A fifth check catches what the other four structurally cannot: **a stale shot is a perfectly
> good image.** Checks 1-4 all ask "is this a real frame"; last cycle's PNGs pass every one. The
> usual cause is not a bug but a path divergence — a capture tool resolves a relative output path
> against its own cwd, not the agent's, and `isolation:'worktree'` makes those differ by
> construction. Observed twice in one session outside this repo. Gate on mtime (`--max-age`
> against the capture start) and clear `SHOT_DIR` first: a reviewer handed last build's frames
> returns confident verdicts — including "fixed" — about a build that never rendered.

---

## B. A graceful fallback is invisible to a screenshot reviewer — NOT APPLIED

This one has no code fix yet because the right gate depends on the engine's error channel.

The loop's entire thesis is that a multimodal reviewer judges production value **from the
pixels**. That thesis has a blind spot: *an asset that fails to load but degrades prettily is
indistinguishable from an asset that loaded.*

Observed live. A gallery of nine images where **every single one 404'd**. An `onerror` handler
substituted a tasteful placeholder — correct aspect ratio, on-palette border, centred label. The
resulting page looks *designed*. It would pass all five `verify_shots.py` checks: real, distinct,
colourful, and (in a game) moving. A consumer-persona reviewer looking at that screenshot would
praise the "elegant minimalist gallery" and never report the actual defect, which is that the
page is 100% broken. The only channel that revealed it was the **console error log — a channel
entirely outside the image.**

Note the asymmetry that makes this dangerous: Godot's own missing-texture magenta is *loud*, so
it gets caught immediately and nobody worries about it. The failure that survives is the
**tasteful** fallback — a default material, a `load()` returning null with a substituted stand-in,
a silent `AudioStreamPlayer`, a placeholder mesh. The better a project's fallback hygiene, the
more invisible its missing assets are to this loop. Polish hides breakage from a polish reviewer.

**Draft, as a new bullet under Gotchas (or as failure mode 6):**
> **A graceful fallback defeats a screenshot-only gate.** The reviewer judges pixels, so an asset
> that fails to load but degrades *prettily* reads as a deliberate art choice. Godot's magenta
> missing-texture is loud and gets caught; a default material, a null `load()` with a substituted
> stand-in, or a silent audio stream does not — and the better the fallback, the more invisible
> the breakage. Observed live outside this repo: nine images, every one 404, rendered as
> on-palette placeholders; the page looked *designed* and only the console log disagreed.
> So capture the engine's **error channel** alongside the frames (stdout/stderr for
> `ERROR:`/`Failed to load`/`res://… not found`/null-instance warnings), attach it to the
> dossier, and gate on it. Allowlist the known-benign ones — a gate that fails on *any* line is
> noise and will be switched off. In the observed case 11 console errors were all expected
> fallbacks, and telling expected from novel is the whole job.

---

## C. Method note — the cheap check that found both

Both were found the same way, and it is worth stating as a rule: **after every capture, read the
error channel and classify each line as expected or novel — before looking at the picture.** The
picture is the thing designed to look right. Finding A was a `Read` that failed on a path a tool
had just reported; finding B was 11 console 404s behind a page that rendered beautifully. Neither
was visible in the artifact the loop is built to examine.
