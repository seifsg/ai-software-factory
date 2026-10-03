# PR workflow and project adapter

Read this before executing the original PR skills in a factory-managed project. Keep the original wording; resolve its project assumptions here.

## Pick the actual task

- Feature draft: use [How to Make a PR](../.agents/skills/how-to-make-a-pr/SKILL.md). Its original is from Seif's routines repository. Mobile's `release-pr` is a release rollup with version bumps and changelog changes, so it is not a substitute for an ordinary feature draft.
- PR review: use the Mobile `pr-review` original at [How to Review a PR](../.agents/skills/how-to-review-a-pr/SKILL.md). The existing factory path is retained for callers.
- Explicit analysis-only or review-only: remain read-only. Do not start repairs, push or comment from an implied later phase.
- Bounded implementation or PR update: use the [Small Change](../.agents/skills/small-change/SKILL.md) scope below.

For authorized factory PR delivery, both creation and a separate-instance review are required. Local controller review and `ready` are not PR completion. Keep the PR draft; the human owns ready, merge and release.

The creation original contains an older summary of its paired review. Follow the actual Mobile review file: four themes, synthesis/compliance, question gate, permitted fixes, checks and authorized handoff. Do not revive the old three-option PR phase or retry-once limit from that summary. The local controller's five acceptance passes are separate.

For a read-only review, judge the current candidate. Proposed or hypothetical fixes remain unresolved; do not report their future result as a present pass. Label a conditional verdict and its remaining fixes explicitly.

The creation original also refers to `clickup-task`, `how-to-write-a-clickup-task` and `bug-investigation`. They are not bundled here. Resolve them from an authorized target installation when needed; if unavailable, report the dependent step as incomplete. Do not fabricate a local substitute or import the wider library automatically.

## Resolve project bindings

Use [project bindings](../.agents/skills/how-to-make-a-pr/references/project-bindings.md) to find the actual repository, branches, rules, commands, tracker, review owner and authorized notification destination. Reuse recorded decisions. Ask only for consequential missing facts after discovery.

RepairCheck account names, Slack channels, ClickUp lists, tool names and example PRs in the source are source-project context. Do not send to them or create automations merely because they appear in an original. Existing task authorization still governs external actions.

Mobile paths and checks describe Expo/React Native. For another stack, map the same risk to its real code and tools. Report a justified N/A; unknown is not N/A or PASS. The copied Mobile rules are source context; load the target's actual rules. Do not impose NestJS, Expo, German copy, npm or a telemetry vendor where it does not apply.

Missing required bindings block the affected external action and PR completion. Continue authorized local work. Do not invent a replacement tracker, recipient or evidence.

## Keep current factory decisions explicit

These are factory policies, separate from the restored source wording:

- Seif removed artificial correction/retry/session ceilings. Diagnose and continue useful authorized corrections under the [session contract](../.agents/skills/safe-engine/references/session-contract.md). Preserve owner stops, command timeouts and actual access limits.
- If a reviewer repairs a candidate, get a fresh independent assessment of the resulting candidate. Its own repair is not independent approval.
- Follow Mobile's no-code review phases and push/comment checkpoints. Reuse explicit authorization already given; do not ask again for the same authorized action.
- For factory acceptance, uncertain rule applicability stays UNKNOWN and blocks the dependent decision. An exception needs actual authority; a written justification alone does not waive a requirement. See decisions I1/I2.
- Use real evidence. A clean review may have no findings. Do not invent issues or product requirements to fill a table.
- Preserve honest authorship. Never claim someone authored or tested work they did not. Follow actual project attribution/signing rules.
- Never force-push or rewrite another author's history. Preserve dirty work in a suitable isolated checkout; do not silently stash or switch it.

## Small direct changes

Both PR procedures still apply to an authorized small PR. Use their relevant outcomes within the selected [Small Change](../.agents/skills/small-change/SKILL.md) method:

1. Inspect the PR's original purpose, base/head and prior review boundary.
2. Assess the new delta and affected consumers. Keep unresolved older findings visible.
3. Prepare a focused draft/update with actual task links, attribution and handoff.
4. Have one independent reviewer cover the changed behavior and applicable security, performance, journey, regression and compliance concerns together. No automatic fleet or full-version workflow.
5. Reuse current evidence; rerun affected checks when necessary. Report the verdict's exact scope.

No automatic broad regression or five-artifact planning for a bounded fix. A narrow assessment does not turn an unreviewed whole PR green. Missing required checks or permissions stay unresolved.

## This repository's bindings

| Binding | Recorded status |
|---|---|
| Repository | Private `seifsg/ai-software-factory`. Discover current remote branches when preparing a PR. `main` was the verified default on 2 October. |
| Task tracker / awaiting-review state | Not selected. Do not invent a tracker or mark local work as a task transition. |
| Human reviewer / notifications | No permanent binding selected. The one-time Slack notification authorized on 2 October is not standing permission for later messages. GitHub self-review restrictions still apply. |
| Checks | Relevant Python controller/distribution tests, skill structure and references, affected JavaScript syntax and rendered preview. No npm build/typecheck/lint toolchain is configured for this repository. |
| Observability | The local pilot had no production session. |
| Merge / release | Human decision. Prior specific merge instructions do not create standing permission. |

The earlier proposal was GitHub Issues with a human GitHub handoff; an existing team tracker or leaving settings pending were alternatives. No choice is inferred from this writing pass. Discover current project/session evidence before escalating a missing binding.

## Enforcement and evidence

The procedures are instructions. The controller fingerprints guidance and runs its own local candidate review; it does not create a PR, notify anyone or enforce GitHub merges. No host hook or protected remote merge gate is implemented.

[PR #1](https://github.com/seifsg/ai-software-factory/pull/1) and the [pilot verification](pilot-verification.md) are historical evidence. They do not certify the restored Mobile PR procedure or this edited candidate.
