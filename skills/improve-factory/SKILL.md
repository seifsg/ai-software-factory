---
name: improve-factory
description: "Load the complete private Safe Engine factory for isolated maintenance and independent review. Preserve active project progress. Product defects stay in delivery."
---

# Improve Factory

Load the complete factory; execute canonical Improve Factory. This launcher does not replace the user's methods.

Source: `https://github.com/seifsg/ai-software-factory`, branch `main`, private. Use existing authorized Git access. Never request tokens in chat or make it public.

## Find the right factory version

Preserve report/project goal. Inspect active legacy/ticket runs, checkpoints and session contract before fetching. Ticket state lives in `.factory/runs/<key>/state.json`; preserve legacy `.factory/state.json` and exact pins.

Existing run: use recorded absolute bundle path and exact revision/dirty state. Inspect evidence; if identity remains unknown, preserve run and stop dependent changes. Never substitute latest.

Find `scripts/resolve_bundle.py` beside this installed file. Use available Python 3 (`python3`, `python`, Windows `py -3`); quote paths/use argument arrays.

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

Mode: Fast by default; read canonical `.agents/skills/safe-engine/references/speed-modes.md` when the pin has it. Safe maintenance uses canonical `.agents/skills/ticketing/SKILL.md` and `docs/ticketing.md`: preferred authorized tracker MCP, otherwise GitHub Issues (Seif's current choice). Confirm before/after scope; dispatch a dedicated maintenance builder session and complete the full cycle, even for small repairs. Keep fixes surgical. Select `--ticket <key>` and initialize with `--session <real-builder-session-id>`; preserve separate app/maintenance history and ownership. Old pins need authorized trial/adoption before new methods.

Keep active cached bundles unchanged. Repair in a separate worktree from their revision; follow compatibility/evidence rules before adoption. Never pull/reset active bundles or silently change global settings. Resume this case's recorded selection even when the branch advances.

## Missing capabilities

Missing Git, Python, private access, complete files or required independent review: name the prerequisite; preserve project state. Cloud/other hosts need their own authorized tools/checkout.

Finish all repair work before manual walkthroughs or automated tests. Local independent maintenance review and remote/cloud PR review are separate; PR review needs a fresh remote context and exact candidate evidence. A local subagent cannot replace it. No app/game/mobile pilot or simulation unless specifically requested.

Resolver installs no hooks or host automation, provisions no sessions/worktrees, selects no models, pushes/merges/notifies nothing and launches no product.

## Invoke

Codex: `$improve-factory The factory did X; expected Y. Preserve project progress.`

Claude Code, after installation there: `/improve-factory The factory did X; expected Y. Preserve project progress.`

See source `docs/install-improve-factory.md` for installation/GitHub references. Host discovery/permissions still apply; if discovery fails, read this installed file by explicit path.
