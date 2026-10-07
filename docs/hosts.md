# Hosts

Seif, 7 October 2026: the factory is agent-agnostic. Its methods live in `.agents/skills/` (the open [Agent Skills](https://agentskills.io) folder) and [AGENTS.md](../AGENTS.md); every coding agent reads the same files. This page is the only place for host-specific commands. Everything else in the factory says "your agent".

First-class hosts get a tested installer route, gate hooks and a Safe reviewer preset. Other agents run the same methods with the gate called by hand.

## First-class hosts

| | Claude Code | Codex | Cursor |
|---|---|---|---|
| Factory skills | `safe-engine` plugin (skills + hooks) | `~/.agents/skills/` | `~/.agents/skills/` |
| Rules file | `AGENTS.md` (read when no `CLAUDE.md` exists) | `AGENTS.md` | `AGENTS.md` |
| Install | [Claude Code install](#claude-code) | `fast_gate.py install --host codex`, then trust it in `/hooks` | `fast_gate.py install --host cursor` |
| Invoke | `/safe-engine Build ...` | `$safe-engine Build ...` | ask for the safe-engine skill: `use safe-engine to build ...` |
| Gate hooks | plugin: `PreToolUse`, `Stop`, `UserPromptSubmit`, `SessionStart` | `~/.codex/hooks.json`: same events and JSON as Claude Code | `~/.cursor/hooks.json`: `preToolUse`, `stop`, `sessionStart` |
| Safe reviewer | `review --agent claude`: `claude -p`, Read/Grep/Glob only, `--json-schema` | `review --agent codex`: `codex exec --sandbox read-only --output-schema` | `review --agent cursor`: `agent -p --mode ask` |
| Checked here (7 Oct) | plugin validated; sandbox installs from a local path and the HTTPS URL; live hook denied a real Write and `npm install` | the 1 Oct recorded pilot ran the Safe cycle in Codex ([pilot verification](pilot-verification.md)); installer and hook dialect exercised with simulated events; no Codex CLI on this machine now | installer and hook dialect exercised with simulated events; no Cursor CLI on this machine |

`fast_gate.py` sits in `skills/safe-engine/scripts/` of the factory bundle; run it with Python 3.9+ (`python`, `python3` or `py -3`). `--project <dir>` installs Codex or Cursor into one project (`<dir>/.agents/skills`, `<dir>/.codex/hooks.json`, `<dir>/.cursor/hooks.json`) instead of your user folders. Re-running replaces only the factory's own hook entries; your other hooks stay.

Safe review picks an installed reviewer that did not build the candidate (`review --agent auto --builder <name>`). Claude Code, Codex and Cursor builders are detected from their environment (`CLAUDECODE`, `CODEX_THREAD_ID`, `CURSOR_AGENT`); when the builder is unknown and several agents are installed, review asks for `--builder` instead of guessing. No agent CLI installed: hand `review-packet` to a fresh read-only subagent of your host, then `review --report <file> --reviewer <id>`.

## Claude Code

The plugin brings `/safe-engine`, `/improve-factory` and the gate hooks. Pick one route.

- **Any surface, one command** (needs the factory checkout or bundle): `python fast_gate.py install --host claude`. It adds the marketplace over HTTPS with auto-update and enables the plugin in `~/.claude/settings.json`, keeping a backup. The repository is private: HTTPS uses your stored Git credentials (no SSH key needed). Start a new session; it installs in the background.
- **Desktop app by hand:** add the same two keys to `~/.claude/settings.json`, then start a new session:

  ```json
  "extraKnownMarketplaces": {"ai-software-factory": {"source": {"source": "git", "url": "https://github.com/seifsg/ai-software-factory.git"}, "autoUpdate": true}},
  "enabledPlugins": {"safe-engine@ai-software-factory": true}
  ```

- **Terminal with the `claude` CLI on PATH:** `claude plugin marketplace add https://github.com/seifsg/ai-software-factory.git`, then `claude plugin install safe-engine@ai-software-factory`. Use the HTTPS URL; the `owner/repo` shorthand tries SSH first.

The desktop app installs a CLI only inside its own folder, so `claude` is usually not on PATH there. The plugin root is the repository's `skills/` folder: installs copy the two entry skills and their scripts only.

## Other agents

| Agent | Skills | Gate | Safe reviewer |
|---|---|---|---|
| GitHub Copilot | reads `.agents/skills`, `~/.agents/skills` | `.github/hooks/*.json` with PascalCase `PreToolUse` (Claude-style payload) → `sh <entries>/safe-engine/scripts/run-gate.sh copilot` (exit 2 denies) | review packet |
| Gemini CLI (Antigravity unverified) | reads `.agents/skills` | `BeforeTool` hook → `sh <entries>/safe-engine/scripts/run-gate.sh gemini` (exit 2 denies) | review packet |
| OpenCode | reads `.agents/skills` | no declarative hooks: run `fast_gate.py start/done/status` yourself | review packet |
| Anything else | point it at `.agents/skills/safe-engine/SKILL.md` | `fast_gate.py` commands by hand | review packet |

Put the two entries where these agents look with `fast_gate.py install --host other` (skills only, into `~/.agents/skills` or `--project <dir>`). Run hooks through `run-gate.sh`: it fails open when Python or the gate is missing, which hosts that block on any other exit code need. Unknown hosts get a generic reader: pre-tool events deny with exit code 2 and the reason on stderr, the signal those agents honor; stop and prompt hooks need a first-class adapter.

## Sources

Read 7 October 2026: Claude Code [hooks](https://code.claude.com/docs/en/hooks.md), [plugins](https://code.claude.com/docs/en/plugins/marketplace-reference.md), [headless](https://code.claude.com/docs/en/headless); Codex [hooks](https://learn.chatgpt.com/docs/hooks.md), [skills](https://learn.chatgpt.com/docs/build-skills), [non-interactive](https://learn.chatgpt.com/docs/non-interactive-mode); Cursor [hooks](https://cursor.com/docs/agent/hooks), [skills](https://cursor.com/docs/context/skills), [headless CLI](https://cursor.com/docs/cli/headless); Copilot [hooks](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-hooks-reference); Gemini CLI [hooks](https://geminicli.com/docs/hooks/reference/); OpenCode [plugins](https://opencode.ai/docs/plugins/); [Agent Skills](https://agentskills.io); [AGENTS.md](https://agents.md).
