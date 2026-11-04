#!/bin/sh
# Run guard for factory runs, one script for both hooks (Claude Code, Codex and Cursor use the same JSON):
#   stop     keeps an open run going, one step per turn, until step 8 is ticked, gates A, B and C and the
#            review are proven on their commits;
#   compact  after compaction or a resume, re-injects the run's place, because compaction drops skill text.
# Finds this session's run in order: its session file, the nearest .factory/run.md inside its checkout, the Workspace
# a step block names. A bound session reaches a run anywhere; an unbound one with no run exits at once.
# Its own state lives in .factory/guard/; proof comes from files the host writes, never from run-file text alone.
#   clear    the owner's command after a halt (clear <run folder>): the guard drives the run again, loop caps count from here.
export LC_ALL=C  # bytes, not characters: a UTF-8 sed stops at a 4-byte emoji and leaks the input into the state
mode=${1:-stop}
self=$0; case $self in *run-guard.sh) ;; *) self=${g:-run-guard.sh} ;; esac  # an older plugin hook sourced it from $g
self=$(printf '%s' "$self" | tr '\\' /)  # a Windows path's backslashes would break the JSON replies
in=; [ "$mode" = clear ] || in=$(cat)
val() { printf '%s' "$in" | sed -n "s/.*\"$1\": *\"\([^\"]*\)\".*/\1/p" | head -n 1; }  # one JSON string field
# Walk from the session's folder (input cwd), else $PWD: a hook may start elsewhere, as in desktop worktree sessions.
c=${in#*\"cwd\":}; [ "$c" = "$in" ] || { c=${c#*\"}; c=${c%%\"*}; cd "$c" 2>/dev/null; }  # no fork: runs at every turn end; Git Bash cd takes JSON's G:\\x
[ "$mode" = clear ] && [ -n "$2" ] && { cd "$2" || exit 1; }
# Nearest run file inside this checkout, stopping at the checkout or drive root (C: too). No fork.
walk() {
  d=$PWD
  while [ ! -f "$d/.factory/run.md" ]; do
    { [ -e "$d/.git" ] || [ "$d" = "${d%/*}" ]; } && { d=; return; }
    d=${d%/*}
  done
}
# Bind this session to the run in the Workspace its step block names: an absolute folder holding a run file, nothing else.
bind() {
  w=${h#*\*\*Workspace:\*\* \`}; [ "$w" = "$h" ] && return 1
  bad=1
  w=$(printf '%s' "${w%%\`*}" | sed 's/\\\\/\//g')
  case $w in *[\'\"\$\\%]*) return 1 ;; /* | [A-Za-z]:/*) ;; *) return 1 ;; esac
  [ -f "$w/.factory/run.md" ] || return 1
  d=$w bad=; [ -z "$s" ] && return 0
  mkdir -p "${b%/*}" && find "${b%/*}" -type f -mtime +30 -exec rm -f {} + ; printf '%s\n' "$w" > "$b"
}
case $in in *\"session_id\":*) s=${in#*\"session_id\":}; s=${s#*\"}; s=${s%%\"*} ;; *) s= ;; esac
case $s in *[!A-Za-z0-9_-]*) s= ;; esac
b=${XDG_CACHE_HOME:-$HOME/.cache}/ai-software-factory/sessions/$s
# The step heading opening this turn's last message, if any: only real step names, so a normal heading is never one.
h=${in#*\"last_assistant_message\":\"## }; [ "$h" = "$in" ] && h=
case $h in '0 Ticket'* | '1 Analyze'* | '2 Recommend'* | '2b Challenge'* | '3 Plan'* | '4 Before'* | '5 Build'* | '6 Verify'* | '7 PR'* | '8 Review'*) ;; *) h= ;; esac
d= bad=
[ -z "$h" ] || bind  # a block naming a run always wins over an older binding
[ -z "$bad$d" ] && [ -n "$s" ] && [ -f "$b" ] && { read -r d < "$b"; [ -f "$d/.factory/run.md" ] || d=; }
[ -n "$d" ] || walk
if [ -z "$d" ]; then
  [ "$mode" = clear ] && { echo "run-guard: no run file here; pass its folder: clear <run folder>" >&2; exit 1; }
  [ -n "$h" ] && [ "$mode" = stop ] || exit 0  # no step block either: not a factory session
  case $in in
    *\"stop_hook_active\":true* | *\"stop_hook_active\":\ true*) printf '{"systemMessage":"Factory step block posted, but no usable run file found: this run may have no guard."}\n' ;;
    *) printf '{"decision":"block","reason":"Factory step block, but no run file found from this folder. If this session runs a factory run, post that block again with a line **Workspace:** `<absolute folder holding .factory/run.md>` so the guard binds it."}\n' ;;
  esac
  exit 0
fi
case $d in /*) command -v cygpath >/dev/null && d=$(cygpath -m "$d") ;; esac  # Git Bash: /tmp/... means nothing to the agent's native tools
run="$d/.factory/run.md" g="$d/.factory/guard"
rf=$run; case $rf in *%*) rf=$(printf '%s' "$rf" | sed 's/%/%%/g') ;; esac  # run path inside printf formats
st="$g/state"
# Untouched for 12 hours: abandoned, not this session's. A resume (compact mode) still gets its place back.
[ "$mode" = stop ] && [ -n "$(find "$run" -mmin +720)" ] && exit 0
sid=$(val session_id) tp=$(val transcript_path | sed 's/\\\\/\//g' | tr -d "'") now=$(date +%s)
# State: single-quoted g_* lines only the guard writes, counters digits only, no $ or backquote anywhere.
# Anything else is never sourced: the run halts until the owner clears it (a lost state halts the same way).
note=
num='ticks|seen|night_until|sig|idle|base_[ABCR]|sstep|rstep|compacts|jobs_since|jobs_key|clear'
if [ -f "$st" ]; then
  if grep -qvE "^g_($num)='[0-9]*'\$|^g_(session|sessions|transcript|halt|end|relay|csession)='[^'\$\`]*'\$" "$st"; then note='guard state was edited outside the guard'; else . "$st"; fi
fi
[ -f "$run.ticks" ] && { g_ticks=$(cat "$run.ticks"); rm -f "$run.ticks" "$run.nudge"; }  # state of an older guard
case $sid in '' | *[!A-Za-z0-9_-]*) ;; *) case " $g_sessions " in *" $sid "*) ;; *) g_sessions="${g_sessions:+$g_sessions }$sid" ;; esac ;; esac
keys='ticks session sessions transcript seen night_until sig idle halt end clear base_A base_B base_C base_R sstep relay rstep compacts csession jobs_since jobs_key'
save() { mkdir -p "$g" && for k in $keys; do eval "printf \"g_%s='%s'\\n\" $k \"\$g_$k\""; done > "$st"; }
if [ "$mode" = clear ]; then  # also ends night mode: the owner is back; keeps the run's sessions for gate proof
  [ -n "$g_sessions" ] || g_sessions=$(sed -n "s/^g_sessions='\([A-Za-z0-9_ -]*\)'\$/\1/p" "$st" 2>/dev/null)
  g_halt= g_end= g_idle=0 g_clear=1 g_night_until=0; save
  grep -v '^Night:' "$run" > "$run.n" && mv "$run.n" "$run"
  printf 'Factory run cleared: the guard drives it again, loop caps count from here, night mode is off.\n'; exit 0
fi
# Evidence: Claude Code keeps each subagent's transcript in <session>/subagents/agent-<id>.jsonl, its brief first,
# for every session of the run (relays). Other hosts: the gate's agent id must appear in the session transcript,
# never in a Claude Code transcript (the model's own edits are in it). No transcript at all: text only.
ev=${tp%/*} ev=${ev%/*} fb=0 nov=0  # every project folder: a moved run's sessions live in different ones
set --; for q in $g_sessions; do for f in "$ev"/*/"$q"/subagents/agent-*.jsonl; do [ -f "$f" ] && set -- "$@" "./${f#"$ev"/}"; done; done  # ./: a project folder name may start with -
if [ $# -gt 0 ]; then set -- $(cd "$ev" && ls -tr "$@")  # oldest first: rounds count in order
else ev=.; if [ -f "$tp" ]; then fb=1; set -- "$tp"; else nov=1; fi; fi
# Posting proof: each session's own transcript beside it, and the heading of the message ending this turn
# (the host may not have written it to the transcript yet).
t=${tp%/*/*}; for q in $g_sessions; do for f in "$t"/*/"$q.jsonl"; do [ -f "$f" ] && [ "$fb$f" != "1$tp" ] && set -- "$@" "$f"; done; done
lh=${in#*\"last_assistant_message\":\"## }; lh=${lh%% *}; case $lh in [0-8] | [0-8]b) ;; *) lh= ;; esac
head=$(git -C "$d" rev-parse HEAD 2>/dev/null) up=$(git -C "$d" rev-parse '@{u}' 2>/dev/null)
[ -n "$up" ] || [ -n "$(git -C "$d" remote 2>/dev/null)" ] || up=$head  # no remote: nothing to push to; a branch never pushed still has one
night=0; [ "${g_night_until:-0}" -gt 0 ] 2>/dev/null && night=1
# One awk pass over the run file and the evidence files. Only a strict "<step> <name> · <skill>" Next value
# is kept for the reply. The step is the later of Next and the last ticked heading, so a malformed Next never
# skips a gate. gate: the first gate the run has reached without proof; R: step 8 without a proven review.
read -r stopped waiting finished ticks gate sig jobs jmax crit fA fB fC fR unp skip step next <<EOF
$(cd "$ev" && awk -v R="$run" -v lh="$lh" -v fb=$fb -v nov=$nov -v head="$head" -v up="$up" -v night=$night -v clr="$g_clear" -v bs="${g_base_A:-0} ${g_base_B:-0} ${g_base_C:-0} ${g_base_R:-0}" '
  BEGIN { split(bs, b); split("A B C R", k); split("3 6 8 8", sp); for (i = 1; i <= 4; i++) { base[k[i]] = b[i]; st[k[i]] = sp[i] } }  # the step of each loop; rounds count since the last clear
  function pre(a, b,  n) { n = length(a) < length(b) ? length(a) : length(b); return n >= 7 && substr(a, 1, n) == substr(b, 1, n) }
  function at(t) { sub(/.*@/, "", t); return t }
  function proven(id, k, sha) {
    if (nov) return 1
    if (fb) return seen[id] && !cc  # a Claude Code transcript also holds the run-file edits of the model
    return kind[id] == k && pre(sha, at(last[id]))
  }
  function opn(x) { return crs[st[x]] || x == "R" && rcr }  # an open CRITICAL in the own step of the loop, or in the last review
  function capped(x) {  # a cap line: 3 failed rounds and no open CRITICAL in its step pass the loop; C and R on the pushed HEAD
    return cs[x] != "" && !opn(x) && (nov || fb && !cc || f[x] - base[x] >= 3) && (x ~ /[AB]/ || pre(cs[x], head) && head == up)
  }
  function ok(x,  id) {
    if (capped(x)) return 1
    id = gid[x]
    if (id == "") return wv[x] && !night  # an owner waiver; nobody waives at night
    return proven(id, x, gsha[x]) && (nov || fb || last[id] ~ /^Gate .: PASS/) && (x != "C" || (pre(gsha[x], head) && head == up))
  }
  FILENAME == R {
    if (/^Status: stopped/) s = 1
    if (/^Waiting: /) hw = 1
    if (/^Waiting: owner/) o = 1
    if (/^Waiting: jobs:/) { j = 1; if (match($0, /\(max [0-9]+ min\)/)) jm = substr($0, RSTART + 5, RLENGTH - 10) + 0 }
    if (/^## [0-8]b? .*✔/) { tk[++c] = $2; dn[$2] = 1 }
    if (/✔/) p++
    if (/^## 8 Review ✔/) r = 1
    if (/^## [0-8] .*✔/) { t = substr($0, 4, 1) + 1; if (t > m) m = t }
    if (n == "" && match($0, /^Next: *[0-8]b? [A-Za-z]+ · [a-z-]+/)) { n = substr($0, RSTART, RLENGTH); sub(/^Next: */, "", n) }
    if (/^Gate [ABC]: PASS \(checker [^ )]+\) @[0-9a-f]+/) { x = substr($0, 6, 1); gid[x] = $5; sub(/\)$/, "", gid[x]); gsha[x] = at($6); want[gid[x]] = 1 }
    if (/^## /) sec = $2
    if (/^CRITICAL: /) crs[sec] = 1
    if (match($0, /^(Gate [ABC]: PASS|Review: ready) \(cap, 3 rounds, no CRITICAL\) @[0-9a-f]+/)) { x = /^R/ ? "R" : substr($0, 6, 1); cs[x] = at(substr($0, 1, RLENGTH)) }
    if (/^Gate [ABC]: WAIVED by owner/) wv[substr($0, 6, 1)] = 1
    if (/^Review: ready \(reviewer [^ )]+\) @[0-9a-f]+/) { rid = $4; sub(/\)$/, "", rid); rsha = at($5); want[rid] = 1 }
    next
  }
  FILENAME !~ /subagents\/agent-[^\/]*$/ {  # a session transcript: the step blocks that reached chat as text
    if (index($0, "\"isSidechain\"")) cx = 1
    if (/"role":"assistant"/) for (l = $0; match(l, /"type":"text","text":"## [0-8]b? /); l = substr(l, RSTART + RLENGTH)) sent[substr(l, RSTART + 25, RLENGTH - 26)] = 1
    if (!fb) next
  }
  fb { if (index($0, "\"isSidechain\"")) cc = 1; for (x in want) if (index($0, x)) seen[x] = 1; next }
  function done1(k) { k = kind[id]; if (k ~ /^[ABC]$/) f[k] = last[id] ~ /^Gate .: PASS/ ? 0 : f[k] + (last[id] ~ /FAIL/) }  # one checker per gate round
  FNR == 1 {  # a subagent, oldest first: its brief names its role; a PASS or ready verdict closes its loop
    done1(); id = FILENAME; sub(/.*agent-/, "", id); sub(/\.jsonl$/, "", id)
    if (match($0, /Role: checker\. Gate [ABC]/)) kind[id] = substr($0, RSTART + RLENGTH - 1, 1)
    else if (index($0, "Role: reviewer")) kind[id] = "R"
    else nextfile
    next
  }
  function final(s, re,  v) { while (match(s, re)) { v = substr(s, RSTART, RLENGTH); s = substr(s, RSTART + RLENGTH) } return v }  # last match: notes may quote older verdicts
  /"role":"assistant"/ && !/api-request-blob/ {  # its own handback; the last one counts, every failed one is a round
    if (kind[id] == "R") {
      v = final($0, "verdict: (not ready|ready after fixes|ready)( @[0-9a-f]+)?")
      if (v != "") { last[id] = v; rcr = index($0, "CRITICAL:") > 0; f["R"] = v ~ /^verdict: ready( @|$)/ ? 0 : f["R"] + 1 }
    } else if ((v = final($0, "Gate " kind[id] ": (PASS|FAIL)[^\"\\\\]*")) != "") last[id] = v
  }
  END {
    done1(); if (clr) for (x in base) base[x] = f[x]  # the owner just cleared: caps count from here
    if (!hw) n = ""  # no Waiting line: a broken header, whatever Next says
    step = n == "" ? 0 : substr(n, 1, 1) + 0; if (m > step) step = m; g = "-"
    rok = capped("R") || rid != "" &&pre(rsha, head) && head == up && proven(rid, "R", rsha) && (nov || fb || last[rid] ~ /^verdict: ready( @|$)/)
    if ((step > 3 || r) && !ok("A")) g = "A"; else if ((step > 6 || r) && !ok("B")) g = "B"; else if (r && !ok("C")) g = "C"; else if (r && !rok) g = "R"
    p += ok("A") + ok("B") + ok("C") + rok  # progress: ticks plus proven gates
    for (x in st) if (opn(x)) oc = oc x
    for (x in f) if (x == "R" ? rok : ok(x)) f[x] = 0  # a loop that converged has no rounds left to cap
    # Past the plan, its steps must be ticked; at the end, all of them. Earlier, a blocked step may wait its turn.
    if (step > 3 || r) for (i = split(r ? "0 1 2 2b 3 4 5 6 7" : "0 1 2 2b 3", q, " "); i > 0; i--) if (!(q[i] in dn)) sk = q[i] (sk == "" ? "" : ",") sk
    sent[lh] = 1; if (cx) for (i = 1; i <= c; i++) if (!sent[tk[i]]) u = u (u == "" ? "" : ",") tk[i]  # Claude Code transcripts only
    printf "%d %d %d %d %s %d %d %d %s %d %d %d %d %s %s %d %s\n", s, !(o || j), r && g == "-" && sk == "", c, g, p, j, jm, oc == "" ? "-" : oc, f["A"], f["B"], f["C"], f["R"], u == "" ? "-" : u, sk == "" ? "-" : sk, step, n
  }' "$run" "$@")
EOF
[ "$gate" = - ] && gate=
[ "$skip" = - ] && skip=
[ -f "$st" ] || [ ! -d "$g" ] || [ "${ticks:-0}" -le 1 ] || [ -n "$g_ticks" ] || note='guard state was lost'  # no folder yet: hooks just added
[ -n "$note" ] && g_halt="$note"  # never trusted, never reset: the owner looks, then clears
prev=${g_ticks:-$ticks}
case $prev in '' | *[!0-9]*) prev=$ticks ;; esac
# A finish the guard saw holds while the run says closed, wherever HEAD went since. Only the guard writes g_end;
# a run that stops saying closed, or a new run in this checkout, proves itself again.
[ "$g_end" = done ] && { grep -q '^Status: closed' "$run" && grep -Eq '^Gate C: (PASS|WAIVED)' "$run" && finished=1 || g_end=; }
[ "$finished" = 1 ] && g_end=done
if [ "$mode" = stop ]; then
  [ "$g_session" = "$sid" ] || g_sstep=$step  # a new session counts phase boundaries from here
  [ -n "$g_relay" ] && [ "$g_relay" != "$sid" ] && g_relay=  # the fresh session took over
  g_ticks=$ticks g_seen=$now g_session=$sid g_transcript=$tp
fi
# Each ticked step's block reaches the owner as its own chat message opening with its heading. One block per
# missing set, before the finished exit: a run chained in one turn is checked when that turn ends. The set lives
# in its own file, so an older guard reading the state never halts on it.
[ "$unp" = - ] && unp=
if [ "$mode" = stop ] && [ -n "$unp" ] && [ "$stopped" != 1 ] && [ -z "$g_halt" ] && [ "$unp" != "$(cat "$g/unposted" 2>/dev/null)" ]; then
  save; printf '%s' "$unp" > "$g/unposted"
  printf '{"decision":"block","reason":"If this session runs the factory run in '"$rf"': Step blocks not posted in chat: %s. Post each full block from '"$rf"' now, each as its own message opening with its heading (## <step> <name>), then go on with the run."}\n' "$unp"; exit 0
fi
[ "$stopped" = 1 ] || [ "$finished" = 1 ] && { [ -z "$s" ] || rm -f "$b"; [ "$mode" = stop ] && save; exit 0; }  # stopped by the owner, or finished: the binding ends
if [ -n "$g_halt" ]; then  # halted: the guard drives nothing until the owner clears it
  [ "$mode" = compact ] && { printf 'Factory run halted (%s): wait for the owner; do not continue the run.\n' "$g_halt"; exit 0; }
  save; printf '{"systemMessage":"Factory run halted (%s). The owner reads the packet in '"$rf"' and resumes with: sh %s clear %s"}\n' "$g_halt" "$self" "$d"
  exit 0
fi
if [ "$mode" = compact ]; then
  case $in in *'"source":"compact"'* | *'"source": "compact"'*)  # count this session's compactions
    [ "$g_csession" = "$sid" ] && g_compacts=$(( ${g_compacts:-0} + 1 )) || g_compacts=1
    g_csession=$sid; save ;;
  esac
  case $in in *'"source":"resume"'* | *'"source": "resume"'*) printf 'Load `safe-factory` first: a resumed session may have lost its Stop guard.
' ;; esac
  case $gate in '') ;; R) next='8 Review: a proven reviewer verdict on HEAD' ;; *) next="Gate $gate checker" ;; esac
  printf 'Factory run open ('"$rf"'). Next: %s. Read the run file, load that skill fresh, do only that step, then end your turn.\n' "${next:-see the run file}"
  [ "${g_compacts:-0}" -ge 2 ] && [ "$g_csession" = "$sid" ] && printf 'Relay due: this session was compacted %s times; at the next turn end the guard hands the run to a fresh session.\n' "$g_compacts"
  exit 0
fi
[ -n "$g_relay" ] && { save; printf '{"systemMessage":"Factory run relayed to a fresh session; this session no longer drives it. Start one with: safe-factory Resume %s"}\n' "$d"; exit 0; }
# More than one heading ticked since the last turn end: two steps shared a turn. Waits update the count too.
batched=$(( ticks - prev > 1 ))
# Loop caps count failed rounds from the host's subagent files, since the owner's last clear.
if [ "$g_clear" = 1 ]; then g_base_A=$fA g_base_B=$fB g_base_C=$fC g_base_R=$fR g_clear=; fi
loop= rounds=0
for x in A B C R; do eval "n=\$((f$x - \${g_base_$x:-0}))"; [ "$n" -gt "$rounds" ] && rounds=$n loop=$x lx=$x; done
# A jobs wait has a deadline; past it the guard wakes the run, even while a subagent still runs (it may hang).
todo=
if [ "$jobs" = 1 ]; then
  k=$(grep '^Waiting: jobs:' "$run" | cksum | cut -d ' ' -f 1)  # a new job text starts a new deadline
  [ -n "$g_jobs_since" ] && [ "$g_jobs_key" = "$k" ] || g_jobs_since=$now g_jobs_key=$k
  [ "$jmax" -gt "${FACTORY_JOB_MAX:-120}" ] && jmax=${FACTORY_JOB_MAX:-120}
  if [ "$jmax" = 0 ]; then todo='Waiting: jobs: needs a deadline: write it as `Waiting: jobs: <what runs> (max <minutes> min)`, then end your turn.'
  elif [ $(( now - g_jobs_since )) -gt $(( jmax * 60 )) ]; then
    todo="The job in Waiting: jobs: is past its deadline ($jmax min): check it, stop it if it hangs, record its result or failure in $run, update Waiting, then end your turn."
  fi
else g_jobs_since= g_jobs_key=; fi
# Progress budget: blocked turns without a new tick or proven gate. Rounds 1-3 run, then a cap line passes the loop;
# 4 and 5 only while the run file names an open CRITICAL; after 5, idle too long or past the night budget: halt.
idle() { [ "$sig" = "$g_sig" ] && g_idle=$(( ${g_idle:-0} + 1 )) || g_idle=0; g_sig=$sig; }
halt() {
  [ "$loop" = R ] && loop='review' || loop="Gate $loop"
  if [ "$night" = 1 ] && [ "$now" -gt "$g_night_until" ]; then g_halt='night time budget spent'
  elif [ "$rounds" -ge 5 ]; then g_halt="$loop: $rounds failed rounds"
  elif [ "$g_idle" -ge "${FACTORY_IDLE_TURNS:-6}" ]; then g_halt="no progress in $g_idle turns"
  fi
  [ -n "$g_halt" ] || return 0
  g_end=halt; save
  printf '{"decision":"block","reason":"HALT (%s): the guard stops driving this run. Start no new round. Write the owner packet under the current step: findings per round (new vs repeated), the shared cause, options (extend, amend scope, cancel). Set Waiting: owner: <question>, then end your turn. Only the owner resumes it: sh %s clear %s"}\n' "$g_halt" "$self" "$d"
  exit 0
}
save
[ -n "$todo" ] && { idle; halt; save; printf '{"decision":"block","reason":"If this session runs the factory run in '"$rf"': %s"}\n' "$todo"; exit 0; }
[ "$waiting" = 1 ] || exit 0  # only a real wait stops a run: any other Waiting spelling is driven
case $in in
  # The host reports a running subagent: its result wakes the session. A background shell (a dev server) never does.
  *'"background_tasks"'*'"type":"subagent"'* | *'"background_tasks"'*'"type": "subagent"'*) exit 0 ;;
  *'"stop_hook_active":true'* | *'"stop_hook_active": true'*)
    # Loop guard: a second stop with no run-file change since the last nudge goes through.
    if [ -f "$g/nudge" ] && [ ! "$run" -nt "$g/nudge" ]; then
      printf '{"systemMessage":"Factory run idle since the last nudge; stopping. See '"$rf"'."}\n'
      exit 0
    fi ;;
esac
: > "$g/nudge"
idle; halt
# Relay: a fresh session takes over after 2 compactions, and at night after plan, build and PR.
why=
[ "${g_compacts:-0}" -ge 2 ] && [ "$g_csession" = "$sid" ] && why="compacted $g_compacts times"
[ "$night" = 1 ] && case $step in 4 | 6 | 8) [ "${g_sstep:-$step}" -lt "$step" ] && [ "$g_rstep" != "$step" ] && why="night phase boundary before step $step" ;; esac
if [ -n "$why" ]; then
  g_relay=$sid g_rstep=$step; save
  printf '{"decision":"block","reason":"Relay (%s): this session stops driving the run. Make sure '"$rf"' and the ticket hold everything the next step needs: the next session reads only those. Start a fresh session with your session tool if you have one, prompt: safe-factory Resume %s; otherwise the watchdog starts it. Set Waiting: jobs: relay to a fresh session (max 30 min), then end your turn."}\n' "$why" "$d"
  exit 0
fi
save
# One step per turn: the next step's prompt arrives only after the last answer is complete, as if the owner typed it.
if [ -n "$skip" ]; then
  todo="Steps not ticked: $skip. Do each now, in order: load its skill, post its block, tick it. Only the owner skips a step: \`Waiting: owner:\` to ask."
elif [ "$batched" = 1 ]; then
  todo="Batched: more than one step heading was ticked in one turn. Redo the last ticked step as its own fresh pass, run any open gate, then end your turn."
elif [ "$rounds" -ge 3 ] && case $crit in *"$lx"*) false ;; *) true ;; esac; then  # the max-rounds loop, no open CRITICAL in its step
  [ "$lx" = R ] && cl='Review: ready' ln=review || cl="Gate $lx: PASS" ln="Gate $lx"
  todo="$ln: $rounds failed rounds, no open CRITICAL: the loop passes by cap. Write \`$cl (cap, 3 rounds, no CRITICAL) @<sha>\` under its step (Gate C and review: on the pushed HEAD), move what is left to the ticket's follow-ups, then go on with the run."
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
    5) todo='Step 5 Build: load Part B of `get-ready-to-code` fresh. Take only the next unticked todo through its loop (before, change, light check, mapped tests), post its log line as your last message, then end your turn. Tick `## 5 Build` and set Next to 6 only after the last todo, then post the full `## 5 Build` block.' ;;
    6) todo='Step 6 Verify: load `deep-review` fresh. Review the whole build, make the final manual pass with After captures, run the full suite once.' ;;
    7) todo='Step 7 PR: load `how-to-make-a-pr` fresh and open the draft PR.' ;;
    8) todo='Step 8 Review: load `how-to-review-a-pr` fresh and brief a fresh reviewer that did not build it.' ;;
    '') todo='Run file header is wrong. Fix these lines, spelled exactly: `Status: open`, `Next: <step> <name> · <skill>`, `Waiting: none`. Then do that step.' ;;
    *) todo="Next: $next. Load that skill fresh." ;;
  esac
  [ "${next%% *}" = 5 ] || todo="$todo Do only this step: post its full block as your last message, update $run (tick, Next), then end your turn."
fi
printf '{"decision":"block","reason":"If this session runs the factory run in '"$rf"': %s%s Ending on purpose? Set Waiting: owner: <question> or Waiting: jobs: <what runs> (max <minutes> min)."}\n' "$todo" "${note:+ Note: $note}"
