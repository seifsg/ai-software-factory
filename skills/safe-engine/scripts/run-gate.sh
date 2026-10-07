#!/bin/sh
# Hook launcher for fast_gate.py (Claude Code plugin, Codex hooks.json).
# Free when no factory run is active; finds a real Python 3.9+ once, caches it, and fails open without one.
# No subshells on the hot path: each fork costs tens of milliseconds in Git Bash.
home="${SAFE_ENGINE_HOME:-$HOME/.safe-engine}"
set -- "$home"/active/*.json
[ -e "$1" ] || exit 0
gate="${0%/*}/fast_gate.py"
cache="$home/hook-python"
if [ -r "$cache" ] && read -r py < "$cache"; then
  $py "$gate" hook 2>/dev/null || rm -f "$cache"  # stale interpreter: re-probe next time
  exit 0
fi
input=$(cat)
# Windows Store stubs and old Pythons fail and fall through to the next name.
for py in python python3 "py -3"; do
  out=$(printf '%s' "$input" | $py "$gate" hook 2>/dev/null) && {
    printf '%s' "$out"
    printf '%s\n' "$py" > "$cache"
    exit 0
  }
done
exit 0
