#!/bin/sh
# Stop guard: keeps an open factory run going until step 8 is ticked and gates A, B and C pass.
# Reads only .factory/run.md in the project, so sessions without a run exit at once.
# Prints Claude Code / Codex Stop JSON: a block with the next step, or nothing to let the stop through.
run="${CLAUDE_PROJECT_DIR:-$PWD}/.factory/run.md"
[ -f "$run" ] || exit 0
grep -q '^Status: stopped' "$run" && exit 0
grep -q '^Waiting: none' "$run" || exit 0  # waiting on the owner or background jobs: stopping is right
gates=$(grep -o '^Gate [ABC]: PASS' "$run" | sort -u | wc -l)
grep -q '^## 8 Review ✔' "$run" && [ "$gates" -eq 3 ] && exit 0
# Loop guard: a second stop with no run-file change since the last nudge goes through.
nudge="${run%.md}.nudge"
case $(cat) in
  *'"stop_hook_active":true'* | *'"stop_hook_active": true'*)
    if [ -f "$nudge" ] && [ ! "$run" -nt "$nudge" ]; then
      printf '{"systemMessage":"Factory run idle since the last nudge; stopping. See .factory/run.md."}\n'
      exit 0
    fi ;;
esac
: > "$nudge"
next=$(sed -n 's/^Next: *//p' "$run" | head -n 1 | tr -d '"\\')
printf '{"decision":"block","reason":"Factory run open (.factory/run.md). Next: %s. Load that skill fresh, finish the step and write its block. Ending on purpose? Set Waiting: owner: <question> or Waiting: jobs: <what runs>."}\n' "${next:-read the run file}"
