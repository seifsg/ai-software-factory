# Maintenance during an active app run

Contents: quiesce, checkpoint, separate versions and writers, delegate, adopt, entry receipt, resume.

Read before touching any workspace while app work is active. The app coordinator owns the project and user updates. The repairer returns factory evidence only.

```text
App coordinator ── checkpoint ─────────────────── revalidate → resume
                        └─ isolated repair ─ review ─┘
                              one writer     fresh agent
```

- No command pauses, resumes, upgrades or migrates a run. Checkpoints are records you write.
- Never invent commands or edit saved run state to allow adoption.
- Keep the selected bundle. New optional methods do not reopen QA on completed or checkpointed work.

## 1. Quiesce

1. At a safe boundary, stop scheduling dependent writes, tests and reviews.
2. List active operations and their owners. Let owned commands finish under real watchdogs, or stop them through supported cancellation. Pending is not stopped.
3. Never kill unrelated processes, clear locks, edit saved state or leave children able to write.
4. No stable boundary: preserve evidence and block dependent changes.
5. Active Fast run: `pause` its gate with the maintenance reason.

## 2. Checkpoint

Save one unique Git-ignored record. Read it back.

| Field | Record |
|---|---|
| Work | Request, acceptance, approved and pending decisions, plan, current todo |
| Tickets | App and maintenance ticket links, confirmed scope revisions, owner sources, latest refresh, pending changes |
| Project | Absolute root or worktree, branch, base and head, run key and phase, status, dirty diff, untracked files |
| Factory | Bundle root, commit, dirty status, hashes of dirty and untracked inputs. A version label is not enough. |
| Evidence | Artifact, log and review paths with hashes, freshness, pending operations, owners, locks |
| Authority | Scope, allowed actions, completion boundary, stops, access limits, available tools and delegation |
| Maintenance | Report, expected result, affected steps, maintenance worktree, writer, reviewer, next resume action |
| Sessions | App and maintenance builder sessions, worktree or shared-epic ownership, shared service leases |

- Keep project files and uncommitted work intact. Never commit secrets. Record input names, not values.
- Reuse controller fingerprints and a focused request packet, not transcripts.
- Inaccessible evidence stays UNKNOWN.

## 3. Separate versions and writers

- Preserve the exact selected bundle, including dirty changes that HEAD omits. Rebuild that state in the candidate from a reviewed patch plus the needed untracked inputs. Record and verify both.
- Create the repair worktree from the bundle's actual revision. Keep the original bundle path, global settings and symlinks.
- Isolate or serialize shared ports, databases, caches, credentials and services.
- Hold affected app work. Parallel app work needs all three:
  - Independent files, runtime effects, acceptance and decisions.
  - An unchanged original bundle.
  - Explicit ownership.

## 4. Delegate

- When available and authorized: repair writers on disjoint files and one fresh reviewer. Otherwise the parent repairs in isolation; independent review is still required.
- Give each delegate: report, expected behavior, invariants, exact project and factory identities, skill paths, raw reproduction, allowed paths and actions, role and return artifact, progress and stops.
- Delegates read the applicable skills and actual files fully. Inherited chat is not verified state.
- Reviewers get requirements and evidence, never a verdict.
- Keep the owner's model and reasoning settings. No hard-coded models, provider switches, reduced reasoning or paid fallbacks without the owner.
- Reconcile completed, failed and in-flight actions before any retry.
- Context lost: reread the case and the actual state, then resume the same case. No duplicate repairs.

## 5. Adopt

1. Stop dependent operations again and take a fresh checkpoint. Earlier snapshots may be stale.
2. Refresh the app and maintenance tickets. Compare candidate, preserved bundle and current project: controller schema, task, profile, acceptance, scope, methods, decisions, evidence. Pending scope, drift or a failed refresh blocks adoption.
3. Read the actual controller version and saved profile.
4. Act on the first row that applies:

| Condition | Action |
|---|---|
| Active operation, missing reviewer, unexpected acceptance change, unknown or incompatible state | Block adoption. Keep checkpoint and candidate. Fix the cause. |
| `cancelled` | Preserve. Restart only as an authorized new run. |
| Instructions skipped; bundle unchanged | Read the full method, recover the missing work, reassess artifacts. Use `repair` when the phase requires it. |
| Repair not adopted | Continue on the old bundle only if the fault cannot undermine next steps or acceptance. Otherwise block affected work. |
| Fast run | Read revised methods, reassess the plan, note compatibility in the work record, `resume` the gate. |
| Compatible; analysis and plan valid; in `build` | Read revised methods, reassess plan and consumers, note compatibility, continue with the next real batch. No passing check carries forward. |
| Compatible; in manual QA, testing or after QA | `repair --reason ...` clears acceptance. Redo affected manual QA (an unaffected PASS may be `carried` with a reason), final tests and a fresh independent review. |
| Inputs changed during `analyze` or `plan` | The fingerprint blocks it. Keep the sound original, or preserve the run and start a separately reviewed run in a fresh project worktree. Never rewrite a fingerprint. |
| Task or profile correction within the same goal | Reviewed `amend`: keep both contracts, protected hashes, authority and reason. Acceptance resets; repeat the final evidence. |
| Controller schema incompatible; analysis or plan invalid | No migration. Preserve run and work. Prepare a reviewed task, profile and clean baseline in a fresh project worktree; carry work and decisions explicitly. Rerun the needed methods and final QA. |

- A fresh run never bypasses a failed gate or revives a cancellation.
- Adopt within authority. A local trial grants no merge, release, global install or change to other sessions.

## 6. Entry receipt

1. Checkpoint `.factory/entry-bundle.json`.
2. After authorized compatible adoption, save the old selection in the maintenance record.
3. Inspect the candidate with the resolver's `--bundle`.
4. Update only the receipt's `bundle_root` and `revision`. Store dirty hashes separately.
5. Read the receipt back. Apply the matching table row.

- Blocked adoption keeps the old receipt. Never delete it to fetch the latest or to copy accepted state.
- Fresh worktrees and runs get their own receipts with old and new lineage.

## 7. Resume

1. Read current status, work and revised methods fully. Compare with the latest checkpoint and the app ticket.
2. Resume at the first unfinished or invalidated step. The app coordinator writes the project; the repairer never overwrites it.
3. Return once to the existing delivery, goal and PR flow. Never reinitialize or silently change requirements.
4. An app run without a ticket keeps its recorded path. Never invent a ticket binding.
5. Fresh-run handoff keeps dirty work, lineage, correction history, authority and constraints. Check copied artifacts for secrets. Never copy verdicts as fresh evidence.
6. Claim "resumed" only after a supported next step succeeds.

Rollback keeps both bundles and the original state. Reassess compatibility and evidence; reverting does not restore QA. Adoption fails: record it, stop dependent work, use the prior bundle only if it is still valid.

Report repair, adoption and PR separately. State whether the old bundle can continue.
