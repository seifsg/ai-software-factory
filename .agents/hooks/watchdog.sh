#!/bin/sh
# Factory watchdog: a check-in from outside the session, every ~30 min (OS scheduler, docs/install.md).
#   sh watchdog.sh <claude|codex> <project>
# Resumes a stalled run, waits out usage limits, starts a pending relay's fresh session, flags a guard that
# stopped firing and notifies once per end (done, halted, waiting on the owner). Reads the guard's state, never
# writes it. Overrides: FACTORY_RESUME, FACTORY_FRESH, FACTORY_NOTIFY (sh -c; $P project, $S session, $MSG text).
host=$1 P=$2 here=$(cd "$(dirname "$0")" && pwd)
run="$P/.factory/run.md" g="$P/.factory/guard"
st="$g/state" w="$g/watch" now=$(date +%s)
[ -f "$run" ] || exit 0
stall=${FACTORY_STALL_MIN:-30} silent=${FACTORY_SILENT_MIN:-90}
load() { [ -f "$1" ] && ! grep -qv -e "^[gw]_[A-Za-z_]*='[^']*'\$" -e '^$' "$1" && . "$1"; }  # single-quoted lines only
load "$st"; load "$w"
mkdir "$g/watch.lock" 2>/dev/null || { [ -n "$(find "$g/watch.lock" -mmin +720)" ] && rmdir "$g/watch.lock" && mkdir "$g/watch.lock"; } || exit 0
trap 'rmdir "$g/watch.lock"' EXIT
save() { printf "w_notified='%s'\nw_backoff_until='%s'\n" "$w_notified" "${w_backoff_until:-0}" > "$w"; }
say() { printf 'watchdog: %s\n' "$1"; }
notify() {  # once per end: $1 key, $2 text
  [ "$w_notified" = "$1" ] && return
  MSG="Factory run in $P: $2"; export MSG P
  if [ -n "$FACTORY_NOTIFY" ]; then sh -c "$FACTORY_NOTIFY"; else printf '%s %s\n' "$(date '+%F %T')" "$MSG" >> "$g/notices"; fi
  w_notified=$1; save; say "notified: $2"
}
old() { [ -n "$(find "$1" -mmin +"$2" 2>/dev/null)" ]; }  # file older than $2 minutes
# Ends: notify once, start nothing.
if grep -q '^Status: \(closed\|stopped\)' "$run" || [ "$g_end" = done ]; then notify done 'done; see the draft PR in .factory/run.md.'; exit 0; fi
[ -n "$g_halt" ] && { notify halt "halted ($g_halt); the packet is in .factory/run.md."; exit 0; }
grep -q '^Waiting: owner' "$run" && { notify owner "waiting on the owner: $(sed -n 's/^Waiting: owner: *//p' "$run" | head -n 1)"; exit 0; }
[ -n "$w_notified" ] && { w_notified=; save; }  # running again: the next end notifies anew
# A guard that stopped firing while the run file moves: the hooks are off.
[ -f "$st" ] && [ "$run" -nt "$st" ] && old "$st" "$silent" && ! old "$run" "$stall" && { notify hooks "the run file changes but the guard has not run for $silent min: check the hooks."; exit 0; }
[ "$now" -lt "${w_backoff_until:-0}" ] && { say "backing off until $(date -d "@$w_backoff_until" '+%H:%M' 2>/dev/null || echo "$w_backoff_until")"; exit 0; }
# Still working: the transcript or the run file moved recently.
if [ -n "$g_relay" ]; then old "$st" 10 || { say 'relay starting'; exit 0; }; mode=fresh
elif old "$run" "$stall" && { [ -z "$g_transcript" ] || old "$g_transcript" "$stall"; }; then mode=resume
else say running; exit 0; fi
S=$g_session MSG='The factory watchdog found this run stalled. Read .factory/run.md and continue its Next step.'; export P S MSG
tpl="$here/claude-settings.json"
if [ "$mode" = fresh ]; then
  say "starting a fresh session (relay)"
  c=${FACTORY_FRESH:-$([ "$host" = codex ] && echo 'codex exec -s workspace-write "\$safe-engine Resume $P"' || echo 'claude -p --permission-mode dontAsk --settings "'"$tpl"'" "/safe-engine Resume $P"')}
else
  say "resuming session $S"
  c=${FACTORY_RESUME:-$([ "$host" = codex ] && echo 'codex exec resume "$S" "$MSG"' || echo 'claude -p -r "$S" --permission-mode dontAsk --settings "'"$tpl"'" "$MSG"')}
fi
(cd "$P" && sh -c "$c") > "$g/watch.log" 2>&1
# A usage limit ends the session at once: wait before the next try.
if grep -qiE 'usage limit|rate limit|limit reached|resets? at|quota' "$g/watch.log"; then
  w_backoff_until=$(( now + ${FACTORY_BACKOFF_MIN:-60} * 60 )); save; say 'usage limit: backing off'
fi
exit 0
