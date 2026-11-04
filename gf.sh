#!/bin/sh
# Guard fixtures for #285. sh gf.sh <run-guard.sh> <out dir> <before|after>: writes <label>-P1,2,3,6,7.txt. Touches only a temp dir.
G=$1 out=$2 lab=$3; d=$(mktemp -d); export XDG_CACHE_HOME="$d/cache" HOME="$d/home"; mkdir -p "$HOME"
g() { git -C "$1" -c user.name=t -c user.email=t@t "$@"; }
repo() { git init -q "$1"; git -C "$1" -c user.name=t -c user.email=t@t commit -q --allow-empty -m i; }
run() { mkdir -p "$1/.factory"; printf '# Run: x · fast · product\nStatus: %s\nNext: 3 Plan · get-ready-to-code\nWaiting: %s\n\n## 0 Ticket ✔\n' "${2:-open}" "${3:-none}" > "$1/.factory/run.md"; }
# j <sid> <cwd> <message>: Stop input as Claude Code sends it.
j() { printf '{"session_id":"%s","transcript_path":"%s/none.jsonl","cwd":"%s","hook_event_name":"Stop","last_assistant_message":"%s"}' "$1" "$d" "$2" "$3"; }
stop() { j "$@" | sh "$G" stop | sed "s#$d/own/##g; s#$d#<d>#g; s# clear <d>/own# clear#; s/\(.\{150\}\).*/\1/"; }
st() { [ -f "$1/.factory/guard/state" ] && echo yes || echo no; }
bound() { [ -f "$XDG_CACHE_HOME/ai-software-factory/sessions/$1" ] && sed "s#$d#<d>#" "$XDG_CACHE_HOME/ai-software-factory/sessions/$1" || echo none; }
show() { echo "--- $1"; shift; "$@"; }

repo "$d/a"; repo "$d/b"; run "$d/b"
{
  echo "P1 session in repo A, run in repo B"
  show "step 0 block names Workspace" stop s1 "$d/a" "## 0 Ticket\\n- **Workspace:** \`$d/b\`, branch x"
  echo "guard state in B: $(st "$d/b"); session file: $(bound s1)"
  show "later plain message" stop s1 "$d/a" "done for now"
  w=$(cygpath -w "$d/b" 2>/dev/null | sed 's/\\/\\\\/g')
  if [ -n "$w" ]; then stop s1w "$d/a" "## 0 Ticket\\n- **Workspace:** \`$w\`, branch x" >/dev/null; echo "Windows path in JSON form binds: $(bound s1w)"; fi
} > "$out/$lab-P1.txt" 2>&1

git -C "$d/a" worktree add -q -b wt "$d/a-wt"; run "$d/a-wt"
{
  echo "P2 session in one worktree, run in a sibling worktree"
  show "step 0 block names Workspace" stop s2 "$d/a" "## 0 Ticket\\n- **Workspace:** \`$d/a-wt\`, branch wt"
  echo "guard state in sibling: $(st "$d/a-wt"); session file: $(bound s2)"
} > "$out/$lab-P2.txt" 2>&1

repo "$d/own"
{
  echo "P3 run in the session's own folder, each guard state"
  show "no run" stop s3 "$d/own" "hi"
  run "$d/own"; show "open" stop s3 "$d/own" "hi"
  rm -rf "$d/own/.factory/guard"; run "$d/own" open "owner: ok?"; show "waiting on owner" stop s3 "$d/own" "hi"
  rm -rf "$d/own/.factory/guard"; run "$d/own"; for i in 1 2 3 4 5 6 7 8; do stop s3 "$d/own" "hi" >/dev/null; done; show "idle after nudges" stop s3 "$d/own" "hi"
  rm -rf "$d/own/.factory/guard"; run "$d/own" closed; show "closed, gate missing" stop s3 "$d/own" "hi"
  rm -rf "$d/own/.factory/guard"; run "$d/own" "stopped (owner)"; show "stopped" stop s3 "$d/own" "hi"
} > "$out/$lab-P3.txt" 2>&1

repo "$d/c"; run "$d/c"
{
  echo "P6 rebind, drop, sweep"
  stop s6 "$d/a" "## 0 Ticket\\n- **Workspace:** \`$d/b\`, branch x" >/dev/null
  echo "first bind: $(bound s6)"
  stop s6 "$d/a" "## 0 Ticket\\n- **Workspace:** \`$d/c\`, branch y" >/dev/null
  echo "after second run's step 0: $(bound s6); guard state in C: $(st "$d/c")"
  run "$d/c" "stopped (owner)"; stop s6 "$d/a" "plain" >/dev/null
  echo "after the run ended: $(bound s6)"
  git init -q --bare "$d/e.git"; git clone -q "$d/e.git" "$d/e" 2>/dev/null; git -C "$d/e" -c user.name=t -c user.email=t@t commit -q --allow-empty -m i; git -C "$d/e" push -q -u origin HEAD 2>/dev/null
  sha=$(git -C "$d/e" rev-parse HEAD); mkdir -p "$d/e/.factory"
  { printf '# Run: x · fast · change\nStatus: closed\nNext: none (closed)\nWaiting: none\n\n'; for h in '0 Ticket' '1 Analyze' '2 Recommend' '2b Challenge' '3 Plan' '4 Before' '5 Build' '6 Verify' '7 PR' '8 Review'; do printf '## %s ✔\nx\n' "$h"; done; printf 'Gate A: PASS (checker a) @%s\nGate B: PASS (checker b) @%s\nReview: ready (reviewer r) @%s\nLeft running: none\nGate C: PASS (checker c) @%s\n' "$sha" "$sha" "$sha" "$sha"; } > "$d/e/.factory/run.md"
  echo "finished run, first stop reply: [$(stop s6c "$d/a" "## 0 Ticket\\n- **Workspace:** \`$d/e\`, branch x")]; session file after: $(bound s6c)"
  mkdir -p "$XDG_CACHE_HOME/ai-software-factory/sessions"; o="$XDG_CACHE_HOME/ai-software-factory/sessions/old"; echo x > "$o"; touch -d '40 days ago' "$o"
  stop s6b "$d/a" "## 0 Ticket\\n- **Workspace:** \`$d/b\`, branch x" >/dev/null
  [ -f "$o" ] && echo "40-day-old session file: kept" || echo "40-day-old session file: swept"
} > "$out/$lab-P6.txt" 2>&1

rm -rf "$d/b/.factory/guard"; repo "$d/q"
{
  echo "P7 other sessions and bad paths"
  show "plain session, plain message" stop s7 "$d/q" "hello"
  show "plain session, normal heading" stop s7 "$d/q" "## 1 Overview of things"
  show "step heading, no path" stop s7 "$d/q" "## 1 Analyze\\nsome text"
  show "unsafe path" stop s7 "$d/q" "## 0 Ticket **Workspace:** \`$d/b\$(id)\`"
  show "folder with no run" stop s7 "$d/q" "## 0 Ticket **Workspace:** \`$d/q\`"
  show "bad session id" stop '../x' "$d/q" "## 0 Ticket **Workspace:** \`$d/b\`"
  echo "session files: $(ls "$XDG_CACHE_HOME/ai-software-factory/sessions" 2>/dev/null | grep -v '^s[0-9]' | tr '\n' ' ')"
} > "$out/$lab-P7.txt" 2>&1
cd /; rm -rf "$d"
