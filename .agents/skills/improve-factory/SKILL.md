---
name: improve-factory
description: "Repairs factory skills, gates, controllers and adapters when factory instructions or behavior fail. Product bugs go back to delivery."
---

# Improve Factory

Repair the factory, never app source. Preserve any active app run; its gate may pause. Analysis/planning stops in that phase.

## Mode

Fast default: light-lane change on its maintenance ticket, gated by `skills/safe-engine/scripts/fast_gate.py` after isolation; pause a blocking app gate first. Small wording repair records cause, success and todos. Method/gate/controller changes run full step3 in Plan. Safe on request: full `ticketing`, separate builder, file-summary stop and step6 review.

## 1. Diagnose

1. Record observed/expected behavior, example, artifacts, commands and factory revision in the ticket.
2. Resolve factory/app roots separately; read both rules/status. Ask only consequential gaps.
3. Classify before changing rules:

| Cause | Correction |
|---|---|
| Skipped instruction | Recover it; inspect invocation/handoff before adding rules |
| Unclear skill | Owning rule, callers and links |
| Gate/controller/adapter | Source/evidence diagnosis; reproduction tests after manual use |
| Missing tool/access/decision | Record real blocker; invent nothing |
| Product defect | Delivery, unless a factory defect is also demonstrated |
| Intended behavior | Explain owning rule; change only on owner request |

## 2. Isolate

- Own branch/worktree, one writer per file. Distinct runner/candidate/app. Pin immutable runner with `resolve_bundle.py --project <candidate> --bundle <runner>` and run its gate with `--project <candidate>`; never edit active pins or select editable candidate as runner.
- Base on runner or owner-approved unmerged commit; record base/unmerged status. No implied release/adoption.
- Active app: [live-session](references/live-session.md) before workspace changes/delegation: checkpoint, isolated repair, independent review, compatible resume. Never silently stash/reset/switch/upgrade app, bundle or global settings.
- Separate maintenance and product scope/tickets. Independent tickets may run in separate worktrees; one open gate per checkout. Worktrees isolate files only: also isolate ports, databases, caches and services.
- Other-session work follows `safe-engine` Delegate. Factory handoff invokes this method with ticket, checkout/report, runner/base/app; fetch before candidate creation, name unmerged base, use intended upstream. Product defects use delivery; active apps read live-session first. Absolute paths, lane resources and verifiable briefs follow Delegate.

## 3. Analyze and plan

1. `analyze-start`: actual source/consumers/flow, claims versus evidence, unknowns, final reproduction. Unobserved failure stays unverified.
2. Record invariants: goal, decisions, complete methods, owner stops, human release. Only owner changes them; failed checks are not weakened and proposals are not approval.
3. Smallest complete root repair, no unrelated improvements or universal rule for an isolated complaint. New skill/gate/helper/report needs a demonstrated gap.
4. `get-ready-to-code`: all five outputs including reproduction, consumers, behavior/proof, compatibility and resume. Choose proof: walkthrough for instructions, actual flow for code/config, both for mixed; delegate when useful.

Record plan before code.

## 4. Repair

- Todo0–4: pre/do/post then tick after use; observed `metrics task` start/finish/fail/cancel/resume. `try` is not completion.
- Relay gate cards where needed, one line per delegation wave, waiting question first. Fix owning cause and affected callers/links; delete duplicate/stale prose. Lasting rules belong in their owning skill; use an available skill-authoring tool.
- Research unfamiliar platforms/APIs in current primary sources, within scope. Never run this method on its own repair.
- Added/moved/deleted factory files: update `safe_engine/bundle-inputs.json` and `safe_engine/distribution.py`, regenerate launchers with `python scripts/package_skill_entries.py`, repair path-dependent tests.

## 5. Manual first, tests last

1. Use realistic raw fixtures: instruction decisions/artifacts, or actual changed commands/flows. Seek independent judgment where needed. No product pilot/simulation without owner request; isolate secrets and project resources.
2. Exercise touched boundaries: real domain tooling; live/adoption dirty bundle, running/pending work, drift before/after QA, stop/cancel/lost context; reuse and rejection for changed/tampered/pending proof.
3. Check skill self-containment, names/dates/host exclusions and budgets. Await producer exit0 before dependent consumers; a yielded session is pending. Sample data/mode/resources never share a live preview root.
4. Then write/adjust affected tests, run them, commit source/docs/tests/packaging and do required source review (`how-to-make-a-pr`). Run `python tests/run.py` on that commit through selected Prove, else its recorded gate. Retain receipt/commit/inputs/command/log/result; edits need affected checks and fresh final proof.
5. Each check proves itself: walkthrough is not code repair; suite is not walkthrough.

## 6. Independent review

- Safe runs locally; Fast skips local review. Every main-branch factory change still needs independent PR review by a human/separate reviewer using `deep-review` on exact candidate/raw evidence. Never self-approve; unavailable reviewer is a named blocker.
- A changed gate needs old rule, reproduction and independent review. Reviewer repairs require a different reviewer.
- Review, author fixes, same reviewer checks delta; replace for lost context/own repairs. After round3 only high/critical continue; lower findings join the epic's one open Backlog follow-ups ticket. At most6 failed rounds, then ask once: findings, shared cause, extend/defer/amend/cancel. Keep independent work moving.

## 7. Deliver

1. Refresh ticket; compare confirmed criteria, change, preserved behavior, proof/limits. Drift or failed refresh blocks acceptance.
2. Draft through `how-to-make-a-pr`; missing bindings block PR, not local repair/checks. Humans ready/merge/release.
3. Active pins never auto-upgrade. Publishing plus the install's update or fresh `fast_gate.py install` delivers launcher/gate/hook changes. Active app adoption/resume follows live-session.
4. Report structure, manual use, tests, review, adoption and PR separately; brief observed Before/After and unverified work.

## Record

One ignored Fast work record, or `.factory/maintenance/<id>/` in Safe: report/cause; ticket/scope/authority/refresh; invariants/plan/0–4; checkpoint/commits/dirty manifest; proof/limits/reviewer/PR; adoption/rollback/resume. No secrets; share sanitized evidence only.
