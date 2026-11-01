#!/bin/sh
# Run guard for factory runs, one script for both hooks (Claude Code and Codex use the same JSON):
#   stop     keeps an open run going, one step per turn, until step 8 is ticked and gates A, B and C pass or are waived;
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
read -r stopped waiting finished ticks gate next <<EOF
$(awk '
  /^Status: stopped/ { s = 1 }
  /^## [0-8]b? .*✔/ { c++ }
  /^Waiting: none/ { w = 1 }
  /^## 8 Review ✔/ { r = 1 }
  /^Gate [ABC]: (PASS|WAIVED)/ { p[substr($0, 6, 1)] = 1 }
  /^## [0-8] .*✔/ { t = substr($0, 4, 1) + 1; if (t > m) m = t }
  n == "" && match($0, /^Next: *[0-8]b? [A-Za-z]+ · [a-z-]+/) { n = substr($0, RSTART, RLENGTH); sub(/^Next: */, "", n) }
  END {
    step = n == "" ? 0 : substr(n, 1, 1) + 0; if (m > step) step = m; g = "-"
    if ((step > 3 || r) && !p["A"]) g = "A"; else if ((step > 6 || r) && !p["B"]) g = "B"; else if (r && !p["C"]) g = "C"
    printf "%d %d %d %d %s %s\n", s, w, r && g == "-", c, g, n
  }' "$run")
EOF
[ "$stopped" = 1 ] || [ "$finished" = 1 ] && exit 0  # stopped by the owner, or finished
[ "$gate" = - ] && gate=
if [ "$mode" = compact ]; then
  [ -n "$gate" ] && next="Gate $gate checker"
  printf 'Factory run open (.factory/run.md). Next: %s. Read the run file, load that skill fresh, do only that step, then end your turn.\n' "${next:-see the run file}"
  exit 0
fi
# More than one heading ticked since the last turn end: two steps shared a turn. Waits update the count too.
prev=$(cat "$run.ticks" 2>/dev/null || echo "$ticks")  # no count yet (hooks added mid-run): no flag
case $prev in '' | *[!0-9]*) prev=$ticks ;; esac
echo "$ticks" > "$run.ticks"
batched=$(( ticks - prev > 1 ))
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
# One step per turn: the next step's prompt arrives only after the last answer is complete, as if the owner typed it.
if [ "$batched" = 1 ]; then
  todo="Batched: more than one step heading was ticked in one turn. Redo the last ticked step as its own fresh pass, run any open gate, then end your turn."
elif [ -n "$gate" ]; then
  todo="Gate $gate has not passed: run the checker for Gate $gate, paste its line, then end your turn."
else
  case ${next%% *} in
    0) todo='Step 0 Ticket: load `ticketing` fresh. Check access, ask the owner once for anything the host may block, open or reuse the ticket.' ;;
    1) todo='Step 1 Analyze: load `analyze-start` fresh. Analyze the request and everything it touches, then teach the owner what exists and what we want: visual (tables, ASCII diagrams, emojis), no code.' ;;
    2) todo='Step 2 Recommend: load `recommend` fresh. The three best real solutions, no fillers or placeholders, compared in one table; pick one and say why not the others.' ;;
    2b) todo='Step 2b Challenge: I don'\''t think this is the best we could do. Do better. Make no mistake. Use the Challenge section of `recommend` and stay neutral: keep the pick and make it stronger if it truly is the best, else replace it and say why.' ;;
    3) todo='Step 3 Plan: load `get-ready-to-code` fresh and write Part A: the plan, the todo checklist, the proof list and the test map.' ;;
    4) todo='Step 4 Before: load `how-to-make-a-pr` fresh and capture every Before proof the plan lists, before any source edit.' ;;
    5) todo='Step 5 Build: load Part B of `get-ready-to-code` fresh. Take only the next unticked todo through its loop (before, change, light check, mapped tests), post its log line as your last message, then end your turn. Tick `## 5 Build` and set Next to 6 only after the last todo.' ;;
    6) todo='Step 6 Verify: load `deep-review` fresh. Review the whole build, make the final manual pass with After captures, run the full suite once.' ;;
    7) todo='Step 7 PR: load `how-to-make-a-pr` fresh and open the draft PR.' ;;
    8) todo='Step 8 Review: load `how-to-review-a-pr` fresh and brief a fresh reviewer that did not build it.' ;;
    *) todo="Next: ${next:-read the run file}. Load that skill fresh." ;;
  esac
  [ "${next%% *}" = 5 ] || todo="$todo Do only this step: post its full block as your last message, update .factory/run.md (tick, Next), then end your turn."
fi
printf '{"decision":"block","reason":"If this session runs the factory run in .factory/run.md: %s Ending on purpose? Set Waiting: owner: <question> or Waiting: jobs: <what runs>."}\n' "$todo"
