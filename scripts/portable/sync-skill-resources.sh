#!/bin/sh
# Sync repo-level shared assets into each skill for npx skills portability.
#
# Source of truth stays at repo root:
#   shared/
#   templates/
#   scripts/hooks/
#   scripts/plugin/
#
# Generated per-skill copies:
#   skills/<name>/_shared/
#   skills/<name>/_templates/
#   skills/<name>/_scripts/
#   skills/<name>/_cli/

set -eu

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
SKILLS_DIR="$ROOT_DIR/skills"

copy_dir() {
  src="$1"
  dest="$2"

  rm -rf "$dest"
  mkdir -p "$(dirname "$dest")"
  cp -R "$src" "$dest"
}

sync_skill() {
  skill_dir="$1"

  copy_dir "$ROOT_DIR/shared" "$skill_dir/_shared"
  copy_dir "$ROOT_DIR/templates" "$skill_dir/_templates"

  rm -rf "$skill_dir/_scripts"
  mkdir -p "$skill_dir/_scripts"
  cp -R "$ROOT_DIR/scripts/hooks" "$skill_dir/_scripts/hooks"
  if [ -d "$ROOT_DIR/scripts/plugin" ]; then
    cp -R "$ROOT_DIR/scripts/plugin" "$skill_dir/_scripts/plugin"
  fi

  if [ -d "$ROOT_DIR/cli" ]; then
    copy_dir "$ROOT_DIR/cli" "$skill_dir/_cli/cli"
  fi
}

for skill_md in "$SKILLS_DIR"/*/SKILL.md; do
  [ -f "$skill_md" ] || continue
  skill_dir="$(dirname "$skill_md")"
  printf 'Syncing portable resources: %s\n' "${skill_dir#$ROOT_DIR/}"
  sync_skill "$skill_dir"
done

printf 'Portable skill resources synced.\n'
