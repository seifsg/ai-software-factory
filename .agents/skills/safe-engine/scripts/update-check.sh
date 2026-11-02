#!/bin/sh
# Update check at session start: reads a cached latest version (no network, few forks), refreshes it in the background once a day.
# Prints one context line when a newer factory release exists. FACTORY_NO_UPDATE_CHECK=1 turns it off.
[ -n "$FACTORY_NO_UPDATE_CHECK" ] && exit 0
m="${1:-${0%/*}/../../..}/.claude-plugin/plugin.json"; have=  # $1: plugin root
[ -f "$m" ] || exit 0  # a skills-only copy has no manifest: nothing to compare
while IFS= read -r l; do case $l in *'"version"'*) have=${l#*: \"}; have=${have%%\"*}; break;; esac; done < "$m"
[ -n "$have" ] || exit 0
c="${XDG_CACHE_HOME:-$HOME/.cache}/ai-software-factory"; f="$c/latest"; slug=seifsg/ai-software-factory
# Stale or missing: refresh in the background from the release marked Latest (deprecated tags stay), never wait on it.
[ -n "$(find "$f" -mmin -1440 2>/dev/null)" ] || { mkdir -p "$c" && touch "$f" && ( gh api "repos/$slug/releases/latest" --jq .tag_name 2>/dev/null \
  | sed -n 's/^v//p' > "$f.tmp" && [ -s "$f.tmp" ] && mv "$f.tmp" "$f" ) >/dev/null 2>&1 & }
new=; [ -s "$f" ] && read -r new < "$f"
case $have$new in *[!0-9.]*) exit 0;; esac  # only plain x.y.z versions
[ -n "$new" ] && [ "$new" != "$have" ] || exit 0
# Newer only: compare major, minor, patch as numbers.
IFS=. read -r a b d <<EOF
$have
EOF
IFS=. read -r x y z <<EOF
$new
EOF
[ "$x" -gt "$a" ] || { [ "$x" -eq "$a" ] && { [ "$y" -gt "$b" ] || { [ "$y" -eq "$b" ] && [ "${z%%[!0-9]*}" -gt "${d%%[!0-9]*}" ]; }; }; } 2>/dev/null || exit 0
printf 'AI Software Factory %s is out (installed %s). Before any factory run, tell the owner and ask: update now or continue? What is new: https://github.com/%s/releases/tag/v%s. Update: Claude Code `claude plugin update safe-engine@ai-software-factory`, Codex `codex plugin marketplace upgrade ai-software-factory`, Cursor: Customize, Plugins, update. Then start a new session.\n' "$new" "$have" "$slug" "$new"
