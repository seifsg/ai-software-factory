#!/bin/sh
# P6: a new run in a session whose earlier run failed Gate B three times. sh gx.sh <run-guard.sh> > out. Temp dir only.
G=$1; d=$(mktemp -d); r=$d/r; mkdir -p "$r/.factory" "$d/p/x/s/subagents"; git init -q "$r"
for i in 1 2 3; do { printf '{"message":"Role: checker. Gate B"}\n'; printf '{"message":{"role":"assistant","content":[{"type":"text","text":"Gate B: FAIL 1 missing"}]}}\n'; } > "$d/p/x/s/subagents/agent-c$i.jsonl"; done
printf '{"isSidechain":false}\n' > "$d/p/x/s.jsonl"
printf '# Run: x\nStatus: open\nNext: 1 Analyze · analyze-start\nWaiting: none\n\n## 0 Ticket ✔\nx\n' > "$r/.factory/run.md"
stop() { printf '{"session_id":"s","transcript_path":"%s/p/x/s.jsonl","cwd":"%s","last_assistant_message":"## 0 Ticket x"}' "$d" "$r" | HOME="$d" XDG_CACHE_HOME="$d/c" sh "$G" stop | sed 's/.*run.md: //' | cut -c1-100; }
echo "first stop of the new run: $(stop)"
echo "second stop: $(stop)"
