#!/bin/sh
# Update check at session start: reads a cached latest version (no network, few forks), refreshes it in the background each start.
# Prints one context line when a newer factory release exists, and the leftovers doctor.sh finds. FACTORY_NO_UPDATE_CHECK=1 turns both off.
[ -n "$FACTORY_NO_UPDATE_CHECK" ] && exit 0
# Leftovers of old versions and copies (doctor.sh, read-only here): one notice, never a stop.
o=$(set -- ${1:+"$1"}; . "${0%/*}/doctor.sh" 2>/dev/null) || [ -z "$o" ] || printf 'Factory leftovers on this machine:\n%s\nTell the owner in one line and offer what each line says, owner'"'"'s OK first (`sh "%s/doctor.sh" --fix` moves leftovers to a backup). Never stop or wait for it.\n' "$o" "${0%/*}"
m="${1:-${0%/*}/../../..}/.claude-plugin/plugin.json"; have=  # $1: plugin root
[ -f "$m" ] || exit 0  # a skills-only copy has no manifest: nothing to compare
while IFS= read -r l; do case $l in *'"version"'*) have=${l#*'"version"'*\"}; have=${have%%\"*}; break;; esac; done < "$m"
[ -n "$have" ] || exit 0
c="${XDG_CACHE_HOME:-$HOME/.cache}/ai-software-factory"; f="$c/latest"; slug=seifsg/ai-software-factory
# Every start: refresh in the background from the release marked Latest (deprecated tags stay), never wait on it; curl when gh
# is absent, signed out or hangs (killed after 20 s, like curl -m 20). Written only on success (own tmp, atomic mv), so a failed
# fetch retries next start; a tmp a killed fetch left is swept after a minute. One detached subshell owns all output: hook pipes close.
( mkdir -p "$c" && t="$f.$$" || exit; find "$c" -name 'latest.?*' -mmin +1 -exec rm -f {} +
  gh api "repos/$slug/releases/latest" --jq .tag_name > "$t" & p=$!; { sleep 20; kill $p; } & w=$!
  wait $p; r=$?; kill $w 2>/dev/null  # its sleep may outlive it by up to 20 s: harmless, no output
  [ $r = 0 ] && [ -s "$t" ] || curl -fsm 20 "https://api.github.com/repos/$slug/releases/latest" | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' > "$t"
  v=$(sed -n 's/^v//p' "$t"); [ -n "$v" ] && echo "$v" > "$t" && mv "$t" "$f" || rm -f "$t" ) </dev/null >/dev/null 2>&1 &
new=; [ -s "$f" ] && read -r new < "$f"
for v in "$have" "$new"; do case $v in [0-9]*.[0-9]*.[0-9]*) ;; *) exit 0;; esac; case $v in *[!0-9.]*) exit 0;; esac; done  # only plain x.y.z
[ -n "$new" ] && [ "$new" != "$have" ] || exit 0
# Newer only: compare major, minor, patch as numbers.
IFS=. read -r a b d <<EOF
$have
EOF
IFS=. read -r x y z <<EOF
$new
EOF
[ "$x" -gt "$a" ] || { [ "$x" -eq "$a" ] && { [ "$y" -gt "$b" ] || { [ "$y" -eq "$b" ] && [ "${z%%[!0-9]*}" -gt "${d%%[!0-9]*}" ]; }; }; } 2>/dev/null || exit 0
printf 'AI Software Factory %s is out (installed %s). Before any factory run, tell the owner and ask: update now or continue? What is new: https://github.com/%s/releases/tag/v%s. Update: Claude Code `claude plugin update safe-factory@ai-software-factory`, Codex `codex plugin marketplace upgrade ai-software-factory` (clone timed out: `codex plugin marketplace remove ai-software-factory`, `codex plugin marketplace add https://github.com/%s.git --sparse .claude-plugin --sparse .agents`, `codex plugin add safe-factory@ai-software-factory`, then trust the hooks in `/hooks`), Cursor: Marketplace installs update by themselves; team imports once an admin enables Auto Refresh; a GitHub install has no proven update path, see docs/install.md. Then start a new session.\n' "$new" "$have" "$slug" "$new" "$slug"
