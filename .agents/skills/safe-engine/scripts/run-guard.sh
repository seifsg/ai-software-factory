#!/bin/sh
# Run guard for factory runs, one script for both hooks (Claude Code and Codex use the same JSON):
#   stop     keeps an open run going until step 8 is ticked and gates A, B and C pass or are waived, in order;
#   compact  after compaction or a resume, re-injects the run's place, because compaction drops skill text.
# Reads only the nearest .factory/run.md inside the current Git checkout, so other sessions exit at once.
mode=${1:-stop}
d=$PWD
while [ ! -f "$d/.factory/run.md" ]; do
  { [ -e "$d/.git" ] || [ -z "$d" ]; } && exit 0  # checkout root reached: no run here
  d=${d%/*}
done
run="$d/.factory/run.md"
# Untouched for 12 hours: abandoned, not this session's. A resume (compact mode) still gets its place back.
[ "$mode" = stop ] && [ -n "$(find "$run" -mmin +720)" ] && exit 0
# One pass over the run file. Only a strict "<step> <name> · <skill>" Next value is kept for the reply:
# no free text, quotes or control characters. The step is the later of Next and the last ticked heading,
# so a malformed Next never skips a gate. gate: the first gate the run has reached without a PASS.
read -r stopped waiting finished gate next <<EOF
$(awk '
  /^Status: stopped/ { s = 1 }
  /^Waiting: none/ { w = 1 }
  /^## 8 Review ✔/ { r = 1 }
  /^Gate [ABC]: (PASS|WAIVED)/ { p[substr($0, 6, 1)] = 1 }
  /^## [0-8] .*✔/ { t = substr($0, 4, 1) + 1; if (t > m) m = t }
  n == "" && match($0, /^Next: *[0-8]b? [A-Za-z]+ · [a-z-]+/) { n = substr($0, RSTART, RLENGTH); sub(/^Next: */, "", n) }
  END {
    step = n == "" ? 0 : substr(n, 1, 1) + 0; if (m > step) step = m; g = "-"
    if ((step > 3 || r) && !p["A"]) g = "A"; else if ((step > 6 || r) && !p["B"]) g = "B"; else if (r && !p["C"]) g = "C"
    printf "%d %d %d %s %s\n", s, w, r && g == "-", g, n
  }' "$run")
EOF
[ "$stopped" = 1 ] || [ "$finished" = 1 ] && exit 0  # stopped by the owner, or finished
[ "$gate" = - ] && gate=
if [ "$mode" = compact ]; then
  printf 'Factory run open (.factory/run.md). Next: %s. Read the run file, load that skill fresh, then continue.\n' "${next:-see the run file}"
  exit 0
fi
[ "$waiting" = 1 ] || exit 0  # waiting on the owner or background jobs: stopping is right
case $(cat) in
  # The host reports a running subagent: its result wakes the session. A background shell (a dev server) never does.
  *'"background_tasks"'*'"type":"subagent"'* | *'"background_tasks"'*'"type": "subagent"'*) exit 0 ;;
  *'"stop_hook_active":true'* | *'"stop_hook_active": true'*)
    # Loop guard: a second stop with no run-file change since the last nudge goes through.
    if [ -f "$run.nudge" ] && [ ! "$run" -nt "$run.nudge" ]; then
      printf '{"systemMessage":"Factory run idle since the last nudge; stopping. See .factory/run.md."}\n'
      exit 0
    fi ;;
esac
: > "$run.nudge"
if [ -n "$gate" ]; then
  todo="Gate $gate has not passed: run the checker for Gate $gate before going on."
else
  todo="Next: ${next:-read the run file}. Load that skill fresh, finish the step and write its block."
fi
printf '{"decision":"block","reason":"If this session runs the factory run in .factory/run.md: %s Ending on purpose? Set Waiting: owner: <question> or Waiting: jobs: <what runs>."}\n' "$todo"
