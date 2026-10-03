---
name: safe-engine
description: "Build or resume an app or feature through Seif's Safe Engine software factory. Loads the complete versioned factory, analysis charts, planning and coding methods, batched QA and independent review from private GitHub. Use for factory delivery, not factory maintenance or ordinary questions."
---

# Safe Engine — reusable factory entry

Use this skill to build applications and features in the user's chosen project. This is the factory's entry point; `improve-factory` is for changing the factory. The full workflow has one canonical owner in `https://github.com/seifsg/ai-software-factory`. This folder is a standalone installation adapter, not a substitute for Seif's complete methods.

## Load the factory, then run it

1. Preserve the actual app request, existing answers, decision authority and project work. Establish the absolute target directory from session context or the user. Inspect its project instructions, `.factory/state.json`, selection record and existing session/checkpoint artifacts before choosing a bundle. Create a missing directory only within the requested app scope; do not initialize a second run or choose a substitute example.
2. Locate `scripts/resolve_bundle.py` relative to this installed skill. Run with Python 3 (`python3`, `python`, or `py -3` on Windows), quoting paths or using an argument array:

   ```text
   python3 <installed-skill>/scripts/resolve_bundle.py --entrypoint safe-engine --project <absolute-target-directory>
   ```

   New projects resolve private GitHub `main` once to a complete detached checkout in `~/.safe-engine/bundles/<commit>`. The helper records the selection in the project's excluded `.factory/entry-bundle.json`. Existing selections resume offline at their recorded path and revision; `--ref` cannot upgrade them. For a new run, an explicit `--ref <full-SHA>` pins the bundle as well as the separately installed launcher.

   A legacy run without a selection record needs its **established original bundle**, supplied with `--bundle <absolute-factory-root>` and `--project`. Inspect original session evidence to establish it; a version label or matching HEAD alone cannot identify dirty inputs. If that identity is missing, preserve the run and stop dependent actions. Never substitute latest `main`, rewrite its state or reset acceptance. A receipt selects source files; it does not certify compatibility or QA.
3. Read the returned JSON: actual bundle root, revision, dirty status, selection record and canonical entrypoint. Verify the intended identity. Preserve the installed launcher's separate identity in the session contract. For explicit dirty bundles, record actual diff/untracked input hashes through the canonical checkpoint method. Keep the selected bundle unchanged; a resolver failure must be diagnosed, never ignored.
4. Read the **entire returned `entrypoint`** (`.agents/skills/safe-engine/SKILL.md`), its session contract, usage guide and method handoff. Read every full method and applicable reference when its phase requires it. Execute that canonical procedure once, from the returned bundle root against the target project. Do not recursively invoke this adapter, run the controller from the app directory, or treat file loading as a completed build.
5. Check actual prerequisites before dependent execution: Python 3.11+, Git, private-repository access, authenticated Codex CLI for the implemented fresh review, project check tools, and real browser tools for browser QA. Use existing capabilities and diagnose missing access honestly. Local installation does not provision another machine or cloud environment; a Claude-only reviewer adapter is not implemented.

The canonical flow preserves `analyze-start` charts → `get-ready-to-code` planning → new-app research/revised plan → the 0–4 coding loop → coherent feature feedback → full QA → worthwhile improvement → final QA → fresh independent review → checked handoff. Every authorized PR also executes both complete PR procedures with separate-instance review. Follow recorded autonomous scope, batch tests, keep meaningful progress visible, and preserve human release boundaries. No hooks, daemon, global permission changes or universal host enforcement are installed here.

## Invoke after installation

Codex: `$safe-engine Build [app or feature] in [absolute project path]. Success means [observable outcome].`

Claude Code: `/safe-engine Build [app or feature] in [absolute project path]. Success means [observable outcome].`

Resume: `$safe-engine Resume the existing run in [absolute project path]. Preserve its decisions, bundle and evidence.`

The maintenance skill is optional for normal delivery; this entry does not require it to be separately installed. The complete bundle includes the canonical maintenance procedure for a mid-build factory correction. See `docs/install-safe-engine.md` in the source repository for installation, cloud and host limits. Skill discovery remains host-controlled; explicitly reading the installed file is the fallback.
