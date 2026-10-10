# Hosts

The methods live in `.agents/skills/` (the open Agent Skills folder) and `AGENTS.md`; every coding agent reads the same files. This page is the only place for agent-specific commands. Everything else says "your agent".

First-class hosts get an installer route, gate hooks and a Safe reviewer preset. Other agents run the same methods and call the gate by hand.

## First-class hosts

| | Claude Code | Codex | Cursor |
|---|---|---|---|
| Skills | `safe-engine` plugin (skills + hooks) | `~/.agents/skills/` | `~/.agents/skills/` |
| Rules file | `AGENTS.md` (read when no `CLAUDE.md` exists; otherwise import it with `@AGENTS.md`) | `AGENTS.md` | `AGENTS.md` |
| Install | `fast_gate.py install --host claude` or [by hand](#claude-code) | `fast_gate.py install --host codex`, then trust it in `/hooks` | `fast_gate.py install --host cursor` |
| Invoke | `/safe-engine Build ...` | `$safe-engine Build ...` | `use safe-engine to build ...` |
| Question tool | `AskUserQuestion` (4 questions, 4 options each) | chat message | chat message |
| Gate progress messages | hook `systemMessage`, shown to the user | hook `systemMessage`, shown as a warning | not shown: the agent relays the gate's card |
| Delegate hook calls | marked (`agent_id`): they show no progress; the next main-thread call does | not marked: tool hooks carry no `agent_id` and use the parent session id, so a delegate's call may show it | not applicable |
| Task list | `TaskCreate` / `TaskUpdate` when the session has them (on by default only for older models; `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` opts in) | the plan view, when the session has its plan tool | none documented: chat lines only |
| Gate hooks | plugin: `PreToolUse`, `Stop`, `UserPromptSubmit`, `SessionStart` | `~/.codex/hooks.json`: same events and JSON as Claude Code | `~/.cursor/hooks.json`: `preToolUse`, `stop`, `sessionStart` |
| Safe reviewer | `review --agent claude`: `claude -p`, Read/Grep/Glob only, `--json-schema` | `review --agent codex`: `codex exec --sandbox read-only --output-schema` | `review --agent cursor`: `agent -p --mode ask` |
| Model tiers (light / standard / deep) | `haiku` / `sonnet` / `opus` | host models | host models |

Python runs as `python`, `python3` or `py -3` (Windows). Claude Code hooks need a POSIX `sh` (Git Bash on Windows): the plugin sources `run-gate.sh` in the shell Claude Code already starts for a hook, so a call with no factory run starts no other process. The Codex and Cursor Windows command checks for an active run in Python before loading the gate. Ticket checks use the GitHub CLI `gh` when the tracker is GitHub.

Reference commands are written for a POSIX shell: run them in Git Bash on Windows. PowerShell 5.1 breaks `{owner}/{repo}` placeholders and nested quotes in `--jq` filters. Stuck in PowerShell: replace the placeholders with real names and pass each jq filter in single quotes, inner double quotes escaped as `\"`.

Safe review picks an installed reviewer that did not build the candidate: `review --agent auto --builder <name>`. Builders are detected from `CLAUDECODE`, `CODEX_THREAD_ID` and `CURSOR_AGENT`; when the builder is unknown and several agents are installed, review asks for `--builder`. No agent CLI: hand `review-packet` to a fresh read-only subagent, then `review --report <file> --reviewer <id>`.

## Claude Code

The plugin brings `/safe-engine`, `/improve-factory` and the gate hooks. Its root is the repository's `skills/` folder. Pick one route:

- **Installer:** `python fast_gate.py install --host claude` adds the marketplace over HTTPS with auto-update and enables the plugin in `~/.claude/settings.json`, keeping a backup.
- **Settings by hand** (desktop app): add these keys to `~/.claude/settings.json`, then start a new session:

  ```json
  "extraKnownMarketplaces": {"ai-software-factory": {"source": {"source": "git", "url": "https://github.com/seifsg/ai-software-factory.git"}, "autoUpdate": true}},
  "enabledPlugins": {"safe-engine@ai-software-factory": true}
  ```

- **Terminal:** `claude plugin marketplace add https://github.com/seifsg/ai-software-factory.git`, then `claude plugin install safe-engine@ai-software-factory`. Use the HTTPS URL; the `owner/repo` shorthand tries SSH first.

## Other agents

| Agent | Skills | Gate | Safe reviewer |
|---|---|---|---|
| GitHub Copilot | reads `.agents/skills`, `~/.agents/skills` | `.github/hooks/*.json`, PascalCase `PreToolUse` → `sh <launchers>/safe-engine/scripts/run-gate.sh copilot` (exit 2 denies) | review packet |
| Gemini CLI | reads `.agents/skills` | `BeforeTool` hook → `sh <launchers>/safe-engine/scripts/run-gate.sh gemini` (exit 2 denies) | review packet |
| OpenCode | reads `.agents/skills` | no declarative hooks: run `fast_gate.py` yourself | review packet |
| Anything else | point it at `.agents/skills/safe-engine/SKILL.md` | `fast_gate.py` by hand | review packet |

Their hooks show no gate progress messages: the agent relays the card from the gate's command output.

`fast_gate.py install --host other` copies the launchers into `~/.agents/skills` (or `--project <dir>`). Run hooks through `run-gate.sh`: it fails open when Python or the gate is missing. Unknown hosts get a generic reader: pre-tool events deny with exit code 2 and the reason on stderr; stop and prompt hooks need a first-class adapter.

## Evals

`python -m evals run` lives in the factory repository only (`evals/README.md`); installed copies leave `evals/` out. It takes each agent's non-interactive command as a template. The prompt arrives on stdin and also sits at `../prompt.md` from the workspace. In the factory arm, `{factory}` is a fresh export of the factory bundle. Real runs cost model tokens; check each flag against the installed version before one.

| Agent | `--agent` (plain arm, and factory arm unless overridden) | `--factory-agent` (factory arm) | Gate hooks in the factory arm |
|---|---|---|---|
| Claude Code | `claude -p --dangerously-skip-permissions` | `claude -p --dangerously-skip-permissions --plugin-dir {factory}/skills` | from the plugin directory |
| Codex | `codex exec --sandbox workspace-write --ignore-user-config -` | not needed | only from the user's `~/.codex/hooks.json` |
| Cursor | `agent -p --force "Read ../prompt.md and do what it says."` | not needed | only from the user's `~/.cursor/hooks.json` |

Claude Code: start `python -m evals` with `CLAUDE_CONFIG_DIR` set to an empty folder and `ANTHROPIC_API_KEY` set, so neither arm loads the user's plugins, hooks or `CLAUDE.md`, and only the factory arm loads the factory plugin with its gate hooks. The templates avoid `--bare`: the CLI reference says it skips hooks and installed plugins and does not say whether a `--plugin-dir` plugin's hooks still run.

Codex and Cursor read gate hooks only from the user's hooks file, which `fast_gate.py install --host codex|cursor` writes. Without that install, their factory arm follows the method and calls the gate by hand, with no hook enforcement. To measure enforcement, run the factory arm as a user or profile with the install and the plain arm as one without it. The plain arm must never see an installed factory (skills folder, plugin or hooks).

## Sources

Claude Code [hooks](https://code.claude.com/docs/en/hooks.md), [plugins](https://code.claude.com/docs/en/plugins/marketplace-reference.md), [headless](https://code.claude.com/docs/en/headless), [CLI reference](https://code.claude.com/docs/en/cli-reference), [environment variables](https://code.claude.com/docs/en/env-vars) · Codex [hooks](https://learn.chatgpt.com/docs/hooks.md), [skills](https://learn.chatgpt.com/docs/build-skills), [non-interactive](https://learn.chatgpt.com/docs/non-interactive-mode) · Cursor [hooks](https://cursor.com/docs/agent/hooks), [skills](https://cursor.com/docs/context/skills), [headless CLI](https://cursor.com/docs/cli/headless) · Copilot [hooks](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-hooks-reference) · Gemini CLI [hooks](https://geminicli.com/docs/hooks/reference/) · OpenCode [plugins](https://opencode.ai/docs/plugins/) · [Agent Skills](https://agentskills.io) · [AGENTS.md](https://agents.md)
