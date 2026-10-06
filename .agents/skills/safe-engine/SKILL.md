---
name: safe-engine
description: "Build/resume games, apps, services and tools with Seif's methods. Fast by default, Lucky one-shot, or Safe with saved stages, final checks and independent review. Factory delivery; preserve phase-only requests."
---

# Safe Engine

Build the requested outcome. Read the complete methods. Keep decisions, work and evidence resumable.

Use [Working iterations](references/delivery-readiness.md#working-iterations): next complete useful result first, required quality intact. Keep full-product acceptance open.

For human-facing prose, apply [Clear Writing](references/clear-writing.md): preserve details/voice, ground claims, cut filler. One finishing pass within existing review.

Follow [tests-last order](../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests): finish the complete iteration's implementation/improvements → final manual/user QA → author/polish/run automated tests → final review/PR. No manual tests, playtests, instruction walkthroughs, test writing/edits or automated checks during development. Source inspection/research/existing-log reading remain allowed. Carry this into delegates, repairs and resumed runs.

## Choose the scope

Analysis, planning and review requests stay in that phase. No implied coding.

Read [speed modes](references/speed-modes.md) first. No mode named means **Fast**. Fast and Lucky follow that table, which overrides conflicting rules in this file; tickets, controller commands, the phase table and Codex review are Safe only.

Safe implementation starts with [Ticketing](../ticketing/SKILL.md). Use the chosen tracker/MCP; default to GitHub Issues. Reuse Seif's confirmed GitHub choice. Capture original input, actual before, expected after and criteria; secure owner confirmation before implementation. Split a backlog into complete ticket outcomes, not tiny steps that evade final QA.

Each ticket gets its own builder session and full flow below. Independent tickets use isolated worktrees; related tickets may share an epic checkout serially with separate histories. Read [ticket setup](../../../docs/ticketing.md) for tracker capture, binding, ownership and dependency gates. Tools do not create sessions/worktrees automatically.

[Small Change](../small-change/SKILL.md) supplies surgical tactics for bugs; ticketed fixes keep full methods and final review. Its six light routines remain for legacy unticketed work only. A narrow handoff certifies no whole version.

Discover the actual domain, stack, platforms, interfaces, workload and constraints. Games, desktop/mobile/web apps, servers, libraries and tools share the method; their evidence differs.

Read [logging](references/app-diagnostics.md) and [efficiency](references/app-efficiency.md) during delivery analysis/planning. Every app/game needs working shared logging: adequate facilities/preferred provider or internal module/local sink. Discover preferences/access; implement detailed success/failure events. Read existing logs during development; actual actions and emitted-trail checks wait until final manual QA. Plan coverage, resource targets and evidence. Research material unknowns through [Research Market](../research-market/SKILL.md). Required logging stays surgical.

## Start or resume

Use applicable [Delivery Readiness](references/delivery-readiness.md): inspect capabilities before dependent work; preserve game challenge; plan browser lifecycle, durable external effects and authorized release/operations. Manual/automated/mixed criteria need suitable evidence. No early product tests or automatic pilots.

Use [Application Security](references/app-security.md) from planning: cheap relevant protections now, exposure-based checks before production. Keep local MVPs simple; carry evidence into the existing security review.

Public landing/marketing/content pages meant for indexing use [Public Web SEO](../ux-quality/references/web-seo.md). Plan crawlability, metadata and production verification; preserve private/staging boundaries.

Every UI/interaction change uses [UX Quality](../ux-quality/SKILL.md) through planning, manual QA and independent review. Research uncertain patterns/assets; compare three options, justify/choose within delegation. Verify simplicity, accessibility, visuals/audio and interaction. No extra phase or automatic redesign.

New/material persistence design uses [Database Schema](../database-schema/SKILL.md) before dependent implementation: whole-product access map → three viable designs → reasoned choice → written schema → fresh audit. Preserve engine choices and routine-fix scope; pass query/migration evidence to review. No invented database or controller phase.

Resolve this bundle's root. Read [pilot usage](../../../docs/pilot-usage.md) for supported commands, profile, limits and recovery. Run from the bundle:

```text
python -m safe_engine --project <absolute-target-root> status
```

Read request, rules and [session contract](references/session-contract.md). Reuse answers/authority; discover tools before asking. When ticketed, refresh canonical scope/activity at intake/resume; select its recorded run, binding and session. Pending scope, drift or unavailable refresh blocks dependent progression. Status remains inspectable. No run? Preserve work in a suitable isolated checkout with clean Git baseline and ignored `.factory/`. Commit a minimal new-project baseline before initialization.

Inspect check definitions, runtime inputs and interaction tools; author/run no tests. Choose prospective validation by effect/consumers: guidance, runtime/config or mixed. Keep every configured/protected gate; no saved/failed profile shrink. Ticketed task/criteria come from the confirmed revision; keep original input and scope digest. Unbound runs preserve their recorded contract. Map each criterion to manual, automated or mixed evidence. New version-2 runs may start with draft acceptance and no tests. Declare test-only paths; seal reviewed acceptance at the final stage. Actual browser/native/game/API/CLI interaction waits until implementation is finished; screenshots cannot prove behavior. Missing tools/reserved choices block dependent work only.

Resolve material unknowns before dependent choices. Planning/research may precede initialization; record in stage order. Owner changes go into ticket activity and scope revisions before dependent work. Proposed scope stays pending; explicit owner confirmation binds the new outcome. Rebind through supported reviewed amendments, preserving old/new ticket and contract history and invalidating affected acceptance. Never patch state. Legacy runs retain their recorded contract/workflow. Read [pilot usage](../../../docs/pilot-usage.md) for exact schemas and limits.

Initialize once. Resume the saved phase. Follow [control-route recovery](references/session-contract.md#recover-a-failed-control-route) when needed. No invented credits, retry ceilings, session deadlines or permissions. Honor real limits, checkpoints and stops.

## Follow the saved phase

PR-bound work: plan [before/after proof](../../../docs/pr-workflow.md#beforeafter-proof) before edits. Capture-only UI baseline now; finished screenshots and optional journey video during final manual QA. Use equivalent output for nonvisual changes; attach accessible proof to the PR.

Read each phase's full method/applicable references before using it. Reuse fully read, unchanged text while available; names/summaries never suffice. On resume/context loss/delegation, use [method handoff](references/method-handoff.md); receivers read methods themselves. Missing methods block their phase.

With no existing implementation, say so; analyze requirements, available platform facilities and intended consumers. Never invent code evidence. Preserve Get Ready's O(1) question as a prompt to examine workload-appropriate complexity, not a universal acceptance target; [I5](../../../docs/current-decisions.md#further-improvement-decisions) governs measured performance.

| Phase | Do |
|---|---|
| `analyze` | [Analyze Start](../analyze-start/SKILL.md): actual code, purpose, consumers, ASCII charts, verified claims and unknowns. Save analysis. No code. |
| `plan` | Compare three credible approaches for new substantive choices; recommend one under session authority. [Get Ready to Code](../get-ready-to-code/SKILL.md): five outputs, original file-summary stop unless continuation is authorized. For new software, preserve the first plan, run [research](../research-market/SKILL.md), revise all five outputs and link evidence/decisions. Research new material unknowns for existing features too. No code. |
| `build` | Get Ready's 0–4 source-inspection loop for every todo. Finish requested implementation and worthwhile in-scope improvements; record implementation completion. No testing yet. |
| `manual` | Final actual-use QA, including relevant failure/recovery paths. Save candidate-bound receipts. Fixes return through completed implementation and affected manual QA before final automation. |
| `testing` | Author/polish useful tests in declared test-only paths. Seal independently reviewed final task/profile, then record the batch. Production changes invalidate manual evidence. |
| `verify` | One complete configured final gate, including applicable diagnostic/resource evidence. Read logs; investigate failures. Use supported repair before changing a recorded candidate. |
| Legacy `improve` / `final-verify` | Existing version-1 runs keep their recorded sequence and exact-input reuse rules. No silent migration. New version-2 runs have no duplicate final gate. |
| `review` | Fresh local read-only Codex review: core methods plus applicable evidence/references, three themed passes plus Change Guard and Compliance. Severity and blocking/approved-deferral disposition stay distinct. Never supply your own passing review. Repair supported findings, check corrections and obtain fresh assessment. |
| `ready` | When ticketed, refresh scope; map latest confirmed criteria to changes, actual journey proof and limits. Checked local handoff includes diagnostics, resources and research. Authorized PRs/updates require [creation](../how-to-make-a-pr/SKILL.md) and separate remote/cloud [PR review](../how-to-review-a-pr/SKILL.md), including skill/docs PRs without controller runs. Ticketed work keeps full review; local review never substitutes for cloud review. Preserve human ready/merge/release decisions. |
| `cancelled` | Stop. Preserve records and checkout. |

Keep evidence in excluded `.factory/` or equivalent. Report unverified coverage. Never edit protected acceptance files/task records to obtain a pass. Use reviewed amendments with history for legitimate version-2 contract corrections; preserve failures and authority. Legacy corrections follow their supported boundary.

## Keep the work usable

Give brief batch updates. For watch/learn requests, show actual brief, criteria, chart, plan, running product and results; label historical walkthroughs. Updates grant no approval gate. Pause only for real authority/access/decision gaps, checkpoints/stops or unrecoverable required gates.

For factory faults, use [Improve Factory](../improve-factory/SKILL.md): checkpoint → isolated repair → independent review → compatible resume. No recursive delivery runs or silent upgrades. Reloaded text is not new QA.

For another host/session, read [setup](../../../docs/start-another-session.md). The current session builds; the controller records stages/checks and launches fresh read-only review. It does not provision tools, run a daemon, push, merge or deploy. Verify host capabilities and report limits. Missing PR bindings block that action, while independent local delivery continues. New follow-ups use tickets; surgical scope stays. Existing unticketed runs retain their recorded path, pins and acceptance.
