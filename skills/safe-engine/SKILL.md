---
name: safe-engine
description: "Build or resume an app or feature with Seif's complete Safe Engine factory from private GitHub. Loads the versioned methods, checks, and independent review. Use for factory delivery, not factory maintenance or ordinary questions."
---

# Safe Engine

Load the complete factory and use its methods in the user's project. The canonical source is `https://github.com/seifsg/ai-software-factory`. This installed folder only loads it. Use `improve-factory` to change the factory.

An explicit analysis, planning, or review request stays in that phase. Do not turn it into a build or small-fix delivery run.

## Check existing work and local trials

Preserve the request, answers, decision authority, and project work. Establish the absolute target directory from the session or user. Read project instructions, `.factory/state.json`, selection record, and session/checkpoint artifacts before choosing a bundle. Create a missing directory only within the requested app scope. Do not initialize a second run or substitute a demo.

If this installed folder has `references/local-app-diagnostics.md`, read it before selecting a method. The optional host-local record may cover both diagnostics and efficiency; keep its filename for continuity. Check its owner-authorized scope, candidate root/revision, fresh independent assessment, and rollback destination. Verify candidate identity and clean status. Read its entire selected method and references.

Within that record's authority:

- A new project without a run or selection may explicitly select the complete candidate with `--bundle <verified-candidate-root> --project <target>`.
- An existing app's bounded fix may use the candidate's Small Change method as a separate trial, preserving its original version pin and state.
- Substantial version adoption still needs the canonical compatibility handoff.

Record both identities and evidence limits. A local trial record is neither a universal default nor proof that a draft merged.

For a requested bounded fix, load the resolved bundle's entire `.agents/skills/small-change/SKILL.md`, or the applicable verified trial above. Use only that method and applicable references. It owns six light routines, focused checks, narrow independent review, and scoped PR delivery; it does not need a full controller run or CLI reviewer.

If `references/local-small-change.md` exists here, read its authority, exact candidate, and scope. Verify path, revision, and clean status before use. An applicable app-defaults trial takes precedence within its scope. Such a verified trial may route a bounded fix before resolving the older version bundle, while leaving that selection intact.

If the pinned bundle lacks Small Change, preserve it. Use an already authorized reviewed candidate by explicit path as a separate trial, or explain the available method and obtain the missing adoption decision. Do not simulate Small Change by skipping controller gates. Updating this launcher never migrates an app.

## Resolve and read the factory

Locate `scripts/resolve_bundle.py` relative to this installed skill. Use Python 3 (`python3`, `python`, or `py -3` on Windows). Quote paths or pass an argument array.

```text
python3 <installed-skill>/scripts/resolve_bundle.py --entrypoint safe-engine --project <absolute-target-directory>
```

New projects resolve private GitHub `main` once into `~/.safe-engine/bundles/<commit>`. The helper records the selection in the project's excluded `.factory/entry-bundle.json`. Existing selections resume offline at their recorded path/revision; `--ref` cannot upgrade them. For a new run, `--ref <full-SHA>` pins the bundle separately from the installed launcher.

For a legacy run without a selection record, establish its original bundle from session evidence and supply `--bundle <absolute-factory-root> --project <target>`. A version label or matching HEAD cannot identify dirty inputs. If identity is unknown, preserve the run and stop dependent work. Do not substitute latest `main`, rewrite state, or reset acceptance. A selection receipt does not certify compatibility or QA.

Read the returned JSON. Check bundle root, revision, dirty status, selection record, and canonical entrypoint against the intended identity. Record the launcher's separate identity in the session contract. For an explicit dirty bundle, capture actual diff and untracked-input hashes through the canonical checkpoint method. Diagnose resolver failures; do not ignore them. Keep the selected bundle unchanged.

Read the entire returned `entrypoint` (`.agents/skills/safe-engine/SKILL.md`). For version work, also read its session contract, usage guide, and method handoff. For Small Change, read its entire method and applicable references. Load every complete method and applicable reference when its phase needs it.

Run the canonical procedure once from the returned bundle root against the target project. Do not recursively call this adapter or run the controller from the app directory. Loading files is not a completed build.

## Check the required capabilities

Before dependent work, check Python 3.11+, Git, authorized private-repository access, authenticated Codex CLI for the implemented fresh review, project check tools, and real browser tools for browser QA. Use available capabilities and report actual missing access. Local installation does not provision another machine or cloud session. A Claude-only reviewer adapter is not implemented.

The selected method owns app defaults. Read its canonical `safe-engine/references/app-diagnostics.md` and `safe-engine/references/app-efficiency.md` through that method:

- New apps need sufficient app-wide logs; existing changes inspect coverage and include minimum missing modules/events with focused evidence.
- Plan CPU, memory, resource lifetimes, and useful safe reuse early.

Do not duplicate these contracts here. If an older selected bundle lacks them, preserve its pin and report the gap. Use an already authorized reviewed trial or Improve Factory's adoption procedure. Installing this entry alone neither upgrades that bundle nor optimizes an app.

The full flow is analysis with charts → planning → new-app research and revised plan → 0–4 coding loop → feature feedback → full QA → worthwhile improvement → final QA → fresh independent review → checked handoff. Authorized PR delivery also runs both complete PR methods with separate-instance review through the project adapter.

Honor delegated scope and real checkpoints. Batch tests, show meaningful progress, and preserve human release decisions. This entry installs no hooks, daemon, global permissions, or host-wide enforcement.

## Invoke

Codex: `$safe-engine Build [app or feature] in [absolute project path]. Success means [observable outcome].`

Claude Code: `/safe-engine Build [app or feature] in [absolute project path]. Success means [observable outcome].`

Resume: `$safe-engine Resume the existing run in [absolute project path]. Preserve its decisions, bundle and evidence.`

Normal delivery does not require a separate Improve Factory installation; its canonical procedure is in the complete bundle. Read `docs/install-safe-engine.md` in the source repository for installation, cloud, and host limits. Discovery depends on the host. If needed, read this installed file by its explicit path.