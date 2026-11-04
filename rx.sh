#!/bin/sh
# P4: release.sh publish on a temp repo with a local origin and a stub gh. sh rx.sh <release.sh> > out. Touches only a temp dir.
R=$1; d=$(mktemp -d); o=$d/github.com/o/r.git; mkdir -p "$d/bin" "$d/github.com/o"; git init -q --bare -b main "$o"
cat > "$d/bin/gh" <<'EOF'
#!/bin/sh
# Stub: signed in; no release exists; create fails while the flag file is there.
case "$1 $2" in
  'auth status') exit 0 ;;
  'release view') [ -f "$GH_D/has-$3" ] && exit 0; exit 1 ;;
  'release create') [ -f "$GH_D/fail" ] && { echo 'stub: create failed' >&2; exit 1; }; : > "$GH_D/has-$3"; exit 0 ;;
esac
EOF
chmod +x "$d/bin/gh"; export GH_D="$d" PATH="$d/bin:$PATH"
git clone -q "$o" "$d/w" 2>/dev/null; w=$d/w; g() { git -C "$w" -c user.name=t -c user.email=t@t -c commit.gpgsign=false "$@"; }
mkdir -p "$w/scripts" "$w/.agents/.claude-plugin"; cp "$R" "$w/scripts/release.sh"
rel() { printf '{\n  "version": "%s"\n}\n' "$1" > "$w/.agents/.claude-plugin/plugin.json"; printf '# Changelog\n\n## [%s] - 2026-11-04\n\n### Fixed\n\n- Fix a thing ([#1])\n' "$1" > "$w/CHANGELOG.md"; g add -A 2>/dev/null; g commit -qm "chore(release): $1"; g push -q origin HEAD:main 2>/dev/null; }
pub() { (cd "$w" && sh scripts/release.sh publish "$1" 2>&1 | sed "s#$d#<d>#g" | cut -c1-110); }
st() { s=$(git -C "$o" rev-parse --short refs/heads/stable 2>/dev/null); t=$(git -C "$o" rev-parse --short "refs/tags/v$1^{commit}" 2>/dev/null); echo "stable: ${s:-none}; v$1: ${t:-none}; same: $([ -n "$s" ] && [ "$s" = "$t" ] && echo yes || echo no)"; }

rel 1.0.0; echo '--- first release'; pub 1.0.0; st 1.0.0
rel 2.0.0; : > "$d/fail"; echo '--- release create fails, then rerun'; pub 2.0.0; st 2.0.0; rm -f "$d/fail"; pub 2.0.0; st 2.0.0
echo '--- rerun of a finished release'; pub 2.0.0
rel 3.0.0; g commit -q --allow-empty -m stray; git -C "$w" push -q "$o" HEAD:refs/heads/stable 2>/dev/null; git -C "$w" reset -q --hard HEAD~1; rel 4.0.0
echo '--- stable moved elsewhere, not a fast-forward'; before=$(git -C "$o" rev-parse --short refs/heads/stable); pub 4.0.0; echo "stable kept: $([ "$before" = "$(git -C "$o" rev-parse --short refs/heads/stable)" ] && echo yes || echo no); release created: $([ -f "$d/has-v4.0.0" ] && echo yes || echo no)"
