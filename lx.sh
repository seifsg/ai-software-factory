#!/bin/sh
# Live proofs for #289: P5 misspelled header, P6 a real Haiku factory run. sh lx.sh <.agents dir> <out dir> <before|after> <work dir>. Temp folders only; gh blocked; spend capped.
A=$1 out=$2 lab=$3 W=$4; C=${CLAUDE_CLI:-claude}
mkdir -p "$W"; printf '{"enabledPlugins":{"safe-factory@ai-software-factory":false}}' > "$W/off.json"
repo() { git init -q "$1"; git -C "$1" -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q --allow-empty -m i; }
cl() { "$C" -p "$@" --plugin-dir "$A" --settings "$W/off.json" --model claude-haiku-5-5 --permission-mode dontAsk --allowedTools Skill Read Write Edit Glob Grep Agent Bash --disallowedTools "Bash(gh:*)" --output-format json </dev/null; }
# Transcript of a session, by the id in its JSON output.
tr_of() { s=$(grep -oE '"session_id":"[^"]*"' "$1" | head -1 | sed 's/.*:"//;s/"//'); ls ~/.claude/projects/*/"$s".jsonl 2>/dev/null | head -1; }

# P5: run file with a misspelled header, an agent told to answer and stop.
r=$W/p5; repo "$r"; mkdir -p "$r/.factory"
printf '# Run: x · fast · change\n**Status:** open\n**Next:** 1 Analyze | **Waiting:** none\n\n## 0 Ticket\n' > "$r/.factory/run.md"
( cd "$r" && XDG_CACHE_HOME="$W/c5" cl "/safe-factory:safe-factory This is a hook test, no real work. Use no tools. Reply with only this text, then stop: done" --max-budget-usd 0.3 --max-turns 3 > "$W/p5.out" 2>&1 )
t=$(tr_of "$W/p5.out")
{ echo "P5 live: real agent, run file with a misspelled header"; echo "guard firings: $(grep -h stop_hook_summary "$t" | grep -c run-guard); guard prompts: $(grep -c 'Stop hook feedback' "$t")"; grep -oE 'factory run in [^"]{0,170}' "$t" | sed "s#[^ ]*/p5/##" | head -1; } > "$out/$lab-P5.txt"

[ -n "$P5_ONLY" ] && exit 0
# P6: a real small product run on Haiku: is each block clean, and does the guard read the file?
r=$W/p6; mkdir -p "$r"
( cd "$r" && XDG_CACHE_HOME="$W/c6" cl '/safe-factory:safe-factory Fast, kind product. Build wc2: a tiny POSIX sh script that prints the word count of a file. Project folder: this one. Owner decisions, already answered: no tracker and no remote, so use local .factory/ticket.md and never run gh; no market research and no kickoff questions; nothing is owner-reserved.' --max-budget-usd 1.5 --max-turns 60 > "$W/p6.out" 2>&1 )
t=$(tr_of "$W/p6.out"); R=$r/.factory/run.md
{
  echo "P6 live: Haiku, new product, real steps"
  echo "guard state: $([ -f "$r/.factory/guard/state" ] && echo yes || echo no); guard prompts: $(grep -c 'Stop hook feedback' "$t")"
  if [ -f "$R" ]; then
    grep -nE '^(Status|Next|Waiting): |^## ' "$R" | cut -c1-70
    awk 'BEGIN { f = 0 } /^```/ { f = !f; next } f || /^\|/ { next } { l = length($0); if (l > m) m = l; if (l > 300) c++ } END { printf "longest line outside tables and fences: %d; lines over 300: %d\n", m, c + 0 }' "$R"
    echo "table rows: $(grep -c '^|' "$R"); bullets: $(grep -cE '^- ' "$R"); fences: $(( $(grep -c '^```' "$R") / 2 ))"
  else echo "no run file"; fi
} > "$out/$lab-P6.txt"
