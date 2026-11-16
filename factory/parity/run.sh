#!/bin/sh
# Parity harness: the sh guard and the factory binary on the same inputs, byte for byte.
#   sh factory/parity/run.sh <factory binary>
# Runs cases.sh (check.sh's guard scenarios) and corpus.sh (recorded runs r1-r4, stripped) once per side,
# each side in its own temp folder, then diffs every reply and state file. Prints one summary line;
# exit 0 with 0 diffs, else the diff and exit 1. Only the program's own path in halt replies is normalized.
set -u
bin=${1:?usage: sh factory/parity/run.sh <factory binary>}
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
sg=$repo/.agents/skills/safe-factory/scripts/run-guard.sh
[ -f "$bin" ] || { echo "parity: no binary at $bin"; exit 1; }
bin=$(cd "$(dirname "$bin")" && pwd)/$(basename "$bin")  # absolute: the cases change folders
w=$(mktemp -d) || exit 1
trap 'rm -rf "$w"' EXIT
# The path form the agent's tools read: C:/x on Windows, as both guards print it.
native() { if command -v cygpath >/dev/null; then cygpath -m "$1"; else printf '%s' "$1"; fi; }
for side in sh bin; do
  mkdir -p "$w/$side"
  if [ "$side" = sh ]; then g="sh $sg"; else g="$bin guard"; fi
  for part in cases corpus tools; do
    W=$(native "$w/$side/$part") G=$g BIN=$bin SIDE=$side sh "$here/$part.sh" > "$w/$side.$part" 2>&1
  done
done
# Replies name the run folder (each side has its own) and the program the owner runs next: after a halt
# (`clear`) and for leftovers (`doctor --fix`). A doctor backup folder is named for the clock. On Windows the
# temp folder has a short (8.3) and a long spelling, and either guard may print either.
long=$w; command -v cygpath >/dev/null && long=$(cygpath -m -l "$w")
norm() {
  sed -e "s#$(native "$w")/[a-z]*/#W/#g" -e "s#$long/[a-z]*/#W/#g" -e "s#$w/[a-z]*/#W/#g" \
    -e 's#resumes with: [^"]* clear #resumes with: CLEAR #' -e 's#resumes it: [^"]* clear #resumes it: CLEAR #' \
    -e 's#(`[^`]* --fix` moves#(`DOCTOR --fix` moves#' -e 's#/removed/[0-9-]*/#/removed/STAMP/#g' "$1"
}
bad=0 n=0
for part in cases corpus tools; do
  norm "$w/sh.$part" > "$w/a"; norm "$w/bin.$part" > "$w/b"
  n=$((n + $(grep -c '^== ' "$w/a")))
  if ! cmp -s "$w/a" "$w/b"; then
    diff "$w/a" "$w/b" | head -n 40
    bad=$((bad + $(diff "$w/a" "$w/b" | grep -c '^[<>]')))
  fi
done
echo "parity: $n cases, $bad diff lines"
[ "$bad" = 0 ]
