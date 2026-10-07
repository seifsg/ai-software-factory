---
name: improve-factory
description: "Load the complete private Safe Engine factory for isolated maintenance and independent review. Preserve active project progress. Product defects stay in delivery."
---

# Improve Factory

Load the complete factory; execute canonical Improve Factory. This launcher does not replace the user's methods.

Source: `https://github.com/seifsg/ai-software-factory`, branch `main`, private. Use existing authorized Git access. Never request tokens in chat or make it public.

## Get the requirements

Needs Git and Python 3.9+. Works with any coding agent that reads Agent Skills; canonical `docs/hosts.md` lists per-host install, invocation, gate hooks and Safe reviewers. Safe local review launches any installed agent CLI (Claude Code, Codex, Cursor), otherwise the controller's review-packet fallback. Set them up on any OS without asking Seif to prepare the machine:

1. Find them: `git --version`; Python through `python3`, `python` or Windows `py -3`. Use the first that reports 3.9+, by full path, for every later command.
2. Missing or too old: install from the official source, user scope when possible.
   - Windows: `winget install -e --id Python.Python.3.12` and `winget install -e --id Git.Git`.
   - macOS: `brew install python git`. No Homebrew: `xcode-select --install` for Git, the python.org installer for Python.
   - Linux: the distro manager (`apt-get`, `dnf`, `pacman`, `zypper` or `apk`).
   - No admin or package manager: install [uv](https://docs.astral.sh/uv/getting-started/installation/) (`winget install astral-sh.uv`, `brew install uv` or its official installer), run `uv python install 3.12`, then `uv run --python 3.12 python ...`.
   - A headless agent CLI for Safe review is optional: any of Claude Code, Codex or Cursor; canonical `docs/hosts.md` names each one's reviewer command.
3. Check the versions again. Report what was installed, from where.
4. Host asks before installs: ask once, naming each tool and source. Still blocked (no network, admin or approval): say what is missing. Fast and Lucky can read the bundle with Git alone: `git ls-remote https://github.com/seifsg/ai-software-factory main`, clone that SHA into `~/.safe-engine/bundles/<sha>`, detach, read it only; record steps by hand and report the gate as unavailable. Safe waits for Python.
5. Official sources only. No system settings beyond the install. No credentials in commands.

## Find the right factory version

Preserve report/project goal. Inspect active legacy/ticket runs, checkpoints and session contract before fetching. Ticket state lives in `.factory/runs/<key>/state.json`; preserve legacy `.factory/state.json` and exact pins.

Existing run: use recorded absolute bundle path and exact revision/dirty state. Inspect evidence; if identity remains unknown, preserve run and stop dependent changes. Never substitute latest.

Find `scripts/resolve_bundle.py` beside this installed file. Use the Python from [Get the requirements](#get-the-requirements); quote paths/use argument arrays.

Existing run or supplied checkout:
```text
python3 <skill-dir>/scripts/resolve_bundle.py --bundle <absolute-factory-root>
```

New maintenance case without active run:
```text
python3 <skill-dir>/scripts/resolve_bundle.py
```

The resolver selects the branch once into a complete detached `~/.safe-engine/bundles/<commit>` checkout. For a user-pinned new case, add `--ref <full-commit-sha>`. Pins cannot authorize active-run upgrades.

## Read the result and use the method

Follow Working iterations where present in the selected canonical method. Older pins keep their recorded method; no silent upgrade.

Check JSON against intended identity; record `bundle_root`, `revision`, dirty state and entrypoint. Dirty active checkout: use canonical checkpointing to capture actual diff/untracked-input hashes; commit alone is insufficient.

Current bundles check required guidance through `safe_engine/bundle-inputs.json`; old bundles retain legacy completeness inspection. Record launcher identity separately; declare it as a profile input when used in acceptance. Resolver checks identity/files, not behavior, compatibility or permission.

Read the whole returned canonical `entrypoint` and applicable references/methods. Execute once. Analysis/planning stays in phase. No recursive launcher, standalone canonical-folder installation or claim that loading files repaired anything.

Mode: Fast by default; read canonical `.agents/skills/safe-engine/references/speed-modes.md` when the pin has it. Fast maintenance is a `change` run of canonical `fast-run.md`: one ticket, recorded steps and the bundle's `skills/safe-engine/scripts/fast_gate.py`. Safe maintenance uses canonical `.agents/skills/ticketing/SKILL.md` and `docs/ticketing.md`: preferred authorized tracker MCP, otherwise GitHub Issues (Seif's current choice). Confirm before/after scope; dispatch a dedicated maintenance builder session and complete the full cycle, even for small repairs. Keep fixes surgical. Select `--ticket <key>` and initialize with `--session <real-builder-session-id>`; preserve separate app/maintenance history and ownership. Old pins need authorized trial/adoption before new methods.

Keep active cached bundles unchanged. Repair in a separate worktree from their revision; follow compatibility/evidence rules before adoption. Never pull/reset active bundles or silently change global settings. Resume this case's recorded selection even when the branch advances.

## Missing capabilities

Missing Git, Python, private access, complete files or required independent review: name the prerequisite; preserve project state. Cloud/other hosts need their own authorized tools/checkout.

Follow the tests-last order in canonical `docs/current-decisions.md`. Local independent maintenance review and PR review are separate; PR review follows canonical `docs/pr-workflow.md`. No app/game/mobile pilot or simulation unless specifically requested.

Resolver installs no hooks or host automation, provisions no sessions/worktrees, selects no models, pushes/merges/notifies nothing and launches no product. Gate hooks come only from what the user installed per host (canonical `docs/hosts.md`).

## Invoke

Ask your agent for this skill with its own syntax (canonical `docs/hosts.md`):

`improve-factory The factory did X; expected Y. Preserve project progress.`

See source `docs/install-improve-factory.md` for installation/GitHub references. Host discovery/permissions still apply; if discovery fails, read this installed file by explicit path.
