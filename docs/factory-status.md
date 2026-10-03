# Factory status — 3 October 2026

**The core workflow is coherent. Seven known gaps remain.** All 69 existing tests passed; the audit found additional cases that those tests do not cover.

Read this page in the GitHub mobile app or your phone's browser. Sign in with an account that has access to this private repository. Every link below opens on GitHub; no local filesystem or localhost link is needed. Running the controller still requires a configured computer.

## Publication

The restored skills, factory coordination, documentation and preview are collected in [PR #5](https://github.com/seifsg/ai-software-factory/pull/5), targeting `main`. Seif explicitly requested publication and merge after receiving the audit. The PR page shows the live merge state; the [open PR list](https://github.com/seifsg/ai-software-factory/pulls?q=is%3Apr+is%3Aopen) shows any remaining work.

This publication preserves the current implementation. It does **not** fix the seven audit findings, update personal installations or migrate existing pinned app runs.

## What changed

- Restored six matching skills from Seif's **RepairCheck Mobile** originals.
- Retained the original feature-PR procedure from his routines repository, because Mobile's release procedure serves a different purpose.
- Kept Analyze Start's three approved additions.
- Rewrote four factory-specific skills in direct language while preserving their requirements.
- Updated references, callers, required resources, review context, documentation and the factory map together.

See the [source map](skill-provenance.md) and [writing-pass inventory](skill-writing-audit.md) for exact sources and changes.

## Read every skill

### RepairCheck Mobile originals

1. [Analyze Start](../.agents/skills/analyze-start/SKILL.md)
2. [Get Ready to Code](../.agents/skills/get-ready-to-code/SKILL.md)
3. [Deep Review](../.agents/skills/deep-review/SKILL.md)
4. [Change Guard](../.agents/skills/change-guard/SKILL.md)
5. [Compliance Check](../.agents/skills/compliance-check/SKILL.md)
6. [How to Review a PR](../.agents/skills/how-to-review-a-pr/SKILL.md)

### Other original

7. [How to Make a PR](../.agents/skills/how-to-make-a-pr/SKILL.md)

### Factory-specific skills

8. [Safe Engine](../.agents/skills/safe-engine/SKILL.md)
9. [Improve Factory](../.agents/skills/improve-factory/SKILL.md)
10. [Research Market](../.agents/skills/research-market/SKILL.md)
11. [Small Change](../.agents/skills/small-change/SKILL.md)

Each skill links its supporting resources. The [complete skill directory](../.agents/skills) lets you browse all files.

## How the factory works

1. Understand the request and actual code.
2. Prepare the original plan. For a new app, research the market and revise the plan.
3. Implement in substantial batches, checking each change as the original method requires.
4. Run the complete configured checks.
5. Make useful improvements and validate the final candidate.
6. Obtain a fresh independent review.
7. Return evidence, then perform the authorized PR/human handoff.

Analysis-only and planning-only requests stop at their requested phase. Small changes use the separate lightweight method. Local readiness, a merged PR and a tested real app are distinct results.

## Audit: what needs repair

**F1 — High:** Windows output cleanup can follow a directory junction and delete a project source file. Reproduced using synthetic data.

**F2 — Medium:** A reviewer that stops reading its prompt can exceed its timeout on Windows.

**F3 — Medium:** IDs such as `unit` and `UNIT` overwrite each other's logs on a case-insensitive filesystem and block review.

**F4 — Medium:** Temporary output capture has no size cap while a command runs.

**F5 — Medium:** The fresh review packet does not explicitly require all diagnostic, efficiency and new-app research evidence. Indirect reference paths exist.

**F6 — Medium:** Research-only requests are forced into coding-plan/controller steps.

**F7 — Medium:** The documented legacy-resume route rejects the actual historical pilot bundle.

Five failures were reproduced locally. Two are procedural coverage/scope gaps. The four runtime defects and legacy-resume logic predate the writing pass. [Full findings, evidence and repair order](factory-audit-2026-10-03.md).

## What is verified

- **69/69 Python tests passed** on Windows with Python 3.12.14.
- **13 skill entrypoints** passed structural validation.
- **236 local links/anchors** passed checks during the writing pass.
- The preview passed desktop/mobile rendering and interaction checks.
- Required resources exist; the two portable resolver copies match their canonical source.
- Independent source comparison confirmed original fidelity and documented adaptations.

These results apply to the inspected candidate. They do not prove production readiness or a complete real app delivery using the revised methods.

## What remains unfinished

- Required external PR dependencies and tracker/reviewer/notification bindings.
- Updating personal installed launchers and deliberately adopting new bundles in existing app runs.
- A complete current app demonstration, including interrupted factory maintenance and resume.
- Broader host support, dedicated specialist modules and protected remote merge/release enforcement.

## Tomorrow's test — 4 October

The requested one-time reminder is scheduled for **10:00 Europe/Paris** in the originating chat.

Use a disposable project:

1. Confirm the selected factory revision and installed entry actually load the intended `main` version. Preserve existing app pins.
2. Ask Analyze Start for analysis only. Check the original wording and stopping point.
3. Use Get Ready to Code. Check its file-summary checkpoint and planning outputs.
4. Run a small authorized change through focused checks and independent review.
5. Save, close and resume. Confirm the task, decisions, files and evidence remain intact.
6. Record actual results and unresolved findings. A successful smoke test does not close the seven audit issues automatically.

## Setup and source

- [Install Safe Engine](install-safe-engine.md)
- [Install Improve Factory](install-improve-factory.md)
- [Start or resume another session](start-another-session.md)
- [Controller usage](pilot-usage.md)
- [Selected decisions](safe-engine-decisions.md)
- [Controller source](../safe_engine)
- [Tests](../tests)
- [Examples and historical demonstration](../examples)
- [All repository files](https://github.com/seifsg/ai-software-factory/tree/main)

The interactive HTML preview is source code in this repository and is not deployed as a phone-hosted application. This page provides the readable workflow and navigation on GitHub.
