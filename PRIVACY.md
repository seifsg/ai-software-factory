# Privacy

AI Software Factory is a set of skills and local scripts. Its author runs no server and receives no data from it.

## What is collected

Nothing by the author: no telemetry, accounts or analytics.

## What leaves your machine

- **Update check:** a request to GitHub's public API for the latest release, by `gh` or `curl`, at a run's first step (Claude Code) or at session start (Codex, Cursor). GitHub sees the request as it sees any other. Turn it off with `FACTORY_NO_UPDATE_CHECK=1`.
- **Your work:** tickets, branches, commits and pull requests go to the repository and tracker you use, through your own `git` and `gh`.
- **Your agent:** your conversation goes to your AI provider as usual. On Claude Code, the Stop hook's check runs on Claude Code's background model.

## What stays on your machine, and for how long

- `.factory/` in your project: the run file, guard state and proof files. Git ignores it. Delete it whenever you like.
- `ai-software-factory` in your cache folder: the latest version seen, session links (removed after 30 days) and any backups `doctor.sh --fix` made. Delete it whenever you like.

The doctor reads your agent settings files, only to list leftovers of old factory versions.

On Claude Code the plugin reads no conversation or chat history. Overnight tools, which you install apart from a clone, read the running session's delegate files to prove gates; they stay on your machine.

## Contact

Open an issue: https://github.com/seifsg/ai-software-factory/issues
