#!/bin/sh
# Repository checks (AGENTS.md "Keep it working"), one command from the repo root: sh scripts/check.sh [<ref>] [<base>]
# Static checks read the blobs of <ref>; the update-check and doctor checks run the working-tree scripts.
# sh scripts/check.sh bytes [<ref>] prints "<all methods> <read set>" for a PR's before and after line.
# Byte counts read Git blobs of <ref> (default HEAD); <base> also fails any method byte growth against it.
# Prints nothing and exits 0 when all pass; otherwise one FAIL line per failed check, exit 1.
ref=${1:-HEAD} base=$2 bad=0
cd "$(git rev-parse --show-toplevel)" || exit 1
w=$(mktemp -d) || exit 1; trap 'rm -rf "$w"' EXIT  # short POSIX temp path: a C:/ path would split PATH at its colon
fail() { echo "FAIL: $*"; bad=1; }
skills=.agents/skills
read_set='safe-factory/SKILL.md safe-factory/references/run-file.md safe-factory/references/checker.md safe-factory/references/sizes.md safe-factory/references/delegate.md safe-factory/references/owner-reports.md safe-factory/references/worth-it.md ticketing/SKILL.md ticketing/references/ticket-layout.md analyze-start/SKILL.md recommend/SKILL.md get-ready-to-code/SKILL.md how-to-make-a-pr/SKILL.md how-to-make-a-pr/references/media-proof.md how-to-make-a-pr/references/pr-layout.md how-to-make-a-pr/references/github.md how-to-make-a-pr/references/credit.md deep-review/SKILL.md deep-review/references/change-guard.md deep-review/references/compliance.md'

# Method bytes of a ref: "<all methods> <read set>".
bytes() {
  a=$(git ls-tree -rl "$1" $skills | awk '$5 ~ /\/(SKILL|references\/[^\/]+)\.md$/ {s += $4} END {print s + 0}')
  r=$(cd $skills && git ls-tree -l "$1" $read_set | awk '{s += $4} END {print s + 0}')
  echo "$a $r"
}
good() { git rev-parse -q --verify "$1^{commit}" >/dev/null || { echo "FAIL: unknown ref $1"; exit 1; }; }
[ "$ref" = bytes ] && { good "${2:-HEAD}"; bytes "${2:-HEAD}"; exit; }
good "$ref"; [ -z "$base" ] || good "$base"

# Skill hygiene: links stay inside a skill's folder, no SKILL.md at 17000 bytes, no media in Git (proof goes to refs/proof/).
o=$(git grep -nE '\]\(\.\./' "$ref" -- $skills) && fail "links out of a skill folder: $o"
o=$(git ls-tree -rl "$ref" $skills | awk '$5 ~ /\/SKILL\.md$/ && $4 >= 17000 {print $5}') && [ -n "$o" ] && fail "SKILL.md at 17000 bytes or over: $o"
o=$(git ls-tree -r --name-only "$ref" | grep -iE '\.(png|jpe?g|gif|webp|mp4|webm|mov)$') && fail "media committed (proof belongs in refs/proof/): $o"

# Budgets: all methods under 170000, read set under 105000; with <base>, neither grows.
set -- $(bytes "$ref")
[ "$1" -lt 170000 ] || fail "methods $1 bytes, budget 170000"
[ "$2" -lt 105000 ] || fail "read set $2 bytes, budget 105000"
if [ -n "$base" ]; then
  b=$(bytes "$base"); [ "$1" -le "${b% *}" ] || fail "methods grew: ${b% *} -> $1"; [ "$2" -le "${b#* }" ] || fail "read set grew: ${b#* } -> $2"
fi

# Every manifest agrees with the canonical version.
blob() { MSYS_NO_PATHCONV=1 git show "$ref:$1"; }  # <ref>:<path> as typed under Git Bash
v=$(blob .agents/.claude-plugin/plugin.json | grep -o '"version": "[^"]*"' | cut -d'"' -f4)
[ -n "$v" ] || fail "no version in .agents/.claude-plugin/plugin.json"
for f in .agents/.codex-plugin/plugin.json .agents/.cursor-plugin/plugin.json .claude-plugin/marketplace.json; do
  blob "$f" | grep -qF "\"$v\"" || blob "$f" | grep -qF "\"v$v\"" || fail "$f disagrees with version $v"
done

# Update check, offline: newer release tells the owner, older stays quiet; gh signed out still finds it through curl.
uc() { PATH="$1/b:$PATH" FACTORY_NO_UPDATE_CHECK= HOME="$1" CLAUDE_PROJECT_DIR="$1" XDG_CACHE_HOME="$1" sh $skills/safe-factory/scripts/update-check.sh .agents; }
bins() { mkdir -p "$1/b" "$1/ai-software-factory"; printf '#!/bin/sh\nexit 4\n' > "$1/b/gh"; printf '#!/bin/sh\n%s\n' "$2" > "$1/b/curl"; chmod +x "$1/b/gh" "$1/b/curl"; }
bins "$w/u" 'exit 4'
for c in 9.9.9:out 0.0.1:quiet; do
  echo "${c%:*}" > "$w/u/ai-software-factory/latest"; o=$(uc "$w/u")
  case "${c#*:}:$o" in out:*"is out"*|quiet:) ;; *) fail "update check wrong for ${c%:*}";; esac
done
bins "$w/c" 'echo "  \"tag_name\": \"v9.9.9\","'; uc "$w/c"
for i in 1 2 3 4 5; do [ -s "$w/c/ai-software-factory/latest" ] && break; sleep 1; done
grep -qx 9.9.9 "$w/c/ai-software-factory/latest" 2>/dev/null || fail "update check: no curl fallback"

# Doctor: a file holding only old hooks moves; a mixed or other-settings file stays.
h=$w/d; mkdir -p "$h/.codex" "$h/.cursor" "$h/p/.claude"
printf '{\n  "hooks": {\n    "Stop": [{"hooks": [{"command": "sh x/run-gate.sh"}]}]\n  }\n}\n' > "$h/.codex/hooks.json"
printf '{\n  "hooks": {\n    "stop": [{"command": "sh x/run-gate.sh"}, {"command": "sh x/skills/safe-factory/scripts/run-guard.sh"}]\n  }\n}\n' > "$h/.cursor/hooks.json"
printf '{\n\t"permissions": {},\n\t"hooks": {"Stop": [{"hooks": [{"command": "sh x/run-gate.sh"}]}]}\n}\n' > "$h/p/.claude/settings.json"
dr() { HOME="$h" CLAUDE_PROJECT_DIR="$h/p" XDG_CACHE_HOME="$h" sh $skills/safe-factory/scripts/doctor.sh "$@" >/dev/null; }
dr && fail "doctor missed a leftover"
dr --fix; [ -f "$h/.codex/hooks.json" ] && fail "doctor --fix left the old hook"
[ -f "$h/.cursor/hooks.json" ] && [ -f "$h/p/.claude/settings.json" ] || fail "doctor --fix moved a file holding more than old hooks"

# Guard wiring: Stop lives in the skill on Claude Code; the portable file serves the other hosts.
blob .agents/hooks/hooks.json | grep -q '"Stop"' && fail "Stop hook in hooks.json: every Claude Code session would run it"
blob .agents/hooks/portable.json | grep -q '"Stop"' || fail "no Stop hook in portable.json"
for m in codex cursor; do blob ".agents/.$m-plugin/plugin.json" | grep -qF hooks/portable.json || fail "$m manifest does not name hooks/portable.json"; done
blob $skills/safe-factory/SKILL.md | sed -n '2,/^---/p' | grep -q 'run-guard.sh" stop' || fail "no Stop hook in safe-factory's frontmatter"

# Session binding: a step block binds a run in another repository; a plain session stays quiet.
b=$w/g; mkdir -p "$b/a/.git" "$b/b/.factory"; printf '# Run: x · fast · change\nStatus: open\nNext: 3 Plan · get-ready-to-code\nWaiting: none\n\n## 0 Ticket ✔\n' > "$b/b/.factory/run.md"
gd() { printf '{"session_id":"%s","cwd":"%s","last_assistant_message":"%s"}' "$1" "$b/a" "$2" | HOME="$b" XDG_CACHE_HOME="$b" sh $skills/safe-factory/scripts/run-guard.sh stop; }
[ -z "$(gd plain 'hello')" ] && [ -z "$(gd plain '## 1 Overview')" ] || fail "guard spoke to a plain session"
p=$b/b; command -v cygpath >/dev/null && p=$(cygpath -w "$p" | sed 's/\\/\\\\/g')  # Windows: the path as JSON carries it
case $(gd s1 "## 0 Ticket\\n- **Workspace:** \`$p\`") in *'"decision":"block"'*) ;; *) fail "guard did not bind a run in another repository" ;; esac
[ -f "$b/b/.factory/guard/state" ] || fail "no guard state in the bound run's folder"
[ -f "$b/ai-software-factory/sessions/s1" ] || fail "no session file for the bound session"
case $(gd s2 '## 1 Analyze') in *'no run file found'*) ;; *) fail "a step block with no run did not ask" ;; esac
case $(gd s1 "## 1 Analyze **Workspace:** \`/nope\`") in *'no run file found'*) ;; *) fail "a bound session with a bad Workspace did not ask" ;; esac
case $(printf '{"session_id":"s3","cwd":"%s","last_assistant_message":"## 1 Analyze **Workspace:** `/nope`"}' "$b/b" | HOME="$b" XDG_CACHE_HOME="$b" sh $skills/safe-factory/scripts/run-guard.sh stop) in *'no run file found'*) fail "an own-folder run with a bad Workspace was not driven" ;; esac
sg=$PWD/$skills/safe-factory/scripts/run-guard.sh
mkdir "$b/none"; (cd "$b/none" && sh "$sg" clear) 2>/dev/null && fail "clear with no run passed silently"
[ "$(grep -c 'clear %s' "$sg")" -ge 2 ] || fail "a halt reply does not name the run's folder for clear"

# A moved run keeps its proof: session A proved Gate A in one project folder, session F drives it from another.
e=$w/e; mkdir -p "$e/p/-home-x-A/sA/subagents" "$e/p/-home-x-F" "$e/r/.factory"; git init -q "$e/r"; git -C "$e/r" -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q --allow-empty -m i; sha=$(git -C "$e/r" rev-parse HEAD)
{ printf '{"message":"Role: checker. Gate A"}\n'; printf '{"message":{"role":"assistant","content":[{"type":"text","text":"Gate A: PASS @%s"}]}}\n' "$sha"; } > "$e/p/-home-x-A/sA/subagents/agent-chk.jsonl"
{ printf '# Run: x · fast · change\nStatus: open\nNext: 4 Before · how-to-make-a-pr\nWaiting: none\n\n'; for h in '0 Ticket' '1 Analyze' '2 Recommend' '2b Challenge' '3 Plan'; do printf '## %s ✔\nx\n' "$h"; done; printf 'Gate A: PASS (checker chk) @%s\n' "$sha"; } > "$e/r/.factory/run.md"
for h in '0 Ticket' '1 Analyze' '2 Recommend' '2b Challenge' '3 Plan'; do printf '{"isSidechain":false,"message":{"role":"assistant","content":[{"type":"text","text":"## %s x"}]}}\n' "$h"; done > "$e/p/-home-x-A/sA.jsonl"
printf '{"isSidechain":false}\n' > "$e/p/-home-x-F/sF.jsonl"
ge() { printf '{"session_id":"%s","transcript_path":"%s","cwd":"%s","last_assistant_message":"x"}' "$1" "$e/p/$2/$1.jsonl" "$e/r" | HOME="$e" XDG_CACHE_HOME="$e" sh "$sg" stop; }
ge sA -home-x-A >/dev/null
case $(ge sF -home-x-F) in *'Gate A has not'* | *'not posted'*) fail "a run moved to a session in another project folder lost its proof" ;; esac

# Stop rules: only a real wait stops a run; a finish holds once seen; no remote passes; a skipped step or a wall of text never finishes.
h=$w/h; mkdir -p "$h/.factory"; git init -q "$h"; git -C "$h" -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q --allow-empty -m i; a=$w/hp/-home-x-H/sH/subagents; mkdir -p "$a"
hs() { printf '{"session_id":"sH","transcript_path":"%s","cwd":"%s","last_assistant_message":"x"}' "$w/hp/-home-x-H/sH.jsonl" "$h" | HOME="$h" XDG_CACHE_HOME="$h" sh "$sg" stop; }
hd() { rm -rf "$h/.factory/guard"; printf '# Run: x\nStatus: open\nNext: 1 Analyze · analyze-start\n%s\n' "$1" > "$h/.factory/run.md"; }
# A run file with these steps ticked and every gate proven on HEAD.
full() {
  sha=$(git -C "$h" rev-parse HEAD)
  for g in A B C; do { printf '{"message":"Role: checker. Gate %s"}\n' $g; printf '{"message":{"role":"assistant","content":[{"type":"text","text":"Gate %s: PASS @%s"}]}}\n' $g "$sha"; } > "$a/agent-c$g.jsonl"; done
  { printf '{"message":"Role: reviewer."}\n'; printf '{"message":{"role":"assistant","content":[{"type":"text","text":"verdict: ready @%s"}]}}\n' "$sha"; } > "$a/agent-r.jsonl"
  { printf '# Run: x\nStatus: closed\nNext: none (closed)\nWaiting: none\n\n'; for s in '0 Ticket' '1 Analyze' '2 Recommend' '2b Challenge' '3 Plan' '4 Before' '5 Build' '6 Verify' '7 PR' '8 Review'; do case " $1 " in *" ${s%% *} "*) printf '## %s ✔\n' "$s" ;; *) printf '## %s\n' "$s" ;; esac; done
    printf 'Gate A: PASS (checker cA) @%s\nGate B: PASS (checker cB) @%s\nReview: ready (reviewer r) @%s\nGate C: PASS (checker cC) @%s\n' "$sha" "$sha" "$sha" "$sha"; } > "$h/.factory/run.md"
}
all='0 1 2 2b 3 4 5 6 7 8'
for x in '**Waiting:** none' '- Waiting: none' ''; do hd "$x"; case $(hs) in *'"decision":"block"'*'Waiting: none'*) ;; *) fail "a Waiting line reading '$x' let the agent stop" ;; esac; done
for x in 'Waiting: owner: q' 'Waiting: jobs: x (max 9 min)'; do hd "$x"; [ -z "$(hs)" ] || fail "'$x' did not end the turn"; done
rm -rf "$h/.factory/guard"; full "$all"; [ -z "$(hs)" ] || fail "a proven run with no remote did not finish"
git -C "$h" -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q --allow-empty -m later; [ -z "$(hs)" ] || fail "a finished closed run was asked again after its checkout moved on"
printf '# Run: x\nStatus: closed\nNext: none (closed)\nWaiting: none\n\n## 0 Ticket ✔\n' > "$h/.factory/run.md"; [ -n "$(hs)" ] || fail "a closed run with no gates in a used checkout passed"
rm -rf "$h/.factory/guard"; full '0 1 2 2b 3 4 6 7 8'; case $(hs) in *'Steps not ticked: 5'*) ;; *) fail "a skipped step was not named" ;; esac
sed 's/^Waiting: none/Waiting: owner: q/' "$h/.factory/run.md" > "$h/n" && mv "$h/n" "$h/.factory/run.md"; case $(hs) in *'Steps not ticked: 5'*) ;; *) fail "a wait hid a skipped step" ;; esac
rm -rf "$h/.factory/guard"; full "$all"; awk 'BEGIN { for (i = 0; i < 31; i++) printf "ten chars "; print "" }' >> "$h/.factory/run.md"; case $(hs) in *'over 300 characters'*) ;; *) fail "a wall of text passed" ;; esac
rm -rf "$h/.factory/guard"; git -C "$h" remote add origin "$h/none.git"; full "$all"; [ -n "$(hs)" ] || fail "an unpushed head with a remote passed Gate C"
if command -v cygpath >/dev/null; then case $(hs) in *'factory run in /'*) fail "a prompt named a Git Bash path" ;; esac; fi
exit $bad
