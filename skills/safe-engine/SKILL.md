---
name: safe-engine
description: "Launches the AI Software Factory to build, extend, fix or resume games, apps, services, tools and libraries in a target project. Fast by default; lucky or safe on request; verify or promote a Fast run. Use when asked to build or resume software with the factory."
---

# Safe Engine

This folder only launches the factory. The methods live in the factory bundle. Analysis, planning or review requests keep their phase.

## Requirements

Git and Python 3.9+. Find them by full path (`python3`, `python` or the platform launcher). Missing or too old: install from the official source with the platform's package manager, user scope when possible, asking first if your agent requires it. Report what was installed. No credentials in commands.

## Select the bundle

1. Establish the absolute target project; create the folder if it is new. Read its rules and any `.factory/` run records. Preserve existing work and answers.
2. Run the resolver beside this file (quote paths):

```text
python scripts/resolve_bundle.py --entrypoint safe-engine --project <absolute-target>
```

3. A new project gets a pinned checkout of the newest verified factory release (main on the edge channel or before the first release) in `~/.safe-engine/bundles/<commit>`; `.factory/entry-bundle.json` records it. A project with a selection resumes it offline. `--ref <vX.Y.Z, branch or full-sha>` pins a new selection; it never upgrades an existing one. `--bundle <absolute-factory-root>` inspects a given checkout.
4. Check the returned root, revision, dirty status and entrypoint. Failure: diagnose; never edit a selected bundle.

## Run

Before starting a new run in any mode, run `python scripts/fast_gate.py pr-proof-method` beside this entry. It verifies the owner's optional PR-policy default and prints its method path and digest. When selected, record them in the run plan, read that method now and use it for PR proof instead of the bundle's older PR method; all other methods stay pinned. No override: use the selected bundle's method. A failed lookup blocks dependent proof work; diagnose it. Resumed runs keep their recorded PR method; active Fast/Lucky adoption is named by gate status, not a later default.

1. Read the returned `entrypoint` (`.agents/skills/safe-engine/SKILL.md`) fully and follow it from the bundle against the target.
2. Fast and Lucky: the gate is `scripts/fast_gate.py` beside this file. Start it after the resolver, before research.
3. Read each method the entrypoint names when its step starts.
4. Safe runs the controller from the bundle root, as the entrypoint's controller reference describes.

## Invoke

`safe-engine Build [software or feature] in [absolute project path]. Success means [outcome].`

Add `lucky` or `safe` after the skill name for those modes. `verify` or `promote` any time. Resume: `safe-engine Resume [absolute project path].` Factory faults: `improve-factory`.
