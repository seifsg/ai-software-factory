#!/bin/sh
# Hook launcher for fast_gate.py: run-gate.sh <host> (claude, codex, cursor, or another hook-capable agent).
# Free when no factory run is active; finds a real Python 3.9+ once, caches it, and fails open otherwise.
# Only non-first-class hosts ever get exit 2 (deny, reason on stderr): first-class hosts read JSON, and a
# stray 2 (Python exits 2 when it cannot open a script) must never block them. No subshells on the hot path.
home="${SAFE_ENGINE_HOME:-$HOME/.safe-engine}"
host="${1:-claude}"
set -- "$home"/active/*.json
[ -e "$1" ] || exit 0
gate="${0%/*}/fast_gate.py"
[ -f "$gate" ] || exit 0  # half-installed or removed copy: never block the session
case "$host" in claude|codex|cursor) native=1 ;; *) native=0 ;; esac
cache="$home/hook-python"
if [ -r "$cache" ] && read -r py < "$cache"; then
  $py "$gate" hook --host "$host"
  status=$?
  if [ "$status" -eq 2 ] && [ "$native" -eq 0 ]; then exit 2; fi
  if [ "$status" -ne 0 ] && [ "$status" -ne 2 ]; then rm -f "$cache"; fi  # stale interpreter: re-probe next time
  exit 0
fi
input=$(cat)
# Windows Store stubs and old Pythons fail and fall through to the next name.
for py in python python3 "py -3"; do
  out=$(printf '%s' "$input" | $py "$gate" hook --host "$host" 2>"$home/hook-stderr")
  status=$?
  if [ "$status" -eq 0 ] || [ "$status" -eq 2 ]; then
    printf '%s\n' "$py" > "$cache"
    printf '%s' "$out"
    if [ "$status" -eq 2 ] && [ "$native" -eq 0 ]; then cat "$home/hook-stderr" >&2; exit 2; fi
    exit 0
  fi
done
exit 0
