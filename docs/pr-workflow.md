# PR workflow and project adapter

Read before factory PR work. Preserve source methods/reminders; resolve actual project bindings. [Provenance](skill-provenance.md).

## Pick the actual task

- Create/update: [How to Make a PR](../.agents/skills/how-to-make-a-pr/SKILL.md).
- Incoming review: [How to Review a PR](../.agents/skills/how-to-review-a-pr/SKILL.md).
- Analysis/review-only: read-only; no implied repair/push/comment.
- Bounded implementation/update: [Small Change](../.agents/skills/small-change/SKILL.md) scope below.

Authorized delivery requires both procedures and separate-instance review. Controller review/`ready` cannot complete PR delivery. Open draft; human owns ready/merge/release unless explicitly authorized.

Review: four themes → synthesis/compliance → question gate → permitted fixes → manual action QA → final test authoring/execution → authorized handoff. Controller's five acceptance passes stay separate. No added three-option phase or retry-once ceiling.

Full review: four isolated themes, capacity-bounded waves if needed; synthesize all four. Record actual execution, never call sequential work simultaneous or drop themes. Small Change: one scoped reviewer.

Judge the actual candidate. Proposed fixes mean a **conditional** verdict; list remaining fixes. Read-only review cannot count hypothetical repairs as passed.

## Resolve project bindings

Read [bindings](../.agents/skills/how-to-make-a-pr/references/project-bindings.md). Discover repository, branches, rules, commands, tracker, review owner and authorized destinations. Reuse decisions; ask only consequential remaining gaps.

Map risks to actual games, clients, servers/services or tools: platforms, languages, persistence, trust boundaries, versions and interfaces. No fixed framework, package manager, locale, vendor, person or channel.

UNKNOWN is neither N/A nor PASS. Justify inapplicability. Missing required bindings block dependent external actions/PR completion; continue independent local work. Use authorized integrations; invent no tracker, recipient or success.

Save bindings in the existing task/session record. One-time notification/merge permission is not standing authority. Source accounts/examples grant none.

## Keep current factory decisions explicit

[Tests last](current-decisions.md#finish-work-use-it-then-automate-tests), including updates/reviewer fixes: finish implementation/improvements → pass manual action QA → write/change/polish/run final tests → prepare/create PR. Read-only review inspects evidence, runs no suites. Final-test production fixes return through manual QA. Missing manual coverage stays unverified.

- No artificial correction/retry/session ceilings. Diagnose useful corrections under [session authority](../.agents/skills/safe-engine/references/session-contract.md); honor stops, command timeouts and access limits.
- Repairing reviewers need fresh independent assessment.
- Preserve no-code phases and push/comment checkpoints; reuse explicit authorization.
- Uncertain applicability blocks dependent judgment. Mandatory exceptions need authority, not explanation alone.
- Evidence only. Clean reviews need no invented findings. Preserve honest authorship/attribution/signing; claim no unperformed tests.
- No force-push/history rewrite. Preserve dirty work in an isolated checkout.
- Reviewers read applicable requirements/linked methods and raw evidence, including diagnostics, efficiency and research. Never assume missing evidence.
- App/game changes, even small: verify [shared logging](../.agents/skills/safe-engine/references/app-diagnostics.md), emitted detailed success/failure trails, provider/local access, redaction/retention and gaps. Module presence proves too little.
- Material persistence: [Database Schema](../.agents/skills/database-schema/SKILL.md), whole-product access, integrity/isolation, indexes, runtime evidence, safe migration. Reject unsupported O(1)/scale claims. Reuse reviewer, no extra fleet.

## Small direct changes

Every UI/interaction PR/update includes [UX Quality](../.agents/skills/ux-quality/SKILL.md) in its existing reviewer scope: friction, current patterns, accessibility, visual/audio inspection, uncertain-choice comparisons and manual evidence. Source alone cannot certify unseen/unheard output.

Both PR procedures apply within Small Change:

1. Inspect purpose, base/head and prior review boundary.
2. Assess delta/consumers; retain unresolved older findings.
3. Prepare focused draft/update with task links, attribution, handoff.
4. One independent reviewer covers applicable security, performance, journey, regression and compliance. No automatic fleet/full-version workflow.
5. Reuse valid evidence; repeat affected checks when needed. State exact verdict scope.

No automatic broad regression or five-output planning for bounded fixes. Narrow review cannot approve an unreviewed whole PR. Missing checks/permissions remain unresolved.

## Enforcement and evidence

Instructions only. Controller fingerprints guidance and runs local candidate review; no PR creation, notifications, remote merge enforcement or host hook.

Historical evidence covers its recorded candidate/scope. Validate changed methods; disclose remaining unknowns.
