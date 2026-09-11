#!/usr/bin/env bash
# Fails when SKILL.md asserts something scripts/ does not do.
#
# This loop's most-found defect class is "the view asserts what the sim does not do".
# SKILL.md is the view; scripts/ is the sim. The skill had never run that check on itself,
# and every drift below shipped at least once — the MIN_MOTION one cost 45 cycles.
#
# Run from pre-flight, before quoting any number in SKILL.md to the user.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

DOC=SKILL.md
WF=scripts/wf_aaa.js
VS=scripts/verify_shots.py
AR=scripts/aaa_review.py
fail=0

check() { # check <label> <condition-result> <detail>
  if [[ "$2" == 0 ]]; then printf '  ok    %s\n' "$1"
  else printf '  DRIFT %s\n        %s\n' "$1" "$3"; fail=1; fi
}

# 1. Every gate in verify_shots.py must be documented. MIN_MOTION was the one that mattered.
for k in MIN_COLORS MIN_MOTION; do
  grep -q "$k" "$VS" || continue
  grep -qi "${k#MIN_}" "$DOC"; check "$VS gate $k is documented" $? \
    "$VS enforces $k but $DOC never mentions it — an agent reading the doc will not know the check exists."
done

# 2. The reviewer slug the doc quotes must be the one the script defaults to.
slug=$(grep -oE '^MODEL = "[^"]+"' "$AR" | head -1 | sed 's/.*"\(.*\)"/\1/')
grep -qF "$slug" "$DOC"; check "reviewer default ($slug) matches doc" $? \
  "$AR defaults to '$slug'; $DOC quotes a different slug."

# 3. The pacing probe path the doc shows must be the one the workflow actually stages.
probe=$(grep -oE 'res://\.aaa/[a-z_]+\.gd' "$WF" | head -1)
[[ -n "$probe" ]] && { grep -qF "$probe" "$DOC"; check "pacing probe ($probe) matches doc" $? \
  "$WF runs '$probe'; $DOC shows a different path, so a copy-pasted override will not run."; }

# 4. Model roster. The doc quotes cycle timings; if the roster moved, the timings are stale.
opus=$(grep -cE "model: *'opus'" "$WF")
total=$(grep -cE "\bagent\(" "$WF")   # derive BOTH numbers; a hard-coded denominator can never go green
grep -qE "$opus of its $total agents" "$DOC"; check "opus agent count ($opus of $total) matches doc" $? \
  "$WF has $opus opus agents of $total; $DOC states a different count. Cost estimates measured on another roster are inputs, not measurements."

# 5b. The doc says pre-flight refreshes the import cache; the baseline prompt must actually run it.
if grep -q 'refresh the import cache' "$DOC"; then
  grep -q -- '--import' "$WF"; check "preflight import-cache refresh matches doc" $? \
    "$DOC claims pre-flight runs --import but $WF never does — a stale .godot/ makes the whole run judge old pixels."
fi

# 5. Files the workflow writes and the doc should tell you to look for.
for f in calibration.json journal.jsonl; do
  grep -qF "$f" "$DOC"; check "$f is documented" $? \
    "$WF/runtime produces $f but $DOC never names it."
done

[[ $fail == 0 ]] && echo "doc/script agreement: clean" || echo "doc/script agreement: DRIFTED (fix SKILL.md, not this script)"
exit $fail
