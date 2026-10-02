# Maintenance during an app-building session

Read this reference whenever a factory improvement interrupts an active app run. The app goal stays active. The parent remains responsible for the app and user communication; delegates do focused factory work and return evidence.

```text
App coordinator ── save checkpoint ─────────────────── revalidate and resume
                         │                                      ▲
                         └─ isolated factory repair ─ review ───┘
                              one writer             fresh instance
```

## Quiesce and checkpoint

Stop scheduling dependent app writes, tests and reviews at the next safe boundary. Identify active operations and their owners before acting; a pending operation is not proof a process has stopped. Let an owned command finish under its actual process watchdog, or use supported cancellation for the owned operation and verify its outcome. Do not kill unrelated processes, clear a lock, edit saved state, or abandon a child that can still write. If you cannot establish a stable boundary, block dependent mutation and retain the evidence.

Read [the complete method handoff](../../safe-engine/references/method-handoff.md). Save that packet plus the maintenance additions below in a unique ignored local record. Verify the record can be read back. It should recover the work even if conversation context is compacted.

| Checkpoint field | Required information |
|---|---|
| Original work | Original request, acceptance criteria, approved/pending choices, analysis chart, plan and current todo |
| App identity | Absolute root/worktree, branch, base/head, controller run ID and phase, task/profile digest, actual status, dirty diff and untracked-file inventory |
| Preservation | Leave original app files and uncommitted work intact; securely preserve relevant diffs and needed untracked files if migration is proposed, without committing secrets |
| Factory identity | Resolved bundle root, commit, dirty status and hashes of dirty/untracked bundle inputs; a version label alone is insufficient |
| Evidence | Paths and hashes for saved artifacts/logs/reviews; fresh/stale status; pending operations, owners and locks |
| Authority and continuity | Authorized scope/actions, completion boundary, explicit owner checkpoints/stops and actual access/provider constraints, available tools/delegation and model configuration as observed |
| Maintenance | User's complaint and expected result, affected app steps, maintenance worktree, writer, reviewer, next resume action |

Do not record secret environment values. Record declared input names and use the controller's existing fingerprints. Do not copy an entire private transcript when a focused request/decision packet suffices. Inaccessible evidence remains UNKNOWN.

## Keep the versions and writers separate

Preserve the exact bundle currently used by the app. Inspect that checkout for uncommitted skills/config/controller changes: a worktree created at HEAD does not include them. Retain the dirty original and, when required for reproduction, carry an explicit reviewed patch and necessary untracked bundle files into the isolated candidate. Record both states and verify the resulting files. Never call a bare commit the exact snapshot of a dirty bundle.

Create or reuse a suitable isolated factory worktree from the actual app bundle revision, following host/repository rules. Keep the original bundle path unchanged while the app uses it; do not point global settings or symlinks at the candidate. Worktrees separate files, but ports, databases, caches, credentials and external services may still be shared: isolate or serialize the relevant effects. A sub-agent must operate at its assigned absolute path; creating a worktree does not change its working directory automatically.

The approved policy is to hold affected app work while repairing. Parallel app work is allowed only if its files, runtime effects, acceptance and decisions are independent of the reported fault, the app keeps its fixed original bundle, and ownership is explicit. Otherwise keep it checkpointed. Before any adoption, quiesce again and capture the current app state; the earlier checkpoint may have become stale.

## Delegate with sufficient context

Where supported and authorized, delegate the focused factory repair to one writer and the assessment to a fresh reviewer. Keep dependent coordination in the parent; multiple overlapping writers add risk. If repair delegation is unavailable, the parent can perform the isolated repair sequentially. Independent assessment is still required before acceptance; do not substitute same-instance approval.

Give each delegate the original relevant report, expected behavior, invariant/decision record, precise app and factory identities, canonical skill/reference paths, raw reproduction artifacts, allowed paths/actions, own role, progress history, actual constraints and owner stop conditions, and expected return artifact. Require it to read the actual files and full applicable routines. A fork's inherited conversation is useful context, not a replacement for verified state. A fresh reviewer gets the requirements and evidence, without the builder's desired verdict.

Preserve the user's or host's existing model/reasoning configuration. Do not hard-code a model, switch providers, lower reasoning, or launch a paid fallback on the assumption that it is best. If an approved role configuration exists, verify its model/tools/context capability is available and record actual routing when exposed; otherwise inherit the current configuration and label unavailable model identity as unknown. A skill cannot guarantee which model an external host runs. If capability is insufficient, give the user three available alternatives and one recommendation before a new routing decision.

Agents preserve one maintenance record and the same authority/completion boundary; they do not create artificial correction allowances. The parent reconciles completed/failed/in-flight actions before retrying. Keep one active maintenance case for the same cause and checkpoint; resume its record after interruption instead of launching duplicate repairs. When already maintaining the factory, continue that case rather than recursively invoking this skill.

## Review, adoption and resume

After independent assessment, compare the exact reviewed candidate with the app's preserved bundle and current state. Establish whether the change affects runtime version/schema, task/profile/acceptance, required methods, app decisions or evidence. Check actual controller code and CLI; the table below describes the current 0.1.0 implementation, not future versions.

**No automatic pause, resume, upgrade or migrate command exists in 0.1.0.** A checkpoint here is an agent-managed record. Never invent a command or modify `.factory/state.json` to make adoption possible.

| Current condition | Supported action |
|---|---|
| Existing instructions were skipped; no bundle change needed | Load the complete routine and recover the missing work. Reassess dependent artifacts/evidence; use the normal phase rules and `repair` where required. |
| Repair is not adopted in this run | Continue with the unchanged old bundle only if the fault does not undermine the next steps or acceptance. Otherwise keep affected work blocked. |
| Candidate preserves version/schema/task/profile and existing recorded analysis/plan remain substantively valid; phase is `build` | After authorized adoption, read the revised routines, re-evaluate the plan/consumers, append a compatibility note, then produce the next real batch artifact using the selected bundle. There are no passing checks to carry forward. |
| Same compatible candidate; phase is `verify`, `improve`, `final-verify`, `review` or `ready` | Use the supported `repair --reason ...` transition before further work. This records a diagnostic correction and clears check/review acceptance; former max-repairs integers are historical metadata under the continuous controller; record a new batch, run the required check/improvement/final-check cycle, then obtain fresh review. |
| Bundle inputs change during `analyze` or `plan` | The initial fingerprint prevents recording under changed inputs. Continue on the unchanged original bundle if sound, or preserve this run and prepare a separately reviewed run in a fresh app worktree. Do not rewrite its initial fingerprint. |
| Version/schema/task/profile differs, or the earlier plan/analysis is no longer valid | No automatic migration is implemented. Preserve the original run and app work; prepare a reviewed task/profile and clean baseline in a fresh app worktree, explicitly carrying the relevant work and decisions. Re-run the necessary methods and QA there. |
| Operation still active, protected acceptance changed unexpectedly, unavailable reviewer, or incompatible/unknown state | Block adoption. Retain the app checkpoint and exact candidate; resolve the actual condition. A fresh run must not bypass a failed gate or revive an owner-cancelled run. |
| Phase is `cancelled` | Preserve the cancelled run. Restarting requires an authorized new task/run; do not revive it by editing state. |

Adoption must be within existing user authority. A verified compatible local trial does not imply merge, release, global installation, or changing other sessions. Report the exact chosen bundle path and revision/dirty manifest. When the gate implementation itself changes, the separate assessor must validate its behavior independently; its own output alone cannot establish compatibility.

If a fresh app worktree/run is necessary, leave the original intact, preserve needed dirty/untracked app work, record old/new run lineage and diagnostic history, authority and actual constraints, and inspect all copied artifacts for secrets and applicability. Do not copy accepted state or verdicts as fresh evidence. A new baseline must not silently redefine the original acceptance or claim unverified partial work passed. Historical exhausted allowances remain recorded as history; they are not active gates under the owner-selected continuous policy. Do not edit saved state to remove them.

Re-read the current app status and actual work, compare against the latest checkpoint, and load the full revised routines before resuming the first unfinished or invalidated step. The app coordinator performs app mutations; the factory repairer does not overwrite them. Return to the existing delivery cycle once, preserving the original goal and required PR procedures.

For rollback, preserve both bundle revisions and the original app state. Reverting the selected bundle does not restore old QA validity after app/environment changes: reassess compatibility and evidence again. If adoption fails, record the failure, stop dependent work, and use the known prior bundle only when it remains valid. Never label the app resumed until the actual supported next step has succeeded.

## Basis and limits

The checkpoint/isolation policy is Seif's selection on 2 October 2026. Provider documentation supports bounded delegation and explicit context handling; the policy above is our design, not a provider guarantee:

- [OpenAI subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): separate delegated tasks and keep coordination in the main agent.
- [OpenAI worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees): independent Git working directories for concurrent work.
- [Claude Code subagents](https://code.claude.com/docs/en/sub-agents): ordinary subagents start with separate context; forks and model configuration have distinct behavior.

Documentation was checked on 2 October 2026. Actual host tools and permissions control availability. This skill ships no Claude-native adapter, hook installation, model router, state migration or automatic bundle pinning.
