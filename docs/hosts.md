# Hosts

The methods live in `.agents/skills/` (the open Agent Skills folder) and `AGENTS.md`; every coding agent reads the same files. Host-specific commands live here and in `docs/install.md`. Everything else says "your agent".

First-class hosts get an installer route, gate hooks and a Safe reviewer preset. Other agents run the same methods and call the gate by hand.

## First-class hosts

| | Claude Code | Codex | Cursor |
|---|---|---|---|
| Skills | `safe-engine` plugin (skills + hooks) | `~/.agents/skills/` | `~/.agents/skills/` |
| Rules file | `AGENTS.md` (read when no `CLAUDE.md` exists; otherwise import it with `@AGENTS.md`) | `AGENTS.md` | `AGENTS.md` |
| Install | `fast_gate.py install --host claude` or [by hand](#claude-code) | `fast_gate.py install --host codex` (global skills); opt projects into hooks below | `fast_gate.py install --host cursor` |
| Invoke | `/safe-engine Build ...` | `$safe-engine Build ...` | `use safe-engine to build ...` |
| Question tool | `AskUserQuestion` (4 questions, 4 options each) | chat message | chat message |
| Gate progress messages | hook `systemMessage`, shown to the user | hook `systemMessage`, shown as a warning | not shown: the agent relays the gate's card |
| Delegate hook calls | marked (`agent_id`): they show no progress; the next main-thread call does | not marked: tool hooks carry no `agent_id` and use the parent session id, so a delegate's call may show it | not applicable |
| Task list | `TaskCreate` / `TaskUpdate` when the session has them (on by default only for older models; `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` opts in) | the plan view, when the session has its plan tool | none documented: chat lines only |
| Gate hooks | plugin: `PreToolUse`, `Stop`, `UserPromptSubmit`, `SessionStart` | `<project>/.codex/hooks.json`: same events and JSON as Claude Code; retained user hooks also run | `~/.cursor/hooks.json`: `preToolUse`, `stop` (a follow-up only when `status` is `completed`), `sessionStart` |
| Safe reviewer | `review --agent claude`: `claude -p`, Read/Grep/Glob only, `--json-schema` | `review --agent codex`: `codex exec --sandbox read-only --output-schema` | `review --agent cursor`: `agent -p --mode ask` |
| Model tiers (light / standard / deep) | `haiku` / `sonnet` / `opus` | host models | host models |

Python runs as `python`, `python3` or `py -3` (Windows). Claude Code hooks need a POSIX `sh` (Git Bash on Windows): the plugin sources `run-gate.sh` in the shell Claude Code already starts for a hook, so a call with no factory run starts no other process. Codex project hooks use an already-connected local stdio MCP tool, reusing one Python process per MCP connection; the host can create separate connections across chats. Setup needs the native Codex CLI on PATH or its absolute executable in `CODEX_EXECUTABLE`; it parses configuration privately without starting a thread or MCP server. Cursor and retained legacy Codex Windows commands still start Python per event. Ticket checks use the GitHub CLI `gh` when the tracker is GitHub.

At a stop, Claude Code lists the session's background work (`background_tasks`). A running or pending `subagent` or `workflow` entry lets the stop pass: its result starts a new turn, whose stop the gate checks. Other entries (`shell`, `monitor`, `teammate` and the rest) and hosts without the list (Codex, Cursor) keep one block per stop. Limit: experimental observer agents (`CLAUDE_CODE_EXPERIMENTAL_OBSERVER_AGENTS`) are listed as `subagent` but may never report back, so with them on, the last stop can pass without the reminder. The gate log records each passed stop as `hook.wait_stop`.

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

## Codex

`install --host codex` installs global skills only on a clean setup. `install --host codex --project <dir>` retains the skills-plus-project-hooks route and refuses canonical skills it does not own. To add hooks without copying skills, including in a factory checkout, use:

```text
python fast_gate.py hooks --host codex --project <absolute-dir>
```

See [installation and migration](install.md#codex-project-hooks) for paired configuration, backups and legacy global sources. The project-only MCP server binds a normalized project hash and the gate home selected during setup (`SAFE_ENGINE_HOME`, default `~/.safe-engine`). Its callback checks that project's `active/<hash>.json` and `runs/<hash>.json`. Other projects' runs do not trigger state evaluation. Either home file invokes fresh policy so a deleted registration recovers from open state, and missing or unreadable state stays protected. Project mirrors are never authority. Failed closed-state retirement can require one recovery call. No run means an empty result without a new shell or interpreter per event.

Each MCP connection starts one Python process even in an opted-in project with no run, and keeps code imports until the connection closes. Separate chats can create separate processes, even in the same host/project. A process can outlive an unsubscribed chat; host EOF disposes it. There is no global daemon or polling. Startup, resident memory and callbacks still cost resources; this design does not promise zero overhead. Policy, state and consent are read fresh, never cached. A fresh connection is required after runtime updates; a configured receipt does not prove which version is loaded.

Codex calls only already-connected MCP servers. The required server must connect during session startup; a startup failure needs runtime/CLI/config repair before retrying. Hook calls do not reconnect it, and missing/disconnected/failed calls fail open. SessionStart can run before readiness, so use a later participating prompt or direct `status` to refresh guidance. Inspect connection status and real hook events before relying on protection. The single hook tool is hidden from model-facing tools using supported MCP metadata; a hook invocation returns one JSON text block.

Review project configuration and exact-hook trust in `/hooks`; open a fresh connection after configuration changes. A file or receipt proves neither trust, effective loading nor MCP readiness. Inspect every effective source: user JSON, project JSON, inline configuration, plugins and managed hooks can add together. User migration removes only recognized handlers in the selected JSON file; project removal also removes its verified owned MCP block. Installed runtimes and pinned methods do not reload or upgrade implicitly.

### Protection and workflow participation

- All chats that loaded the hooks share the active project's preparation and destructive-command protection. Participation never grants write authorization.
- Workflow participation is explicit: `start`, `resume` or `join` records the session in the run's optional home-state `participants` list. Pass `--session <ID>` when the host identity is available; these commands otherwise use `CODEX_THREAD_ID` when present.
- To join an existing run without resuming a paused one: `python fast_gate.py join --project <absolute-dir> --session <ID>`. Missing identity: obtain the actual host session ID; do not invent one. Legacy registration `sessions` are not participation.
- Reading, editing, prompts and session starts do not opt a chat into workflow messages. Stop reminders, status and progress messages require both participation and current-directory ownership by that project. A participating chat that moves to another project receives no workflow reminders from its prior project.
- A delegate using its participating parent's session ID can receive the parent's messages. A host that omits a matching session ID cannot deliver those messages; direct gate commands still show the run card.

Project hooks only protect chats that actually load that project layer and have the server connected. A chat opened in an unrelated workspace without those hooks can write an absolute target in the active project without interception. Moving cwd does not grant new project trust or load its configuration automatically; open a fresh connection in that project after its own setup/review. A previously loaded scoped hook still checks absolute targets in its protected project. The gate's command-line checks and work record remain necessary.

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
| Codex | `codex exec --sandbox workspace-write --ignore-user-config -` | not needed | from effective trusted hook sources; configure a scoped project layer explicitly |
| Cursor | `agent -p --force "Read ../prompt.md and do what it says."` | not needed | only from the user's `~/.cursor/hooks.json` |

Claude Code: start `python -m evals` with `CLAUDE_CONFIG_DIR` set to an empty folder and `ANTHROPIC_API_KEY` set, so neither arm loads the user's plugins, hooks or `CLAUDE.md`, and only the factory arm loads the factory plugin with its gate hooks. The templates avoid `--bare`: the CLI reference says it skips hooks and installed plugins and does not say whether a `--plugin-dir` plugin's hooks still run.

Codex can load trusted project hooks as well as user and other additive sources; a clean `install --host codex` adds no hooks. Configure the factory arm's workspace with `hooks --host codex --project <workspace>`, complete host project/exact-hook trust and verify effective loading for that CLI invocation. The template's `--ignore-user-config` flag is not proof that project or other hook sources are absent. Without effective hooks, the arm follows the method and calls the gate by hand, with no hook enforcement. Cursor retains its user hook route from `install --host cursor`. To measure enforcement, isolate each arm's effective sources and verify them: the plain arm must never see an installed factory (skills folder, plugin or hooks).

## Sources

Claude Code [hooks](https://code.claude.com/docs/en/hooks.md), [plugins](https://code.claude.com/docs/en/plugins/marketplace-reference.md), [headless](https://code.claude.com/docs/en/headless), [CLI reference](https://code.claude.com/docs/en/cli-reference), [environment variables](https://code.claude.com/docs/en/env-vars) · Codex [hooks](https://learn.chatgpt.com/docs/hooks.md), [skills](https://learn.chatgpt.com/docs/build-skills), [non-interactive](https://learn.chatgpt.com/docs/non-interactive-mode) · Cursor [hooks](https://cursor.com/docs/agent/hooks), [skills](https://cursor.com/docs/context/skills), [headless CLI](https://cursor.com/docs/cli/headless) · Copilot [hooks](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-hooks-reference) · Gemini CLI [hooks](https://geminicli.com/docs/hooks/reference/) · OpenCode [plugins](https://opencode.ai/docs/plugins/) · [Agent Skills](https://agentskills.io) · [AGENTS.md](https://agents.md)
