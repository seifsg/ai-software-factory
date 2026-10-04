---
name: safe-engine
description: "Load the complete private Safe Engine factory to build or resume games, apps, services and tools. Factory maintenance uses improve-factory."
---

# Safe Engine

Load `https://github.com/seifsg/ai-software-factory`; run its complete methods in the target project. This folder only launches them. Analysis/planning/review requests keep their phase.

## Select the bundle

Preserve request, answers, authority and work. Establish the absolute target; read project rules, legacy `.factory/state.json`, ticket `.factory/runs/<key>/state.json`, selection and session/checkpoint records. Create directories only within requested scope. No second run or substituted demo.

If `references/local-app-diagnostics.md` or `references/local-small-change.md` exists here, read [local trials](references/local-trials.md) before selecting a method. Otherwise skip that reference. Trials never silently upgrade pins.

Use available Python 3.11+ and authorized Git access. Locate the resolver beside this installed file; quote paths/use argument arrays:

```text
python3 <installed-skill>/scripts/resolve_bundle.py --entrypoint safe-engine --project <absolute-target>
```

New projects resolve private GitHub `main` once into `~/.safe-engine/bundles/<commit>`; excluded `.factory/entry-bundle.json` records selection. Existing selections resume offline at their recorded path/revision. `--ref <full-SHA>` pins a new selection; it cannot upgrade an existing one.

Legacy run without receipt: establish its original bundle from evidence and pass `--bundle <absolute-factory-root> --project <target>`. Unknown identity blocks dependent work. Preserve the run; never substitute latest, reset acceptance or rewrite state. Version/HEAD alone cannot identify dirty inputs.

Verify returned root, revision, dirty status, receipt and entrypoint. Record launcher identity separately. Dirty inputs need canonical checkpointing of diff/untracked hashes. Diagnose failures; keep selected bundles unchanged. Receipts certify neither QA nor compatibility.

## Read and execute

New implementation: read canonical `.agents/skills/ticketing/SKILL.md` and `docs/ticketing.md` from the resolved bundle. Preferred authorized tracker MCP first; GitHub Issues default, Seif's existing choice. Confirm before/after scope. Every ticket gets an actually dispatched builder session and full cycle, even bounded fixes. Small Change keeps patches surgical; its six shortcuts remain for legacy unticketed work.

Ticket commands select `--ticket <key>`; initialization records `--session <real-builder-session-id>`. Preserve namespaced history, legacy state and active pins. Independent ticket worktrees may parallelize independent effects; shared epic checkouts serialize writers. The controller creates neither sessions nor worktrees. Missing ticketing in an old pin needs authorized trial/adoption; never skip gates or silently upgrade.

Read the whole returned `entrypoint`, its session contract, usage guide and method handoff. Read each complete method/reference when its phase needs it. The canonical method owns diagnostics, efficiency, research and PR routing. Missing guidance in an old pin requires an authorized trial/adoption; preserve the pin.

Execute once from bundle root against target. No recursive launcher or controller execution from the target directory. File loading is not completed delivery.

Before dependent work, inspect capabilities without launching product tests. Finish implementation, then final manual/user QA, then author/run automated tests; no early playtests/walkthroughs either. New version-2 runs allow draft acceptance and seal reviewed checks at the end. Full local controller review needs authenticated Codex CLI; PR review separately needs an actual remote/cloud agent with fresh context. Local subagents never count as PR review. Report missing capabilities; installation provisions no cloud route, hooks, daemon or permissions. Preserve checkpoints and human release authority; unrequested product pilots stay deferred.

## Invoke

Codex: `$safe-engine Build [software/feature] in [absolute project path]. Success means [outcome].`

Claude Code: `/safe-engine Build [software/feature] in [absolute project path]. Success means [outcome].`

Resume: `$safe-engine Resume [absolute project path]. Preserve decisions, bundle and evidence.`

The complete bundle includes Improve Factory; no separate maintenance install needed. See source `docs/install-safe-engine.md` for setup/host limits. If discovery fails, read this file by explicit path.
