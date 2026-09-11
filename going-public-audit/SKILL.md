---
name: going-public-audit
description: Use BEFORE flipping any private repo to public (or first-publishing a release/installer) — deep-scans the entire git history for leaked secrets with two independent methods, flags internal info-disclosure (LAN IPs, emails, infra paths) that's safe on a LAN but not on the open internet, checks public-readiness (LICENSE, go-module path), frames the public/private decision for the user, and verifies the published artifact actually installs anonymously. Trigger phrases — "make this repo public", "open-source this", "prep to go public", "publish a release", "is it safe to make X public", "scan history for secrets", "any secrets exposed".
---

# going-public-audit 🔓🛡️

Making a repo public is **outward-facing and hard to reverse** (caches, forks, the Go module proxy keep copies). Never flip it on your own — scan, surface, decide, then flip. Two scanners, because one missing a key is the whole game.

## Checklist (make a todo per item)

1. **Secrets in history — TWO independent methods.** A clean working tree means nothing; secrets hide in old commits.
   - Real scanner: `gitleaks detect --source . --redact -v` (install via brew/go if absent). Want "no leaks found".
   - Manual blob sweep — catches what gitleaks' rules miss, and proves YOUR specific token never landed:
     ```bash
     # exact-match your own known secret across every blob (report presence, NEVER echo the value)
     TOK=$(cat ~/.config/<svc>/token); n=0
     while read -r oid _; do git cat-file -p "$oid" 2>/dev/null | grep -qF "$TOK" && { echo "⚠️ in $oid"; n=$((n+1)); }; done \
       < <(git rev-list --all --objects); echo "token blob hits: $n"
     # high-signal patterns across all blobs
     git rev-list --all --objects | awk '{print $1}' | sort -u | while read -r o; do
       [ "$(git cat-file -t "$o" 2>/dev/null)" = blob ] || continue
       git cat-file -p "$o" 2>/dev/null | grep -anEi 'BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|xox[baprs]-|AIza[0-9A-Za-z_-]{35}|password\s*[:=]\s*["'"'"'][^"'"'"']{6,}' | sed "s|^|$o: |"
     done
     ```
   - Sensitive filenames ever committed: `git log --all --diff-filter=A --pretty=format: --name-only | sort -u | grep -iE '\.(env|pem|key|p12)$|id_rsa|credential|secret'` (a `secret`-named *package* is fine; a `.env` is not).
   - Committed-then-deleted ghosts: `git log --all --diff-filter=D --name-only --pretty=format: | sort -u`.

2. **Info-disclosure (not secrets, but world-readable).** Surface, don't silently scrub:
   - LAN/tailscale IPs + hostnames, internal filesystem paths, committer emails (`git log --all --format='%ae' | sort -u`).
   - These are usually fine (RFC-1918 isn't routable) — but it's the user's call. Scrubbing HISTORY needs `git filter-repo` + force-push to every remote (invalidates all SHAs) — only if they insist.

3. **Public-readiness.** `LICENSE` present? (no license = all-rights-reserved, kills adoption — **and check the README doesn't already declare a license you'd contradict**: AGPLv3/open-core ≠ MIT; ask before picking). Go module path on an internal host (`git.internal/...`) blocks `go install` from a public mirror — offer to rename to `github.com/owner/repo` (surgical: `s{host/owner/repo/}{github.com/owner/repo/}g` over `.go` with the **trailing slash** so it skips sibling repos like `repo-hub`/`repo-dist`).

4. **Decide WITH the user (AskUserQuestion).** Present the scan verdict, then the real choices: make-public vs a public **dist repo** (code stays private, only installers+binaries go public → `curl|sh` with no token) vs stay-private. License + module-path are separate questions. Licensing is hard-to-reverse — confirm.

5. **Flip + verify anonymously.** `gh repo edit owner/repo --visibility public --accept-visibility-change-consequences`. Then prove a stranger can use it: anon `git clone` works; `curl -fsSL <raw-or-release-url>` returns 200 (private → 404); `go install <module>/cmd/x@latest` builds (use `GOPROXY=direct` to skip proxy lag). For installers, run the real `curl|sh` in a **clean no-toolchain container** (`docker run --rm debian:stable-slim`) — and for ARM targets, download+run the binary INSIDE an `--platform linux/arm64` container (a bind-mounted `/tmp` is often `noexec`, which breaks the qemu exec).

## Extracting a public project OUT of a private one

A different job from flipping a repo: you keep the private original and publish a sanitized
descendant. The failure mode is the one people are most confident they've avoided.

**Deleting the file does not scrub it.** `git rm people.json` / renaming the repo / a fresh commit
that removes every phone number all leave the content in history — `git log -- people.json` finds
it, and so does anyone who clones. On one extraction the private roster had been touched by 3
commits; the working tree was spotless and the data was one `git show` away.

For an extraction, **do not carry the history at all.** There is no history worth preserving in a
private repo's early commits, and rewriting it (`filter-repo`, BFG) is strictly more work than not
having it:

```bash
cp -r private/ public/ && cd public/
rm -rf .git && git init && git add -A && git commit   # one clean commit, no ancestry
```

Then confirm you actually got a fresh tree, because a stale `.git` is invisible:

```bash
git log --oneline | wc -l          # expect 1
git log --all --oneline -- <the-file-you-meant-to-drop>   # expect empty
```

### Sanitization checklist beyond secrets

Grep the whole tree — code, docs, tests, config, **and comments** — for each of these. They are not
credentials, which is exactly why scanners miss them:

- **Real people.** Names, phone numbers, personas, addresses. A fixture file with a family in it is
  a doxx, not test data. Replace with reserved ranges (`+1555555xxxx`, `example.com`).
- **Your own name in docstrings.** `"""...JEREMY'S HOUSE (wick, 192.168.x.x)..."""` reads fine
  internally and is an infra map publicly.
- **Private dependencies.** A hard-coded path to an internal tool (`~/.internal/router.sh`) makes
  the project unrunnable for everyone else — and the *comment explaining what it does* can disclose
  more than the path. One comment cheerfully described an internal multi-account rotation strategy;
  the code was fine, the sentence was the leak.
- **Internal hostnames and buckets** in scripts you're about to ship (`cdn.mycompany.com`).
  If a helper needs infrastructure the reader doesn't own, cut it from v1 rather than porting it —
  a feature that requires an S3 bucket to work is a second setup story nobody asked for.
- **Hardcoded absolute paths** (`/Users/you/...`) in defaults and PATH strings.

Verify with one grep that must return nothing, and keep it as the release gate:

```bash
grep -rniE 'yourname|yourcompany\.(com|net)|192\.168|/Users/you|<real-area-code>' \
  --include='*.py' --include='*.md' --include='*.example' . | grep -v LICENSE
```

### Don't let the README overclaim

Sanitizing the code and leaving the prose aspirational is its own leak — of judgment. If a
README table says a control is enforced, open the code and confirm it is, before publishing. On one
pass an adversarial review found the enforcement table claimed four guarantees the code did not
provide; the fix was to mark the row **not enforced** and say so plainly. A public repo whose first
technical claim is falsifiable in five minutes costs more credibility than shipping later would.

## Boundaries
- Report secret presence, never the value. Quote info-disclosure findings to the user with file:line; let them choose scrub vs accept.
- Never `git filter-repo`/force-push or flip visibility without an explicit yes. The flip is the last step, after the scan is clean and the decisions are made.

## "It was never committed" is false comfort — the harness commits things you didn't

**Measured 2026-08-19.** A live OpenAI key (`sk-proj-…`, 164 chars) sat at
`storage/codex-ads-exp/.oai-key`. It was **untracked** (`??` in `git status`), **never `git add`ed**,
and `git log -- <path>` was empty. Every ordinary signal said "not in git."

It was in git. Two objects held it:

```
refs/t3/checkpoints/<session-id>/turn/0
refs/t3/checkpoints/<session-id>/turn/1
```

Claude Code's checkpoint feature snapshots the working tree — **including untracked files** — into
refs outside `refs/heads/`. Nobody ran `git add`. The blob existed anyway.

**The tell:** `git log --oneline --all -- <path>` returns commits whose subjects look like
`t3 checkpoint ref=refs/t3/checkpoints/…`, while plain `git log -- <path>` returns nothing. If you
only ran the second one, you concluded it was clean.

**Why the audit above still catches it:** `git rev-list --all` means *all refs under `refs/`*, not
just branches and tags — so the token scan is sound as written. **Do not "optimize" it to
`--branches --tags`.** That change would silently blind the whole audit to checkpoint refs.

**But deleting the file is NOT enough**, and neither is `gc`, because the refs keep the blob
reachable. Full scrub:

```bash
BLOB=$(git rev-parse <checkpoint-commit>:<path>)          # capture BEFORE deleting anything
git cat-file -p "$BLOB" | tr -d '\n\r' | shasum -a 256    # confirm it IS the secret, don't print it
rm -P <path>                                              # -P overwrites (BSD); shred -u on GNU
git for-each-ref 'refs/t3/**' --format='%(refname)' | while read r; do git update-ref -d "$r"; done
git reflog expire --expire=now --expire-unreachable=now --all
git gc --prune=now
git cat-file -e "$BLOB" 2>/dev/null && echo "STILL PRESENT" || echo "GONE"   # the check
```

Deleting these refs costs the rewind history of those sessions — real but usually cheap. Confirm
with the user if the session is recent.

**Separate the two questions, because they have different answers and different urgency:**

| Question | Query | Meaning |
|---|---|---|
| Is it in local git objects? | `git log --all -- <path>` | includes checkpoints; a local-machine problem |
| **Did it ever leave this machine?** | `git log --remotes -- <path>` | empty = never pushed = **not a disclosure**, just hygiene |

In the 2026-08-19 case `--remotes` was empty, which downgraded it from "rotate the key now" to
"clean it up." Run that query before you alarm anyone — and run it before you *don't*.

**Also check the ignore status, not just the tracking status.** `git check-ignore -v <path>`
returning nothing on an untracked secret means it is **one `git add -A` away from a real commit**.
Untracked is not protected; ignored is protected.
