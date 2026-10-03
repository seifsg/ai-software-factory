# Full factory audit — 3 October 2026

**Verdict: the core factory is coherent, but it has seven actionable defects/gaps. Fix these before treating this candidate as a dependable complete delivery system.** There is no reason to rewrite Seif's originals again. The repairs belong in runtime code, factory coordination and distribution.

Five findings were reproduced locally; two are demonstrated instruction/handoff gaps. The full existing suite passed **69 tests in 201.938 seconds**. Passing that suite does not cover the newly reproduced cases.

The four runtime defects and legacy completeness logic are in code unchanged by the current writing pass. This broader audit exposed existing bugs alongside the current coordination gaps; restoring the Mobile originals did not create those five runtime/distribution failures.

The audit covered the 85-file candidate based on `17db37c54e5662add9a976ee39c262cfaf70fcbb`, subsequently published as [commit 9a9db80](https://github.com/seifsg/ai-software-factory/commit/9a9db80d2d16b3db48052ee70eea6b2d54a12f7d) in [PR #5](https://github.com/seifsg/ai-software-factory/pull/5). Its pre-publication manifest SHA-256 was `4ee07a697b0ccc963367aa134212c834049e9aba3a2603a85af872bdb095fcd8`; all 85 working files matched after the audit. Git normalizes configured line endings on publication. This portable audit, the [phone-readable status page](factory-status.md) and README navigation were added afterwards without changing runtime or skill behavior.

## Findings

Priority is based on practical effect: P1 / HIGH means address first; P2 / MEDIUM means a material defect or supported-path gap. No critical finding was established. Counts: **1 HIGH, 6 MEDIUM**.

| ID | Priority | Category | Location | Finding and effect | Evidence |
|---|---|---|---|---|---|
| F1 | P1 / HIGH | Filesystem safety | `safe_engine/workflow.py:148–156`, `safe_engine/storage.py:42–45` | Windows output cleanup can delete source files through an NTFS junction. The final gate fails only after deletion. | Real isolated reproduction |
| F2 | P2 / MEDIUM | Timeout | `safe_engine/runner.py:30–37`, `safe_engine/workflow.py:304–306` | A reviewer that stops reading a sufficiently large prompt can block beyond its timeout on Windows while holding the project lock. | Real isolated reproduction |
| F3 | P2 / MEDIUM | Evidence integrity | `safe_engine/project.py:66–71`, `safe_engine/workflow.py:157–167` | IDs such as `unit` and `UNIT` are accepted but overwrite each other's logs on Windows. Checks report success, then review cannot proceed. | Real isolated reproduction |
| F4 | P2 / MEDIUM | Resource bounds | `safe_engine/runner.py:28–44` | Output is capped only after the child exits. Temporary capture can fill the disk during a noisy check/review. | Real isolated reproduction |
| F5 | P2 / MEDIUM | Independent review | `safe_engine/workflow.py:270–287` | The fresh reviewer packet omits required factory diagnostics, efficiency and new-app research instructions. | Missing explicit loading/coverage; procedural walkthrough |
| F6 | P2 / MEDIUM | Skill scope | `.agents/skills/research-market/SKILL.md:14,43,47` | Standalone competitor research is supported by the trigger, but always demands a coding plan and existing controller plan stage. | Contradictory entry/exit paths |
| F7 | P2 / MEDIUM | Resume compatibility | `safe_engine/distribution.py:13–20,47,73–75` | Modern launchers reject the actual historical pilot bundle used by the documented legacy-resume route. | Real historical-revision reproduction |

### F1 — Output cleanup can delete source files

An NTFS junction is not reported as a symlink by `Path.is_symlink()`. The controller therefore accepts `.factory/outputs` pointing to an ordinary directory elsewhere inside the app. It resolves that substituted directory as the trusted output root and deletes declared output names from it before running a check.

The fixture committed `source-assets/proof.txt`, then pointed `.factory/outputs` to `source-assets`. A normal check, inside the real lock, deleted the tracked file. Git reported ` D source-assets/proof.txt`; QA failed afterwards. Only synthetic fixture data was affected.

Reject junction/reparse aliases before cleanup and validate the actual generated-output boundary and ancestors. Preserve Python 3.11 compatibility. Test aliases at both `.factory` and `.factory/outputs` and assert that the source file survives rejection. This is accidental local filesystem safety, within the pilot's stated scope; it does not assume a hostile user.

The independent runtime report originally ranked this P2. This consolidated audit ranks it P1 because the controller itself deletes a source file before reporting failure.

### F2 — Review timeout does not cover a blocked stdin write

The reviewer receives the prompt through `communicate(input=..., timeout=...)`. On Windows, a blocked pipe write can delay the timed wait. A real child that ignored 65,536 bytes of input and self-exited after three seconds took **3.500 seconds** with a valid **one-second timeout**. Its exit code was zero from natural termination; only then could the runner report `timed_out: true`.

A child that neither reads nor exits can remain blocked. Use an input file or a managed writer whose deadline covers input delivery and completion. Add a Windows test exceeding pipe capacity. This reproduction verifies the runner failure mode, not a live Codex service failure.

### F3 — Case-colliding check IDs make a valid run impossible to finish

The validator accepts `unit` and `UNIT` as different IDs, while Windows treats their generated log paths as the same file. The second check overwrites the first log after its hash was saved. Both initial and final batches reported passing; the subsequent evidence check rejected the first log's hash.

Because the profile is immutable, repeating the repair/check cycle does not solve the collision. Reject case-colliding IDs during initial validation or allocate unique physical filenames independently of IDs. The existing case-folded artifact-path validation is a useful precedent.

### F4 — Temporary output is unbounded

A real child wrote **16,777,216 bytes** into the temporary capture file. Only the final persisted log was clipped to **1,000,000 bytes**. The fixture was deliberately small enough to avoid disk pressure, but the code imposes no in-flight size limit, including for checks permitted to run for up to an hour.

Drain output into bounded storage or stop at an explicit cap, preserving timeout and process-tree cleanup. The existing truncation flag correctly describes the final log; it does not protect temporary storage.

### F5 — The fresh reviewer does not receive the full factory contract

The prompt explicitly loads five original methods, three Mobile review rubrics and the project adapter. It does not explicitly require loading `app-diagnostics.md`, `app-efficiency.md` or `method-handoff.md`. An indirect discovery path exists through project bindings → PR adapter → session contract → decisions → app defaults. That does not make the applicable contracts or their coverage explicit in the fresh local review packet. The prompt checks detailed planning outputs but omits the required new-app original-plan → research → revised-plan evidence.

The factory promises checks such as logger secret/content canaries, retention and destination failure, and applicable cache/resource/cold-warm evidence. Generic security/performance rubrics may catch defects, but cannot reliably substitute for those selected requirements. The reviewer runs ephemerally from the app directory, so loading the factory's root rules is not assured.

Pass the applicable references and their evidence requirements explicitly. Extend the delegation packet similarly when launching isolated PR themes, including actual project mappings and selected scope. Keep the Mobile originals unchanged. This is a gap in explicit context loading and review coverage, not an absence of the underlying requirements or all links to them. No live false PASS was claimed or demonstrated.

### F6 — Research-only requests have no coherent exit path

The skill explicitly accepts requested competitor research. A request such as “Compare three note apps; research only” can have no app repository or coding plan. The skill nevertheless routes a missing plan into Get Ready to Code, including its file-summary stop, then requires five revised coding-plan outputs and a return to the existing controller `plan` stage.

Separate standalone research from research inside new-app planning. Only the latter should require original/revised coding plans and controller-stage handoff. This is a change to the factory-specific research coordinator, not the original planning method.

### F7 — Documented legacy resume rejects a legitimate old bundle

The current resolver checks today's mandatory file list before considering a bundle's age or own contract. An isolated checkout of the real historical pilot revision `eeb0da9d26092e67ea2e7abb58ec57ffd815df49` failed the documented `--entrypoint safe-engine --bundle <original> --project <legacy-app>` route because it predates seven later additions.

The resolver exited 1, preserved app state and created no receipt. Thus this is blocked compatibility, not data loss or false acceptance. Existing tests build old-style fixtures from today's required list and miss real historical layouts.

Use version/entrypoint-aware completeness or a verified legacy route without silently upgrading the selected bundle. Keep strict validation for current contracts. Add a fixture representing the actual documented pilot.

## What remains coherent

- **Originals and ownership:** RepairCheck Mobile remains the priority for its six matching methods; the separate PR-creation original is a recorded fallback. Factory-specific adaptations remain outside original bodies. This audit changed none of them.
- **Workflow:** analysis → plan → build → full checks → improvement → final checks → independent review → local handoff is consistently represented. Partial feature feedback cannot substitute for complete version acceptance.
- **Evidence freshness:** fixed task/profile, protected check files, source/input fingerprints, required logs/output hashes, fresh review and cancellation are enforced through normal controller use. Opt-in reuse is explicitly limited to unchanged, controlled inputs.
- **Scope and authority:** standalone analysis/review stays in that phase; small changes have a separate scoped route; PR publication, notifications, merge and deployment remain distinct from local readiness.
- **Recovery:** continuous repair, current-input checks, changed-contract fresh-worktree handling and active-app maintenance checkpoints are documented. The audit did not establish a stale-acceptance bypass in normal PR repair.
- **Packaging:** current required files exist, including all four imported Mobile `.mdc` rules. Both repository resolver copies match the canonical implementation. The checked documentation/skill references resolve; dated design records are labeled as history.

## Real unfinished work, already disclosed

These are completion limits rather than newly discovered code regressions:

| Area | Current gap | Consequence |
|---|---|---|
| Full PR delivery | `clickup-task`, `how-to-write-a-clickup-task` and `bug-investigation` are referenced but not bundled; actual tracker, reviewer-owner and notification bindings remain unselected. | The repository alone cannot complete every step of the paired PR procedure. Required external actions must await real bindings. |
| Installed personal skills | Personal entries have not received the current source changes. The installed Improve Factory resolver still defaults to `docs/skill-lifecycle-map`; the source defaults to `main`. | Calling the installed skill is not proof that this candidate is active. Installation, bundle adoption and release must be verified separately. Remote branch freshness was not checked this turn. |
| Current end-to-end proof | The historical app demo predates restored methods/defaults; a full live app → factory repair → app resume demonstration is still absent. | Unit tests and instruction exercises cannot certify current whole-app delivery. |
| Host capacity and adapters | Mobile PR review requires four concurrent child reviews. This host exposes only three child slots alongside the parent; equivalent separate processes need a defined route. Claude-only/cloud review is not demonstrated. | Host portability remains conditional. Preserve independent review intent and explicitly resolve the concurrency mapping. |
| Specialists and enforcement | Dedicated architecture, UX/product, TDD/test review and other planned modules; managed workflow integration; protected remote merge/release controls and universal host hooks are unfinished. | The implemented local pilot covers part of the broader factory vision. These should not be described as already delivered. |

A production-only repository's hotfix companion-branch policy also needs a project mapping. Do not invent a `dev` branch to satisfy a source-specific example.

## Concerns checked and not counted as defects

- Full PR repairs already inherit a current-input resume packet and the session contract's repair cycle. A more explicit reminder may help, but a broken return path or accepted stale result was not established.
- Changed requirements after market research already have a specific preserve-run/fresh-worktree rule. The broad “do not restart” instruction does not override that exception.
- Relative executable handling merits a Linux reproduction. Windows resolves executable paths differently; this audit did not establish a hash/run mismatch on the current host.
- Interrupted batches, unchanged dirty-bundle identities, unsigned local records and hidden service inputs have documented reconciliation/trust limits. No additional bypass was demonstrated.

## Verification and coverage

The audited 85-file candidate was inventoried and matched against its pre-audit hashes before these publication-only documentation additions. Three independent audits covered runtime/schema/tests, all 30 canonical skill files, and distribution/docs/preview/examples/installed entry drift. Parent review checked reproductions and challenged suspected findings before consolidation.

| Check | Result |
|---|---|
| Full Python unittest discovery | **69 passed**, 201.938 seconds; CPython 3.12.14 on Windows |
| Runtime failure fixtures | Four confirmed defects, real local subprocesses/filesystem behavior |
| Legacy distribution fixture | Rejected actual historical bundle; app state preserved |
| Procedural walkthroughs | Two actionable scope/context gaps; two suspected recovery gaps withdrawn |
| Current packaging/link inspection | Required files present; resolver copies identical; no missing real target in distribution audit's relative-link scan |
| Prior structural/browser evidence | Retained because all source hashes remain unchanged; not represented as a new app demonstration |
| Source preservation | All 85 pre-audit candidate files unchanged; no new nonignored files |

The audit itself did not execute a live PR, remote service, new application delivery, Linux/macOS runtime or actual model-based false verdict. The later publication and PR assessment are recorded separately in PR #5. The suite uses review doubles in relevant tests. Those limits are material to readiness.

## Repair order

1. Prevent junction cleanup outside the actual generated-output area; add the no-deletion regression case.
2. Fix blocked-stdin timeout and bounded capture; reject case-colliding IDs. Reuse the concrete runtime fixtures as regression scenarios.
3. Pass the complete applicable factory review context; provide a standalone research branch.
4. Repair genuine legacy resolution and test a historical bundle shape.
5. Exercise one complete current app run and an interrupted maintenance/resume scenario, then verify distribution/adoption and remaining PR bindings before claiming those routes complete.

The first four items are targeted runtime/coordinator/distribution repairs. They do not require rewriting Seif's original procedures or implementing the entire planned specialist library.

## Evidence available from your phone

The observations below summarize the isolated local fixtures. No real project source file was deleted by the audit. Runtime logs, disposable repositories and machine-specific paths remain outside Git; all findings and material reproduction outcomes are included here.

| Scenario | Observed result |
|---|---|
| Full test suite | `Ran 69 tests in 201.938s` → `OK`; Windows CPython 3.12.14 |
| Junction output cleanup | `is_symlink=false`, `is_junction=true`; synthetic tracked `source-assets/proof.txt` deleted; `checks_passed=false` |
| Blocked stdin | Requested timeout `1s`; input `65,536 bytes`; child ignored stdin and self-exited after `3s`; measured `3.500s`; natural exit code `0`, eventual `timed_out=true` |
| Case-colliding IDs | `unit` and `UNIT` accepted; initial/final batches passed; both paths held `UNIT\n`; required-evidence check rejected overwritten hash |
| Output capture | Actual temporary file `16,777,216 bytes`; final log `1,000,000 bytes`; `log_truncated=true` |
| Legacy resume | Actual bundle `eeb0da9d26092e67ea2e7abb58ec57ffd815df49`; resolver exit `1`; app state preserved; no new receipt |
| Source preservation during audit | 85 manifest entries, 85 source files, 0 changed, 0 missing, 0 added |

For legacy resume, the resolver reported these later-added files missing from the historical bundle:

```text
docs/pr-workflow.md
.agents/skills/safe-engine/references/session-contract.md
.agents/skills/improve-factory/references/live-session.md
.agents/skills/improve-factory/SKILL.md
.agents/skills/how-to-make-a-pr/SKILL.md
.agents/skills/how-to-review-a-pr/SKILL.md
.agents/skills/research-market/SKILL.md
```

Inspect the corresponding source at the audited commit:

- [Output cleanup and reviewer handoff](https://github.com/seifsg/ai-software-factory/blob/9a9db80d2d16b3db48052ee70eea6b2d54a12f7d/safe_engine/workflow.py)
- [Process runner](https://github.com/seifsg/ai-software-factory/blob/9a9db80d2d16b3db48052ee70eea6b2d54a12f7d/safe_engine/runner.py)
- [Lock/path checks](https://github.com/seifsg/ai-software-factory/blob/9a9db80d2d16b3db48052ee70eea6b2d54a12f7d/safe_engine/storage.py)
- [Profile validation](https://github.com/seifsg/ai-software-factory/blob/9a9db80d2d16b3db48052ee70eea6b2d54a12f7d/safe_engine/project.py)
- [Bundle resolver](https://github.com/seifsg/ai-software-factory/blob/9a9db80d2d16b3db48052ee70eea6b2d54a12f7d/safe_engine/distribution.py)
- [Research Market](https://github.com/seifsg/ai-software-factory/blob/9a9db80d2d16b3db48052ee70eea6b2d54a12f7d/.agents/skills/research-market/SKILL.md)
- [Original fidelity and writing-pass validation](skill-writing-audit.md)
- [Factory status and every skill](factory-status.md)

No source fixes, commits, pushes, personal installations or external messages were performed during the audit. Publication was separately authorized afterwards; PR #5 records its current state. The seven findings remain unresolved by that publication.
