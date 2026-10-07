---
name: safe-engine
description: "Load the complete private Safe Engine factory to build or resume games, apps, services and tools. Fast by default (tickets, quick research, owner questions, gated steps); lucky or safe on request. Factory maintenance uses improve-factory."
---

# Safe Engine

Load `https://github.com/seifsg/ai-software-factory`; run its complete methods in the target project. This folder only launches them. Analysis/planning/review requests keep their phase.

## Get the requirements

Needs Git and Python 3.9+. Safe local review uses the Codex CLI when present, otherwise the controller's review-packet fallback. Set them up on any OS without asking Seif to prepare the machine:

1. Find them: `git --version`; Python through `python3`, `python` or Windows `py -3`. Use the first that reports 3.9+, by full path, for every later command.
2. Missing or too old: install from the official source, user scope when possible.
   - Windows: `winget install -e --id Python.Python.3.12` and `winget install -e --id Git.Git`.
   - macOS: `brew install python git`. No Homebrew: `xcode-select --install` for Git, the python.org installer for Python.
   - Linux: the distro manager (`apt-get`, `dnf`, `pacman`, `zypper` or `apk`).
   - No admin or package manager: install [uv](https://docs.astral.sh/uv/getting-started/installation/) (`winget install astral-sh.uv`, `brew install uv` or its official installer), run `uv python install 3.12`, then `uv run --python 3.12 python ...`.
   - Codex CLI, Safe only and optional: [openai/codex](https://github.com/openai/codex) (`npm install -g @openai/codex` or `brew install --cask codex`).
3. Check the versions again. Report what was installed, from where.
4. Host asks before installs: ask once, naming each tool and source. Still blocked (no network, admin or approval): say what is missing. Fast and Lucky can read the bundle with Git alone: `git ls-remote https://github.com/seifsg/ai-software-factory main`, clone that SHA into `~/.safe-engine/bundles/<sha>`, detach, read it only; record steps by hand and report the gate as unavailable. Safe waits for Python.
5. Official sources only. No system settings beyond the install. No credentials in commands.

## Select the bundle

Preserve request, answers, authority and work. Establish the absolute target; read project rules, legacy `.factory/state.json`, ticket `.factory/runs/<key>/state.json`, selection and session/checkpoint records. Create directories only within requested scope. No second run or substituted demo.

If `references/local-app-diagnostics.md` or `references/local-small-change.md` exists here, read [local trials](references/local-trials.md) before selecting a method. Otherwise skip that reference. Trials never silently upgrade pins.

Use the Python and Git from [Get the requirements](#get-the-requirements) and authorized GitHub access. Locate the resolver beside this installed file; quote paths/use argument arrays:

```text
python3 <installed-skill>/scripts/resolve_bundle.py --entrypoint safe-engine --project <absolute-target>
```

New projects resolve private GitHub `main` once into `~/.safe-engine/bundles/<commit>`; excluded `.factory/entry-bundle.json` records selection. Existing selections resume offline at their recorded path/revision. `--ref <full-SHA>` pins a new selection; it cannot upgrade an existing one.

Legacy run without receipt: establish its original bundle from evidence and pass `--bundle <absolute-factory-root> --project <target>`. Unknown identity blocks dependent work. Preserve the run; never substitute latest, reset acceptance or rewrite state. Version/HEAD alone cannot identify dirty inputs.

Verify returned root, revision, dirty status, receipt and entrypoint. Record launcher identity separately. Dirty inputs need canonical checkpointing of diff/untracked hashes. Diagnose failures; keep selected bundles unchanged. Receipts certify neither QA nor compatibility.

## Read and execute

Follow Working iterations where present in the selected canonical method. Older pins keep their recorded method; no silent upgrade.

Mode: read canonical `.agents/skills/safe-engine/references/speed-modes.md` when the pin has it. No mode named means Fast. Fast and Lucky read the returned `entrypoint`, canonical `fast-run.md`, `product-bar.md` and the methods their table names; they create the epic and sub-issues and record every step with the gate beside this file, `scripts/fast_gate.py` (Claude Code expands `${CLAUDE_SKILL_DIR}/scripts/fast_gate.py`). After the resolver, before research: `python <gate> start --project <absolute-target> --key <slug> --mode fast|lucky --kind product|feature|change [--auth] [--no-ui] [--no-data] --request-file <file>`. Controller commands, checks and Codex review below are Safe only. Older pins without `fast-run.md` keep their recorded method.

Safe implementation: read canonical `.agents/skills/ticketing/SKILL.md` and `docs/ticketing.md` from the resolved bundle. Preferred authorized tracker MCP first; GitHub Issues default, Seif's existing choice. Confirm before/after scope. Every ticket gets an actually dispatched builder session and full cycle, even bounded fixes. Small Change keeps patches surgical; its six shortcuts remain for legacy unticketed work.

Ticket commands select `--ticket <key>`; initialization records `--session <real-builder-session-id>`. Preserve namespaced history, legacy state and active pins. Independent ticket worktrees may parallelize independent effects; shared epic checkouts serialize writers. The controller creates neither sessions nor worktrees. Missing ticketing in an old pin needs authorized trial/adoption; never skip gates or silently upgrade.

Read the whole returned `entrypoint`, its session contract, usage guide and method handoff. Read each complete method/reference when its phase needs it. The canonical method owns diagnostics, efficiency, research and PR routing. Missing guidance in an old pin requires an authorized trial/adoption; preserve the pin.

Execute once from bundle root against target. No recursive launcher or controller execution from the target directory. File loading is not completed delivery.

Before dependent work, inspect capabilities without launching product tests. Follow the tests-last order in canonical `docs/current-decisions.md`. New version-2 runs allow draft acceptance and seal reviewed checks at the end. Full local controller review needs authenticated Codex CLI; PR review separately follows canonical `docs/pr-workflow.md`. Report missing capabilities; installation provisions no cloud route, hooks, daemon or permissions. Preserve checkpoints and human release authority; unrequested product pilots stay deferred.

## Invoke

Codex: `$safe-engine Build [software/feature] in [absolute project path]. Success means [outcome].`

Claude Code (plugin or personal install): `/safe-engine Build [software/feature] in [absolute project path]. Success means [outcome].` The plugin also installs the gate hooks.

Modes: add `lucky` or `safe` after the command, e.g. `$safe-engine lucky Build ...`. Then `verify` or `promote` any time.

Resume: `$safe-engine Resume [absolute project path]. Preserve decisions, bundle and evidence.`

The complete bundle includes Improve Factory; no separate maintenance install needed. See source `docs/install-safe-engine.md` for setup/host limits. If discovery fails, read this file by explicit path.
