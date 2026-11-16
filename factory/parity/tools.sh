#!/bin/sh
# check.sh's update-check and doctor scenarios, printing outputs and moved files. Env: W, SIDE (sh or bin),
# BIN (the binary). The sh side runs the scripts, the bin side `factory update-check` and `factory doctor`.
set -u
export LC_ALL=C
here=$(cd "$(dirname "$0")" && pwd)
s=$(cd "$here/../../.agents/skills/safe-factory/scripts" && pwd)
plugin=$(cd "$here/../../.agents" && pwd); command -v cygpath >/dev/null && plugin=$(cygpath -m "$plugin")
mkdir -p "$W"
uc() { if [ "$SIDE" = sh ]; then sh "$s/update-check.sh" "$plugin"; else "$BIN" update-check "$plugin"; fi; }
dr() { if [ "$SIDE" = sh ]; then sh "$s/doctor.sh" "$@"; else "$BIN" doctor "$@"; fi; echo "exit $?"; }

# Update check, from the cache only: a newer release tells the owner, an older or equal one stays quiet.
for c in 9.9.9 0.0.1 0.7.2 1.0.0-rc1 v2; do
  u=$W/u-$c; mkdir -p "$u/ai-software-factory"; echo "$c" > "$u/ai-software-factory/latest"
  printf '== update %s\n' "$c"; HOME="$u" CLAUDE_PROJECT_DIR="$u" XDG_CACHE_HOME="$u" FACTORY_NO_UPDATE_CHECK= uc
done
printf '== update off\n'; HOME="$W/u-9.9.9" XDG_CACHE_HOME="$W/u-9.9.9" FACTORY_NO_UPDATE_CHECK=1 uc

# Doctor: a file holding only old hooks moves; a mixed or other-settings file stays; stale copies refresh.
h=$W/d; mkdir -p "$h/.codex" "$h/.cursor" "$h/p/.claude"
printf '{\n  "hooks": {\n    "Stop": [{"hooks": [{"command": "sh x/run-gate.sh"}]}]\n  }\n}\n' > "$h/.codex/hooks.json"
printf '{\n  "hooks": {\n    "stop": [{"command": "sh x/run-gate.sh"}, {"command": "sh x/skills/safe-factory/scripts/run-guard.sh"}]\n  }\n}\n' > "$h/.cursor/hooks.json"
printf '{\n\t"permissions": {},\n\t"hooks": {"Stop": [{"hooks": [{"command": "sh x/run-gate.sh"}]}]}\n}\n' > "$h/p/.claude/settings.json"
mkdir -p "$h/.claude"; printf '{"enabledPlugins": {"safe-factory@ai-software-factory": true}, "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "sh y/run-guard.sh stop"}]}]}}\n' > "$h/.claude/settings.json"
mkdir -p "$h/.safe-engine"; echo x > "$h/.safe-engine/state"
d() { HOME="$h" CLAUDE_PROJECT_DIR="$h/p" XDG_CACHE_HOME="$h" dr "$@"; }
printf '== doctor list\n'; d "$plugin"
printf '== doctor fix\n'; d "$plugin" --fix
printf '== doctor after\n'; d "$plugin"
mkdir -p "$h/.codex/rules"; echo stale > "$h/.codex/rules/factory.rules"
printf '== doctor stale\n'; d "$plugin"
printf '== doctor stale fix\n'; d "$plugin" --fix
printf -- '-- rules copy\n'; cmp -s "$h/.codex/rules/factory.rules" "$here/../../tools/night/codex.rules" && echo same || echo differs
printf -- '-- files left\n'; (cd "$h" && find . -type f | grep -v '/removed/' | sort)
printf -- '-- backup index\n'; cat "$h"/ai-software-factory/removed/*/index 2>/dev/null | cut -f2- | sort
printf '== update with leftovers\n'; mkdir -p "$h/.safe-engine"; HOME="$h" CLAUDE_PROJECT_DIR="$h/p" XDG_CACHE_HOME="$h" FACTORY_NO_UPDATE_CHECK= uc
