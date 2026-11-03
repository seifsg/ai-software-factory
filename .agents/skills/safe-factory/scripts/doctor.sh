#!/bin/sh
# Finds what old factory versions and copies left behind: hooks naming removed scripts, old launchers and state,
# a second Stop guard, an old plugin id, stale copied files. Usage: doctor.sh [plugin root] [--fix]. One line each.
# --fix moves each safe item into a dated backup (never deletes) and refreshes stale copies; a config file holding
# anything else is only reported, with what to edit. Exit 1 while anything is left to do. Add each rename here.
r=${0%/*}/../../..; fix=; for a; do case $a in --fix) fix=1 ;; *) r=$a ;; esac; done
H=$HOME; P=${CLAUDE_PROJECT_DIR:-$PWD}; X=${CODEX_HOME:-$H/.codex}; left=0; stamp=; n=0
[ "$P" = "$H" ] && P=/nonexistent  # project is home: check each file once
old='fast_gate|run-gate[.]sh|skills/safe-engine/|resolve_bundle'
bak="${XDG_CACHE_HOME:-$H/.cache}/ai-software-factory/removed"
[ -n "$fix" ] && stamp=$(date +%Y%m%d-%H%M%S)
say() { printf '%s: %s\n' "$1" "$2"; }
todo() { left=1; say "$1" "$2"; }
# Moves $1 into the backup with --fix, else reports it.
move() {
  [ -n "$fix" ] || { todo "$1" "$2; --fix moves it to a backup"; return 0; }
  b=$bak/$stamp; t=  # numbered: two settings.json, or two runs in one second, never collide; index maps back
  while [ -z "$t" ] || [ -e "$t" ]; do n=$((n + 1)); t=$b/$n-${1##*/}; done
  mkdir -p "$b" && mv "$1" "$t" && printf '%s\t%s\n' "$t" "$1" >> "$b/index" && say "$1" "$2; moved to $t" \
    || { todo "$1" "$2; move failed"; return 1; }
}
# Copy $1 differs from plugin file $2: --fix backs it up and copies the current one.
stale() {
  cmp -s "$1" "$2" && return 0
  [ -n "$fix" ] || { todo "$1" "stale copy of $2; --fix refreshes it"; return 0; }
  move "$1" "stale copy" && { cp "$2" "$1" && say "$1" "refreshed from $2" || todo "$1" "refresh failed; restore it from $t"; }
}
# A factory checkout tracks its own skills: only home and other projects hold leftover launchers.
for d in "$H" "$P"; do
  [ -f "$d/.agents/.claude-plugin/plugin.json" ] && continue
  d=$d/.agents/skills
  [ -d "$d/safe-engine" ] && move "$d/safe-engine" "old launcher, now safe-factory"
  [ -f "$d/improve-factory/scripts/resolve_bundle.py" ] && move "$d/improve-factory" "1.x launcher"
done
[ -d "$H/.safe-engine" ] && move "$H/.safe-engine" "1.x run state and self-updater"
on=; grep -qs 'safe-factory@' "$H/.claude/settings.json" && on=1
# One grep over every hook file; only hits get a closer look.
hits=$(grep -lsE "$old|run-guard[.]sh|safe-engine@" "$X/hooks.json" "$H/.cursor/hooks.json" "$H/.claude/settings.json" \
  "$P/.claude/settings.json" "$P/.claude/settings.local.json" "$P/.codex/hooks.json" "$P/.cursor/hooks.json")
while IFS= read -r f; do
  [ -f "$f" ] || continue  # empty list
  grep -q 'safe-engine@ai-software-factory' "$f" && todo "$f" "old plugin id enabled: /plugin install safe-factory@ai-software-factory, then delete the safe-engine@ line"
  if grep -qE "$old" "$f"; then
    # Whole file moves only when pretty-printed (2 spaces), holding nothing but old factory command hooks.
    if awk -v p="$old" '{ m = split($0, a, /"command":/); for (i = 2; i <= m; i++) { n++; if (a[i] ~ p) k++ } } /"type": *"[^c]/ { o++ }
      NR == 2 && !/^  "/ { o++ } /^  "/ && !/^  "(hooks|version)"/ { o++ }
      END { exit !(NR > 2 && n && n == k && !o) }' "$f"; then move "$f" "hooks of an old factory version; the plugin brings its own"
    else todo "$f" "hooks of an old factory version; delete entries naming fast_gate, run-gate.sh or skills/safe-engine/"; fi
  elif [ -n "$on" ] && case $f in */.claude/*) grep -q 'run-guard[.]sh' "$f" ;; *) false ;; esac; then
    todo "$f" "second Stop guard: the plugin already runs it; delete that entry"
  fi
done <<EOF
$hits
EOF
[ -f "$r/hooks/codex.rules" ] && [ -f "$X/rules/factory.rules" ] && stale "$X/rules/factory.rules" "$r/hooks/codex.rules"
# Copied pre-push: main checkout or worktree (hooks live in the common dir); core.hooksPath is not followed.
g=$P/.git; [ -f "$g" ] && { read -r g < "$g"; g=${g#gitdir: }/../..; case $g in /* | ?:*) ;; *) g=$P/$g ;; esac; }; g=$g/hooks/pre-push
[ -f "$r/hooks/pre-push" ] && grep -qs 'Factory pre-push hook' "$g" && stale "$g" "$r/hooks/pre-push"
exit $left
