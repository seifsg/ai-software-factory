#!/bin/sh
# Hook launcher for fast_gate.py: run-gate.sh <host> (claude, codex, cursor, or another hook-capable agent).
# Run it (`sh run-gate.sh codex`; session-start entries add `update`) or source it in the host's own shell with
# $safe_engine_scripts set (the Claude Code plugin): sourced, a call with no factory run starts no process at all.
# Finds a real Python 3.9+ once, caches it, imports the gate from its bytecode cache, and fails open otherwise.
# Only non-first-class hosts ever get exit 2 (deny, reason on stderr): first-class hosts read JSON, and a
# stray 2 (Python exits 2 when it cannot open a script) must never block them. No subshells on the hot path.
home="${SAFE_ENGINE_HOME:-$HOME/.safe-engine}"
host="${1:-claude}"
dir="${safe_engine_scripts:-${0%/*}}"
# Session start of an install that recorded its clone: the daily self-update, before the gate loads (fast_update.py)
if [ "$2" = update ] && [ -z "$SAFE_ENGINE_NO_UPDATE" ] && [ -f "$home/install.json" ]; then
  for py in python3 python "py -3"; do $py "$dir/fast_update.py" </dev/null >/dev/null 2>&1 && break; done
fi
set -- "$home"/active/*.json
[ -e "$1" ] || { set -- "$home"/runs/*.json; [ -e "$1" ]; } || exit 0  # a lone open state re-registers its run
[ -f "$dir/fast_gate.py" ] || exit 0  # half-installed or removed copy: never block the session
case "$host" in claude|codex|cursor) native=1 ;; *) native=0 ;; esac
# The gate from its bytecode cache in the gate home (same text as fast_install.BOOT; a test keeps them equal)
boot="import os,sys;h=os.environ.get('SAFE_ENGINE_HOME') or os.path.join(os.path.expanduser('~'),'.safe-engine');import json,re,pathlib;d=sys.argv[1];sys.dont_write_bytecode=False;sys.pycache_prefix=os.path.join(h,'pycache');sys.path.insert(0,d);sys.argv=[os.path.join(d,'fast_gate.py'),'hook','--host',sys.argv[2]];import fast_gate;fast_gate.main()"
cache="$home/hook-python"
if [ -r "$cache" ] && read -r py < "$cache"; then
  $py -c "$boot" "$dir" "$host"
  status=$?
  if [ "$status" -eq 2 ] && [ "$native" -eq 0 ]; then exit 2; fi
  if [ "$status" -ne 0 ] && [ "$status" -ne 2 ]; then rm -f "$cache"; fi  # stale interpreter: re-probe next time
  exit 0
fi
input=$(cat)
# Windows Store stubs and old Pythons fail and fall through to the next name.
for py in python python3 "py -3"; do
  out=$(printf '%s' "$input" | $py -c "$boot" "$dir" "$host" 2>"$home/hook-stderr")
  status=$?
  if [ "$status" -eq 0 ] || [ "$status" -eq 2 ]; then
    printf '%s\n' "$py" > "$cache"
    printf '%s' "$out"
    if [ "$status" -eq 2 ] && [ "$native" -eq 0 ]; then cat "$home/hook-stderr" >&2; exit 2; fi
    exit 0
  fi
done
exit 0
