# Hosts

Contents: first-class hosts · delegation · other agents · sources

Methods are host-neutral. This page = what differs per agent: where skills live, how a step loads its skill fresh, how hooks are wired, how delegates get their model.

## First-class hosts

| | Claude Code | Codex |
|---|---|---|
| Install | plugin, root `.agents/` ([install](install.md#claude-code)) | plugin, root `.agents/`, or copied skills + `~/.codex/hooks.json` ([install](install.md#codex)) |
| Invoke | `/safe-factory …` | `$safe-factory …` |
| Load a step's skill fresh | the Skill tool, `safe-factory:<name>` | `$<name>`, or read its `SKILL.md` |
| What compaction keeps | the first 5k tokens of each recently used skill, 25k in total; CLAUDE.md is re-read | AGENTS.md and the skill list; skill bodies are dropped |
| Stop guard | `Stop` hook in the `safe-factory` skill's frontmatter, so it exists only once that skill loads through the Skill tool or `/safe-factory` and other sessions start no process (tested on 2.1.309: survives later turns and compaction, gone after a process resume). The agent loading it needs permission: an allow rule, auto mode or the owner's yes. Also checks each ticked step's block opened a chat message (transcript text blocks) | `Stop` hook in `hooks/portable.json`, which the manifest names and which replaces `hooks/hooks.json`; runs in every session; trust once in `/hooks`; no block check (other transcript format) |
| Compact hook | plugin `SessionStart`, matcher `compact\|resume`; stdout becomes context | `SessionStart`, matcher `compact\|resume`; stdout becomes developer context |
| Guard output | `{"decision":"block","reason":…}`: the next step's prompt; Claude Code overrides after 8 blocks in a row, a count every tool call resets, so one step per turn never reaches it | same JSON; each reason becomes a user-role hook prompt and each phase has its own final response. Codex groups these rounds under one outer native turn ID |
| Fresh-context delegate | Agent tool with a plugin role | `spawn_agent` with `fork_turns: "none"` |
| Checker | `safe-factory:checker` | `spawn_agent`, `fork_turns: "none"`, `reasoning_effort: "low"`, message = the [checker](../.agents/skills/safe-factory/references/checker.md) brief plus `.agents/agents/checker.md`'s body |
| Live preview and captures | the desktop app's browser pane (`preview_start`, `.claude/launch.json`, then show the browser pane so the owner sees it) keeps the dev server the owner watches and takes every screenshot; the agent and the owner see them in chat, but the pane saves no file, so the PR carries `pane:` observations instead of image files | the browser or screenshot tool the session has |
| Background jobs | background subagents report back in a later turn: set `Waiting: jobs: … (max <n> min)` first; the guard also lets the stop through when the Stop input's `background_tasks` lists a running subagent (a background shell such as a dev server does not count), until the deadline | subagent results arrive in the parent: set `Waiting: jobs: … (max <n> min)` while they run |
| Gate and review proof | `transcript_path` → `<session>/subagents/agent-<id>.jsonl` for every session of the run, oldest first: first line the brief (`Role: checker. Gate X` or `Role: reviewer`), its own last handback the verdict | no per-agent file: the id must appear in `transcript_path` (never accepted for a Claude Code transcript); the handback text is not checked (weaker) |
| Night session | `claude -p --permission-mode dontAsk --settings <clone>/.agents/hooks/claude-settings.json "/safe-factory Resume <dir>"` (live: denied commands fail without a prompt, allowed ones run) | `codex exec -s workspace-write -c 'approval_policy="never"' "$safe-factory Resume <dir>"` (live on Windows: flags accepted, no prompt, but the sandboxed exec helper ran nothing, so `night.sh` first runs one sandboxed command and refuses when it does not run) |
| Deny rules | `claude-settings.json` `permissions.deny` (Bash prefixes, `Edit` paths); a command hidden in `sh -c` or a script escapes them | `~/.codex/rules/factory.rules` `prefix_rule(..., decision = "forbidden")`: leading arguments only |
| Watchdog resume | `claude -p -r <session> --permission-mode dontAsk --settings <template> "<prompt>"` | `codex exec resume -c 'approval_policy="never"' -c 'sandbox_mode="workspace-write"' <session> "<prompt>"` (not yet run live) |

Every host runs `run-guard.sh` through a POSIX `sh`; on Windows that is Git Bash. Plugin hook commands start with `git --git-dir=/nonexistent -c alias…` (Git's `sh`, `GIT_DIR` unset, exit 0 always), so a host that runs them in PowerShell (Cursor on Windows) still reaches Git's `sh`. Codex can launch hook commands in PowerShell or cmd, so its `commandWindows` entries use `.agents/hooks/windows.cmd` to locate Git Bash beside `git.exe` on `PATH` and preserve native stdin/stdout. Missing Git Bash prints an actionable notice without continuing the factory. Finds the run in order: the session file `${XDG_CACHE_HOME:-~/.cache}/ai-software-factory/sessions/<session id>`, nearest `.factory/run.md` inside session's checkout (walking up from the hook input's `cwd`, else the hook's own directory: a desktop worktree session's hook may start elsewhere), then the `**Workspace:**` path of a step block opening the turn's last message. A step block naming a run rebinds first. A desktop worktree session cannot change folder, so its run often lives elsewhere; a step block with no findable run blocks once and asks, then warns the owner. A stopped or finished run deletes its session file; files over 30 days go at the next bind. A worktree's run stays separate from its parent's. Also reads that session's subagent files and, on Claude Code, the run's session transcripts (posted step blocks). State: `.factory/guard/state` (single-quoted `g_*` lines; anything else reported and ignored). Ignores runs untouched for 12 hours. Runs once per turn end, never per tool call. `night.sh` and `watchdog.sh` in `.agents/hooks/` call the host CLIs above; `FACTORY_CLAUDE` and `FACTORY_CODEX` name a CLI off PATH (desktop installs), `FACTORY_START`, `FACTORY_RESUME`, `FACTORY_FRESH` and `FACTORY_NOTIFY` replace the commands, `FACTORY_IDLE_TURNS` (6) and `FACTORY_JOB_MAX` (120 min) tune the guard.

## Delegation

Roles (runner, analyst, maker, builder, reviewer, checker), their tiers and brief, gate and handback rules live in `.agents/skills/safe-factory/references/delegate.md`. Hosts differ only in how a role gets model, effort and edit limits. Owner's own session model and effort never change.

Pass request, decisions, interfaces, stops and artifact paths explicitly; full history needs a reason. Keep short jobs local.

| | Claude Code | Codex |
|---|---|---|
| Roles | plugin agents `safe-factory:<role>` from `.agents/agents/`; when missing, a general-purpose agent with the tier's `model` and `effort`, told to stay read-only where the role is | none shipped: the brief names its role |
| Tier models, light / standard / deep | `haiku` low / `sonnet` medium / `opus` high, pinned in each agent file | the spawn asks for effort `low` / `medium` / `high`; the model stays the parent's unless the owner sets one |
| Read-only roles | a `tools` allowlist without write tools; shell writes barred by instruction | by instruction only |
| Session ceiling | a role above the session's tier runs on the session's model | the parent's model, unless the owner sets one |
| Owner override | per-call `model` and `effort`; `CLAUDE_CODE_SUBAGENT_MODEL` with `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`; `CLAUDE_CODE_EFFORT_LEVEL` | an agent file in `~/.codex/agents/` or `.codex/agents/` named for the role, with `model` and `model_reasoning_effort` |

## Other agents

| Agent | Skills | Hooks |
|---|---|---|
| Cursor | plugin, root `.agents/` (`.cursor-plugin/plugin.json`: skills, agents), [install](install.md#cursor) | runs `hooks/portable.json`, named by its manifest (fills in `${CLAUDE_PLUGIN_ROOT}`; Windows: in PowerShell), and Claude Code's installed plugins too, whose hook file has no Stop: install one, not both |
| GitHub Copilot, Gemini CLI, OpenCode | read `.agents/skills` | none wired: apply the run-file rules by hand |
| Anything else | point it at `.agents/skills/safe-factory/SKILL.md` | none |

Guard live: step 0 checks the skill brought its hook or the hook entry predates the session (hooks added mid-session never load), and step 1 finds `.factory/guard/state`. Not live on a host with hooks: the run moves to a fresh session with `safe-factory Resume <run folder>`. On a host without hooks, Fast chains steps in one turn, one block message per step, never waits and never ends a turn with the run open and `Waiting: none`; Safe ends each step with `Say go for step <n>`. Each step still rereads `.factory/run.md` and loads the `Next:` skill fresh; checker gates and PR review still apply.

## Sources

Claude Code [hooks](https://code.claude.com/docs/en/hooks.md), [hooks guide](https://code.claude.com/docs/en/hooks-guide.md), [skills](https://code.claude.com/docs/en/skills.md), [subagents](https://code.claude.com/docs/en/sub-agents.md), [plugins](https://code.claude.com/docs/en/plugins/marketplace-reference.md) · Codex [hooks](https://learn.chatgpt.com/docs/hooks), [subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [skills](https://learn.chatgpt.com/docs/build-skills), compaction in [`codex-rs/core/src/compact.rs`](https://github.com/openai/codex/blob/main/codex-rs/core/src/compact.rs).
