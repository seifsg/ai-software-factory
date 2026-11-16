#!/bin/sh
# Recorded runs (corpus/r1-r4: final run file, guard state, session and subagent transcripts stripped to
# what the guard reads) replayed through one guard, printing every reply and state. Variants per run: as
# recorded; state lost; every gate and verdict moved onto this checkout's HEAD (with its suite receipt);
# and the run file cut after each step heading. Each variant takes the same five events.
# Env: W (a fresh folder, native form), G (the guard command), BIN (the binary, for receipts).
set -u
export HOME="$W" XDG_CACHE_HOME="$W" LC_ALL=C
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$W"
state() { printf -- '-- state\n'; sed "s/^g_seen='[0-9]*'/g_seen='T'/; s/^g_jobs_since='[0-9][0-9]*'/g_jobs_since='T'/" "$1/.factory/guard/state" 2>/dev/null; }
k=0
# Writes a full-suite PASS receipt for every Gate B, Gate C, review and cap sha the run file names.
receipts() {
  mkdir -p "$1/.factory/receipts"
  for s in $(sed -n -E 's/^(Gate [BC]: PASS|Review: ready) .*@([0-9a-f]{7,40}).*/\2/p' "$1/.factory/run.md" | sort -u); do
    printf 'factory-receipt 1\nsuite full\ntree x\nhead %s\nclean yes\nresult PASS\ncmd parity\n' "$s" > "$1/.factory/receipts/$s-full.txt"
  done
}
# One variant: a checkout holding run file $2 (and state $3, or none), the transcripts of run $1.
variant() {
  k=$((k + 1)); v=$W/v$k; sid=$(cat "$here/corpus/$1/sid")
  mkdir -p "$v/r/.factory/guard" "$v/projects"
  cp -r "$here/corpus/$1/projects/p" "$v/projects/p"
  i=0; while IFS= read -r f; do i=$((i + 1)); touch -t "$(printf '20230101%04d.00' "$i")" "$v/projects/p/$sid/subagents/$f"; done < "$here/corpus/$1/order"
  git init -q "$v/r"; git -C "$v/r" -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q --allow-empty -m i
  head=$(git -C "$v/r" rev-parse HEAD)
  cp "$2" "$v/r/.factory/run.md"
  if [ -n "$3" ]; then sed "s#@TP@#$v/projects/p/$sid.jsonl#; s#^g_seen='@NOW@'#g_seen='1'#" "$3" > "$v/r/.factory/guard/state"; else rmdir "$v/r/.factory/guard"; fi
  # The binary guard also wants a passing full-suite receipt for each Gate B, C and review commit (sh reads none):
  # one per gate sha, matched on its head. A receipt is data, so both guards get the same files.
  receipts "$v/r"
  if [ "${4:-}" = onhead ]; then
    for f in "$v/r/.factory/run.md" "$v/projects/p/$sid/subagents/"*.jsonl; do sed -E "s/@[0-9a-f]{7,40}/@$head/g" "$f" > "$f.n" && mv "$f.n" "$f"; done
    i=0; while IFS= read -r f; do i=$((i + 1)); touch -t "$(printf '20230101%04d.00' "$i")" "$v/projects/p/$sid/subagents/$f"; done < "$here/corpus/$1/order"
    (cd "$v/r" && "$BIN" receipt write --suite full --result PASS --cmd parity 2>/dev/null)
  fi
  ev() { printf '{"session_id":"%s","transcript_path":"%s","cwd":"%s","stop_hook_active":%s,"last_assistant_message":"%s"%s}' "$sid" "$v/projects/p/$sid.jsonl" "$v/r" "$1" "$2" "${3:-}"; }
  printf '== %s %s\n' "$1" "$5"; ev false x | $G stop | sed "s/$head/HEAD/g"
  printf '== %s %s active\n' "$1" "$5"; ev true x | $G stop | sed "s/$head/HEAD/g"
  printf '== %s %s heading\n' "$1" "$5"; ev false '## 8 Review x' | $G stop | sed "s/$head/HEAD/g"
  printf '== %s %s compact\n' "$1" "$5"; ev false x ',"source":"compact"' | $G compact | sed "s/$head/HEAD/g"
  printf '== %s %s check\n' "$1" "$5"; (cd "$v/r" && $G check "$sid") | sed "s/$head/HEAD/g"
  state "$v/r"
}
for r in r1 r2 r3 r4; do
  run=$here/corpus/$r/run.md
  variant $r "$run" "$here/corpus/$r/state" "" recorded
  variant $r "$run" "" "" state-lost
  variant $r "$run" "$here/corpus/$r/state" onhead on-head
  # The run file cut after each step heading, opened again with that step next.
  n=0
  for h in '0 Ticket' '1 Analyze' '2 Recommend' '2b Challenge' '3 Plan' '4 Before' '5 Build' '6 Verify' '7 PR' '8 Review'; do
    n=$((n + 1)); cut=$W/cut-$r-$n.md
    awk -v h="## $h" 'index($0, h) == 1 { stop = 1 } stop && /^## / && index($0, h) != 1 { exit } { print }' "$run" |
      sed "s/^Status: .*/Status: open/; s/^Next: .*/Next: ${h%% *} ${h#* } · skill/" > "$cut"
    variant $r "$cut" "$here/corpus/$r/state" onhead "cut-$h"
  done
done
