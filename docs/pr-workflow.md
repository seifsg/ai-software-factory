# PR workflow and project adapter

Read before executing factory PR procedures. They preserve the source methods and deliberate
reminders while adapting project bindings for generic software. Exact sources and deviations:
[provenance](skill-provenance.md).

## Pick the actual task

- Feature draft/update: [How to Make a PR](../.agents/skills/how-to-make-a-pr/SKILL.md).
- Incoming PR review: [How to Review a PR](../.agents/skills/how-to-review-a-pr/SKILL.md).
- Explicit analysis-only/review-only: stay read-only. Do not infer repair, push or comment authority.
- Bounded implementation/update: use the [Small Change](../.agents/skills/small-change/SKILL.md) scope below.

Authorized factory PR delivery requires creation plus separate-instance review. Controller review
and `ready` do not complete PR delivery. Open draft; human owns ready, merge and release unless
the user explicitly authorizes that action.

The review method is: four themes → synthesis/compliance → question gate → permitted fixes →
manual action QA → final test authoring/execution → authorized handoff. The local controller's five acceptance passes are separate.
Do not insert a three-option PR phase or a retry-once ceiling.

Full review keeps four isolated theme passes. If host capacity cannot run all four together,
run independent sessions in capacity-bounded waves, then synthesize all four results. Record
the actual arrangement; never label sequential work simultaneous or drop a theme to fit slots.
Small Change keeps its single scoped reviewer.

Judge the actual candidate. A verdict dependent on proposed fixes is **conditional**; report its
remaining fixes. A read-only review cannot count hypothetical repairs as a present pass.

## Resolve project bindings

Read [project bindings](../.agents/skills/how-to-make-a-pr/references/project-bindings.md).
Discover repository, branches, rules, commands, tracker, review owner and authorized destinations.
Reuse recorded decisions; ask only after discovery leaves a consequential gap.

Map each risk to the real product: games, web/mobile/desktop clients, servers, services and tools.
Discover platforms, languages, persistence, trust boundaries, version compatibility and interfaces.
No fixed framework, package manager, locale, telemetry vendor, person or channel is prescribed.

Unknown is not N/A or PASS. Justify genuinely inapplicable checks. Missing required bindings block
the affected external action and PR completion; keep authorized independent local work moving.
Use installed authorized integrations; do not invent a replacement tracker, recipient or success.

Store resolved bindings in the project's task/session record. A prior one-time notification or merge
request creates no standing permission. No source-project account or historical example authorizes action.

## Keep current factory decisions explicit

Follow [tests-last order](current-decisions.md#finish-work-use-it-then-automate-tests) for creation, updates and reviewer repairs. Finish implementation/improvements and pass manual action QA before writing, changing or running automated tests. Prepare/create the PR only after final tests. Read-only reviews inspect evidence; they do not launch suites. A failed final test returns production fixes through manual QA before testing resumes. Missing manual coverage remains unverified.

- No artificial correction/retry/session ceilings. Diagnose and continue useful authorized corrections
  under the [session contract](../.agents/skills/safe-engine/references/session-contract.md).
  Preserve owner stops, command timeouts and actual access limits.
- A reviewer who repairs code needs a fresh independent assessment of the resulting candidate.
- Preserve no-code phases and push/comment checkpoints. Reuse existing explicit authorization.
- Uncertain rule applicability stays UNKNOWN and blocks the dependent decision. A mandatory exception
  needs actual authority; written justification alone cannot waive it.
- Use real evidence. Clean reviews may have no findings. Never invent issues to fill a table.
- Preserve honest authorship, actual attribution and signing rules. Never claim unperformed tests.
- Never force-push or rewrite another author's history. Preserve dirty work in an isolated checkout.
- Each independent reviewer receives applicable requirements and evidence, including diagnostics,
  efficiency and research decisions. Read the relevant linked methods; never assume missing evidence exists.
- For app/game changes, verify the mandatory shared logger and actual detailed success/failure trails, including small fixes. Inspect provider/local access, redaction, retention and coverage gaps through [the logging contract](../.agents/skills/safe-engine/references/app-diagnostics.md); module presence alone is insufficient.
- For material persistence changes, read [Database Schema](../.agents/skills/database-schema/SKILL.md). Assess chosen design against whole-product access patterns, integrity/isolation, indexes, runtime evidence and safe migration; reject unsupported O(1) or scale claims. Reuse the current reviewer rather than adding a fleet.

## Small direct changes

Both PR procedures apply to an authorized small PR, within the selected Small Change method:

1. Inspect original purpose, base/head and prior review boundary.
2. Assess the new delta and consumers. Keep unresolved older findings visible.
3. Prepare the focused draft/update with real task links, attribution and handoff.
4. One independent reviewer covers applicable security, performance, journey, regression and compliance
   together. No automatic fleet or full-version workflow.
5. Reuse valid evidence; rerun affected checks when needed. State the exact verdict scope.

No automatic broad regression or five-artifact planning for a bounded fix. Narrow review does not
turn an unreviewed whole PR green. Missing required checks and permissions remain unresolved.

## Enforcement and evidence

These procedures are instructions. The controller fingerprints guidance and runs local candidate
review; it does not create PRs, notify people or enforce remote merges. No host hook or protected
remote merge gate is implemented.

Historical pilot and review evidence certifies only its recorded candidate and scope. Validate the
current changed methods and report what remains unverified.
