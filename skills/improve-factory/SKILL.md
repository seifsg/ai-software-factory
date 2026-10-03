---
name: improve-factory
description: "Load the complete Safe Engine factory from private GitHub to repair its skills or workflow. Preserve active app progress and use isolated repair and independent review. Ordinary app defects stay in app work."
---

# Improve Factory

Load the complete factory, then use its canonical Improve Factory method. This installed entry does not replace Seif's methods.

Source: `https://github.com/seifsg/ai-software-factory`. Distribution branch: `main`. The repo is private. Use the environment's authorized Git access. Do not ask for tokens in chat or make the repo public.

## Find the right factory version

Preserve the report and original app goal. Check for an active app run, checkpoint, or session contract before fetching another version.

If an app run exists, use its recorded absolute bundle path and exact revision/dirty state. Inspect saved evidence if needed. If identity remains unknown, preserve the run and stop dependent changes. Do not substitute the newest branch.

Locate `scripts/resolve_bundle.py` relative to this installed file. Use the available Python 3 interpreter: `python3`, `python`, or `py -3` on Windows. Quote paths or use an argument array.

For an existing run or supplied checkout:

```text
python3 <skill-dir>/scripts/resolve_bundle.py --bundle <absolute-factory-root>
```

For a new maintenance case without an active run:

```text
python3 <skill-dir>/scripts/resolve_bundle.py
```

The helper resolves the distribution branch once and obtains a complete detached checkout in `~/.safe-engine/bundles/<commit>`. For a new case, add `--ref <full-commit-sha>` when the user specifies a pin. A pin does not authorize changing an active run's bundle.

## Read the result and use the method

Read the JSON. Verify it identifies the intended run. Record `bundle_root`, `revision`, dirty state, and entrypoint in the maintenance record.

For a dirty active checkout, capture actual diff and untracked-input hashes through the canonical checkpoint procedure. The commit alone is insufficient. Current bundles use `safe_engine/bundle-inputs.json` to check required guidance; older bundles keep their legacy completeness inspection.

Record the installed launcher's separate identity. Declare it as a profile input when used in acceptance. The helper checks repository identity and required files. It does not test code, establish app compatibility, or grant permission.

Open the entire returned canonical `entrypoint`, then its applicable references and linked methods. Execute that procedure once. Keep an analysis-only or planning-only request within that phase. Do not recursively call this launcher, install the canonical folder alone, or call file loading a successful repair.

Keep a cache checkout unchanged while an app uses it. Repair in a separate worktree from that revision. Follow the canonical compatibility and evidence rules before adoption. Do not pull/reset an active bundle or silently change global settings. Reuse this case's recorded bundle on later turns even if the branch advances.

## Missing capabilities

If Git, Python, private-repository access, full skill files, or required independent review is unavailable, report the exact missing prerequisite and preserve app state. A cloud agent needs its own authorized checkout and tools; local installation does not install into another host or session.

The helper resolves files. It does not install hooks, choose models, push, merge, notify anyone, or launch an app.

## Invoke

Codex: `$improve-factory The factory did X; it should do Y. Preserve this app's progress.`

Claude Code, after installing this folder in its skill location: `/improve-factory The factory did X; it should do Y. Preserve this app's progress.`

Read `docs/install-improve-factory.md` in the source repo for installation and exact GitHub references. Host discovery and permissions still apply. If discovery fails, read this `SKILL.md` by explicit path.