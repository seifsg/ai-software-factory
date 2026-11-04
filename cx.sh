#!/bin/sh
# P5: real Codex update path, temp home, real repository. Old install pinned to v0.5.0, then unpinned. sh cx.sh <codex> > out.
X=$1; U=https://github.com/seifsg/ai-software-factory.git; d=$(mktemp -d); export CODEX_HOME="$(cygpath -m "$d" 2>/dev/null || echo "$d")"
q() { "$X" "$@" 2>&1 | grep -v WARNING; }
ver() { q plugin list | grep -E '^safe-factory@' | sed 's/  */ /g' | cut -c1-70; echo "cache: $(ls "$d/plugins/cache/ai-software-factory/safe-factory/" 2>/dev/null | tr '\n' ' ')"; }
q plugin marketplace add "$U" --ref v0.5.0 --sparse .claude-plugin --sparse .agents | tail -1 | sed 's/.*marketplaces/marketplaces/'
q plugin add safe-factory@ai-software-factory | tail -1 | sed 's/.*cache/cache/'
echo '--- installed from the old tag'; ver
grep -n 'ref\b\|ref =' "$d/config.toml" | head -3
sed 's/^ref = .*//' "$d/config.toml" > "$d/c" && mv "$d/c" "$d/config.toml"
echo '--- codex plugin marketplace upgrade'; q plugin marketplace upgrade ai-software-factory | tail -1 | cut -c1-90; ver
echo '--- codex plugin add again'; q plugin add safe-factory@ai-software-factory | tail -1 | sed 's/.*cache/cache/'; ver
