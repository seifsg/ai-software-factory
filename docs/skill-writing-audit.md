# Whole-repository skill writing pass — 3 October 2026

Revisited all 79 previously tracked files. Added five required Mobile source resources. This report records the local candidate, not a release or an app adoption.

## Sources and writing

Six canonical skills now use RepairCheck Mobile originals: Analyze Start, Get Ready to Code, Deep Review, Change Guard, Compliance Check and PR Review. Analyze Start retains its three approved additions. Original wording, priorities and checkpoints remain.

Feature PR creation is the one fallback to the routines original. Mobile's release-pr performs release rollups, version bumps and changelog work; it is not an ordinary feature-draft workflow. The [source map](skill-provenance.md#current-source-map--3-october-2026) records revisions, paths and every packaging exception.

Four factory-specific skills, six supporting references, two portable entries and current adapters use direct instructions modeled on the originals. Requirements were compared before and after. Factory entry wording fell from 7,232 to 6,465 words; the six references are about 14% shorter. Imported originals can be longer than the former adaptations; fidelity takes precedence over word count.

## Integration and verification

- Removed obsolete Part A/B callers and old PR-review routing. Explicit analysis/planning/review stays in that phase; the original file-summary checkpoint remains unless continuation is already authorized.
- Kept factory acceptance policies in visible coordinator/adapters: current evidence, authorized exceptions, scoped checks and usable app exit/recovery. Original bodies were not rewritten to carry them.
- Updated the controller review prompt and required-input contract for restored Mobile resources. Controller states, profile schema and generated resolver code remain unchanged.
- All 13 entrypoints pass Skill Creator's official validator using UTF-8 and a locally isolated PyYAML dependency.
- 235 relative Markdown links/anchors passed before adding this report; the report's links are checked in the final pass.
- Eight focused tests passed: six bundle-input cases and two reviewer dispatch/handoff cases. New coverage exercises missing Mobile resources and delivery of real rubric/adapter paths to the independent reviewer.
- Both generated resolvers match their canonical source. Preview JavaScript syntax passed.
- Desktop and 390-pixel mobile preview rendered correctly; review dialogs and the 38-entry historical catalog worked, with no browser errors or horizontal overflow.
- Independent requirement/source review found no remaining loss after corrections. A separate six-request instruction exercise exposed stale routing, an anchor, acceptance ambiguity and the app-exit check; these were corrected in their owners. These exercises are not a complete live app or PR run.

The source checkouts remain clean. No personal skill installation, push, PR, notification, release or target-app adoption occurred. Historical results and screenshots remain historical.

## Every file considered

Files marked updated include existing local drafting changes. No file was rewritten merely to increase the changed-file count.

| File | Disposition |
|---|---|
| `.agents/skills/README.md` | Updated index for current sources, roles and dependencies. |
| `.agents/skills/analyze-start/SKILL.md` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/change-guard/SKILL.md` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/compliance-check/SKILL.md` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/deep-review/SKILL.md` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/deep-review/references/theme-performance.md` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/deep-review/references/theme-security.md` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/deep-review/references/theme-user-journey.md` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/get-ready-to-code/SKILL.md` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/how-to-make-a-pr/SKILL.md` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/how-to-make-a-pr/references/pr-body-template.md` | Points to the original template; removes duplicate authored wording. |
| `.agents/skills/how-to-make-a-pr/references/project-bindings.md` | Updated target settings and factory review adapter; originals stay intact. |
| `.agents/skills/how-to-review-a-pr/SKILL.md` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/how-to-review-a-pr/references/mobile-rules/coding-style.mdc` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/how-to-review-a-pr/references/mobile-rules/dont-code.mdc` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/how-to-review-a-pr/references/mobile-rules/issue-handling.mdc` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/how-to-review-a-pr/references/mobile-rules/no-ai-commit-attribution.mdc` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/how-to-review-a-pr/references/pr-comment-template.md` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/how-to-review-a-pr/references/synthesis-and-verdict.md` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/how-to-review-a-pr/references/theme-change-guard.md` | Compared with selected original; restored or preserved with documented packaging changes. |
| `.agents/skills/improve-factory/SKILL.md` | Rewritten in direct instructions; before/after requirements reviewed. |
| `.agents/skills/improve-factory/references/live-session.md` | Rewritten in direct instructions; before/after requirements reviewed. |
| `.agents/skills/improve-factory/references/validation-scenarios.md` | Rewritten in direct instructions; before/after requirements reviewed. |
| `.agents/skills/research-market/SKILL.md` | Rewritten in direct instructions; before/after requirements reviewed. |
| `.agents/skills/safe-engine/SKILL.md` | Rewritten in direct instructions; before/after requirements reviewed. |
| `.agents/skills/safe-engine/references/app-diagnostics.md` | Rewritten in direct instructions; before/after requirements reviewed. |
| `.agents/skills/safe-engine/references/app-efficiency.md` | Rewritten in direct instructions; before/after requirements reviewed. |
| `.agents/skills/safe-engine/references/method-handoff.md` | Rewritten in direct instructions; before/after requirements reviewed. |
| `.agents/skills/safe-engine/references/session-contract.md` | Rewritten in direct instructions; before/after requirements reviewed. |
| `.agents/skills/small-change/SKILL.md` | Rewritten in direct instructions; before/after requirements reviewed. |
| `.gitignore` | Inspected repository support file; retained. |
| `AGENTS.md` | Updated current authorship, scope, source priority and workflow instructions. |
| `README.md` | Updated current authorship, scope, source priority and workflow instructions. |
| `docs/install-improve-factory.md` | Read dated design/reference material; retained as history or unchanged setup guidance. |
| `docs/install-safe-engine.md` | Reconciled current guidance or labeled superseded methods as historical. |
| `docs/pilot-implementation.md` | Reconciled current guidance or labeled superseded methods as historical. |
| `docs/pilot-usage.md` | Reconciled current guidance or labeled superseded methods as historical. |
| `docs/pilot-verification.md` | Reconciled current guidance or labeled superseded methods as historical. |
| `docs/pr-workflow.md` | Reconciled current guidance or labeled superseded methods as historical. |
| `docs/qa-enforcement-gap-analysis.md` | Read dated design/reference material; retained as history or unchanged setup guidance. |
| `docs/safe-engine-build-plan.md` | Read dated design/reference material; retained as history or unchanged setup guidance. |
| `docs/safe-engine-decisions.md` | Reconciled current guidance or labeled superseded methods as historical. |
| `docs/safe-engine-expanded-scope.md` | Read dated design/reference material; retained as history or unchanged setup guidance. |
| `docs/safe-engine-fast-delivery.md` | Reconciled current guidance or labeled superseded methods as historical. |
| `docs/skill-lifecycle-map.md` | Reconciled current guidance or labeled superseded methods as historical. |
| `docs/skill-provenance.md` | Reconciled current guidance or labeled superseded methods as historical. |
| `docs/start-another-session.md` | Reconciled current guidance or labeled superseded methods as historical. |
| `examples/README.md` | Aligned reproduction instructions with original planning checkpoint. |
| `examples/pilot-app/.gitignore` | Read disposable fixture or historical record; preserved its purpose and evidence. |
| `examples/pilot-app/app.js` | Read disposable fixture or historical record; preserved its purpose and evidence. |
| `examples/pilot-app/index.html` | Read disposable fixture or historical record; preserved its purpose and evidence. |
| `examples/pilot-app/model.mjs` | Read disposable fixture or historical record; preserved its purpose and evidence. |
| `examples/pilot-app/style.css` | Read disposable fixture or historical record; preserved its purpose and evidence. |
| `examples/pilot-app/tests/browser.cjs` | Read disposable fixture or historical record; preserved its purpose and evidence. |
| `examples/pilot-app/tests/unit.mjs` | Read disposable fixture or historical record; preserved its purpose and evidence. |
| `examples/pilot-commands.md` | Aligned reproduction instructions with original planning checkpoint. |
| `examples/pilot-profile.json` | Read disposable fixture or historical record; preserved its purpose and evidence. |
| `examples/pilot-task.json` | Read disposable fixture or historical record; preserved its purpose and evidence. |
| `examples/pilot-walkthrough.md` | Read disposable fixture or historical record; preserved its purpose and evidence. |
| `examples/recorded-demo/desktop-after.png` | Visually inspected dated evidence; preserved unchanged. |
| `examples/recorded-demo/mobile-after.png` | Visually inspected dated evidence; preserved unchanged. |
| `examples/recorded-demo/mobile-before.png` | Visually inspected dated evidence; preserved unchanged. |
| `examples/serve-pilot.py` | Read disposable fixture or historical record; preserved its purpose and evidence. |
| `preview/factory-map.css` | Inspected styling; retained. |
| `preview/factory-map.js` | Updated current source/review labels; desktop/mobile interaction and rendering checked. |
| `preview/index.html` | Updated current source/review labels; desktop/mobile interaction and rendering checked. |
| `safe_engine/__init__.py` | Read for consumers and compatibility; no unrelated executable rewrite. |
| `safe_engine/__main__.py` | Read for consumers and compatibility; no unrelated executable rewrite. |
| `safe_engine/bundle-inputs.json` | Requires the five added Mobile resources, including .mdc rule inputs. |
| `safe_engine/distribution.py` | Read for consumers and compatibility; no unrelated executable rewrite. |
| `safe_engine/project.py` | Read for consumers and compatibility; no unrelated executable rewrite. |
| `safe_engine/review-schema.json` | Read for consumers and compatibility; no unrelated executable rewrite. |
| `safe_engine/runner.py` | Read for consumers and compatibility; no unrelated executable rewrite. |
| `safe_engine/storage.py` | Read for consumers and compatibility; no unrelated executable rewrite. |
| `safe_engine/workflow.py` | Updated reviewer context: explicit rubrics/adapter, original checkpoint, scoped alternatives; transitions unchanged. |
| `scripts/package_skill_entries.py` | Read for consumers and compatibility; no unrelated executable rewrite. |
| `skills/improve-factory/SKILL.md` | Rewritten portable entry; loading/pinning requirements preserved. |
| `skills/improve-factory/scripts/resolve_bundle.py` | Inspected generated helper; identical to canonical distribution.py; retained. |
| `skills/safe-engine/SKILL.md` | Rewritten portable entry; loading/pinning requirements preserved. |
| `skills/safe-engine/scripts/resolve_bundle.py` | Inspected generated helper; identical to canonical distribution.py; retained. |
| `tests/test_bundle_inputs.py` | Extended affected review-context or required-input coverage; focused checks passed. |
| `tests/test_feature_batches.py` | Inspected existing fault scenarios; retained. |
| `tests/test_skill_distribution.py` | Inspected existing fault scenarios; retained. |
| `tests/test_workflow.py` | Extended affected review-context or required-input coverage; focused checks passed. |
| `docs/skill-writing-audit.md` | This source, coverage and verification record. |
