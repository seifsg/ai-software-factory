# Independent scoped-check method walkthrough

Read changed methods before implementation review. These are paper scheduling decisions, not actual product/runtime passes.

1. Small prose change: use the changed instruction on a realistic fixture, then run relevant method/docs/budget checks as one batch. Record that exact command/scope in the existing plan. Do not run the complete factory suite just because a PR/push follows; do not offer an unsolicited Safe round. Missing/uncertain impact changes scope rather than inventing a pass.
2. Three related low-risk logic todos covered by existing independently written tests: use each result, then run the applicable existing tests once after the coherent batch. Point every criterion at real evidence. Explicit hidden:false may avoid authoring and running a second hidden harness only with the recorded reason and current passing planned validation; the default hidden route remains if coverage is not established. Reuse an identical intact pass, not a failed/stale receipt.
3. Shared proof gate, data/safety/mixed behavior, unknown mapping or release integration: keep independent proof obligations and justified full validation. A shared test-selector/proof-boundary repair needs final full regression even though a future leaf change can be narrow. Owner stops, current candidate identity, actual acceptance and human merge authority stay intact.

No extra checker, stage, quota or required form is introduced by these scheduling choices.
