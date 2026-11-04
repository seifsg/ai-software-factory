# Safe Factory

Delivers games, apps, services, tools and libraries in ten visible steps: ticket, analyze, recommend, challenge, plan, Before proof, build, verify, draft PR and review. Eleven skills and six delegate roles. Humans decide ready, merge and release.

## What it runs

- A prompt Stop hook, added when the `safe-factory` skill loads: at each turn end a small model checks the last message and sends the next step. Nothing runs in sessions that never load the skill.
- `scripts/run-guard.sh check`, which the skill tells the agent to run: reads `.factory/run.md` and Git, prints the next step. It reads no conversation.
- `scripts/update-check.sh` at step 0, and `scripts/doctor.sh`, which lists leftovers of old versions.
- `git` and `gh`, as each step needs them. Your agent's permissions still decide.

## What it sends and fetches

- It sends nothing to the factory's author, and has no telemetry.
- The update check asks GitHub's public API for the latest release, through `gh` or `curl`. Turn it off with `FACTORY_NO_UPDATE_CHECK=1`.
- Tickets, branches and pull requests go to the repository and tracker you choose.
- The hook's small model is Claude Code's own background model, under your Claude terms.

Files stay on your machine: `.factory/` in your project, and `ai-software-factory` in your cache folder.

[Privacy](https://github.com/seifsg/ai-software-factory/blob/main/PRIVACY.md) · [Security](https://github.com/seifsg/ai-software-factory/blob/main/SECURITY.md) · [Full guide](https://github.com/seifsg/ai-software-factory#readme)
