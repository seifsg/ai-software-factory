# Hosts

Contents: first-class hosts · delegation · other agents · sources

The methods are host-neutral. This page holds what differs per agent: where skills live, how a step loads its skill fresh, how the hooks are wired and how delegates get their model.

## First-class hosts

| | Claude Code | Codex |
|---|---|---|
| Install | plugin, root `.agents/` ([install](install.md#claude-code)) | copied skills + `~/.codex/hooks.json` ([install](install.md#codex)) |
| Invoke | `/safe-engine …` | `$safe-engine …` |
| Load a step's skill fresh | the Skill tool, `safe-engine:<name>` | `$<name>`, or read its `SKILL.md` |
| What compaction keeps | the first 5k tokens of each recently used skill, 25k in total; CLAUDE.md is re-read | AGENTS.md and the skill list; skill bodies are dropped |
| Stop guard | plugin `Stop` hook, sourced in the hook shell | `Stop` hook; trust once in `/hooks` |
| Compact hook | plugin `SessionStart`, matcher `compact\|resume`; stdout becomes context | `SessionStart`, matcher `compact\|resume`; stdout becomes developer context |
| Guard output | `{"decision":"block","reason":…}`: the next step's prompt; Claude Code overrides after 8 blocks in a row, a count every tool call resets, so one step per turn never reaches it | same JSON; the reason arrives as a new prompt |
| Fresh-context delegate | Agent tool with a plugin role | `spawn_agent` with `fork_turns: "none"` |
| Checker | `safe-engine:checker` | `spawn_agent`, `fork_turns: "none"`, `reasoning_effort: "low"`, message = the [checker](../.agents/skills/safe-engine/references/checker.md) brief plus `.agents/agents/checker.md`'s body |
| Live preview and captures | the desktop app's browser pane (`preview_start`, `.claude/launch.json`, then show the browser pane so the owner sees it) keeps the dev server the owner watches and takes every screenshot; the agent and the owner see them in chat, but the pane saves no file, so the PR carries `pane:` observations instead of image files | the browser or screenshot tool the session has |
| Background jobs | background subagents report back in a later turn: set `Waiting: jobs: …` first; the guard also lets the stop through when the Stop input's `background_tasks` lists a running subagent (a background shell such as a dev server does not count) | subagent results arrive in the parent: set `Waiting: jobs: …` while they run |

Both hosts run `run-guard.sh` through a POSIX `sh`; on Windows that is Git Bash. It reads only the nearest `.factory/run.md` inside the session's current checkout, so a worktree's run stays separate from its parent's. It ignores runs untouched for 12 hours and costs about 65 ms with no run and 150 ms with one, once per turn end.

## Delegation

The roles (runner, analyst, maker, builder, reviewer, checker), their tiers and the brief, gate and handback rules live in `.agents/skills/safe-engine/references/delegate.md`. Hosts differ only in how a role gets its model, effort and edit limits. The owner's own session model and effort never change.

Pass the request, decisions, interfaces, stops and artifact paths explicitly; full history needs a reason. Keep short jobs local.

| | Claude Code | Codex |
|---|---|---|
| Roles | plugin agents `safe-engine:<role>` from `.agents/agents/`; when missing, a general-purpose agent with the tier's `model` and `effort`, told to stay read-only where the role is | none shipped: the brief names its role |
| Tier models, light / standard / deep | `haiku` low / `sonnet` medium / `opus` high, pinned in each agent file | the spawn asks for effort `low` / `medium` / `high`; the model stays the parent's unless the owner sets one |
| Read-only roles | a `tools` allowlist without write tools; shell writes barred by instruction | by instruction only |
| Session ceiling | a role above the session's tier runs on the session's model | the parent's model, unless the owner sets one |
| Owner override | per-call `model` and `effort`; `CLAUDE_CODE_SUBAGENT_MODEL` with `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`; `CLAUDE_CODE_EFFORT_LEVEL` | an agent file in `~/.codex/agents/` or `.codex/agents/` named for the role, with `model` and `model_reasoning_effort` |

## Other agents

| Agent | Skills | Hooks |
|---|---|---|
| Cursor | reads `.agents/skills` | its `stop` hook expects a different reply; not wired yet: apply the run-file rules by hand |
| GitHub Copilot, Gemini CLI, OpenCode | read `.agents/skills` | none wired: apply the run-file rules by hand |
| Anything else | point it at `.agents/skills/safe-engine/SKILL.md` | none |

Without hooks, the agent ends each step with `Say go for step <n>`; the owner's `go` starts the next turn, which rereads `.factory/run.md` and loads the `Next:` skill fresh; the checker gates and the PR review still apply.

## Sources

Claude Code [hooks](https://code.claude.com/docs/en/hooks.md), [hooks guide](https://code.claude.com/docs/en/hooks-guide.md), [skills](https://code.claude.com/docs/en/skills.md), [subagents](https://code.claude.com/docs/en/sub-agents.md), [plugins](https://code.claude.com/docs/en/plugins/marketplace-reference.md) · Codex [hooks](https://learn.chatgpt.com/docs/hooks), [subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [skills](https://learn.chatgpt.com/docs/build-skills), compaction in [`codex-rs/core/src/compact.rs`](https://github.com/openai/codex/blob/main/codex-rs/core/src/compact.rs).
