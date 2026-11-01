#!/bin/sh
# Run guard for factory runs, one script for both hooks (Claude Code and Codex use the same JSON):
#   stop     keeps an open run going, one step per turn, until step 8 is ticked, gates A, B and C and the
#            review are proven on their commits;
#   compact  after compaction or a resume, re-injects the run's place, because compaction drops skill text.
# Reads only the nearest .factory/run.md inside the current Git checkout, so other sessions exit at once.
# Its own state lives in .factory/guard/; proof comes from files the host writes, never from run-file text alone.
#   clear    the owner's command after a halt: the guard drives the run again, loop caps count from here.
mode=${1:-stop}
self=$0; case $self in *run-guard.sh) ;; *) self=${g:-run-guard.sh} ;; esac  # the plugin hook sources it from $g
d=$PWD
while [ ! -f "$d/.factory/run.md" ]; do
  { [ -e "$d/.git" ] || [ -z "$d" ]; } && exit 0  # checkout root reached: no run here
  d=${d%/*}
done
run="$d/.factory/run.md" g="$d/.factory/guard"
st="$g/state"
# Untouched for 12 hours: abandoned, not this session's. A resume (compact mode) still gets its place back.
[ "$mode" = stop ] && [ -n "$(find "$run" -mmin +720)" ] && exit 0
in=; [ "$mode" = clear ] || in=$(cat)
val() { printf '%s' "$in" | sed -n "s/.*\"$1\": *\"\([^\"]*\)\".*/\1/p" | head -n 1; }  # one JSON string field
sid=$(val session_id) tp=$(val transcript_path | sed 's/\\\\/\//g' | tr -d "'") now=$(date +%s)
# State: single-quoted g_* lines only the guard writes. Anything else is reported and ignored, never trusted.
note=
if [ -f "$st" ]; then
  if grep -qv "^g_[A-Za-z_]*='[^']*'\$" "$st"; then note='guard state was edited outside the guard; ignored.'; else . "$st"; fi
fi
[ -f "$run.ticks" ] && { g_ticks=$(cat "$run.ticks"); rm -f "$run.ticks" "$run.nudge"; }  # state of an older guard
keys='ticks session transcript seen night_until sig idle halt end clear base_A base_B base_C base_R sstep relay rstep compacts csession jobs_since'
save() { mkdir -p "$g" && for k in $keys; do eval "printf \"g_%s='%s'\\n\" $k \"\$g_$k\""; done > "$st"; }
if [ "$mode" = clear ]; then  # also ends night mode: the owner is back
  g_halt= g_end= g_idle=0 g_clear=1 g_night_until=0; save
  grep -v '^Night:' "$run" > "$run.n" && mv "$run.n" "$run"
  printf 'Factory run cleared: the guard drives it again, loop caps count from here, night mode is off.\n'; exit 0
fi
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
read -r stopped waiting finished ticks gate sig jobs jmax crit fA fB fC fR step next <<EOF
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
    if (/^Gate [ABC]: PASS \(checker [^ )]+\) @[0-9a-f]+/) { x = substr($0, 6, 1); gid[x] = $5; sub(/\)$/, "", gid[x]); gsha[x] = at($6); want[gid[x]] = 1 }
    if (/^CRITICAL: /) cr = 1
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
  /"role":"assistant"/ && !/api-request-blob/ {  # its own handback; the last one counts, every failed one is a round
    if (kind[id] == "R") {
      if (match($0, /verdict: (not ready|ready after fixes|ready)( @[0-9a-f]+)?/)) { last[id] = substr($0, RSTART, RLENGTH); if (last[id] !~ /^verdict: ready( @|$)/) f["R"]++ }
    } else if (match($0, "Gate " kind[id] ": (PASS|FAIL)[^\"\\\\]*")) last[id] = substr($0, RSTART, RLENGTH)
  }
  END {
    for (id in kind) if (kind[id] != "R" && last[id] ~ /FAIL/) f[kind[id]]++  # one checker per gate round
    step = n == "" ? 0 : substr(n, 1, 1) + 0; if (m > step) step = m; g = "-"
    rok = rid != "" && pre(rsha, head) && head == up && proven(rid, "R", rsha) && (nov || fb || last[rid] ~ /^verdict: ready( @|$)/)
    if ((step > 3 || r) && !ok("A")) g = "A"; else if ((step > 6 || r) && !ok("B")) g = "B"; else if (r && !ok("C")) g = "C"; else if (r && !rok) g = "R"
    p += ok("A") + ok("B") + ok("C") + rok  # progress: ticks plus proven gates
    printf "%d %d %d %d %s %d %d %d %d %d %d %d %d %d %s\n", s, w, r && g == "-", c, g, p, j, jm, cr, f["A"], f["B"], f["C"], f["R"], step, n
  }' "$run" "$@")
EOF
[ "$gate" = - ] && gate=
[ -f "$st" ] || [ "${ticks:-0}" -le 1 ] || [ -n "$g_ticks" ] || note='guard state was missing; counts restart from here.'
prev=${g_ticks:-$ticks}
case $prev in '' | *[!0-9]*) prev=$ticks ;; esac
[ "$finished" = 1 ] && g_end=done
if [ "$mode" = stop ]; then
  [ "$g_session" = "$sid" ] || g_sstep=$step  # a new session counts phase boundaries from here
  [ -n "$g_relay" ] && [ "$g_relay" != "$sid" ] && g_relay=  # the fresh session took over
  g_ticks=$ticks g_seen=$now g_session=$sid g_transcript=$tp
fi
[ "$stopped" = 1 ] || [ "$finished" = 1 ] && { [ "$mode" = stop ] && save; exit 0; }  # stopped by the owner, or finished
if [ -n "$g_halt" ]; then  # halted: the guard drives nothing until the owner clears it
  [ "$mode" = compact ] && { printf 'Factory run halted (%s): wait for the owner; do not continue the run.\n' "$g_halt"; exit 0; }
  save; printf '{"systemMessage":"Factory run halted (%s). The owner reads the packet in .factory/run.md and resumes with: sh %s clear"}\n' "$g_halt" "$self"
  exit 0
fi
if [ "$mode" = compact ]; then
  case $in in *'"source":"compact"'* | *'"source": "compact"'*)  # count this session's compactions
    [ "$g_csession" = "$sid" ] && g_compacts=$(( ${g_compacts:-0} + 1 )) || g_compacts=1
    g_csession=$sid; save ;;
  esac
  case $gate in '') ;; R) next='8 Review: a proven reviewer verdict on HEAD' ;; *) next="Gate $gate checker" ;; esac
  printf 'Factory run open (.factory/run.md). Next: %s. Read the run file, load that skill fresh, do only that step, then end your turn.\n' "${next:-see the run file}"
  [ "${g_compacts:-0}" -ge 2 ] && [ "$g_csession" = "$sid" ] && printf 'Relay due: this session was compacted %s times; at the next turn end the guard hands the run to a fresh session.\n' "$g_compacts"
  exit 0
fi
[ -n "$g_relay" ] && { save; printf '{"systemMessage":"Factory run relayed to a fresh session; this session no longer drives it."}\n'; exit 0; }
# More than one heading ticked since the last turn end: two steps shared a turn. Waits update the count too.
batched=$(( ticks - prev > 1 ))
# Loop caps count failed rounds from the host's subagent files, since the owner's last clear.
if [ "$g_clear" = 1 ]; then g_base_A=$fA g_base_B=$fB g_base_C=$fC g_base_R=$fR g_clear=; fi
loop= rounds=0
for x in A B C R; do eval "n=\$((f$x - \${g_base_$x:-0}))"; [ "$n" -gt "$rounds" ] && rounds=$n loop=$x; done
# A jobs wait has a deadline; past it the guard wakes the run, even while a subagent still runs (it may hang).
todo=
if [ "$jobs" = 1 ]; then
  [ -n "$g_jobs_since" ] || g_jobs_since=$now
  [ "$jmax" -gt "${FACTORY_JOB_MAX:-120}" ] && jmax=${FACTORY_JOB_MAX:-120}
  if [ "$jmax" = 0 ]; then todo='Waiting: jobs: needs a deadline: write it as `Waiting: jobs: <what runs> (max <minutes> min)`, then end your turn.'
  elif [ $(( now - g_jobs_since )) -gt $(( jmax * 60 )) ]; then
    todo="The job in Waiting: jobs: is past its deadline ($jmax min): check it, stop it if it hangs, record its result or failure in .factory/run.md, update Waiting, then end your turn."
  fi
else g_jobs_since=; fi
save
[ -n "$todo" ] && { printf '{"decision":"block","reason":"If this session runs the factory run in .factory/run.md: %s"}\n' "$todo"; exit 0; }
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
# Progress budget: turns that change the run file without a new tick or proven gate.
[ "$sig" = "$g_sig" ] && g_idle=$(( ${g_idle:-0} + 1 )) || g_idle=0
g_sig=$sig
# Rounds 1-3 run; 4 and 5 only while the run file names an open CRITICAL; after 5, or idle too long: halt.
[ "$loop" = R ] && loop='review' || loop="Gate $loop"
if [ "$night" = 1 ] && [ "$now" -gt "$g_night_until" ]; then g_halt='night time budget spent'
elif [ "$rounds" -ge 5 ] || { [ "$rounds" -ge 3 ] && [ "$crit" != 1 ]; }; then g_halt="$loop: $rounds failed rounds"
elif [ "$g_idle" -ge "${FACTORY_IDLE_TURNS:-6}" ]; then g_halt="no progress in $g_idle turns"
fi
if [ -n "$g_halt" ]; then
  g_end=halt; save
  printf '{"decision":"block","reason":"HALT (%s): the guard stops driving this run. Start no new round. Write the owner packet under the current step: findings per round (new vs repeated), the shared cause, options (extend, defer with an owner record, amend scope, cancel). Set Waiting: owner: <question>, then end your turn. Only the owner resumes it: sh %s clear"}\n' "$g_halt" "$self"
  exit 0
fi
# Relay: a fresh session takes over after 2 compactions, and at night after plan, build and PR.
why=
[ "${g_compacts:-0}" -ge 2 ] && [ "$g_csession" = "$sid" ] && why="compacted $g_compacts times"
[ "$night" = 1 ] && case $step in 4 | 6 | 8) [ "${g_sstep:-$step}" -lt "$step" ] && [ "$g_rstep" != "$step" ] && why="night phase boundary before step $step" ;; esac
if [ -n "$why" ]; then
  g_relay=$sid g_rstep=$step; save
  printf '{"decision":"block","reason":"Relay (%s): this session stops driving the run. Make sure .factory/run.md and the ticket hold everything the next step needs: the next session reads only those. Start a fresh session with your session tool if you have one, prompt: safe-engine Resume %s; otherwise the watchdog starts it. Set Waiting: jobs: relay to a fresh session (max 30 min), then end your turn."}\n' "$why" "$d"
  exit 0
fi
save
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
