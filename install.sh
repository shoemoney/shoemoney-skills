#!/usr/bin/env bash
# install.sh — symlink (or copy) shoemoney-skills skill folders into a target dir.
#
# Usage:
#   install.sh [--target DIR] [--copy] [--list] [--all] [--help] [skill ...]
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.claude/skills"
MODE="link"
DO_ALL=0
DO_LIST=0
SKILLS=()

usage() {
  cat <<'EOF'
Usage: install.sh [--target DIR] [--copy] [--list] [--all] [--help] [skill ...]

  --target DIR   Directory to install skills into (default: ~/.claude/skills)
  --copy         Copy skill folders instead of symlinking them
  --list         Print available skill names, one per line, and exit
  --all          Install every skill in this repo
  --help         Show this help and exit

Examples:
  install.sh scopecreep im5
  install.sh --all
  install.sh --target .claude/skills scopecreep
EOF
}

list_skills() {
  local d
  for d in "$REPO_DIR"/*/; do
    d="${d%/}"
    [ -f "$d/SKILL.md" ] || continue
    basename "$d"
  done
}

while [ $# -gt 0 ]; do
  case "$1" in
    --target)
      TARGET="$2"
      shift 2
      ;;
    --copy)
      MODE="copy"
      shift
      ;;
    --list)
      DO_LIST=1
      shift
      ;;
    --all)
      DO_ALL=1
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      SKILLS+=("$1")
      shift
      ;;
  esac
done

if [ "$DO_LIST" -eq 1 ]; then
  list_skills
  exit 0
fi

ALL_SKILLS=()
while IFS= read -r line; do ALL_SKILLS+=("$line"); done < <(list_skills)

if [ "$DO_ALL" -eq 1 ]; then
  if [ ${#ALL_SKILLS[@]} -gt 0 ]; then
    SKILLS=("${ALL_SKILLS[@]}")
  fi
fi

if [ ${#SKILLS[@]} -eq 0 ]; then
  usage
  exit 1
fi

is_valid_skill() {
  local name="$1" s
  [ ${#ALL_SKILLS[@]} -eq 0 ] && return 1
  for s in "${ALL_SKILLS[@]}"; do
    [ "$s" = "$name" ] && return 0
  done
  return 1
}

for name in "${SKILLS[@]}"; do
  if ! is_valid_skill "$name"; then
    echo "error: unknown skill '$name'. Valid skills:" >&2
    if [ ${#ALL_SKILLS[@]} -gt 0 ]; then
      printf '  %s\n' "${ALL_SKILLS[@]}" >&2
    fi
    exit 1
  fi
done

mkdir -p "$TARGET"

for name in "${SKILLS[@]}"; do
  src="$REPO_DIR/$name"
  dest="$TARGET/$name"
  if [ "$MODE" = "copy" ]; then
    if [ -L "$dest" ]; then
      rm -f "$dest"
    fi
    rm -rf "$dest"
    cp -R "$src" "$dest"
    echo "copied $name -> $dest"
  else
    ln -sfn "$src" "$dest"
    echo "linked $name -> $dest"
  fi
done
