#!/bin/sh
# Repository checks (AGENTS.md "Keep it working"), one command from the repo root: sh scripts/check.sh [<ref>] [<base>]
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
[ "$ref" = bytes ] && { bytes "${2:-HEAD}"; exit; }
git rev-parse -q --verify "$ref^{commit}" >/dev/null || { echo "FAIL: unknown ref $ref"; exit 1; }

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
for f in .agents/.codex-plugin/plugin.json .agents/.cursor-plugin/plugin.json .claude-plugin/marketplace.json; do
  blob "$f" | grep -qF "\"${v:?}\"" || blob "$f" | grep -qF "\"v$v\"" || fail "$f disagrees with version $v"
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
exit $bad
