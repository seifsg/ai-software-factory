---
name: improve-factory
description: "Launches the AI Software Factory's maintenance method to repair or improve the factory itself (skills, gate, controller, adapters) in isolation, preserving any active project run. Use when the factory misbehaved or needs a change. Product bugs stay in delivery."
---

# Improve Factory

This folder only launches the factory's maintenance method. The method lives in the factory bundle.

## Requirements

Git and Python 3.9+. Find them by full path (`python3`, `python` or the platform launcher). Missing or too old: install from the official source with the platform's package manager, user scope when possible, asking first if your agent requires it. No credentials in commands.

## Select the bundle

1. Preserve the report and any active project run: read its `.factory/` records and recorded bundle first.
2. Run the resolver beside this file (quote paths):

```text
python scripts/resolve_bundle.py --entrypoint improve-factory --bundle <absolute-factory-root>
python scripts/resolve_bundle.py --entrypoint improve-factory
```

   Active run or a local factory checkout: the first, on that checkout. Otherwise the second: it pins the newest verified release (main on the edge channel or before the first release) in `~/.safe-engine/bundles/<commit>`; `--ref <vX.Y.Z, branch or full-sha>` pins another.
3. Check the returned root, revision, dirty status and entrypoint. Never pull, reset or edit an active run's bundle; repair in a separate worktree.

## Run

For a new maintenance run in any mode, use the installed `safe-engine` entry's `scripts/fast_gate.py pr-proof-method` to verify the owner's optional PR-policy default. Record its method path and digest in the plan; read and use that method when selected, preserving every other bundle method. No override: use the bundle's PR method. A failed lookup blocks dependent proof work. Resumed runs retain their recorded PR method; active Fast/Lucky adoption is named by gate status.

Read the returned `entrypoint` (`.agents/skills/improve-factory/SKILL.md`) fully and follow it. Analysis or planning requests keep their phase.

## Invoke

`improve-factory The factory did [observed]; expected [result]. Preserve project progress.`
