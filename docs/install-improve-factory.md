# Install Improve Factory from GitHub

Install **`skills/improve-factory`**, the portable launcher. The canonical procedure in `.agents/skills/improve-factory` depends on the complete factory, so copying that folder alone is insufficient.

The repository is private. Use an agent environment with your authorized GitHub access, Git and Python 3.9+. The launcher finds or installs them from official sources. `main` holds the published factory; [PR #1](https://github.com/seifsg/ai-software-factory/pull/1) records its initial review/merge. Unmerged changes are not the default install. Current publication waits for Seif-arranged cloud PR review and authorized merge. To build apps, install [Safe Engine itself](install-safe-engine.md); this guide installs maintenance only. Merge proves neither deployment nor production readiness.

## Install for your agent

The same installer that sets up Safe Engine also installs this launcher: `python <factory>/skills/safe-engine/scripts/fast_gate.py install --host claude|codex|cursor` ([install](install-safe-engine.md#install-for-your-agent), [hosts](hosts.md)). Claude Code gets `/improve-factory` from the `safe-engine` plugin; Codex and Cursor get it in `~/.agents/skills/improve-factory`. Other agents: copy the whole `skills/improve-factory` folder (with `scripts/`) into the folder they read skills from; never the canonical `.agents/skills/improve-factory` alone, because it has bundle dependencies.

Then ask your agent for improve-factory, in its skill syntax, and describe what happened and what should happen. The skill appears on the next turn or in a new session; if not, ask the agent to read the installed file by path. To reproduce a tested version, install from the full commit SHA supplied in the completion message **and tell the skill to use that same SHA with `--ref` for a new maintenance case**. Pinning the installed launcher alone does not pin the bundle it fetches. Active app runs always retain their recorded bundle instead.

Personal installation does not reach cloud sessions or other machines; install there too.

## What first use does

Follow Working iterations where present in the selected canonical method. Older pins retain their recorded method; installation never proves adoption.

```text
Installed portable skill
  -> existing app run? use its recorded bundle; do not upgrade
  -> otherwise resolve GitHub ref to a commit
  -> obtain complete detached checkout in ~/.safe-engine/bundles/<commit>
  -> read full canonical improve-factory + applicable routines
  -> checkpoint, isolate repair, verify and independently review
```

The resolver prints the full path, commit and dirty status. It rejects wrong repositories, incomplete bundles and modified cached checkouts. It can inspect an explicitly supplied dirty app bundle without altering it; the main procedure then records the actual dirty inputs. Keep a run's selected bundle unchanged and perform factory edits in another worktree. This is a local procedure, not an automatic hook or background service.

Current bundles declare their required procedural files and source areas in [bundle-inputs.json](../safe_engine/bundle-inputs.json). The resolver validates that contract when present or recorded at the selected commit; deleting it cannot fall back to older completeness checks. Older bundles without the contract retain the legacy required-file inspection so active runs can keep their pinned version. Neither path certifies QA. The installed launcher is a separate copy: record its identity, and declare it as a profile input if it participates in target acceptance. The selected bundle's controller enforces the [procedural fingerprint boundary](pilot-usage.md).

To inspect an existing bundle without downloading/updating it:

```text
python <installed-skill>/scripts/resolve_bundle.py --bundle <absolute-factory-checkout>
```

Use `py -3` on Windows or another available Python 3 interpreter where needed. Paths with spaces require quoting. Private clone failures need the environment's normal credential setup; never paste tokens into prompts or URLs. Existing cached checkouts are never pulled, reset or deleted. Failed download directories are retained with their path for diagnosis.

Distribution choices: a small launcher (selected under this request) preserves one canonical method; embedding a complete copy duplicates the factory; a plugin marketplace adds host-specific packaging. The launcher is intended for initial reuse/testing through ordinary skill installers.

Host references: [hosts](hosts.md#sources). Host discovery, authentication and independent-review tooling remain prerequisites. A portable file layout does not demonstrate a complete factory run on every host.

## Version 2 launcher upgrade

Older installed resolvers accept only input-contract v1. Resolving a v2 bundle can fail with `Invalid factory input contract`. Refresh both portable entries from the approved v2 revision before selecting that bundle. Preserve the previous installations and active bundle receipts; do not reset or upgrade existing runs. The current resolver supports both contract versions. Source publication alone does not update personal installations.
