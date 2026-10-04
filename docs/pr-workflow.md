# PR workflow and project adapter

Read before factory PR work. Preserve source methods/reminders; resolve actual project bindings. [Provenance](skill-provenance.md).

New PR prose uses [Clear Writing](../.agents/skills/safe-engine/references/clear-writing.md); preserve required evidence, attribution, history and source wording.

Public-page changes include affected [SEO evidence](../.agents/skills/ux-quality/references/web-seo.md) in the same review. Distinguish local checks, live verification and actual indexing.

## Pick the actual task

- Create/update: [How to Make a PR](../.agents/skills/how-to-make-a-pr/SKILL.md).
- Incoming review: [How to Review a PR](../.agents/skills/how-to-review-a-pr/SKILL.md).
- Analysis/review-only: read-only; no implied repair/push/comment.
- New implementation/update: [Ticketing](../.agents/skills/ticketing/SKILL.md), confirmed scope and full cycle. Bounded fixes keep [Small Change](../.agents/skills/small-change/SKILL.md)'s surgical tactics.
- Existing unticketed work: preserve its recorded small/full path; no silent migration or acceptance refresh.

Authorized delivery requires both procedures and remote/cloud PR review: a separate agent, fresh context and checkout of the exact remote candidate. Verify actual remote execution and record provider/task identity, base/head, evidence and verdict. Local controller review remains separate; local subagents never satisfy PR review. Missing cloud access blocks that review/merge, not independent local work. Open draft; human owns ready/merge/release unless explicitly authorized.

Review: four themes → synthesis/compliance → question gate → permitted fixes → manual action QA → final test authoring/execution → authorized handoff. Controller's five acceptance passes stay separate. No added three-option phase or retry-once ceiling.

Ticketed/full cloud review: four isolated themes, capacity-bounded waves if needed; synthesize all four. Record actual execution, never call sequential work simultaneous or drop themes. Legacy unticketed Small Change: one scoped cloud reviewer. Supply core methods plus applicable references and raw evidence, not every unrelated checklist; reviewer challenges omissions.

Judge the actual candidate. Proposed fixes mean a **conditional** verdict; list remaining fixes. Read-only review cannot count hypothetical repairs as passed. Separate severity from disposition: unresolved HIGH/CRITICAL, core failures and required unknowns block. Lower-risk accepted deferrals need owner, reason, scope, authority and revisit trigger; before-exposure obligations remain open until that boundary.

## Compare the current ticket

Refresh the selected tracker ticket and meaningful activity before PR submission/update and cloud verdict. Use the owner's preferred MCP; GitHub Issues is the default and Seif's current choice. Reuse the existing ticket; read before writing, reconcile uncertain effects and verify remote updates. Local records are cache/evidence.

Pin original input, latest confirmed after/criteria, scope revision/digest, owner source, dependencies and exact PR base/head. Proposed changes remain pending. Resolve drift through owner authority and supported reviewed rebinds; invalidate affected evidence. Failed refresh or unresolved scope blocks dependent acceptance, while independent work continues.

Include one comparison in the existing verification/compliance section:

| Confirmed criterion | Actual change/journey | Candidate-bound proof | Gap/deviation |
|---|---|---|---|

Explain approved scope changes with actor/source, what, why and result; preserve ticket and PR history. Compare the real owner expectation, not only PR claims or an old plan. Ticket `closed`, controller `ready` and a green suite never prove integrated delivery. Keep awaiting-review state until its recorded review/integration criteria and authorized tracker completion are satisfied. No routine/skill exception bypasses an already ticketed contract.

## Before/after proof

Plan proof before edits; attach it to the PR before submission/update. Show the changed outcome, not a screenshot dump.

- **Visible/UI change:** capture the affected screen before edits; capture its finished counterpart during final manual QA. Default: one focused before/after pair, same viewport, state and safe sample data. Add views only when needed to explain the change. New UI: show the prior entry/empty state and label what did not exist. Screenshots are required where applicable; video does not replace them.
- **No useful screenshot:** show equivalent before/after evidence, e.g. the same API request with status/body before and after, CLI output or measured behavior. Preserve existing baseline evidence before edits; if a fresh execution is needed, compare isolated base/head versions during final QA. Label versions, inputs and limits. Documentation-only changes may use a short text diff; no decorative screenshot.
- **Feature proof:** final manual QA demonstrates the actual journey and outcome. Offer a short computer-use recording when motion or several steps add value; ask once, honor the answer, continue other work. No routine video mandate. When chosen, show relevant entry/sign-in → action → confirmed result. Email example: fill form → send → verify receipt in the test inbox, not merely a success toast. Use authorized test accounts/recipients; recording grants no sending permission.

Baseline screenshot is a narrow capture-only exception to tests-last: minimum safe navigation to the unchanged view, no feature exercise, submission or test suite. Use existing evidence if access would require a side effect; report missing baseline honestly. Never fabricate a before image or reset dirty work to recreate it. Final screenshots, journey tests and videos wait until implementation finishes; reuse that QA session.

Embed labeled Before/After and any chosen clip in the PR, with observed result, base/head and applicable ticket revision/criterion. Use durable attachments/links the reviewer can open; verify access. No localhost/local-path links or unconfirmed uploads. Keep credentials, private data and notifications out of captures; record safe fixtures. Missing capture/recording/upload access: disclose the gap and available evidence, never claim proof exists. No new media host or public upload implied.

## Resolve project bindings

Read [bindings](../.agents/skills/how-to-make-a-pr/references/project-bindings.md). Discover repository, branches, rules, commands, tracker, review owner and authorized destinations. Reuse decisions; ask only consequential remaining gaps.

Map risks to actual games, clients, servers/services or tools: platforms, languages, persistence, trust boundaries, versions and interfaces. No fixed framework, package manager, locale, vendor, person or channel.

UNKNOWN is neither N/A nor PASS. Justify inapplicability. Missing required bindings block dependent external actions/PR completion; continue independent local work. Use authorized integrations; invent no tracker, recipient or success.

Save bindings in the canonical ticket and local context cache when bound; legacy unticketed work retains its task/session record. One-time notification/merge permission is not standing authority. Source accounts/examples grant none.

## Keep current factory decisions explicit

[Tests last](current-decisions.md#finish-work-use-it-then-automate-tests), including updates/reviewer fixes: finish implementation/improvements → final manual/user QA → write/change/polish/run final tests → prepare/create PR. No manual reproduction, playtests, walkthroughs or automated checks during development. Read-only review inspects evidence, runs no suites. Final-test production fixes return through completed implementation and manual QA. Missing manual coverage stays unverified.

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

New ticketed bugs keep full factory methods and full cloud PR review. Keep implementation surgical, evidence/checks relevant and unrelated cleanup deferred. The light route below applies only to existing unticketed Small Change work; it cannot override a ticket's complete cycle.

Include applicable [security controls/evidence](../.agents/skills/safe-engine/references/app-security.md) in the existing review. Distinguish local development gaps from production blockers; no whole-app hardening for an unrelated small fix.

Every UI/interaction PR/update includes [UX Quality](../.agents/skills/ux-quality/SKILL.md) in its existing reviewer scope: friction, current patterns, accessibility, visual/audio inspection, uncertain-choice comparisons and manual evidence. Source alone cannot certify unseen/unheard output.

Both PR procedures apply within Small Change:

1. Inspect purpose, base/head and prior review boundary.
2. Assess delta/consumers; retain unresolved older findings.
3. Prepare focused draft/update with task links, attribution, handoff.
4. One remote/cloud independent PR reviewer covers applicable security, performance, journey, regression and compliance. No automatic fleet/full-version workflow; a local scoped review cannot replace this.
5. Reuse valid evidence; repeat affected checks when needed. State exact verdict scope.

No automatic broad regression or five-output planning for bounded fixes. Narrow review cannot approve an unreviewed whole PR. Missing checks/permissions remain unresolved.

## Enforcement and evidence

Instructions only. Controller fingerprints operative guidance and runs local candidate review; no PR creation, notifications, remote merge enforcement or host hook. Factory publication to `main` needs actual cloud PR review and authorized merge; verify the remote result. Use [release/operations](../.agents/skills/safe-engine/references/delivery-readiness.md#authorized-release-and-operation) when shipping. Existing installations/pins do not auto-upgrade.

Historical evidence covers its recorded candidate/scope. Validate changed methods; disclose remaining unknowns.
