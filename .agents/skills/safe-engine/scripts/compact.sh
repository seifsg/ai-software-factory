#!/bin/sh
# Compact hook: after context compaction or a resume, re-injects an open factory run's place,
# because compaction drops skill text. Plain stdout becomes context in Claude Code and Codex.
run="${CLAUDE_PROJECT_DIR:-$PWD}/.factory/run.md"
[ -f "$run" ] || exit 0
grep -q '^Status: open' "$run" || exit 0
sed -n '1,4p' "$run"
echo "Factory run open. Read .factory/run.md, load the Next: skill fresh, then continue that step."
