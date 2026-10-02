---
name: improve-factory
description: "Improve or repair your Safe Engine software factory from feedback, including during an app build. Loads the complete versioned factory from its private GitHub repository, preserves app progress, and coordinates isolated repair and independent review. Ordinary app defects stay in the app workflow."
---

# Improve Factory — portable entry

This installable entry loads the canonical `improve-factory` procedure and its complete dependencies. It does not replace or summarize Seif's methods. Source: `https://github.com/seifsg/ai-software-factory`; current distribution branch: `docs/skill-lifecycle-map`. The repository is private: the current agent environment needs authorized Git access. Never request tokens in chat or make the repository public.

## Resolve the factory before acting

1. Preserve the user's report and original app goal. Check for an active app run, checkpoint or session contract **before fetching a different factory version**. If one exists, use its recorded absolute bundle path and exact revision/dirty state. If that identity cannot be established, inspect the existing evidence and block dependent changes; do not substitute the newest branch.
2. Locate `scripts/resolve_bundle.py` relative to this installed skill file. Run it with the available Python 3 interpreter (`python3`, `python`, or `py -3` on Windows). Use an argument array or proper shell quoting for paths with spaces.
   - Existing run or explicitly supplied checkout: `python3 <skill-dir>/scripts/resolve_bundle.py --bundle <absolute-factory-root>`.
   - New maintenance case with no active run: `python3 <skill-dir>/scripts/resolve_bundle.py`. This resolves the distribution branch once, obtains a complete detached checkout in the user's `.safe-engine/bundles/<commit>` cache, and returns the exact identity.
   - User-specified pinned revision: add `--ref <full-commit-sha>` for a new case. A pin is not permission to change an active run's bundle.
3. Read the JSON result, verify it matches the intended run, and record its `bundle_root`, `revision`, dirty state and entrypoint in the maintenance record. For a dirty active checkout, capture the actual diff/untracked input hashes under the canonical checkpoint procedure; the commit alone is insufficient. The helper validates repository identity and required files; it does not establish app compatibility, test code, or grant permissions.
4. Open and read the **entire returned canonical `entrypoint`**, then its applicable references and linked routines. Continue that procedure once. Never call this launcher recursively, install the canonical folder alone, or treat loading this entry as successful maintenance.

Keep the resolved cache checkout unchanged while any app uses it. Repair in a separate worktree from that revision; follow the canonical compatibility and evidence rules before adopting any candidate. Never pull/reset an active bundle or silently switch global settings. Reuse the recorded bundle for this case on subsequent turns, even if the distribution branch advances.

If Git, Python, private-repository access, full skill files, or required independent review are unavailable, report the exact missing prerequisite and preserve the app state. A cloud agent needs its own authorized checkout and tools; a local installation does not install into other machines or cloud sessions. The helper only resolves files; it does not install hooks, select models, push, merge, notify or launch an app.

## Invoke

Codex: `$improve-factory The factory did X; it should do Y. Preserve this app's progress.`

Claude Code, after installing this folder in its skill location: `/improve-factory The factory did X; it should do Y. Preserve this app's progress.`

For installation and exact GitHub references, read `docs/install-improve-factory.md` in the source repository. Host discovery and permissions still apply; the explicit `SKILL.md` path works when discovery is unavailable.
