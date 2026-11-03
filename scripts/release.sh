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
slug=$(git config --get remote.origin.url | sed 's#.*github\.com[:/]##; s#\.git$##')
case $slug in ?*/?*) ;; *) die "origin is not a GitHub repository: $slug" ;; esac
git fetch -q origin '+refs/heads/main:refs/remotes/origin/main' '+refs/tags/*:refs/tags/*' || die "git fetch failed"  # explicit: --tags alone may skip main

# Rewrite file $2 with sed script $1 (portable: no sed -i), CR endings of a Windows checkout dropped.
sub() { tr -d '\r' < "$2" | sed "$1" > "$2.n" && mv "$2.n" "$2"; }
# <ref>:<path> as typed: Git Bash would turn it into a Windows path list.
show() { MSYS_NO_PATHCONV=1 git show "$1"; }
# Version in <ref>'s canonical manifest.
ver() { show "$1:$man" | grep -o '"version": "[^"]*"' | cut -d'"' -f4; }
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
  git rev-parse -q --verify "refs/tags/v$v" >/dev/null && die "tag v$v exists; fix forward with a new version"
  [ -z "$(git status --porcelain)" ] || die "working tree not clean"
  old=$(ver origin/main); above "$v" "$old" || die "$v is not above $old on origin/main"
  show origin/main:CHANGELOG.md | awk '/^## \[Unreleased\]/ {on = 1; next} on && /^## \[/ {exit} on && /^- /' | grep -q . ||
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
  grep -q "\"version\": \"$v\"" $man && grep -q "^## \[$v\] - " CHANGELOG.md || die "edit did not apply: check the formats in docs/releasing.md"
  grep -q "^## $v$" UPGRADING.md || echo "release: UPGRADING.md has no '## Unreleased' section: no upgrade steps for $v (fine when none are needed)"
  git commit -q -am "chore(release): $v" || die "commit failed"
  sh scripts/check.sh HEAD origin/main && sh scripts/check.sh || die "checks failed on the release commit; fix, amend, push release/v$v yourself"
  git push -q -u origin "release/v$v" || die "push failed"
  b=$(mktemp) || exit 1; trap 'rm -f "$b"' EXIT; { notes "$v" CHANGELOG.md; printf '\n---\n🏭 Built with [AI Software Factory](https://softwarefactory.company/) by Seif\n'; } > "$b"
  gh pr create -R "$slug" --draft --base main --head "release/v$v" --title "chore(release): $v" --body-file "$b" || die "PR not created; branch release/v$v is pushed"
  echo "release: PR for $v open. After the owner merges it: sh scripts/release.sh publish $v"
}

publish() {
  [ "$(ver origin/main)" = "$v" ] || die "origin/main is not at $v: merge the release PR first"
  # The first-parent commit on main that set the version: the release PR's merge, even with later merges on top.
  m=$(git log --first-parent --format=%H -1 -G"\"version\": \"$v\"" origin/main -- $man)
  [ -n "$m" ] && [ "$(ver "$m")" = "$v" ] || die "cannot find the commit that set $v"
  # A rerun resumes: the tag may already be pushed at this commit while its release is missing.
  t=$(git ls-remote origin "refs/tags/v$v" | cut -f1)
  if [ -n "$t" ]; then
    [ "$(git rev-parse "refs/tags/v$v^{commit}")" = "$m" ] || die "tag v$v is on origin at another commit; fix forward with a new version"
    gh release view "v$v" -R "$slug" >/dev/null 2>&1 && die "v$v is already published"
    echo "release: tag v$v is already pushed; creating its release"
  else
    git rev-parse -q --verify "refs/tags/v$v" >/dev/null && die "local tag v$v is not on origin: git tag -d v$v, then rerun"
  fi
  # Everything that can fail runs before the irreversible tag push.
  gh auth status >/dev/null 2>&1 || die "gh is not signed in: run gh auth login, then rerun"
  b=$(mktemp) || exit 1; trap 'rm -f "$b" "$b.c"' EXIT; show "$m:CHANGELOG.md" > "$b.c"; notes "$v" "$b.c" > "$b"
  [ -s "$b" ] || die "no ## [$v] section in CHANGELOG.md at $m: fix it on main first"
  if [ -z "$t" ]; then
    git tag -a "v$v" -m "v$v" "$m" || die "cannot tag"
    git push -q origin "refs/tags/v$v" || { git tag -d "v$v" >/dev/null; die "tag push failed; local tag removed, rerun"; }
  fi
  gh release create "v$v" -R "$slug" --verify-tag --latest --title "v$v" --notes-file "$b" || die "release not created (tag v$v is pushed): rerun publish $v"
  echo "release: v$v published as Latest from $m"
}

$cmd
