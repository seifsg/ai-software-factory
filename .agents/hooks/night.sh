#!/bin/sh
# Night mode: preflight, then start an unattended factory session that denies instead of prompting.
#   sh night.sh <claude|codex> <hours> [--check]     run from the project; --check stops after the preflight
# Refuses to start when anything the run needs would prompt, fail or go unguarded. FACTORY_START overrides
# the start command (run with sh -c; $P is the project).
host=$1 hours=$2 check=$3 here=$(cd "$(dirname "$0")" && pwd) P=$PWD
run="$P/.factory/run.md" st="$P/.factory/guard/state" bad=0
say() { printf '%-8s %s\n' "$1" "$2"; [ "$1" = ok ] || bad=1; }
case $host in claude | codex) ;; *) echo 'usage: sh night.sh <claude|codex> <hours> [--check]' >&2; exit 2 ;; esac
case $hours in '' | *[!0-9]*) echo 'hours: a whole number' >&2; exit 2 ;; esac
has() { t=$1; shift; grep -qs -- "$t" "$@"; }  # has <text> <files...>: any file contains the text
cfg=${CLAUDE_CONFIG_DIR:-$HOME/.claude}
# 1. The run: open, not waiting on the owner.
grep -q '^Status: open' "$run" 2>/dev/null && say ok 'run file open' || say MISSING "open run file $run"
grep -q '^Waiting: owner' "$run" 2>/dev/null && say MISSING 'the run waits on the owner: answer first'
# 2. The guard is wired for this host.
if [ "$host" = claude ]; then
  { has run-guard.sh "$cfg/settings.json" "$P/.claude/settings.json" "$P/.claude/settings.local.json" || has 'safe-engine@' "$cfg/settings.json"; } \
    && say ok 'guard hooks wired' || say MISSING 'guard hooks (plugin or settings)'
  [ -f "$here/claude-settings.json" ] && say ok 'deny/allow template' || say MISSING "$here/claude-settings.json"
else
  has run-guard.sh "$HOME/.codex/hooks.json" && say ok 'guard hooks wired' || say MISSING "guard hooks in $HOME/.codex/hooks.json"
  has OWNER "$HOME/.codex/rules/factory.rules" && say ok 'forbidden rules' || say MISSING "$HOME/.codex/rules/factory.rules"
fi
command -v "$host" >/dev/null && say ok "$host CLI" || say MISSING "$host CLI on PATH"
# 3. Outward actions work without a prompt: own branch, pre-push hook installed, push dry run, tracker access.
b=$(git -C "$P" branch --show-current 2>/dev/null)
case $b in '' | main | master) say MISSING "a feature branch (on '${b:-detached}')" ;; *) say ok "branch $b" ;; esac
hk="$(git -C "$P" rev-parse --git-common-dir 2>/dev/null)/hooks/pre-push"
cmp -s "$here/pre-push" "$hk" && say ok 'pre-push hook' || say MISSING "pre-push hook at $hk"
git -C "$P" push --dry-run origin HEAD >/dev/null 2>&1 && say ok 'push dry run' || say MISSING 'git push --dry-run origin HEAD'
gh auth status >/dev/null 2>&1 && say ok 'gh signed in' || say MISSING 'gh auth status'
[ "$bad" = 0 ] || { echo 'Night mode refused: fix the MISSING lines.' >&2; exit 1; }
# Budget: the guard halts the run at the deadline. The run file shows it to the owner.
until=$(( $(date +%s) + hours * 3600 ))
mkdir -p "${st%/*}"; { grep -sv '^g_night_until=' "$st"; printf "g_night_until='%s'\n" "$until"; } > "$st.n" && mv "$st.n" "$st"
grep -v '^Night:' "$run" | awk -v n="Night: until $(date -d "@$until" '+%Y-%m-%d %H:%M' 2>/dev/null || date -r "$until" '+%Y-%m-%d %H:%M') ($hours h)" '{ print } /^Waiting:/ && !x { print n; x = 1 }' > "$run.n" && mv "$run.n" "$run"
echo "Preflight passed. Night budget: $hours h."
[ "$check" = --check ] && exit 0
export P
[ -n "$FACTORY_START" ] && exec sh -c "$FACTORY_START"
[ "$host" = claude ] && exec claude -p --permission-mode dontAsk --settings "$here/claude-settings.json" "/safe-engine Resume $P"
exec codex exec -s workspace-write -c 'approval_policy="never"' "\$safe-engine Resume $P"
