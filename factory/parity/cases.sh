#!/bin/sh
# check.sh's guard scenarios, printing every reply and state instead of asserting: run.sh plays them
# through both guards and diffs the bytes. Env: W (a fresh folder, native form), G (the guard command:
# `sh <run-guard.sh>` or `<binary> guard`), BIN (the binary: writes the suite receipts Gate B and C need).
set -u
export HOME="$W" XDG_CACHE_HOME="$W" LC_ALL=C
mkdir -p "$W"
say() { printf '== %s\n' "$1"; }
# Prints the guard state with the clock fields masked (each side runs at its own second).
state() { printf -- '-- state %s\n' "$1"; sed "s/^g_seen='[0-9]*'/g_seen='T'/; s/^g_jobs_since='[0-9][0-9]*'/g_jobs_since='T'/" "$W/$1/.factory/guard/state" 2>/dev/null; for f in unposted skipwait remote; do [ -f "$W/$1/.factory/guard/$f" ] && printf -- '-- %s: %s\n' "$f" "$(cat "$W/$1/.factory/guard/$f")"; done; }
commit() { git -C "$1" -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q --allow-empty -m "${2:-i}"; }
receipt() { rm -f "$1"/.factory/receipts/*-full.txt; (cd "$1" && "$BIN" receipt write --suite full --result PASS --cmd parity 2>/dev/null); }

# Session binding: a step block binds a run in another repository; a plain session stays quiet.
b=$W/g; mkdir -p "$b/a/.git" "$b/b/.factory"
printf '# Run: x · fast · change\nStatus: open\nNext: 3 Plan · get-ready-to-code\nWaiting: none\n\n## 0 Ticket ✔\n' > "$b/b/.factory/run.md"
gd() { printf '{"session_id":"%s","cwd":"%s","last_assistant_message":"%s"}' "$1" "$b/a" "$2" | $G stop; }
say plain; gd plain 'hello'
say plain-heading; gd plain '## 1 Overview'
say bind; gd s1 "## 0 Ticket\\n- **Workspace:** \`$b/b\`"
state g/b
say bind-file; cat "$W/ai-software-factory/sessions/s1" 2>/dev/null
say no-run; gd s2 '## 1 Analyze'
say bad-workspace; gd s1 "## 1 Analyze **Workspace:** \`/nope\`"
say own-folder; printf '{"session_id":"s3","cwd":"%s","last_assistant_message":"## 1 Analyze **Workspace:** `/nope`"}' "$b/b" | $G stop
mkdir "$b/none"; say clear-none; (cd "$b/none" && $G clear 2>/dev/null; echo "exit $?")

# The check, a host with no command hook: an open run continues, a real wait may stop.
cm() { (cd "$b/$1" && $G check c1); }
mkdir -p "$b/c/.factory" "$b/c/.git"; printf '# Run: x · fast · change\nStatus: open\nNext: 1 Analyze · analyze-start\nWaiting: none\n\n## 0 Ticket ✔\n\n## 1 Analyze\n' > "$b/c/.factory/run.md"
say check-open; cm c
sed 's/^Waiting: none/Waiting: owner: ok?/' "$b/c/.factory/run.md" > "$b/c/w" && mv "$b/c/w" "$b/c/.factory/run.md"
say check-wait; cm c
say check-none; cm none
mkdir -p "$b/.claude/projects/pj/c1/subagents"; printf '{"role":"assistant","content":"Role: checker. Gate A"}\nGate A: FAIL\n' > "$b/.claude/projects/pj/c1/subagents/agent-x.jsonl"; : > "$b/.claude/projects/pj/c1.jsonl"
mkdir -p "$b/d/.factory" "$b/d/.git"; R='# Run: x · fast · change\nStatus: open\nNext: 4 Before · how-to-make-a-pr\nWaiting: none\n\n## 0 Ticket ✔\n## 1 Analyze ✔\n## 2 Recommend ✔\n## 2b Challenge ✔\n## 3 Plan ✔\n'
printf "$R"'Gate A: PASS (checker x) @1234567\n## 4 Before\n' > "$b/d/.factory/run.md"
say check-1g-a; cm d; say check-1g-b; cm d
printf "$R"'## 4 Before\n' > "$b/d/.factory/run.md"; rm -rf "$b/d/.factory/guard"
say check-gate-a; cm d; say check-gate-b; cm d
mkdir -p "$b/e/.factory" "$b/e/.git"; printf '# Run: x · fast · change\nStatus: open\nNext: 1 Analyze · analyze-start\nWaiting: none\n\n## 0 Ticket ✔\n## 1 Analyze\n## 2 Recommend\n' > "$b/e/.factory/run.md"
say check-e1; cm e
sed 's/^## 1 Analyze$/## 1 Analyze ✔/; s/^## 2 Recommend$/## 2 Recommend ✔/; s/^Next: .*/Next: 2b Challenge · recommend/' "$b/e/.factory/run.md" > "$b/e/n" && mv "$b/e/n" "$b/e/.factory/run.md"
say check-batched; cm e
state g/e

# A moved run keeps its proof: session A proved Gate A in one project folder, session F drives it from another.
e=$W/e; mkdir -p "$e/p/-home-x-A/sA/subagents" "$e/p/-home-x-F" "$e/r/.factory"; git init -q "$e/r"; commit "$e/r"; sha=$(git -C "$e/r" rev-parse HEAD)
{ printf '{"message":"Role: checker. Gate A"}\n'; printf '{"message":{"role":"assistant","content":[{"type":"text","text":"Gate A: PASS @%s"}]}}\n' "$sha"; } > "$e/p/-home-x-A/sA/subagents/agent-chk.jsonl"
{ printf '# Run: x · fast · change\nStatus: open\nNext: 4 Before · how-to-make-a-pr\nWaiting: none\n\n'; for h in '0 Ticket' '1 Analyze' '2 Recommend' '2b Challenge' '3 Plan'; do printf '## %s ✔\nx\n' "$h"; done; printf 'Gate A: PASS (checker chk) @%s\n' "$sha"; } > "$e/r/.factory/run.md"
for h in '0 Ticket' '1 Analyze' '2 Recommend' '2b Challenge' '3 Plan'; do printf '{"isSidechain":false,"message":{"role":"assistant","content":[{"type":"text","text":"## %s x"}]}}\n' "$h"; done > "$e/p/-home-x-A/sA.jsonl"
printf '{"isSidechain":false}\n' > "$e/p/-home-x-F/sF.jsonl"
ge() { printf '{"session_id":"%s","transcript_path":"%s","cwd":"%s","last_assistant_message":"x"}' "$1" "$e/p/$2/$1.jsonl" "$e/r" | $G stop; }
say moved-a; ge sA -home-x-A | sed "s/$sha/SHA/g"
say moved-f; ge sF -home-x-F | sed "s/$sha/SHA/g"
state e/r

# Stop rules: only a real wait stops a run; a finish holds once seen; no remote passes; skips and walls of text never finish.
h=$W/h; mkdir -p "$h/.factory"; git init -q "$h"; commit "$h"; a=$W/hp/-home-x-H/sH/subagents; mkdir -p "$a"
hs() { printf '{"session_id":"sH","transcript_path":"%s","cwd":"%s","stop_hook_active":%s,"last_assistant_message":"x"}' "$W/hp/-home-x-H/sH.jsonl" "$h" "${1:-false}" | $G stop | sed "s/$(git -C "$h" rev-parse HEAD)/SHA/g"; }
hd() { rm -rf "$h/.factory/guard"; printf '# Run: x\nStatus: open\nNext: 1 Analyze · analyze-start\n%s\n' "$1" > "$h/.factory/run.md"; }
full() {
  sha=$(git -C "$h" rev-parse HEAD)
  for g in A B C; do { printf '{"message":"Role: checker. Gate %s"}\n' $g; printf '{"message":{"role":"assistant","content":[{"type":"text","text":"Gate %s: PASS @%s"}]}}\n' $g "$sha"; } > "$a/agent-c$g.jsonl"; done
  { printf '{"message":"Role: reviewer."}\n'; printf '{"message":{"role":"assistant","content":[{"type":"text","text":"verdict: ready @%s"}]}}\n' "$sha"; } > "$a/agent-r.jsonl"
  { printf '# Run: x\nStatus: closed\nNext: none (closed)\nWaiting: none\n\n'; for s in '0 Ticket' '1 Analyze' '2 Recommend' '2b Challenge' '3 Plan' '4 Before' '5 Build' '6 Verify' '7 PR' '8 Review'; do case " $1 " in *" ${s%% *} "*) printf '## %s ✔\n' "$s" ;; *) printf '## %s\n' "$s" ;; esac; done
    printf 'Gate A: PASS (checker cA) @%s\nGate B: PASS (checker cB) @%s\nReview: ready (reviewer r) @%s\nGate C: PASS (checker cC) @%s\n' "$sha" "$sha" "$sha" "$sha"; } > "$h/.factory/run.md"
  receipt "$h"
}
all='0 1 2 2b 3 4 5 6 7 8'
for x in '**Waiting:** none' '- Waiting: none' ''; do hd "$x"; say "wait-spelling $x"; hs; done
hd 'Waiting: none'; printf 'Waiting: owner: old\n' >> "$h/.factory/run.md"; say old-wait; hs
hd '**Waiting:** none'; printf '## 0 Ticket\nWaiting: owner: old\n' >> "$h/.factory/run.md"; say body-wait; hs
hd 'Waiting: none'; printf '## 0 Ticket\nStatus: stopped (old)\n' >> "$h/.factory/run.md"; say body-status; hs
hd '**Waiting:** none'; say idle-1; hs; say idle-2; hs true
for x in 'Waiting: owner: q' 'Waiting: jobs: x (max 9 min)'; do hd "$x"; say "real-wait $x"; hs; state h; done
rm -rf "$h/.factory/guard"; full "$all"; say finished; hs; state h
commit "$h" later; say finished-later; hs
sed 's/^Status: closed/Status: open/' "$h/.factory/run.md" > "$h/n" && mv "$h/n" "$h/.factory/run.md"; say reopened; hs
sed 's/^Status: open/Status: closed/' "$h/.factory/run.md" > "$h/n" && mv "$h/n" "$h/.factory/run.md"; say reclosed; hs
printf '# Run: x\nStatus: closed\nNext: none (closed)\nWaiting: none\n\n## 0 Ticket ✔\n' > "$h/.factory/run.md"; rm -rf "$h/.factory/guard"; say closed-unproven; hs
printf '# Run: x\nStatus: open\nNext: 5 Build · get-ready-to-code\nWaiting: none\n\n## 3 Plan ✔\n' > "$h/.factory/run.md"; rm -rf "$h/.factory/guard"; say skipped-early; hs
rm -rf "$h/.factory/guard"; full '0 1 2 2b 3 4 6 7 8'; say skipped-5; hs
sed 's/^Waiting: none/Waiting: owner: q/' "$h/.factory/run.md" > "$h/n" && mv "$h/n" "$h/.factory/run.md"; say skipped-wait; hs; say skipped-wait-active; hs true; say skipped-wait-again; hs; state h
rm -rf "$h/.factory/guard"; full "$all"; awk 'BEGIN { for (i = 0; i < 31; i++) printf "ten chars "; print "" }' >> "$h/.factory/run.md"; say wall; hs
L=$(awk 'BEGIN { for (i = 0; i < 31; i++) printf "ten chars " }')
hd 'Waiting: none'; printf '| %s |\n' "$L" >> "$h/.factory/run.md"; say long-table; hs
hd 'Waiting: none'; printf '%s\n%s\n%s\n' '```' "$L" '```' >> "$h/.factory/run.md"; say long-fence; hs
hd 'Waiting: none'; printf '%s\n%s\n' '```' "$L" >> "$h/.factory/run.md"; say long-open-fence; hs
hd 'Waiting: none'; printf '  %s\n  %s\n  %s\n' '```' "$L" '```' >> "$h/.factory/run.md"; say long-indented-fence; hs
hd 'Waiting: none'; printf '%s\n%s\n%s\n%s\n' '```' "$L" '```' '```' >> "$h/.factory/run.md"; say long-later-fence; hs
hd 'Waiting: none'; hs >/dev/null; printf '## 0 Ticket ✔\n## 1 Analyze ✔\n## 2 Recommend ✔\n%s\n' "$L" >> "$h/.factory/run.md"; say long-batched; hs
hd 'Waiting: none'; awk 'BEGIN { for (i = 0; i < 110; i++) printf "█"; print "" }' >> "$h/.factory/run.md"; say long-utf8; hs
rm -rf "$h/.factory/guard"; git -C "$h" remote add origin "$h/none.git"; full "$all"; say unpushed; hs
hs >/dev/null; git -C "$h" remote remove origin; say remote-removed; hs; state h

# Rounds: a new run in a session that already failed a gate starts at zero; an old run keeps its rounds;
# deleting state lifts no halt.
n=$W/n; mkdir -p "$n/r/.factory" "$n/p/x/s/subagents"; git init -q "$n/r"; printf '{}\n' > "$n/p/x/s.jsonl"
for i in 1 2 3; do { printf '{"message":"Role: checker. Gate B"}\n'; printf '{"message":{"role":"assistant","content":[{"type":"text","text":"Gate B: FAIL 1 missing"}]}}\n'; } > "$n/p/x/s/subagents/agent-c$i.jsonl"; touch -t "202301010000.0$i" "$n/p/x/s/subagents/agent-c$i.jsonl"; done
printf '# Run: x\nStatus: open\nNext: 1 Analyze · analyze-start\nWaiting: none\n' > "$n/r/.factory/run.md"
ns() { printf '{"session_id":"s","transcript_path":"%s/p/x/s.jsonl","cwd":"%s","last_assistant_message":"x"}' "$n" "$n/r" | $G stop; }
say new-run; ns
nf() { { printf '# Run: x\nStatus: open\nNext: 7 PR · how-to-make-a-pr\nWaiting: none\n\n'; for s in '0 Ticket' '1 Analyze' '2 Recommend' '2b Challenge' '3 Plan' '4 Before' '5 Build' '6 Verify'; do printf '## %s ✔\n' "$s"; done; } > "$n/r/.factory/run.md"; }
rm -rf "$n/r/.factory/guard"; nf; ns >/dev/null; printf '# Run: y\nStatus: open\nNext: 1 Analyze · analyze-start\nWaiting: none\n\n## 0 Ticket ✔\nx\n' > "$n/r/.factory/run.md"; say used-checkout; ns
rm -rf "$n/r/.factory/guard"; nf; ns >/dev/null; say by-cap; ns; state n/r
for i in 4 5; do cp "$n/p/x/s/subagents/agent-c1.jsonl" "$n/p/x/s/subagents/agent-c$i.jsonl"; touch -t "202301010000.0$i" "$n/p/x/s/subagents/agent-c$i.jsonl"; done
rm -rf "$n/r/.factory/guard"; nf; ns >/dev/null; ns >/dev/null; rm -rf "$n/r/.factory/guard"; ns >/dev/null; say halt-kept; ns; state n/r
say clear; (cd "$n/r" && $G clear); state n/r
say after-clear; ns; state n/r
# Compaction: the place re-injected, counted per session, relay due after two.
say compact-1; printf '{"session_id":"s","transcript_path":"%s/p/x/s.jsonl","cwd":"%s","source":"compact"}' "$n" "$n/r" | $G compact
say compact-2; printf '{"session_id":"s","transcript_path":"%s/p/x/s.jsonl","cwd":"%s","source":"compact"}' "$n" "$n/r" | $G compact
say resume; printf '{"session_id":"s","transcript_path":"%s/p/x/s.jsonl","cwd":"%s","source":"resume"}' "$n" "$n/r" | $G compact
say relay; ns; state n/r
say relayed; ns
# Jobs waits: a deadline is required; a new job text starts a new one.
j=$W/j; mkdir -p "$j/.factory"; git init -q "$j"
printf '# Run: x\nStatus: open\nNext: 5 Build · get-ready-to-code\nWaiting: jobs: suite\n\n## 0 Ticket ✔\n' > "$j/.factory/run.md"
jb() { printf '{"session_id":"sj","cwd":"%s","last_assistant_message":"x"}' "$j" | $G stop; }
say jobs-no-max; jb; state j
sed 's/^Waiting: .*/Waiting: jobs: suite (max 0 min)/' "$j/.factory/run.md" > "$j/n" && mv "$j/n" "$j/.factory/run.md"; say jobs-zero; jb
sed 's/^Waiting: .*/Waiting: jobs: suite (max 5 min)/' "$j/.factory/run.md" > "$j/n" && mv "$j/n" "$j/.factory/run.md"; say jobs-five; jb; state j
say jobs-subagent; printf '{"session_id":"sj","cwd":"%s","last_assistant_message":"x","background_tasks":[{"type":"subagent"}]}' "$j" | $G stop
# State edited by hand halts; an old field form passes.
printf "g_ticks='1'\ng_new='x'\n" > "$j/.factory/guard/state"; say edited; jb; state j
