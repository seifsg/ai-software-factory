# Maintenance during an app-building session

Read this when factory repair interrupts an active app run. Keep the app goal active. The parent owns the app and user updates; delegates do focused factory work and return evidence.

An optional new method does not require another QA cycle for a completed/checkpointed app. Keep its selected bundle. A separately authorized [small-change trial](../../small-change/SKILL.md#continue-alongside-a-version-run) records both identities without changing controller state or claiming fresh version acceptance. Use the adoption table below when changing a controller run's bundle.

```text
App coordinator ── save checkpoint ─────────────────── revalidate and resume
                         │                                      ▲
                         └─ isolated factory repair ─ review ───┘
                              one writer             fresh instance
```

## Quiesce and checkpoint

Stop scheduling dependent app writes, tests and reviews at the next safe boundary. Identify active operations and owners. A pending operation has not necessarily stopped.

Let an owned command finish under its actual watchdog, or use supported cancellation and verify the result. Do not kill unrelated processes, clear locks, edit saved state or leave a child able to write. If the boundary is unstable, block dependent mutation and preserve the evidence.

Read the [complete method handoff](../../safe-engine/references/method-handoff.md). Save its packet and these additions in a unique ignored local record. Read it back. It must recover the work after context loss.

| Field | Record |
|---|---|
| Original work | Request, acceptance, approved/pending choices, analysis chart, plan and current todo |
| App identity | Absolute root/worktree, branch, base/head, controller run ID/phase, task/profile digest, actual status, dirty diff and untracked inventory |
| Preservation | Keep app files and uncommitted work intact. If migration is proposed, securely preserve relevant diffs and needed untracked files. Never commit secrets. |
| Factory identity | Bundle root, commit, dirty status and hashes of dirty/untracked bundle inputs. A version label is not enough. |
| Evidence | Artifact/log/review paths and hashes, fresh/stale status, pending operations, owners and locks |
| Authority and continuity | Authorized scope/actions, completion boundary, owner checkpoints/stops, real access/provider constraints, observed tools/delegation and model configuration |
| Maintenance | Complaint, expected result, affected app steps, maintenance worktree, writer, reviewer and next resume action |

Record declared input names, not secret environment values. Use existing controller fingerprints. Keep a focused request/decision packet instead of a private transcript. Inaccessible evidence stays UNKNOWN.

## Keep the versions and writers separate

Preserve the exact app bundle. Inspect uncommitted skill/config/controller changes. A worktree at HEAD does not contain them. Keep the dirty original. If reproduction needs them, carry a reviewed patch and necessary untracked bundle files into the isolated candidate. Record both states and verify the files. Do not call a bare commit an exact dirty snapshot.

Create or reuse a suitable isolated factory worktree from the app's actual bundle revision. Follow host/repo rules. Keep the original bundle path, global settings and symlinks unchanged while the app uses it.

Worktrees separate files. Ports, databases, caches, credentials and services may still be shared. Isolate or serialize affected operations. Give each agent its absolute work path; a new worktree does not change its working directory.

Hold affected app work during repair. Parallel app work is allowed only when:
- Files, runtime effects, acceptance and decisions are independent of the fault.
- The app keeps its original fixed bundle.
- Ownership is explicit.

Otherwise keep it checkpointed. Before adoption, stop dependent operations again and capture current app state. The earlier checkpoint may be stale.

## Delegate with sufficient context

When supported and authorized, assign one repair writer and a fresh reviewer. Keep dependent coordination in the parent. Avoid overlapping writers. If delegation is unavailable, the parent can repair sequentially in isolation. Independent assessment is still required; same-instance approval cannot replace it.

Give each delegate:
- The relevant original report, expected behavior and invariants/decisions.
- Exact app/factory identities and canonical skill/reference paths.
- Raw reproduction artifacts.
- Allowed paths/actions, role and expected return artifact.
- Progress history, actual constraints and owner stop conditions.

Require full applicable skills and actual files to be read. Inherited conversation does not replace verified state. Give the fresh reviewer requirements and evidence, not the builder's desired verdict.

Keep the user's/host's model and reasoning configuration. Do not hard-code models, switch providers, lower reasoning or buy fallback access because it seems better. If a role configuration is approved, verify its model/tools/context capability and record actual routing when exposed. Otherwise inherit the current configuration; mark unavailable model identity unknown. The skill cannot guarantee the external host's model. If capability is insufficient, present three available alternatives and one recommendation before a new routing decision.

Use one maintenance record and the same authority/completion boundary. No correction allowances. The parent reconciles completed, failed and in-flight actions before retrying. Keep one active case for the same cause/checkpoint. Resume it after interruption; do not launch duplicate or recursive repairs.

## Review, adoption and resume

After independent assessment, compare the exact reviewed candidate with the preserved bundle and current app state. Check effects on version/schema, task/profile/acceptance, methods, app decisions and evidence. Read the actual controller and CLI. This table describes 0.1.0.

Important: **0.1.0 has no automatic pause, resume, upgrade or migrate command.** The checkpoint is an agent record. Do not invent commands or edit `.factory/state.json` to permit adoption.

| Current condition | What to do |
|---|---|
| Instructions were skipped; bundle need not change | Read the full routine and recover missing work. Reassess dependent artifacts/evidence. Follow normal phase rules and use `repair` where required. |
| Repair is not adopted | Continue on the unchanged old bundle only if the fault does not undermine next steps or acceptance. Otherwise block affected work. |
| Same version/schema/task/profile; recorded analysis/plan remain valid; phase is `build` | After authorized adoption, read revised routines, reassess plan/consumers, append a compatibility note and produce the next real batch with the selected bundle. No passing checks carry forward. |
| Same compatible candidate; phase is `verify`, `improve`, `final-verify`, `review` or `ready` | Use `repair --reason ...` before further work. It records correction and clears check/review acceptance. Old max-repairs integers are history. Record a new batch, complete required checks/improvement/final checks, then obtain fresh review. |
| Bundle inputs change during `analyze` or `plan` | The initial fingerprint prevents recording against changed inputs. Use the unchanged original if sound, or preserve the run and prepare a separately reviewed run in a fresh app worktree. Never rewrite the initial fingerprint. |
| Version/schema/task/profile differs, or prior analysis/plan is invalid | No automatic migration exists. Preserve the run and app work. Prepare a reviewed task/profile and clean baseline in a fresh app worktree. Carry relevant work/decisions explicitly; rerun necessary methods and QA. |
| Active operation, unexpected protected-acceptance change, unavailable reviewer, incompatible or unknown state | Block adoption. Keep checkpoint and candidate. Resolve the actual condition. A fresh run cannot bypass a failed gate or revive an owner-cancelled run. |
| Phase is `cancelled` | Preserve it. Restart needs an authorized new task/run. Never revive it by editing state. |

Adopt only within user authority. A compatible local trial does not authorize merge, release, global installation or changes to other sessions. Report the exact selected path and revision/dirty manifest. If gate code changes, the separate assessor validates its behavior independently. The gate's own output is not enough.

For a portable-entry run:
1. Checkpoint `.factory/entry-bundle.json`.
2. After authorized compatible adoption, preserve its old selection in the maintenance record.
3. Validate candidate identity using the portable resolver's explicit `--bundle` inspection.
4. Update only the receipt's `bundle_root` and `revision`. Keep dirty input hashes separately.
5. Read the receipt back. Perform the supported controller step in the table.

Blocked adoption leaves the old receipt intact. Never delete it to fetch latest, copy accepted state or treat a selection as QA. This is a compatibility handoff, not automatic migration or a general upgrade command. A fresh worktree/run gets its own receipt and old/new lineage; preserve the original.

For a fresh app worktree/run, keep the original and needed dirty/untracked work. Record run lineage, correction history, authority and actual constraints. Check copied artifacts for secrets and applicability. Do not copy acceptance/verdicts as fresh evidence, redefine requirements or mark unverified partial work passed. Keep exhausted historical allowances as history; do not remove them from saved state.

Before resuming, read current app status and work, compare with the latest checkpoint and read revised routines fully. Resume the first unfinished/invalidated step. The app coordinator changes the app; the factory repairer does not overwrite it. Return once to the existing delivery cycle, preserving the goal and PR procedures.

For rollback, keep both bundle revisions and original app state. Reverting a bundle does not restore QA after app/environment changes. Reassess compatibility and evidence. If adoption fails, record it and stop dependent work. Use the prior bundle only if still valid. Claim resumed only after the real supported next step succeeds.

## Basis and limits

Seif selected checkpoint/isolation on 2 October 2026. Supporting docs checked that day:
- [OpenAI subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): focused delegation with parent coordination.
- [OpenAI worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees): separate Git working directories.
- [Claude Code subagents](https://code.claude.com/docs/en/sub-agents): separate context, forks and model settings.

This policy is our design, not a provider guarantee. Actual tools/permissions determine availability. This skill installs no Claude-native adapter, hook, model router, state migration or automatic bundle pinning.
