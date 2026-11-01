#!/bin/sh
# Run guard for factory runs, one script for both hooks (Claude Code and Codex use the same JSON):
#   stop     keeps an open run going, one step per turn, until step 8 is ticked, gates A, B and C and the
#            review are proven on their commits;
#   compact  after compaction or a resume, re-injects the run's place, because compaction drops skill text.
# Reads only the nearest .factory/run.md inside the current Git checkout, so other sessions exit at once.
# Its own state lives in .factory/guard/; proof comes from files the host writes, never from run-file text alone.
mode=${1:-stop}
d=$PWD
while [ ! -f "$d/.factory/run.md" ]; do
  { [ -e "$d/.git" ] || [ -z "$d" ]; } && exit 0  # checkout root reached: no run here
  d=${d%/*}
done
run="$d/.factory/run.md" g="$d/.factory/guard"
st="$g/state"
# Untouched for 12 hours: abandoned, not this session's. A resume (compact mode) still gets its place back.
[ "$mode" = stop ] && [ -n "$(find "$run" -mmin +720)" ] && exit 0
in=$(cat)
val() { printf '%s' "$in" | sed -n "s/.*\"$1\": *\"\([^\"]*\)\".*/\1/p" | head -n 1; }  # one JSON string field
sid=$(val session_id) tp=$(val transcript_path | sed 's/\\\\/\//g') now=$(date +%s)
# State: single-quoted g_* lines only the guard writes. Anything else is reported and ignored, never trusted.
note=
if [ -f "$st" ]; then
  if grep -qv "^g_[a-z_]*='[^']*'\$" "$st"; then note='guard state was edited outside the guard; ignored.'; else . "$st"; fi
fi
[ -f "$run.ticks" ] && { g_ticks=$(cat "$run.ticks"); rm -f "$run.ticks" "$run.nudge"; }  # state of an older guard
# Evidence: Claude Code keeps each subagent's transcript in <session>/subagents/agent-<id>.jsonl, its brief first.
# Other hosts: the gate's agent id must appear in the session transcript. No transcript at all: text only.
sub="${tp%.jsonl}/subagents" fb=0 nov=0
set -- "$sub"/agent-*.jsonl
if [ ! -f "$1" ]; then set --; if [ -d "$sub" ]; then :; elif [ -f "$tp" ]; then fb=1; set -- "$tp"; else nov=1; fi; fi
head=$(git -C "$d" rev-parse HEAD 2>/dev/null) up=$(git -C "$d" rev-parse '@{u}' 2>/dev/null)
night=0; [ "${g_night_until:-0}" -gt 0 ] 2>/dev/null && night=1
# One awk pass over the run file and the evidence files. Only a strict "<step> <name> · <skill>" Next value
# is kept for the reply. The step is the later of Next and the last ticked heading, so a malformed Next never
# skips a gate. gate: the first gate the run has reached without proof; R: step 8 without a proven review.
read -r stopped waiting finished ticks gate sig jobs jmax next <<EOF
$(awk -v R="$run" -v fb=$fb -v nov=$nov -v head="$head" -v up="$up" -v night=$night '
  function pre(a, b,  n) { n = length(a) < length(b) ? length(a) : length(b); return n >= 7 && substr(a, 1, n) == substr(b, 1, n) }
  function at(t) { sub(/.*@/, "", t); return t }
  function proven(id, k, sha) {
    if (nov) return 1
    if (fb) return seen[id]
    return kind[id] == k && pre(sha, at(last[id]))
  }
  function ok(x,  id) {
    id = gid[x]
    if (id == "") return wv[x] && !night  # an owner waiver; nobody waives at night
    return proven(id, x, gsha[x]) && (nov || fb || last[id] ~ /PASS/) && (x != "C" || (pre(gsha[x], head) && head == up))
  }
  FILENAME == R {
    if (/^Status: stopped/) s = 1
    if (/^Waiting: none/) w = 1
    if (/^Waiting: jobs:/) { j = 1; if (match($0, /\(max [0-9]+ min\)/)) jm = substr($0, RSTART + 5, RLENGTH - 10) + 0 }
    if (/^## [0-8]b? .*✔/) c++
    if (/✔/) p++
    if (/^## 8 Review ✔/) r = 1
    if (/^## [0-8] .*✔/) { t = substr($0, 4, 1) + 1; if (t > m) m = t }
    if (n == "" && match($0, /^Next: *[0-8]b? [A-Za-z]+ · [a-z-]+/)) { n = substr($0, RSTART, RLENGTH); sub(/^Next: */, "", n) }
    if (/^Gate [ABC]: PASS \(checker [^ )]+\) @[0-9a-f]+/) { x = substr($0, 6, 1); gid[x] = $5; sub(/\)$/, "", gid[x]); gsha[x] = at($6); want[gid[x]] = 1; p++ }
    if (/^Gate [ABC]: WAIVED by owner/) wv[substr($0, 6, 1)] = 1
    if (/^Review: ready \(reviewer [^ )]+\) @[0-9a-f]+/) { rid = $4; sub(/\)$/, "", rid); rsha = at($5); want[rid] = 1 }
    next
  }
  fb { for (x in want) if (index($0, x)) seen[x] = 1; next }
  FNR == 1 {  # a subagent: its brief names its role
    id = FILENAME; sub(/.*agent-/, "", id); sub(/\.jsonl$/, "", id)
    if (match($0, /Role: checker\. Gate [ABC]/)) kind[id] = substr($0, RSTART + RLENGTH - 1, 1)
    else if (index($0, "Role: reviewer")) kind[id] = "R"
    else nextfile
    next
  }
  /"role":"assistant"/ && !/api-request-blob/ {  # its own handback; the last one counts
    if (kind[id] == "R") { if (match($0, /verdict: (not ready|ready after fixes|ready)( @[0-9a-f]+)?/)) last[id] = substr($0, RSTART, RLENGTH) }
    else if (match($0, "Gate " kind[id] ": (PASS|FAIL)[^\"\\\\]*")) last[id] = substr($0, RSTART, RLENGTH)
  }
  END {
    step = n == "" ? 0 : substr(n, 1, 1) + 0; if (m > step) step = m; g = "-"
    rok = rid != "" && pre(rsha, head) && head == up && proven(rid, "R", rsha) && (nov || fb || last[rid] ~ /^verdict: ready( @|$)/)
    if ((step > 3 || r) && !ok("A")) g = "A"; else if ((step > 6 || r) && !ok("B")) g = "B"; else if (r && !ok("C")) g = "C"; else if (r && !rok) g = "R"
    printf "%d %d %d %d %s %d %d %d %s\n", s, w, r && g == "-", c, g, p, j, jm, n
  }' "$run" "$@")
EOF
[ "$gate" = - ] && gate=
[ -f "$st" ] || [ "${ticks:-0}" -le 1 ] || [ -n "$g_ticks" ] || note='guard state was missing; counts restart from here.'
save() {
  mkdir -p "$g" && printf "g_ticks='%s'\ng_session='%s'\ng_transcript='%s'\ng_seen='%s'\ng_night_until='%s'\n" \
    "$ticks" "$sid" "$tp" "$now" "${g_night_until:-0}" > "$st"
}
[ "$stopped" = 1 ] || [ "$finished" = 1 ] && { [ "$mode" = stop ] && save; exit 0; }  # stopped by the owner, or finished
if [ "$mode" = compact ]; then
  case $gate in '') ;; R) next='8 Review: a proven reviewer verdict on HEAD' ;; *) next="Gate $gate checker" ;; esac
  printf 'Factory run open (.factory/run.md). Next: %s. Read the run file, load that skill fresh, do only that step, then end your turn.\n' "${next:-see the run file}"
  exit 0
fi
# More than one heading ticked since the last turn end: two steps shared a turn. Waits update the count too.
prev=${g_ticks:-$ticks}
case $prev in '' | *[!0-9]*) prev=$ticks ;; esac
batched=$(( ticks - prev > 1 ))
save
[ "$waiting" = 1 ] || exit 0  # waiting on the owner or background jobs: stopping is right
case $in in
  # The host reports a running subagent: its result wakes the session. A background shell (a dev server) never does.
  *'"background_tasks"'*'"type":"subagent"'* | *'"background_tasks"'*'"type": "subagent"'*) exit 0 ;;
  *'"stop_hook_active":true'* | *'"stop_hook_active": true'*)
    # Loop guard: a second stop with no run-file change since the last nudge goes through.
    if [ -f "$g/nudge" ] && [ ! "$run" -nt "$g/nudge" ]; then
      printf '{"systemMessage":"Factory run idle since the last nudge; stopping. See .factory/run.md."}\n'
      exit 0
    fi ;;
esac
: > "$g/nudge"
# One step per turn: the next step's prompt arrives only after the last answer is complete, as if the owner typed it.
if [ "$batched" = 1 ]; then
  todo="Batched: more than one step heading was ticked in one turn. Redo the last ticked step as its own fresh pass, run any open gate, then end your turn."
elif [ "$gate" = R ]; then
  todo='Step 8 has no verified reviewer verdict on the pushed HEAD: brief a fresh reviewer on that head, paste its line as `Review: ready (reviewer <id>) @<sha>`, then end your turn.'
elif [ -n "$gate" ]; then
  todo="Gate $gate has not passed: its line needs a checker result on its commit (\`Gate $gate: PASS (checker <id>) @<sha>\`$([ "$gate" = C ] && printf ', HEAD pushed')). Run the checker for Gate $gate, paste its line, then end your turn."
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
printf '{"decision":"block","reason":"If this session runs the factory run in .factory/run.md: %s%s Ending on purpose? Set Waiting: owner: <question> or Waiting: jobs: <what runs> (max <minutes> min)."}\n' "$todo" "${note:+ Note: $note}"
