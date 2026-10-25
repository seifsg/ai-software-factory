# Orchestrators

An orchestrator wakes agents, hands each one a task and wakes it again when something changes. With the factory behind it, every task ends in a proven draft PR and no person starts a session or writes a prompt.

```text
task assigned ─► wake ─► safe-engine run in a fresh worktree ─┬─► question: ASK, wait, answer wakes the same task
                                                               ├─► draft PR: HANDOFF + WATCH
                                                               ├─► CI red / review comment ─► wake ─► fix, push
                                                               ├─► more work: SPAWN a task, picked up the same way
                                                               └─► human merges ─► FINISH
```

## How it works with any orchestrator

The agent follows `safe-engine`'s orchestrated run (`.agents/skills/safe-engine/references/orchestrated-run.md`). It speaks nine verbs: TASK, ASK, OWNER, REPORT, HANDOFF, WATCH, SPAWN, BLOCK, FINISH. A binding maps them to one orchestrator's API.

The orchestrator must:

1. Run Claude Code or Codex (any first-class host in [hosts.md](hosts.md)) with the factory installed, and inject an instructions file on every wake.
2. Give each task its own Git worktree of the product repository.
3. Wake the agent on assignment, on a person's answer and on a timer or PR event.
4. Hold questions for a person and show who answered.

| Orchestrator | Binding | Setup |
|---|---|---|
| Paperclip | `references/paperclip.md` | `fast_gate.py orchestrate paperclip` |
| Another | add `references/<name>.md` mapping the nine verbs, then an entry in `fast_orchestrate.py` | |

## Paperclip

You need a running Paperclip, its company id, the product repository cloned locally, Git, Python 3.9+, `gh auth login`, and the agent CLI signed in. From a factory checkout:

```sh
python skills/safe-engine/scripts/fast_gate.py orchestrate paperclip \
  --agent claude --company <company-id> --project /abs/path/product
```

It installs the factory for that agent, writes `~/.safe-engine/orchestrators/paperclip/instructions.md`, and creates the agent through the API, or updates it when one with the same name exists. Run it again with `--agent codex` for a Codex engineer.

| Flag | Default |
|---|---|
| `--api` | `http://127.0.0.1:3100` |
| `--name` | `Factory engineer (Claude Code)` or `(Codex)` |
| `--base-ref` | origin's default branch |
| `--timeout` | 3600 seconds per wake |
| `--token-env` | `PAPERCLIP_BOARD_TOKEN`: a board API key, for authenticated deployments |
| `--dry-run` | print the agent, change nothing |

Then set the agent's monthly budget in Paperclip (the hard stop for spend) and assign it a task: what to build and what success means.

The agent runs the plain CLI (`engine: "cli"`, Codex `runner: "legacy"`), which loads the factory's plugin, skills and hooks.

### Gate enforcement

| Agent | Gate |
|---|---|
| Claude Code | enforced: the plugin's hooks load from your Claude config |
| Codex | enforced after one step. Paperclip gives each Codex agent its own home, which lacks your hooks, so the setup makes a factory home (`~/.safe-engine/orchestrators/paperclip/codex-home`) with your login, your settings and the gate hooks. Codex runs a hook only after a person trusts it: run the printed `CODEX_HOME=... codex` once, open `/hooks` and trust the factory's hooks. The factory never writes or skips that trust. |

### Limits

- Remote and sandbox execution targets, the ACP engine and Paperclip Runner are untested with the factory.
- Product and big-feature kickoffs wait for a board user's answer. Lucky mode asks nothing.
