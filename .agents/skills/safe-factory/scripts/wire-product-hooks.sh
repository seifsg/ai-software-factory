#!/bin/sh
# Wires Stop/compact hooks into a product checkout so the autonomous loop can advance.
# Usage: wire-product-hooks.sh <product-root> [plugin-root]
# plugin-root defaults to this script's ../../.. (.agents). Idempotent. Exit 1 on bad args.
set -eu
prod=${1:-}
plug=${2:-}
[ -n "$prod" ] || { printf 'usage: wire-product-hooks.sh <product-root> [plugin-root]\n' >&2; exit 1; }
case $prod in /* | ?:*) ;; *) prod=$PWD/$prod ;; esac
[ -d "$prod" ] || { printf 'not a directory: %s\n' "$prod" >&2; exit 1; }
self=$0
case $self in /* | ?:*) ;; *) self=$PWD/$self ;; esac
[ -n "$plug" ] || plug=${self%/*}/../../..
case $plug in /* | ?:*) ;; *) plug=$PWD/$plug ;; esac
guard=$plug/skills/safe-factory/scripts/run-guard.sh
[ -f "$guard" ] || { printf 'missing run-guard: %s\n' "$guard" >&2; exit 1; }

dest=$prod/.agents/skills/safe-factory/scripts
mkdir -p "$dest" "$prod/.agents/hooks" "$prod/.claude" "$prod/.cursor"
cp "$guard" "$dest/run-guard.sh"
# Project-relative path: works after clone without baking a machine-local plugin root.
rel=.agents/skills/safe-factory/scripts/run-guard.sh

# Claude Code / Cursor (project settings): Stop + compact resume.
cat > "$prod/.claude/settings.json" <<'EOF'
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "g=.agents/skills/safe-factory/scripts/run-guard.sh; [ -f \"$g\" ] && { set -- stop; . \"$g\"; }; exit 0",
        "timeout": 10
      }]
    }],
    "SessionStart": [{
      "matcher": "compact|resume",
      "hooks": [{
        "type": "command",
        "command": "g=.agents/skills/safe-factory/scripts/run-guard.sh; [ -f \"$g\" ] && { set -- compact; . \"$g\"; }; exit 0",
        "timeout": 10
      }]
    }]
  }
}
EOF

# Plugin-shaped hooks tree so the product checkout is not bare of .agents/hooks.
cp "$prod/.claude/settings.json" "$prod/.agents/hooks/hooks.json"

# Codex / some Cursor copies read project .cursor/hooks.json.
cat > "$prod/.cursor/hooks.json" <<EOF
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "command": "sh $rel stop",
        "commandWindows": "sh $rel stop"
      }]
    }],
    "SessionStart": [{
      "hooks": [{
        "command": "sh $rel compact",
        "commandWindows": "sh $rel compact"
      }]
    }]
  }
}
EOF

printf 'wired: %s -> %s\n' "$prod" "$rel"
