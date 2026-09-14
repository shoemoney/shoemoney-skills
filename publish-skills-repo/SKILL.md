---
name: publish-skills-repo
description: Curate skills out of a private Claude Code skill library (~/.claude/skills, ~/.agents/skills) into a public repo without leaking, breaking, or misdescribing them. Use WHENEVER the user asks to "put my skills in a repo", "open-source my skills", "add skill X to the repo", "which skills did I write", "which skills should I open-source", or wants to rename an installed skill. Covers finding provenance mechanically (symlink target, git origin, first-commit) instead of asking a model to guess, the hardcoded self-path trap that breaks a renamed skill's scripts, the scrubbed-public-copy-vs-installed-original sync direction, and grepping a subagent's brief against the scripts before it becomes README text. Measured 2026-09-10/11 while building a 19-skill public vault.
---

# publish-skills-repo

A skill library is half yours and half installed packs, the skills hardcode where they live, and
the moment you scrub a public copy you have two versions of one file. Each of those bit once.

## 1. Provenance is a lookup, not a judgement call

**The surprise:** a Haiku agent asked to sort 325 skills into "authored / harvested lesson /
third-party" filed `get-skillz`, `updatedocs`, `refresh-resume` and `im5` as third-party and
returned a hundred "uncertain" entries. A mechanical pass took one shell loop and was right.

**The keys that actually decide it, in order:**

```bash
cd ~/.claude/skills
for d in */; do n=${d%/}
  t=$(readlink "$n" 2>/dev/null || echo REALDIR)        # where it really lives
  echo "$n | ${t/#$HOME\//} | $(stat -f %Sm -t %F "$n/SKILL.md")"
done
```

- Symlink target under a vendored pack dir (`anthropics-skills/`, `claude-office-skills/`,
  `creative-writing-skills/`, `.codex/skills`, `.config/opencode/skills`) → third-party.
- Target in `~/.agents/skills` or `~/Projects/<own repo>` or a real dir → probably yours.
- `cat ~/.agents/.gitmodules` → submodules are third-party by definition.
- `git -C ~/.agents log --diff-filter=A --format=%s -- skills/<n> | tail -1` → if the only
  commit is a bulk "put N skills under version control", provenance is unknown. **Batches of
  skills sharing one mtime date with no author marker are installed packs, not authored.**
  (2026-05-18 and 2026-07-12 here.) Label them "unverified", don't guess either way.
- Name prefixes settle whole families: `tob-*` (Trail of Bits), `composio-*`, `coinbase-*`.

Only after the mechanical pass, hand an LLM the *residue* with the description text. And treat
harvested lesson skills (`x-fakes-y`, `-traps`, `-is-not-`, "measured 2026-…") as authored: the
user's sessions wrote them from the user's outages.

**Portability score** for the open-source shortlist is one grep per skill:

```bash
grep -rhoE '192\.168\.[0-9.]+|/Users/[a-z]+|<yourdomain>\.|/mnt/|Projects/[a-z0-9-]+' "$n" | wc -l
```

Zero means ship as-is. Anything else needs a scrub or stays private.

## 2. Renaming a skill breaks its own scripts

**The tell:** the skill still shows in `/` autocomplete under the new name, `SKILL.md` looks
fine, and the Workflow script fails at runtime because it defaulted to a path that no longer
exists. Skills with scripts hardcode their install path as defaults:

```js
const SCRIPT = A.script || '~/.claude/skills/<old-name>/scripts/review.py'
```

and tests do `os.path.expanduser("~/.claude/skills/<old-name>/scripts/verify.py")`.

**Fix, every time you rename:**

```bash
grep -rn '<old-name>' <skill-dir>          # SKILL.md, scripts/*, tests, workflow names
sed -i '' 's#<old-name>#<new-name>#g' $(grep -rl '<old-name>' <skill-dir>)
sed -n '/^description/,/^---/p' <skill-dir>/SKILL.md   # READ IT: a blanket sed can produce
                                                        # a duplicated trigger phrase when two
                                                        # spellings collapse to one
```

**The same self-path inside a TEST is worse: the test passes for the wrong reason.** Confirmed
2026-09-12: `test_verify_shots_freshness.py` in the public vault ran its subject via
`os.path.expanduser("~/.claude/skills/tripple-a-gamedev/scripts/verify_shots.py")`. Locally the
installed copy is there, so the vault's test was green while exercising a file outside the repo;
on CI (`ubuntu-latest`) it failed with *can't open file '/home/runner/.claude/skills/...'*. Tell:
a test in a repo that is green locally, red in CI with "No such file" on a path under `$HOME`,
or a test that stays green after you break the repo copy. Fix: resolve the subject beside the
test, `os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_shots.py")`. Check:
`mv` the repo copy away, run the test, it must FAIL; put it back. Runtime *defaults* in a
Workflow script (`A.script || '~/.claude/skills/<name>/scripts/x.py'`) can stay — the installer
symlinks to exactly that path and the caller can override — but a test may never resolve its
subject through the install path.

Also fix the install: the `~/.claude/skills/<name>` entry is usually a symlink to
`~/.agents/skills/<name>`, so `mv` the target, `rm` the old link, `ln -s` the new one. The
frontmatter `name:` must equal the folder name or the skill vanishes from the list.

## 3. A scrubbed public copy and the installed original are two files now

You removed a LAN address and an absolute home path from the repo copy and kept the installed
original intact, because the skill has to keep working locally. Correct. **The next `rsync` or
`cp -R` from the installed copy puts the leak back**, and the commit will look like a routine
update.

- Record which direction is canonical in project memory: *edit in the repo, never overwrite it
  from the installed copy* (or the reverse, but pick one).
- Before every commit to the public repo, run the portability grep over the whole tree. It must
  return nothing. This is the same one-grep gate `going-public-audit` uses; run it on updates,
  not just the first flip.
- Prefer placeholders that still document the shape: `<deploy-host>:<deploy-path>/app`,
  `192.168.x.x`, `~/Projects/tool` over deleting the line. The reader needs to know a host is
  expected there.
- Strip `__pycache__/` and `.pyc` on copy (`rsync -aL --exclude __pycache__`). They carry
  absolute paths and are noise in a public tree.

## 4. A subagent's brief is a draft, not a source

Haiku briefs read each `SKILL.md` and its scripts and came back confident and mostly right.
Two of seven invented a mechanism: an env var (`GEMINI_API_KEY`) that no script reads, and
"Opus codes the fix" when the Workflow script assigns `model: 'sonnet'` to that stage. A README
that says either becomes the doc a future builder copies.

Before a brief becomes README text, grep every mechanism claim against the code:

```bash
grep -noE "model: *'[a-z]+'" scripts/*.js | sort | uniq -c     # who does which stage
grep -hoE 'process\.env\.[A-Z_]+|environ\[?"[A-Z_]+|[A-Z_]+_API_KEY' scripts/* | sort -u
```

Behaviour claims ("it verifies screenshots are fresh") age well. Mechanism claims ("reads
`GEMINI_API_KEY`", "Opus codes it") are exactly what drifts and exactly what a brief invents.
See `updatedocs` for the general rule and `agent-invents-the-citation` for the pattern.

## 5. Shape of the public repo that worked

- One folder per skill, folder name == frontmatter `name`. Nothing else at the root but README,
  `.gitignore` (`.remember/`, `__pycache__/`, `*.pyc`, `.DS_Store`), LICENSE.
- Install section offers: symlink from the clone (so `git pull` updates in place), copy one
  skill project-local, and the `~/.agents/skills` convention for other agent CLIs.
- README per skill: what it does, exact triggers, scripts table with CLI, what it leaves behind,
  gotchas in a `<details>`. Plus a "what's inside" subtree section near the top, because a
  skill like `refresh-resume` is three artifacts and a reader can't see that from a one-liner.
- Dual push: `git remote set-url --add --push origin <github>` alongside the self-hosted remote,
  so one `git push origin main` lands on both.
- Dependencies on *other* skills are a real install step (`tripple-a-gamedev` imports
  `or_call.py` from `shoop`). Name them in Prerequisites or the clone doesn't run.
- **A skill that points at a file OUTSIDE its own folder ships a broken promise.** Confirmed
  2026-09-12: `scopecreep` SKILL.md and the README both advertised a `scopecreep-check.sh` Stop
  hook that lived only in `~/.claude/hooks/`, so a clone got the docs and not the hook. Tell:
  the README says "optional hook" or "script" and `ls <skill>/` shows one file. Fix: vendor it
  into `<skill>/hooks/` or `<skill>/scripts/`, rewrite the SKILL.md path to the shipped copy,
  add the `settings.json` wiring snippet, and leave the installed original alone. Check, run
  before every publish and read every hit:

  ```bash
  grep -rnoE '~/\.claude/(hooks|skills)/[A-Za-z0-9_./-]+|[A-Za-z0-9_-]+\.(sh|py|js)\b' */SKILL.md \
    | while IFS=: read f _ ref; do
        d=$(dirname "$f"); b=$(basename "$ref")
        find "$d" -name "$b" | grep -q . || echo "DANGLING $f -> $ref"
      done
  ```
  Anything printed is a file the docs name and the repo does not contain (external-skill
  dependencies like `or_call.py` will show up too; those belong in Prerequisites).
