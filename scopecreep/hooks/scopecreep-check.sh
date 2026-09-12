#!/usr/bin/env bash
# Stop hook: surface the scopecreep queue when it has ready items.
#
# Deliberately quiet. A hook that speaks on every turn gets tuned out, which defeats
# the whole point of having a queue. Rules:
#   - silent when there is no queue file
#   - silent when the Ready section is empty
#   - at most once every THROTTLE_SECS per session
# Exit 0 always; a hook must never block the session.

set -uo pipefail
THROTTLE_SECS=7200          # 2 hours

# Find the queue: project first, then global.
QUEUE=""
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -f "$CLAUDE_PROJECT_DIR/QUEUE.md" ]; then
  QUEUE="$CLAUDE_PROJECT_DIR/QUEUE.md"
elif [ -f "./QUEUE.md" ]; then
  QUEUE="./QUEUE.md"
elif [ -f "$HOME/.claude/QUEUE.md" ]; then
  QUEUE="$HOME/.claude/QUEUE.md"
fi
[ -z "$QUEUE" ] && exit 0

# Count bullets under "## Ready" only — blocked items are not actionable and
# nagging about them is noise.
READY=$(awk '
  /^## Ready/        { inready=1; next }
  /^## /             { inready=0 }
  inready && /^- /   { n++ }
  END                { print n+0 }
' "$QUEUE")
[ "$READY" -eq 0 ] && exit 0

# Throttle per session (falls back to a per-queue stamp if no session id).
SID="${CLAUDE_SESSION_ID:-$(printf '%s' "$QUEUE" | md5 -q 2>/dev/null || echo default)}"
STAMP="${TMPDIR:-/tmp}/.scopecreep-$SID"
NOW=$(date +%s)
if [ -f "$STAMP" ]; then
  LAST=$(cat "$STAMP" 2>/dev/null || echo 0)
  [ $(( NOW - LAST )) -lt "$THROTTLE_SECS" ] && exit 0
fi
echo "$NOW" > "$STAMP"

FIRST=$(awk '
  /^## Ready/      { inready=1; next }
  /^## /           { inready=0 }
  inready && /^- / { sub(/^- +/,""); gsub(/\*\*/,""); print; exit }
' "$QUEUE" | cut -c1-90)

echo "📋 scopecreep queue: ${READY} ready item(s) in ${QUEUE#$HOME/}. Top: ${FIRST}"
exit 0
