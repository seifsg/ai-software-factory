---
name: safe-engine
description: "Launches the AI Software Factory to build, extend, fix or resume games, apps, services, tools and libraries in a target project. Fast by default; lucky or safe on request; verify or promote a Fast run. Use when asked to build or resume software with the factory."
---

# Safe Engine

This folder only launches the factory; the methods live in the factory bundle. Analysis, planning or review requests keep their phase.

## Requirements

Find Git and Python 3.9+ by full path. Missing or old: install from official sources, user scope where possible, with any required approval; report it. No credentials in commands.

## Select the bundle

1. Establish the absolute target project; create the folder if new. Read its rules and any `.factory/` run records. Preserve existing work and answers.
2. Run the resolver beside this file (quote paths):

```text
python scripts/resolve_bundle.py --entrypoint safe-engine --project <absolute-target>
```

3. New projects select the newest verified release (main on edge or before any release), cached by commit. For a new run add `--new-run`: only automatic selections without open or unknown state refresh. Resume omits it and stays offline.
4. `--ref <tag, branch or full-sha>` or `--bundle <absolute-factory-root>` records an explicit pin. Older receipts without pin provenance stay pinned. Never edit a receipt to unpin it.
5. Check root, revision, entrypoint, notice. Failed checks name the retained version; newer release rejections stay visible when an older one verifies. Never edit a selected bundle.

## Run

Before a new run, run `python scripts/fast_gate.py pr-proof-method` beside this entry to verify the owner's optional PR policy.

- Selected: record its path and digest in the plan, read and use it for PR proof. Other methods stay pinned.
- No override: the selected bundle's method.
- A failed lookup blocks dependent proof work; diagnose it.
- Resumed runs keep their recorded PR method; gate status, not a later default, names an active Fast or Lucky adoption.

1. Read the returned `entrypoint` (`.agents/skills/safe-engine/SKILL.md`) fully; follow it from the bundle against the target.
2. Fast and Lucky: `scripts/fast_gate.py start` checks freshness and runs the selected gate. If selection changed, read that entrypoint before proceeding. Project commands and hooks keep the active gate. Receipt-less bare starts are legacy use, with no freshness guarantee.
3. Read each method the entrypoint names when its step starts.
4. Safe runs the controller from the bundle root, as the entrypoint's controller reference describes.

## Invoke

`safe-engine Build [software or feature] in [absolute project path]. Success means [outcome].`

Add `lucky` or `safe` after the skill name for those modes; `verify` or `promote` any time. Resume: `safe-engine Resume [absolute project path].` Factory faults: `improve-factory`.
