#!/bin/sh
# Finds what old factory versions and copies left behind: hooks naming removed scripts, old launchers and state,
# a second Stop guard, an old plugin id, stale copied files. Usage: doctor.sh [plugin root] [--fix]. One line each.
# --fix moves each safe item into a dated backup (never deletes) and refreshes stale copies; a config file holding
# other settings is only reported, with what to edit. Exit 1 while anything is left to do. Add each rename here.
r=${0%/*}/../../..; fix=; for a; do case $a in --fix) fix=1 ;; *) r=$a ;; esac; done
H=$HOME; P=${CLAUDE_PROJECT_DIR:-$PWD}; left=0; stamp=; n=0
old='fast_gate|run-gate[.]sh|skills/safe-engine/|resolve_bundle'
bak="${XDG_CACHE_HOME:-$H/.cache}/ai-software-factory/removed"
[ -n "$fix" ] && stamp=$(date +%Y%m%d-%H%M%S)
say() { printf '%s: %s\n' "$1" "$2"; }
todo() { left=1; say "$1" "$2"; }
# Moves $1 into the backup with --fix, else reports it.
move() {
  [ -n "$fix" ] || { todo "$1" "$2; --fix moves it to a backup"; return 0; }
  n=$((n + 1)); b=$bak/$stamp; t=$b/$n-${1##*/}  # numbered: two settings.json never collide; index maps back
  mkdir -p "$b" && mv "$1" "$t" && printf '%s\t%s\n' "$t" "$1" >> "$b/index" && say "$1" "$2; moved to $t" \
    || { todo "$1" "$2; move failed"; return 1; }
}
# Copy $1 differs from plugin file $2: --fix backs it up and copies the current one.
stale() {
  cmp -s "$1" "$2" && return 0
  [ -n "$fix" ] || { todo "$1" "stale copy of $2; --fix refreshes it"; return 0; }
  move "$1" "stale copy" && cp "$2" "$1" && say "$1" "refreshed from $2"
}
for d in "$H" "$P"; do
  d=$d/.agents/skills
  [ -d "$d/safe-engine" ] && move "$d/safe-engine" "old launcher, now safe-factory"
  [ -f "$d/improve-factory/scripts/resolve_bundle.py" ] && move "$d/improve-factory" "1.x launcher"
done
[ -d "$H/.safe-engine" ] && move "$H/.safe-engine" "1.x run state and self-updater"
on=; grep -qs 'safe-factory@' "$H/.claude/settings.json" && on=1
# One grep over every hook file; only hits get a closer look.
hits=$(grep -lsE "$old|run-guard[.]sh|safe-engine@" "$H/.codex/hooks.json" "$H/.cursor/hooks.json" "$H/.claude/settings.json" \
  "$P/.claude/settings.json" "$P/.claude/settings.local.json" "$P/.codex/hooks.json" "$P/.cursor/hooks.json")
while IFS= read -r f; do
  [ -f "$f" ] || continue  # empty list, or moved already (project is home)
  grep -q 'safe-engine@ai-software-factory' "$f" && todo "$f" "old plugin id enabled: /plugin install safe-factory@ai-software-factory, then delete the safe-engine@ line"
  if grep -qE "$old" "$f"; then
    # Only factory hooks inside: move the whole file; anything else: edit by hand.
    if awk -v p="$old|run-guard[.]sh" '/"command":/ { n++; if ($0 ~ p) k++ } /^  "/ && !/^  "(hooks|version)"/ { o++ }
      END { exit !(NR > 2 && n && n == k && !o) }' "$f"; then move "$f" "hooks of an old factory version"
    else todo "$f" "hooks of an old factory version; delete entries naming fast_gate, run-gate.sh or skills/safe-engine/"; fi
  elif [ -n "$on" ] && case $f in */.claude/*) grep -q 'run-guard[.]sh' "$f" ;; *) false ;; esac; then
    todo "$f" "second Stop guard: the plugin already runs it; delete that entry unless Cursor uses this project"
  fi
done <<EOF
$hits
EOF
[ -f "$r/hooks/codex.rules" ] && [ -f "$H/.codex/rules/factory.rules" ] && stale "$H/.codex/rules/factory.rules" "$r/hooks/codex.rules"
g=$P/.git/hooks/pre-push
[ -f "$r/hooks/pre-push" ] && grep -qs 'Factory pre-push hook' "$g" && stale "$g" "$r/hooks/pre-push"
exit $left
