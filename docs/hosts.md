# Hosts

The methods live in `.agents/skills/` (the open Agent Skills folder) and `AGENTS.md`; every coding agent reads the same files. This page is the only place for agent-specific commands. Everything else says "your agent".

First-class hosts get an installer route, gate hooks and a Safe reviewer preset. Other agents run the same methods and call the gate by hand.

## Local test hosts

Run `python tests/run.py` from the factory checkout. On Windows its setup prefers an installed Git's `bin/sh.exe` and `bin/bash.exe` over the WSL launcher, inside the test process and its workers only. No installation or global PATH change occurs; without those Git shells the inherited PATH remains. Mocked Codex-protocol review tests name a synthetic Cursor builder so the real host's builder identity cannot change their mock's protocol. Production reviewer selection and assertions are unchanged.

Common gate commands load only their requested optional argument module, including their own complete command help. Leading-option input, unknown commands and parse errors use complete registration with the original diagnostics. The selected bundle and state checks are never cached or skipped.

## First-class hosts

| | Claude Code | Codex | Cursor |
|---|---|---|---|
| Skills | `safe-engine` plugin (skills + hooks) | `~/.agents/skills/` | `~/.agents/skills/` |
| Rules file | `AGENTS.md` (read when no `CLAUDE.md` exists; otherwise import it with `@AGENTS.md`) | `AGENTS.md` | `AGENTS.md` |
| Install | `fast_gate.py install --host claude` or [by hand](#claude-code) | `fast_gate.py install --host codex`, then trust it in `/hooks` | `fast_gate.py install --host cursor` |
| Updates | marketplace `autoUpdate`, pinned to the release tag ([updates](#updates)) | session-start hook, once a day, to the newest verified release ([updates](#updates)) | same |
| Invoke (same form for `improve-factory`) | `/safe-engine Build ...` | `$safe-engine Build ...` | `use safe-engine to build ...` |
| Question tool | `AskUserQuestion` (4 questions, 4 options each) | chat message | chat message |
| Gate progress messages | hook `systemMessage`, shown to the user | hook `systemMessage`, shown as a warning | not shown: the agent relays the gate's card |
| Delegate hook calls | marked (`agent_id`): they show no progress; the next main-thread call does | not marked: tool hooks carry no `agent_id` and use the parent session id, so a delegate's call may show it | not applicable |
| Live view subsessions | background agents from each stop's `background_tasks`, with last-observed time; portable `Session` reports supplement them | coordinator records `Session` facts at delegation boundaries; no automatic child telemetry | coordinator records `Session` facts at delegation boundaries; no automatic child telemetry |
| Live view link reminder | this run's project URL in the prompt hook's `systemMessage`, prompts 1, 7, 13 and so on | same | no prompt hook: the agent gives the project link |
| Task list | `TaskCreate` / `TaskUpdate` when the session has them (on by default only for older models; `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` opts in) | the plan view, when the session has its plan tool | none documented: chat lines only |
| Gate hooks | plugin: `PreToolUse`, `Stop`, `UserPromptSubmit`, `SessionStart` | `~/.codex/hooks.json`: same events and JSON as Claude Code | `~/.cursor/hooks.json`: `preToolUse`, `stop` (a follow-up only when `status` is `completed`), `sessionStart` |
| Safe reviewer | `review --agent claude`: `claude -p`, Read/Grep/Glob only, `--json-schema` | `review --agent codex`: `codex exec --sandbox read-only --output-schema` | `review --agent cursor`: `agent -p --mode ask` |
| Delegate roles and tiers | plugin agents `safe-engine:<role>` ([delegation](#delegation)) | the brief names the role ([delegation](#delegation)) | same |

Python runs as `python`, `python3` or `py -3` (Windows). Claude Code hooks need a POSIX `sh` (Git Bash on Windows): the plugin sources `run-gate.sh` in the shell Claude Code already starts for a hook, so a call with no factory run starts no other process. The Codex and Cursor Windows command checks for an active run in Python before loading the gate. Ticket checks use the GitHub CLI `gh` when the tracker is GitHub.

New runs use explicit [quiet wait receipts](waiting.md), not an assumed `background_tasks` list. Codex native subagent final results are delivered to the coordinator; Claude Code documents background subagent completion notifications in a later turn ([subagents](https://code.claude.com/docs/en/sub-agents)). Register only acknowledged finite work with that actual route. Cursor and arbitrary jobs have no verified adapter route here; use their supported event wait tool. A SubagentStop hook can request continuation and is not a terminal callback. Receipts themselves never notify the host. Existing runs retain the previous background-list rule until they explicitly register a wait; observer/persistent entries do not qualify.

Reference commands are written for a POSIX shell: run them in Git Bash on Windows. PowerShell 5.1 breaks `{owner}/{repo}` placeholders and nested quotes in `--jq` filters. Stuck in PowerShell: replace the placeholders with real names and pass each jq filter in single quotes, inner double quotes escaped as `\"`.

Safe review picks an installed reviewer that did not build the candidate: `review --agent auto --builder <name>`. Builders are detected from `CLAUDECODE`, `CODEX_THREAD_ID` and `CURSOR_AGENT`; when the builder is unknown and several agents are installed, review asks for `--builder`. No agent CLI: hand `review-packet` to a fresh read-only subagent, then `review --report <file> --reviewer <id>`.

## Claude Code

The plugin brings `/safe-engine`, `/improve-factory`, the gate hooks and the delegate role agents ([delegation](#delegation)). Its root is the repository's `skills/` folder. Pick one route:

- **Installer:** `python fast_gate.py install --host claude` adds the marketplace over HTTPS with auto-update and enables the plugin in `~/.claude/settings.json`, keeping a backup. It then installs the plugin at user scope with the Claude Code CLI and confirms `claude plugin list --json` shows it installed and enabled; otherwise it exits 1 with the fix. CLI lookup: `SAFE_ENGINE_CLAUDE`, `PATH`, `~/.local/bin`, then the newest `%APPDATA%\Claude\claude-code\<version>\<build>\claude.exe` the Windows desktop app keeps.
- **Settings by hand** (desktop app): add these keys to `~/.claude/settings.json`, then start a new session. Enabled is not installed: Claude Code may register the marketplace and never fetch the plugin, so check `/plugin` or `claude plugin list`, and install from there when it is missing:

  ```json
  "extraKnownMarketplaces": {"ai-software-factory": {"source": {"source": "git", "url": "https://github.com/seifsg/ai-software-factory.git"}, "autoUpdate": true}},
  "enabledPlugins": {"safe-engine@ai-software-factory": true}
  ```

- **Terminal:** `claude plugin marketplace add https://github.com/seifsg/ai-software-factory.git`, then `claude plugin install safe-engine@ai-software-factory`. Use the HTTPS URL; the `owner/repo` shorthand tries SSH first.

Command argument registration lives in the gate's sibling `fast_cli.py`; installed copies include it. The gate keeps hook dispatch direct and routes project commands through the selected bundle before parsing arguments.

## Delegation

The roles (runner, analyst, maker, builder, reviewer), their tiers and the brief, gate and handback rules live in `.agents/skills/safe-engine/references/delegate.md`. Hosts differ only in how a role gets its model, effort and edit limits, and how the owner overrides them. The owner's own session model and effort never change.

Use each host's fresh-context option for focused helper packets; for Codex native delegation, `fork_turns="none"` omits inherited history. Pass the request, current decisions, interfaces, stops and relevant artifact paths explicitly. Full history is an exception with a recorded reason, not a substitute for a brief. Keep short jobs local and use native completion/wait events instead of coordinator polling. This changes no installed model, permissions or global settings.

| | Claude Code | Codex | Cursor | Other agents |
|---|---|---|---|---|
| Roles | plugin agents `safe-engine:runner`, `analyst`, `maker`, `builder`, `reviewer` from `skills/agents/`; when they are missing (plugin off or older), a general-purpose agent with the tier's `model` and `effort` per call, told in its brief to stay read-only (read-only roles) and never to spawn | none shipped: the brief names its role | none shipped: the brief names its role | the brief names its role |
| Tier models, light / standard / deep | `haiku` low / `sonnet` medium / `opus` high, pinned in each agent file | unknown: no documented tier models; the spawn prompt asks for effort `low` / `medium` / `high`, and the model stays the parent's unless the owner sets one | unknown: no documented tier models; a subagent's `model` defaults to `inherit` | unknown: the session's model |
| Read-only roles | a `tools` allowlist (read, search, shell, web) without write tools (a name the host lacks, such as `PowerShell` off Windows, was dropped on 2.1.308: observed, undocumented). The shell stays, so shell writes are barred by instruction only. No role gets `Agent`: only the coordinator spawns | by instruction only: an agent file cannot give a subagent its own read-only sandbox | `readonly: true` in an owner's agent file; otherwise by instruction | by instruction |
| Session ceiling | a role above the session's tier: the coordinator passes the Agent tool's `model` with the session's alias | the parent's model, unless the owner sets one | same | not applicable |
| Owner override | ask in chat: the coordinator passes `model` and `effort` per Agent call, which beat the agent file (per-call effort: v2.1.292 or later); for every delegate, `CLAUDE_CODE_SUBAGENT_MODEL` with `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`; `CLAUDE_CODE_EFFORT_LEVEL` beats agent and per-call effort, and sets the session's too | an agent file in `~/.codex/agents/` or `.codex/agents/` named for the role, with `model` and `model_reasoning_effort`: it beats what a spawn asks. `agents.default_subagent_model` and `agents.default_subagent_reasoning_effort` in `config.toml` are only defaults below a spawn's ask | an agent file in `.cursor/agents/` (beats `~/.cursor/agents/`) named for the role, with `model: <id>[effort=<level>]`; plan, admin and Max Mode limits may still fall back | the host's own means |
| Models used | `/tasks` names each subagent's model and effort; `claude -p --output-format json` (or `stream-json`) ends with `modelUsage` per model, and each subagent's transcript records its `model` and `effort` (observed on 2.1.308, undocumented) | unknown | the subagent task card and the usage dashboard name the model that ran | unknown |

Safe review's reviewer CLI (`review --agent`) passes no model or effort: it runs on that CLI's own defaults, the owner's settings. Sources: Claude Code [subagents](https://code.claude.com/docs/en/sub-agents), [plugin components](https://code.claude.com/docs/en/plugins/components), [CLI reference](https://code.claude.com/docs/en/cli-reference) · Codex [subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [config reference](https://learn.chatgpt.com/docs/config-file/config-reference) · Cursor [subagents](https://cursor.com/docs/context/subagents).

## Other agents

| Agent | Skills | Gate | Safe reviewer |
|---|---|---|---|
| GitHub Copilot | reads `.agents/skills`, `~/.agents/skills` | `.github/hooks/*.json`, PascalCase `PreToolUse` → `sh <launchers>/safe-engine/scripts/run-gate.sh copilot` (exit 2 denies); `SessionStart` → `... run-gate.sh copilot update` | review packet |
| Gemini CLI | reads `.agents/skills` | `BeforeTool` hook → `sh <launchers>/safe-engine/scripts/run-gate.sh gemini` (exit 2 denies); `SessionStart` → `... run-gate.sh gemini update` | review packet |
| OpenCode | reads `.agents/skills` | no declarative hooks: run `fast_gate.py` yourself | review packet |
| Anything else | point it at `.agents/skills/safe-engine/SKILL.md` | `fast_gate.py` by hand | review packet |

Their hooks show no gate progress messages: the agent relays the card from the gate's command output.

`fast_gate.py install --host other` copies the launchers into `~/.agents/skills` (or `--project <dir>`). Run hooks through `run-gate.sh`: it fails open when Python or the gate is missing. Unknown hosts get a generic reader: pre-tool events deny with exit code 2 and the reason on stderr; stop and prompt hooks need a first-class adapter.

## Updates

Every install records this machine's channel in `~/.safe-engine/install.json` (`install --channel stable|edge`, kept until changed; stable by default). New projects follow it: the launcher's resolver pins the newest release tag on `main` whose files match its manifest, or `main` on edge and while no release exists.

**Claude Code** updates through its marketplace. The marketplace entry is a `git-subdir` source pinned to the release tag (`ref: vX.Y.Z`) and the plugin manifest carries the same `version`, so Claude Code fetches exactly that tag and keeps its cached copy until a release changes the version; a tag not yet pushed leaves the installed copy in place. Claude Code has no channels: the edge channel changes what new projects pin; to run the gate and launchers of `main`, disable the plugin (`claude plugin disable safe-engine@ai-software-factory`) and start Claude Code with `--plugin-dir <clone>/skills`.

**Codex, Cursor and other**, installed from a Git clone, also record the clone, its revision and each `--host`/`--project` pair. A copy that is no Git clone, or a pinned project bundle under `~/.safe-engine/bundles/`, never updates. The session-start hook entry carries an `update` argument (`run-gate.sh <host> update`; the Windows command likewise). Before the gate loads, it runs `fast_update.py`, which at most once a day:

1. leaves the clone alone unless its origin is the factory repository, it has no local changes, it is on `main` or detached at a release tag or at the commit it last installed (where a rollback leaves it), and no open Fast or Lucky run in this gate home uses it as its bundle (a Safe run is not detected: pin Safe projects to a release bundle, the default, or another checkout). To keep a hand-picked commit, install from it with `--no-auto-update`;
2. fetches `main` and tags; a tag that moved on the remote fails the fetch, so nothing changes;
3. stable: checks out the newest `vX.Y.Z` tag whose commit is on `main` and passes the release check (version equal to the tag, every file matching the release manifest), trying older tags when one fails; edge, or stable before the first release: fast-forwards `main`;
4. when the revision differs from the last completed install, records the previous ref, revision and version in `install.json`, then reruns the clone's `fast_gate.py install` for each recorded install (it replaces each copy exactly);
5. an install that fails restores the previous revision and reruns its installer.

The gate's next `start`, `status` or `version` shows a one-time notice: the old and new version with pointers to `CHANGELOG.md` and `UPGRADING.md`, or the rollback. Offline, a diverged `main`, no verifying release, a missing Git or any other error changes nothing; the session goes on and `~/.safe-engine/logs/gate.log` gets an `update` line with the result. Projects keep their pinned bundle. Off: `SAFE_ENGINE_NO_UPDATE=1`, or `install --no-auto-update` (the last install decides); either way no extra process starts. Other hook entries are unchanged; a recorded install's session start starts one more Python (about 0.2 s on Windows). Agents with no session-start hook update by hand ([README](../README.md#-update)).

New-run selection is separate from installed-copy updates: `resolve_bundle.py --project <dir> --new-run` refreshes only automatic selections with no active or unknown run. `fast_gate.py start` prints selected/latest versions and executes that bundle's gate while holding the project selection lock. Project commands and hooks route to the active run's saved gate offline. Explicit and legacy-unknown pins stay fixed. Failed release checks identify the retained version. Named Safe runs release selection after cancellation or checked handoff with matching released claims and saved history. Hooks include bound sessions and absolute targets outside cwd; tool calls spanning different factory versions require separate sessions and calls per project. Bare starts without a receipt remain legacy use; see [install](install.md#what-first-use-does).

For factory maintenance, `improve-factory` keeps the selected gate runner separate from the editable candidate and any target app. A new candidate runtime selects its frozen runner with `resolve_bundle.py --project <candidate> --bundle <runner>`. An approved unmerged dependency can be the candidate base; active project selections stay pinned. Finish and commit planned edits before final proof. Use Prove if the selected runner supports it; otherwise run the required full suite directly on the committed candidate under its recorded gate workflow and retain runner, commit, inputs, command, log and result.

## Orchestrators

An orchestrator starts agent sessions and hands each one a task: [orchestrators.md](orchestrators.md).

## Evals

The repository-only rendered pilot is opt-in: `node evals/visual/run.cjs --repeat 3`.
It needs an existing resolvable Playwright installation and compatible Chromium;
`--browser <executable>` selects an existing browser explicitly. It installs nothing
and adds no factory startup, hook or completion step. Browser calibration is outside
the normal suite; three browser-free failure tests remain developer-suite work.
See [setup, output and limits](../evals/README.md#rendered-acceptance-pilot).

`python -m evals run` lives in the factory repository only (`evals/README.md`); installed copies leave `evals/` out. It takes each agent's non-interactive command as a template. The prompt arrives on stdin and also sits at `../prompt.md` from the workspace. In the factory arm, `{factory}` is a fresh export of the factory bundle. Real runs cost model tokens; check each flag against the installed version before one. Windows eval commands require job ownership before execution and confirmed descendant exit at cleanup; failures remain explicit, all registered stops are attempted, and unconfirmed ownership remains retryable. Isolated rubric children receive the canonical ownership helper from the pre-run source snapshot, without importing repository paths or site packages.

| Agent | `--agent` (plain arm, and factory arm unless overridden) | `--factory-agent` (factory arm) | Gate hooks in the factory arm |
|---|---|---|---|
| Claude Code | `claude -p --dangerously-skip-permissions` | `claude -p --dangerously-skip-permissions --plugin-dir {factory}/skills` | from the plugin directory |
| Codex | `codex exec --sandbox workspace-write --ignore-user-config -` | not needed | only from the user's `~/.codex/hooks.json` |
| Cursor | `agent -p --force "Read ../prompt.md and do what it says."` | not needed | only from the user's `~/.cursor/hooks.json` |

Claude Code: start `python -m evals` with `CLAUDE_CONFIG_DIR` set to an empty folder and `ANTHROPIC_API_KEY` set, so neither arm loads the user's plugins, hooks or `CLAUDE.md`, and only the factory arm loads the factory plugin with its gate hooks. The templates avoid `--bare`: the CLI reference says it skips hooks and installed plugins and does not say whether a `--plugin-dir` plugin's hooks still run.

Codex and Cursor read gate hooks only from the user's hooks file, which `fast_gate.py install --host codex|cursor` writes. Without that install, their factory arm follows the method and calls the gate by hand, with no hook enforcement. To measure enforcement, run the factory arm as a user or profile with the install and the plain arm as one without it. The plain arm must never see an installed factory (skills folder, plugin or hooks).

## Sources

Claude Code [hooks](https://code.claude.com/docs/en/hooks.md), [plugins](https://code.claude.com/docs/en/plugins/marketplace-reference.md), [headless](https://code.claude.com/docs/en/headless), [CLI reference](https://code.claude.com/docs/en/cli-reference), [environment variables](https://code.claude.com/docs/en/env-vars) · Codex [hooks](https://learn.chatgpt.com/docs/hooks.md), [skills](https://learn.chatgpt.com/docs/build-skills), [non-interactive](https://learn.chatgpt.com/docs/non-interactive-mode) · Cursor [hooks](https://cursor.com/docs/agent/hooks), [skills](https://cursor.com/docs/context/skills), [headless CLI](https://cursor.com/docs/cli/headless) · Copilot [hooks](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-hooks-reference) · Gemini CLI [hooks](https://geminicli.com/docs/hooks/reference/) · OpenCode [plugins](https://opencode.ai/docs/plugins/) · [Agent Skills](https://agentskills.io) · [AGENTS.md](https://agents.md)
## Lane resources

```text
python skills/safe-engine/scripts/fast_gate.py lane start --project <absolute-lane-folder> --name <lane> --ports 5281,5282 -- <executable> <arguments>
python skills/safe-engine/scripts/fast_gate.py lane status --project <absolute-lane-folder> --name <lane>
python skills/safe-engine/scripts/fast_gate.py lane stop --project <absolute-lane-folder> --name <lane> [--generation <returned-generation>]
```

Use an executable and separate arguments; for shell syntax explicitly launch the host shell. The command runs with `cwd` equal to `--project`. `start` acknowledges process ownership, not HTTP readiness. A supervisor keeps ownership when a command parent exits. `stop` requests only that generation, attempts console/session shutdown, then forces its retained tree after a bounded grace period. It checks declared IPv4 TCP ports by binding them. An occupied port refuses startup or reports incomplete port cleanup; it never authorizes killing an occupant. A stale supervisor identity refuses stop and never signals a reused PID. A replacement generation rejects an old `--generation`.

Windows uses kill-on-close Job Objects, assigned before command execution, and does not allow breakaway. Shutdown seals new child creation, retains member handles, tries console grace, then forces the job and waits up to ten seconds for signaled handles and zero active members. Shutdown hooks cannot launch new children after stop starts. Console grace requires a shared console and may be unavailable. An unconfirmed stop raises an error; a lane keeps its supervisor and `cleanup_failed` state for an explicit `lane stop` retry. A supervisor crash closes its job.

POSIX commands use a retained session guardian; command exit does not reap it or release the process-group identity before shutdown signals finish. After its final signal and guardian reap, stop observes group absence for up to ten seconds before confirming cleanup. Retries only observe after that signal; they never kill a reused group. Remaining zombies, inaccessible or reused groups can conservatively report unconfirmed cleanup. This requires default `SIGCHLD` handling and exclusive reaping of the guardian by its owner. Linux lanes also use `/proc` supervisor creation identity. Other platforms do not currently support the persistent lane launcher. Processes deliberately started through external services or outside the session are not owned; do not use such launch modes for lane stacks. Linux/macOS guardian behavior and supervisor-crash cleanup remain unverified on native runtimes and have no Windows job guarantee.

State and stdout live in `<project>/.factory/lanes/<name>/`. Resources use a hashed generation under the account's local temp `factory-lanes/`, independent of workspace and overridden `TMP` depth. `status` exposes the resource path, owner creation identity and current job member PIDs (the retained guardian PID on Linux). Resource/cache folders remain after stop for inspection and reuse decisions; remove only an owned generation after its processes stop. Screenshot browser profiles use unique short children there and are removed after confirmed shutdown. Screenshot cleanup attempts every acquired server even if another fails. Its `CleanupError` retains failed owners in `failures`, preserved artifact `paths`, and a `retry()` method for a live Python caller. Unconfirmed cleanup preserves the base worktree and affected browser profile; the CLI prints retained paths and exits nonzero. CLI exit cannot retain retry ownership: Windows job closure still requests termination, while POSIX has no supervisor-crash cleanup guarantee. Inspect preserved artifacts and confirm shutdown before removing them. Arguments after `--`, including child `--help` or `--project`, pass unchanged through an installed entry to its selected bundle.

Every lane command receives `CARGO_TARGET_DIR` and `CARGO_BUILD_BUILD_DIR` for Cargo build artifacts, `npm_config_cache` for npm package downloads, `PYTHONPYCACHEPREFIX` for Python bytecode, and `FACTORY_CACHE_DIR` for other tools configured explicitly by the caller. Screenshot setup/server commands receive the same adapters keyed by their checkout. These are process environment settings, never global configuration. Tool flags can override them; record actual writes before claiming isolation. No automatic cache support is claimed for arbitrary bundlers. Browser harnesses use `FACTORY_PROFILE_DIR` or `safe_engine.resources.profile(identity)` and must pass that path to their browser's profile option; environment alone does not configure every browser.

Delegate hosts with a cwd/workdir setting must set it to the absolute lane folder. Hosts without it pass an explicit workdir per tool call. The helper's first action prints and compares its actual cwd before any write. The Paperclip adapter already sets its configured project's `cwd`; newly created worktree lanes must pass their own path. No prompt can claim a host changed directories without that check.
