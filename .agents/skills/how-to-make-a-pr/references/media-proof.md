# Visual and journey proof

Every PR shows a skeptical owner truthful before/after proof: what failed or was missing, what now works, the observed benefit. Required in every mode. A short schema, diagram, table or labeled emoji may explain nonvisual proof; prose or illustrative diagrams never replace observed results. Shared backend changes that affect a UI journey still demonstrate that journey.

1. **Inventory now:** map ticket/diff to changed views, states and journeys, including shared-logic effects. POC/MVP: light desktop; mobile apps: light phone. Extra themes/devices/responsive checks need an explicit request or existing requirement; cite it. Keep design coverage. One outcome per journey; share pairs/clips with chapters across outcomes. Reconcile the final diff. Same-rendered-state input variants need behavioral checks, not duplicate pictures. Unchanged views/speculative cases need no media unless required.
2. **Capture each Before now**, with minimum safe navigation. Exercise or side effects needed: an isolated fixture or existing evidence, conditions stated. Missed: capture from the base commit in a separate checkout and say so. Web views: the gate's `shots` serves base and head on their own ports and shoots the same views at one size. Never fabricate it or reset dirty work to recreate it.
3. **Prepare the demo:** isolate workspace/profile; use safe deterministic fixtures and a reset recipe. Preserve owner data; match viewport/theme/state/data/workload/framing or explain differences. Focus on changes; extra full-page shots need a reason. Design likeness supplements actual Before/After. Preflight capture/playback and authorized upload with the first planned artifact; keep complete command/session/exit receipts. Pending or missing results block dependent proof; never invent an upload or install.
4. **Capture each After during final manual QA**, per the table: each journey from entry, single-step flows included, through real controls to its confirmed result, plus relevant changed validation, failure, edge and recovery paths. A success toast alone does not prove an external result. Use authorized test destinations; recording grants no sending permission.

| Surface | Proof, Before and After |
|---|---|
| Screen, page, section | Screenshot pair per changed view and distinct visual state; no hero image standing in for the rest |
| Touched interactive journey, motion | Final-candidate video per journey, plus screenshot pairs for its changed visuals; Before video optional |
| API | Same request: status and body as one `diff` block |
| CLI, script, gate | Same command: output as one `diff` block |
| Speed, size, cost | Measured numbers, same workload, fenced |
| Internal module | Proof through the screen, endpoint or command it changes |
| Method or prose | A fresh walkthrough's changed result, plus the key text as a `diff` |
| Something new | Before: the prior entry or empty-state screenshot (nonvisual: output), labeled "did not exist"; visual work still needs both screenshots |

- **Bug during capture:** stop, keep a short sanitized failure note, fix it in scope, run affected checks, commit and push the checked fix when authorized, reset the fixture, then restart the whole planned demo on that candidate. Replace failed or stale After media; never edit a failure out to imply success. A fix needing new authority blocks the demo with its cause and next action; no silent deferral or clean-pass claim.
- **Keep it fast:** plan routes once; reuse build/fixtures; screenshot during QA recording; share clips; batch uploads/body updates. No duplicate angles. Record setup/capture/upload durations and slow stage; explain material delay in the PR. Shortest complete demo, never drop required coverage for time.
- Inspect every screenshot/play every clip: readable, correct, no unexplained errors/secrets. Reuse same-candidate/state/input observations and URLs with provenance/access checked. Changed/unknown inputs invalidate affected After; source drift still needs fresh gated Show, including docs/tests. Never restamp stale media. Keep Before and unmatched conditions; a demo cannot rule out bugs.
- Upload first (`github.md`); verify every image renders/video plays for reviewers in the PR. No localhost/local links; inaccessible media is missing proof.
- Each outcome declares **Visual:**/**Journey:** (`pr-layout.md`). **Media waiver:** needs explicit scoped owner authority; tools/access/time imply none. Missing media stays a visible gap with recovery action and blocks evidence completion. An incomplete draft preserves progress, not a completed handoff.


