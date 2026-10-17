# Paperclip

Paperclip schedules agents, assigns them tasks and wakes them on a heartbeat. With this setup each woken agent runs the factory, so a task ends in a proven draft PR instead of a bare agent run.

No adapter code is needed. Paperclip's built-in `claude_local` and `codex_local` adapters run the agent. Their `instructionsFilePath` field points at [paperclip-agent.md](paperclip-agent.md), which tells the agent to run `safe-engine` on each task.

## Flow

```text
board assigns task ─► heartbeat ─► agent checks out task ─► safe-engine in a fresh worktree
                                        │                          │
                       question ◄───────┤                          ├─► draft PR + proof
       (in_review, board answers,       │                          │     (work product, in_review,
        wake resumes the same session)  │                          │      issue monitor)
                                        │                          ▼
                                        └──────── CI red / review comment wakes the agent again
                                                                   ▼
                                                    human merges ─► task done
```

## Setup

1. On the machine that runs the agents, install the factory for each agent (`docs/install.md`) and sign in to the GitHub CLI (`gh auth login`). Keep a factory checkout; its `docs/paperclip-agent.md` is the instructions file.
2. Add the product repository to a Paperclip project as its workspace.
3. Create the agent with one of the configs below. Replace the paths with absolute ones.
4. Set the agent's monthly budget in Paperclip. The budget is the hard stop for spend.
5. Assign it a task written like a factory request: what to build and what success means.

Claude Code:

```json
{
  "name": "Factory engineer (Claude Code)",
  "adapterType": "claude_local",
  "adapterConfig": {
    "engine": "cli",
    "cwd": "/abs/path/product",
    "instructionsFilePath": "/abs/path/ai-software-factory/docs/paperclip-agent.md",
    "workspaceStrategy": {"type": "git_worktree", "baseRef": "origin/main"},
    "timeoutSec": 3600
  }
}
```

Codex:

```json
{
  "name": "Factory engineer (Codex)",
  "adapterType": "codex_local",
  "runner": "legacy",
  "adapterConfig": {
    "engine": "cli",
    "cwd": "/abs/path/product",
    "instructionsFilePath": "/abs/path/ai-software-factory/docs/paperclip-agent.md",
    "workspaceStrategy": {"type": "git_worktree", "baseRef": "origin/main"},
    "timeoutSec": 3600
  }
}
```

`engine: "cli"` runs the plain CLI, which loads the user's installed plugin, skills and hooks. The ACP engine and Paperclip Runner are untested with the factory.

## Gate enforcement

| Agent | Skills | Gate hooks |
|---|---|---|
| Claude Code, local target | the installed plugin | enforced: the CLI uses the host's Claude config |
| Codex | `~/.agents/skills` | not enforced by default: Paperclip gives each agent its own `CODEX_HOME`, which lacks the factory's `hooks.json` and its trust. The agent calls the gate by hand, as on other hosts. |
| Remote or sandbox targets | unverified | unverified: Paperclip uploads a sanitized config seed |

## Limits

- Untested end to end: no live Paperclip run with the factory has been recorded yet.
- `timeoutSec` caps one heartbeat. A run cut off by it should resume on the next wake from its recorded step (unverified); raise the cap for big features.
- Kickoff questions wait for a board user, so a product or big feature pauses at kickoff. Lucky mode asks nothing.
- Paperclip's adapters never push. The agent pushes its own branch when it opens the draft PR, as in any factory run.

## Sources

Paperclip [repository](https://github.com/paperclipai/paperclip): `docs/adapters/claude-local.md`, `docs/adapters/codex-local.md`, `skills/paperclip/SKILL.md`, `packages/adapters/AUTHORING.md`.
