#!/usr/bin/env bash
# Smoke checks for the shoemoney-skills vault. Run on every push and PR (see
# .github/workflows/smoke.yml). Prints PASS/FAIL per check and exits non-zero
# if any check fails.
set -uo pipefail
cd "$(dirname "$0")/.."

OVERALL=0

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; OVERALL=1; }

# --- (a) every top-level non-hidden directory has SKILL.md, and its
# frontmatter `name:` equals the directory name -----------------------------
check_frontmatter() {
    local ok=1
    local dir name
    for dir in */; do
        dir="${dir%/}"
        [ -d "$dir" ] || continue

        if [ ! -f "$dir/SKILL.md" ]; then
            echo "  missing SKILL.md: $dir/"
            ok=0
            continue
        fi

        name="$(grep -m1 '^name:' "$dir/SKILL.md" | sed -E 's/^name:[[:space:]]*//; s/[[:space:]]+$//')"
        if [ "$name" != "$dir" ]; then
            echo "  name mismatch: $dir/SKILL.md has name: '$name'"
            ok=0
        fi
    done

    if [ "$ok" -eq 1 ]; then
        pass "(a) every top-level dir has SKILL.md with name: matching the dir"
    else
        fail "(a) every top-level dir has SKILL.md with name: matching the dir"
    fi
}

# --- (b) python3 -m py_compile on every *.py --------------------------------
check_py_compile() {
    local ok=1
    local f rc
    while IFS= read -r -d '' f; do
        python3 -m py_compile "$f" 2>/tmp/smoke-pycompile.$$
        rc=$?
        if [ "$rc" -ne 0 ]; then
            echo "  py_compile failed ($f):"
            sed 's/^/    /' /tmp/smoke-pycompile.$$
            ok=0
        fi
        rm -f /tmp/smoke-pycompile.$$
    done < <(find . -path ./.git -prune -o -type f -name '*.py' -print0)

    # clean up bytecode caches created by the compile pass above
    find . -type d -name '__pycache__' -not -path './.git/*' -exec rm -rf {} + 2>/dev/null

    if [ "$ok" -eq 1 ]; then
        pass "(b) python3 -m py_compile on every *.py"
    else
        fail "(b) python3 -m py_compile on every *.py"
    fi
}

# --- (c) bash -n on every *.sh ----------------------------------------------
check_bash_syntax() {
    local ok=1
    local f rc
    while IFS= read -r -d '' f; do
        bash -n "$f" 2>/tmp/smoke-bashn.$$
        rc=$?
        if [ "$rc" -ne 0 ]; then
            echo "  bash -n failed ($f):"
            sed 's/^/    /' /tmp/smoke-bashn.$$
            ok=0
        fi
        rm -f /tmp/smoke-bashn.$$
    done < <(find . -path ./.git -prune -o -type f -name '*.sh' -print0)

    if [ "$ok" -eq 1 ]; then
        pass "(c) bash -n on every *.sh"
    else
        fail "(c) bash -n on every *.sh"
    fi
}

# --- (d) portability gate ----------------------------------------------------
# No hardcoded LAN IPs, personal /Users/<name> paths, or /mnt/tank paths
# anywhere in the repo. 192.168.x.x and /Users/you are documented
# placeholders, not leaks.
check_portability() {
    local out
    # --exclude=.git (in addition to --exclude-dir=.git) matters only when this
    # repo is checked out as a git worktree, where .git is a file, not a
    # directory; a normal clone (including actions/checkout) is unaffected.
    out="$(grep -rnE '192\.168\.[0-9]+\.[0-9]+|/Users/[a-z]+|/mnt/tank' \
        --exclude-dir=.git --exclude=.git --exclude-dir=.remember --exclude-dir=.github . 2>/dev/null \
        | grep -v '192\.168\.x\.x' \
        | grep -v '/Users/you')"

    if [ -z "$out" ]; then
        pass "(d) portability gate: no hardcoded LAN IPs / /Users paths / /mnt/tank"
    else
        fail "(d) portability gate: no hardcoded LAN IPs / /Users paths / /mnt/tank"
        echo "$out" | sed 's/^/  /'
    fi
}

# --- (e) tripple-a-gamedev shot-freshness test suite ------------------------
check_shots_freshness() {
    local out rc
    out="$(python3 tripple-a-gamedev/scripts/test_verify_shots_freshness.py 2>&1)"
    rc=$?
    if [ "$rc" -eq 0 ]; then
        pass "(e) tripple-a-gamedev/scripts/test_verify_shots_freshness.py"
    else
        fail "(e) tripple-a-gamedev/scripts/test_verify_shots_freshness.py"
        echo "$out" | sed 's/^/  /'
    fi
}

check_frontmatter
check_py_compile
check_bash_syntax
check_portability
check_shots_freshness

if python3 -m unittest discover -s executive-brief/scripts -p 'test_*.py'; then
    pass "(f) executive briefing history and change guard"
else
    fail "(f) executive briefing history and change guard"
fi

exit "$OVERALL"
