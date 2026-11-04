#!/bin/sh
# Live Claude Code proofs for #285. sh lv.sh <.agents dir> <out dir> <before|after>. The installed plugin is off; temp repos only.
A=$1 out=$2 lab=$3; C=${CLAUDE_CLI:-claude}
d=$(mktemp -d); printf '{"enabledPlugins":{"safe-factory@ai-software-factory":false}}' > "$d/off.json"
repo() { git init -q "$1"; git -C "$1" -c user.name=t -c user.email=t@t commit -q --allow-empty -m i; }
run() { mkdir -p "$1/.factory"; printf '# Run: x · fast · product\nStatus: open\nNext: 3 Plan · get-ready-to-code\nWaiting: %s\n\n## 0 Ticket ✔\n' "${2:-none}" > "$1/.factory/run.md"; }
cl() { "$C" --plugin-dir "$A" --settings "$d/off.json" --model claude-haiku-5-5 "$@"; }
sid() { grep -oE '"session_id":"[^"]*"' "$1" | head -1 | sed 's/.*:"//;s/"//'; }
tr_of() { ls ~/.claude/projects/*/"$1".jsonl 2>/dev/null | head -1; }
# Guard firings in a transcript, and what it said.
fired() { grep -h stop_hook_summary "$1" | grep -c run-guard; }
ms() { grep -h stop_hook_summary "$1" | grep run-guard | grep -oE '"durationMs":[0-9]+' | cut -d: -f2 | tr '\n' ' '; }
said() { grep -c 'factory run in' "$1"; }
ask="/safe-factory:safe-factory This is a hook test, no real work. Use no tools. Reply with only this text, then stop:"

repo "$d/plain"; cd "$d/plain" || exit 1
"$C" --version | head -1 > "$out/$lab-version.txt"
cl -p "say hi" --output-format json </dev/null > "$d/o" 2>&1; s=$(sid "$d/o"); t=$(tr_of "$s")
{ echo "P8 plain session, plugin installed"; echo "stop hook summaries: $(grep -c stop_hook_summary "$t"); guard processes: $(fired "$t"); durationMs: $(ms "$t")"; } > "$out/$lab-P8.txt"

repo "$d/a"; repo "$d/b"; run "$d/b"; cd "$d/a" || exit 1
b=$(cygpath -m "$d/b")
cl -p "$ask ## 0 Ticket
- **Workspace:** \`$b\`, branch x" --max-turns 2 --output-format json </dev/null > "$d/o" 2>&1; s=$(sid "$d/o"); t=$(tr_of "$s")
{ echo "P1 live: session in repo A, run in repo B"; echo "guard state in B: $([ -f "$d/b/.factory/guard/state" ] && echo yes || echo no); guard processes: $(fired "$t"); guard prompts: $(said "$t")"; grep -oE 'factory run in [^:]{0,120}' "$t" | sed "s#$b#<B>#" | head -1; } > "$out/$lab-P1-live.txt"

rm -rf "$d/b/.factory/guard"; run "$d/b" 'jobs: test (max 600 min)'
msg() { printf '{"type":"user","message":{"role":"user","content":"%s"}}\n' "$1"; }
{ msg "$ask ## 0 Ticket\\n- **Workspace:** \`$b\`, branch x"; sleep 20; msg "Write three sentences about git."; sleep 12; msg "/compact"; sleep 45; msg "say four"; sleep 15; } | cl -p --input-format stream-json --output-format stream-json --verbose > "$d/s" 2>&1
s=$(sid "$d/s"); t=$(tr_of "$s"); c=$(grep -c compact_boundary "$d/s")
{ echo "P4 later turn and real compaction, run in repo B"; echo "compact_boundary events: $c; guard state in B: $([ -f "$d/b/.factory/guard/state" ] && echo yes || echo no)"; node -e 'let seen=0,a=0,b=0;for(const l of require("fs").readFileSync(process.argv[1],"utf8").split("\n")){if(!l)continue;let e;try{e=JSON.parse(l)}catch{continue};if(e.subtype==="compact_boundary")seen=1;if(e.subtype==="stop_hook_summary"&&JSON.stringify(e.hookInfos||[]).includes("run-guard")){seen?a++:b++}}console.log("guard firings before compaction: "+b+"; after: "+a)' "$(cygpath -w "$t")"; } > "$out/$lab-P4.txt"

cl -p "say five" -r "$s" --output-format json </dev/null > "$d/o" 2>&1; t=$(tr_of "$s")
{ echo "P5 process resume of that session, id kept: $([ "$(sid "$d/o")" = "$s" ] && echo yes || echo no)"; echo "SessionStart context names the run: $(grep -c 'Factory run open' "$t")"; grep -oE 'Factory run open[^"]{0,200}' "$t" | tail -1 | sed "s#$b#<B>#"; grep -oE 'Load `safe-factory`[^"\\]{0,80}' "$t" | tail -1; f0=$(fired "$t"); cl -p "$ask ok" -r "$s" --max-turns 2 --output-format json </dev/null > "$d/o" 2>&1; echo "guard firings before reload: $f0; after loading safe-factory in the resumed process: $(fired "$t")"; } > "$out/$lab-P5.txt"

rm -rf "$d/b/.factory/guard"; run "$d/own"; cd "$d/own" 2>/dev/null || { repo "$d/own"; run "$d/own"; cd "$d/own"; }
"$C" -p "$ask ## 0 Ticket" --plugin-dir "$A" --permission-mode dontAsk --settings "$A/hooks/claude-settings.json" --settings "$d/off.json" --model claude-haiku-5-5 --max-turns 2 --output-format json </dev/null > "$d/o" 2>&1; s=$(sid "$d/o"); t=$(tr_of "$s")
{ echo "P9 night-style start: dontAsk, template allow list"; echo "guard processes: $(fired "$t"); guard prompts: $(said "$t"); denied tools: $(grep -oE '"tool_name":"[^"]*"' "$d/o" | sort | uniq -c | tr -s ' ' | tr '\n' ';'); Skill denied: $(grep -c '"tool_name":"Skill"' "$d/o")"; cl -p "The factory watchdog found this run stalled. Read .factory/run.md and continue its Next step. This is a test: use no tools, say ok." -r "$s" --permission-mode dontAsk --max-turns 1 --output-format json </dev/null > "$d/o2" 2>&1; echo "watchdog resume, SessionStart names the run: $(grep -c 'Factory run open' "$t")"; } > "$out/$lab-P9.txt"
cd /; for p in ~/.claude/projects/*tmp-*; do rm -rf "$p"; done; rm -rf "$d" 2>/dev/null; echo lv done
