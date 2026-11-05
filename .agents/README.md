# Safe Factory

Delivers games, apps, services, tools and libraries in ten visible steps: ticket, analyze, recommend, challenge, plan, Before proof, build, verify, draft PR and review. Twelve skills and six delegate roles. Humans decide ready, merge and release.

## Try it

- `/safe-factory:safe-factory Build a small habit tracker web app`
- `/safe-factory:safe-factory safe: fix the crash when the login form is empty`
- `/safe-factory:how-to-review-a-pr Review pull request 12`

## What it runs

- A prompt Stop hook, added when a run loads the `stop-check` skill right before a block or todo line: at that turn end a small model reads the last message, and sends the next step only on a step or todo number not seen yet. Nothing runs in sessions that never load it. Any other message ends the turn, so in scripted tests on Haiku and Sonnet a looping agent stopped below the turn limit: very likely, not certain. A run can also stop early: say go on. Esc always stops a run.
- `scripts/run-guard.sh check`, which the skill tells the agent to run: reads `.factory/run.md` and Git, prints the next step. It reads no conversation.
- `scripts/update-check.sh` at step 0, and `scripts/doctor.sh`, which lists leftovers of old versions by reading your agent settings; `--fix` moves them to a backup.
- `git` and `gh`, as each step needs them. Your agent's permissions still decide.

## What it sends and fetches

- It sends nothing to the factory's author, and has no telemetry.
- The update check asks GitHub's public API for the latest release, through `gh` or `curl`. Turn it off with `FACTORY_NO_UPDATE_CHECK=1`.
- Tickets, branches and pull requests go to the repository and tracker you choose.
- The hook's small model is Claude Code's own background model, under your Claude terms.

Files stay on your machine: `.factory/` in your project, and `ai-software-factory` in your cache folder.

## Troubleshooting

- A run stops between steps: `/safe-factory:safe-factory Resume <folder>`. Each step brings the Stop check back after a stop or a resumed session.
- A permission prompt on every step: allow `Skill(safe-factory:*)`, and choose always allow for `run-guard.sh check`.
- The run file reads wrong: `.factory/run.md` needs `Status:`, `Next:` and `Waiting:` spelled exactly.

[Privacy](https://github.com/seifsg/ai-software-factory/blob/main/PRIVACY.md) · [Security](https://github.com/seifsg/ai-software-factory/blob/main/SECURITY.md) · [Full guide](https://github.com/seifsg/ai-software-factory#readme)
