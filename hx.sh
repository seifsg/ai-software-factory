#!/bin/sh
# Guard fixtures for #289. sh hx.sh <run-guard.sh> <out dir> <before|after>: writes <label>-P1,2,3,8.txt. Touches only a temp dir.
G=$1 out=$2 lab=$3; d=$(mktemp -d); export XDG_CACHE_HOME="$d/cache" HOME="$d/home"; mkdir -p "$HOME"
steps='0 1 2 2b 3 4 5 6 7 8'
name() { case $1 in 0) echo 0 Ticket ;; 1) echo 1 Analyze ;; 2) echo 2 Recommend ;; 2b) echo 2b Challenge ;; 3) echo 3 Plan ;; 4) echo 4 Before ;; 5) echo 5 Build ;; 6) echo 6 Verify ;; 7) echo 7 PR ;; 8) echo 8 Review ;; esac; }
git_() { git -C "$1" -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q --allow-empty -m "$2"; }
repo() { git init -q "$1"; git_ "$1" i; }
# One verdict per reply: BLOCK <first words> or SILENT.
say() { case $1 in *'"decision":"block"'*) printf 'BLOCK: %s\n' "$(printf '%s' "$1" | sed 's/.*"reason":"//; s/If this session runs the factory run in [^:]*:[^:]*: //' | cut -c1-110)" ;; '') echo SILENT ;; *) printf 'OTHER: %s\n' "$(printf '%s' "$1" | cut -c1-110)" ;; esac; }
# stop <dir> <session> [active]: the Stop input as Claude Code sends it, with this fixture's transcript.
stop() { printf '{"session_id":"%s","transcript_path":"%s/p/x/%s.jsonl","cwd":"%s","hook_event_name":"Stop","stop_hook_active":%s,"last_assistant_message":"x"}' "$2" "$1" "$2" "$1" "${3:-false}" | sh "$G" stop; }
# proofs <dir> <sha>: checker and reviewer handbacks in the host's subagent files, and every block posted in chat.
proofs() {
  a=$1/p/x/s/subagents; mkdir -p "$a"
  for g in A B C; do { printf '{"message":"Role: checker. Gate %s"}\n' $g; printf '{"message":{"role":"assistant","content":[{"type":"text","text":"Gate %s: PASS @%s"}]}}\n' $g "$2"; } > "$a/agent-c$g.jsonl"; done
  { printf '{"message":"Role: reviewer."}\n'; printf '{"message":{"role":"assistant","content":[{"type":"text","text":"verdict: ready @%s"}]}}\n' "$2"; } > "$a/agent-r.jsonl"
  for s in $steps; do printf '{"isSidechain":false,"message":{"role":"assistant","content":[{"type":"text","text":"## %s x"}]}}\n' "$(name $s)"; done > "$1/p/x/s.jsonl"
}
# file <dir> <header lines> <steps to tick> [gates sha]: a run file.
file() {
  mkdir -p "$1/.factory"
  { printf '# Run: x · fast · change\n%b\n\n' "$2"; for s in $steps; do nm=$(name $s); case " $3 " in *" $s "*) printf '## %s ✔\nx\n' "$nm" ;; *) printf '## %s\n' "$nm" ;; esac
      [ -n "$4" ] && case $s in 3) printf 'Gate A: PASS (checker cA) @%s\n' "$4" ;; 6) printf 'Gate B: PASS (checker cB) @%s\n' "$4" ;; 8) printf 'Review: ready (reviewer r) @%s\nLeft running: none\nGate C: PASS (checker cC) @%s\n' "$4" "$4" ;; esac; done; } > "$1/.factory/run.md"
}
head_() { git -C "$1" rev-parse HEAD; }
OPEN='Status: open\nNext: 1 Analyze · analyze-start'
n=0
variant() { n=$((n + 1)); r=$d/v$n; repo "$r"; file "$r" "$2" 0; printf '%-28s %s\n' "$1" "$(say "$(stop "$r" s)")"; }
{
  echo "P1 open run at step 1, one Waiting spelling each"
  variant 'Waiting: none' "$OPEN\nWaiting: none"
  variant '**Waiting:** none' "$OPEN\n**Waiting:** none"
  variant '- Waiting: none' "$OPEN\n- Waiting: none"
  variant 'no Waiting line' "$OPEN"
  variant 'Waiting: owner: ok?' "$OPEN\nWaiting: owner: ok?"
  variant 'Waiting: jobs: x (max 9 min)' "$OPEN\nWaiting: jobs: x (max 9 min)"
  r=$d/v$n; rm -rf "$r/.factory/guard"; file "$r" "$OPEN\n**Waiting:** none" 0; stop "$r" s >/dev/null
  printf '%-28s %s\n' 'second stop, no file change' "$(say "$(stop "$r" s true)")"
  n=$((n + 1)); r=$d/v$n; repo "$r"; file "$r" 'Status: open\n**Next:** 1 Analyze\nWaiting: none' 0
  printf '%-28s %s\n' 'misspelled Next' "$(say "$(stop "$r" s)")"
} > "$out/$lab-P1.txt" 2>&1

r=$d/fin; git init -q --bare "$d/fin.git"; repo "$r"; git -C "$r" remote add origin "$d/fin.git"; git -C "$r" push -q -u origin HEAD 2>/dev/null; sha=$(head_ "$r"); proofs "$r" "$sha"
{
  echo "P2 closed runs"
  file "$r" 'Status: closed\nNext: none (closed)\nWaiting: none' "$steps" "$sha"
  printf '%-40s %s\n' 'finished, on the proven commit' "$(say "$(stop "$r" s)")"
  git -C "$r" switch -q -c other; git_ "$r" later
  printf '%-40s %s\n' 'same run, other branch, new commit' "$(say "$(stop "$r" s)")"
  file "$r" 'Status: closed\nNext: none (closed)\nWaiting: none' '0' ''
  printf '%-40s %s\n' 'new run in same checkout, closed, no gates' "$(say "$(stop "$r" s)")"
  x=$d/noproof; repo "$x"; file "$x" 'Status: closed\nNext: none (closed)\nWaiting: none' "$steps" ''
  printf '%-40s %s\n' 'closed, all ticked, no gate lines' "$(say "$(stop "$x" s)")"
  y=$d/open; repo "$y"; proofs "$y" "$(head_ "$y")"; git -C "$y" remote add origin "$d/fin.git"; file "$y" 'Status: open\nNext: 8 Review · how-to-review-a-pr\nWaiting: none' "$steps" "$(head_ "$y")"
  git -C "$y" push -q -u origin HEAD:refs/heads/y 2>/dev/null; stop "$y" s >/dev/null; git_ "$y" later; file "$y" 'Status: closed\nNext: none (closed)\nWaiting: none' "$steps" "$(git -C "$y" rev-parse HEAD~1)"
  printf '%-40s %s\n' 'closed after commits past a finish' "$(say "$(stop "$y" s)")"
} > "$out/$lab-P2.txt" 2>&1

gatec() { sha=$(head_ "$1"); proofs "$1" "$sha"; file "$1" 'Status: open\nNext: 8 Review · how-to-review-a-pr\nWaiting: none' "$steps" "$sha"; printf '%-28s %s\n' "$2" "$(say "$(stop "$1" s)")"; }
{
  echo "P3 Gate C and review proven on HEAD"
  a=$d/a; repo "$a"; gatec "$a" 'no remote'
  b=$d/b; repo "$b"; git init -q --bare "$d/b.git"; git -C "$b" remote add origin "$d/b.git"; git -C "$b" push -q -u origin HEAD 2>/dev/null; gatec "$b" 'remote, pushed'
  c=$d/c; repo "$c"; git init -q --bare "$d/c.git"; git -C "$c" remote add origin "$d/c.git"; git -C "$c" push -q -u origin HEAD 2>/dev/null; git_ "$c" later; gatec "$c" 'remote, not pushed'
  e=$d/e; repo "$e"; git init -q --bare "$d/e.git"; git -C "$e" remote add origin "$d/e.git"; gatec "$e" 'remote, branch never pushed'
} > "$out/$lab-P3.txt" 2>&1

gap() { q=$d/g$1; repo "$q"; sha=$(head_ "$q"); proofs "$q" "$sha"; git init -q --bare "$q.git"; git -C "$q" remote add origin "$q.git"; git -C "$q" push -q -u origin HEAD 2>/dev/null; file "$q" "Status: open\nNext: $3\nWaiting: none" "$4" "$sha"; printf '%-34s %s\n' "$2" "$(say "$(stop "$q" s)")"; }
{
  echo "P8 skipped steps"
  gap 1 'all ticked to step 4' '5 Build · get-ready-to-code' '0 1 2 2b 3 4'
  gap 2 'step 1 skipped, past step 3' '5 Build · get-ready-to-code' '0 2 2b 3 4'
  gap 3 'steps 0 to 2b skipped, past step 3' '5 Build · get-ready-to-code' '3 4'
  gap 4 'step 8 ticked, step 5 not ticked' 'none (closed)' '0 1 2 2b 3 4 6 7 8'
  gap 5 'all ticked, all proven' 'none (closed)' "$steps"
  gap 6 'skipped, then Waiting: owner' '5 Build · get-ready-to-code\nWaiting: owner: ok?' '3 4'
  printf '%-34s %s\n' 'second stop, same wait' "$(say "$(stop "$q" s true)")"
} > "$out/$lab-P8.txt" 2>&1

wall() { w=$d/w$1; repo "$w"; printf '%s\n' "$3" > "$w/extra"; { printf '# Run: x · fast · change\nStatus: open\nNext: 1 Analyze · analyze-start\nWaiting: none\n\n## 0 Ticket ✔\n'; cat "$w/extra"; printf '## 1 Analyze\n'; } > "$w/.factory.tmp"; mkdir -p "$w/.factory"; mv "$w/.factory.tmp" "$w/.factory/run.md"; printf '%-30s %s\n' "$2" "$(say "$(stop "$w" s)")"; }
L=$(awk 'BEGIN { for (i = 0; i < 40; i++) printf "ten chars "; }')
{
  echo "P7 walls of text in the run file"
  wall 1 'short lines' '- a fact'
  wall 2 'line of 400 characters' "$L"
  wall 3 'same line in a table' "| $L |"
  printf '```text\n%s\n```\n' "$L" > "$d/fenced"; wall 4 'same line in a fence' "$(cat "$d/fenced")"
  fw=$d/fw; git init -q --bare "$fw.git"; repo "$fw"; git -C "$fw" remote add origin "$fw.git"; git -C "$fw" push -q -u origin HEAD 2>/dev/null; sha=$(head_ "$fw"); proofs "$fw" "$sha"; file "$fw" 'Status: closed\nNext: none (closed)\nWaiting: none' "$steps" "$sha"; printf '%s\n' "$L" >> "$fw/.factory/run.md"
  printf '%-30s %s\n' 'all proven, one long line' "$(say "$(stop "$fw" s)")"
} > "$out/$lab-P7.txt" 2>&1
