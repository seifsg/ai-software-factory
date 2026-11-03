#!/bin/sh
# Release in two commands (docs/releasing.md). Humans run it; it never moves a tag or re-publishes a version.
#   sh scripts/release.sh prepare X.Y.Z   branch from origin/main, bump, move CHANGELOG and UPGRADING, check, open the release PR
#   sh scripts/release.sh publish X.Y.Z   after the owner merged that PR: tag its merge commit, push the tag, publish as Latest
cmd=$1 v=$2
die() { echo "release: $*" >&2; exit 1; }
case $cmd:$v in prepare:[0-9]*.[0-9]*.[0-9]* | publish:[0-9]*.[0-9]*.[0-9]*) ;; *) die "usage: sh scripts/release.sh prepare|publish X.Y.Z" ;; esac
case $v in *[!0-9.]* | *..* | *.*.*.*) die "version must be plain X.Y.Z, got $v" ;; esac
cd "$(git rev-parse --show-toplevel)" || exit 1
man=.agents/.claude-plugin/plugin.json
slug=$(git remote get-url origin | sed 's#.*github\.com[:/]##; s#\.git$##')
git fetch -q --tags origin || die "git fetch failed"
git rev-parse -q --verify "refs/tags/v$v" >/dev/null && die "tag v$v exists; fix forward with a new version"

# Rewrite file $2 with sed script $1 (portable: no sed -i), CR endings of a Windows checkout dropped.
sub() { tr -d '\r' < "$2" | sed "$1" > "$2.n" && mv "$2.n" "$2"; }
# Version in <ref>'s canonical manifest.
ver() { git show "$1:$man" | grep -o '"version": "[^"]*"' | cut -d'"' -f4; }
# True when X.Y.Z $1 is above $2, comparing numbers.
above() {
  IFS=. read -r a b c <<EOF
$1
EOF
  IFS=. read -r x y z <<EOF
$2
EOF
  [ "$a" -gt "$x" ] || { [ "$a" -eq "$x" ] && { [ "$b" -gt "$y" ] || { [ "$b" -eq "$y" ] && [ "$c" -gt "$z" ]; }; }; }
}
# The CHANGELOG section of $1 from file $2, links made absolute for release notes.
notes() {
  awk -v h="## [$1]" '{sub(/\r$/, "")} index($0, h) == 1 {on = 1; next} on && /^## \[/ {exit} on' "$2" |
    sed "s#\[\#\([0-9]*\)\]#[\#\1](https://github.com/$slug/pull/\1)#g; s#](\([A-Z][A-Za-z]*\.md[^)]*\))#](https://github.com/$slug/blob/v$1/\1)#g"
}

prepare() {
  [ -z "$(git status --porcelain)" ] || die "working tree not clean"
  old=$(ver origin/main); above "$v" "$old" || die "$v is not above $old on origin/main"
  git show origin/main:CHANGELOG.md | awk '/^## \[Unreleased\]/ {on = 1; next} on && /^## \[/ {exit} on && /^- /' | grep -q . ||
    die "nothing under ## [Unreleased] in CHANGELOG.md"
  git switch -q -c "release/v$v" origin/main || die "cannot create branch release/v$v"
  for f in $man .agents/.codex-plugin/plugin.json .agents/.cursor-plugin/plugin.json; do
    sub "s/\"version\": \"$old\"/\"version\": \"$v\"/" "$f"
  done
  sub "s/\"ref\": \"v$old\"/\"ref\": \"v$v\"/" .claude-plugin/marketplace.json
  awk -v v="$v" -v o="$old" -v d="$(date +%Y-%m-%d)" -v u="https://github.com/$slug/compare" '
    {sub(/\r$/, "")}
    /^## \[Unreleased\]$/ {print; print ""; print "## [" v "] - " d; next}
    /^\[Unreleased\]: / {print "[Unreleased]: " u "/v" v "...HEAD"; print "[" v "]: " u "/v" o "...v" v; next}
    {print}' CHANGELOG.md > CHANGELOG.md.n && mv CHANGELOG.md.n CHANGELOG.md
  sub "s/^## Unreleased$/## $v/" UPGRADING.md
  sh scripts/check.sh || die "checks failed on the release branch; fix, commit, then push it yourself"
  git commit -q -am "chore(release): $v" || die "commit failed"
  git push -q -u origin "release/v$v" || die "push failed"
  b=$(mktemp) || exit 1; notes "$v" CHANGELOG.md > "$b"
  gh pr create --draft --base main --head "release/v$v" --title "chore(release): $v" --body-file "$b" || die "PR not created; branch release/v$v is pushed"
  rm -f "$b"
  echo "release: PR for $v open. After the owner merges it: sh scripts/release.sh publish $v"
}

publish() {
  [ "$(ver origin/main)" = "$v" ] || die "origin/main is not at $v: merge the release PR first"
  git ls-remote --exit-code --tags origin "refs/tags/v$v" >/dev/null && die "tag v$v exists on origin"
  # The first-parent commit on main that set the version: the release PR's merge, even with later merges on top.
  m=$(git log --first-parent --format=%H -1 -G"\"version\": \"$v\"" origin/main -- $man)
  [ -n "$m" ] && [ "$(ver "$m")" = "$v" ] || die "cannot find the commit that set $v"
  git tag -a "v$v" -m "v$v" "$m" && git push -q origin "v$v" || die "tag push failed"
  b=$(mktemp) || exit 1; git show "$m:CHANGELOG.md" > "$b.c"; notes "$v" "$b.c" > "$b"
  [ -s "$b" ] || die "no ## [$v] section in CHANGELOG.md at $m (tag v$v is pushed)"
  gh release create "v$v" --latest --title "v$v" --notes-file "$b" || die "release not created (tag v$v is pushed): rerun gh release create"
  rm -f "$b" "$b.c"
  echo "release: v$v published as Latest from $m"
}

$cmd
