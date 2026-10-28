# Reuse approved planning

Read when the owner links an already approved plan. Reuse decisions, not old execution proof.

1. Resolve the exact source section and the owner's approval using the connected source. Verify the quote authorizes this scope. Missing access, ambiguous authority or changed scope: stop reuse and name the missing evidence. A plan, status update or proposed approval is not approval.
2. Save its complete planning record inside the project. Preserve the bytes the owner approved. Include every applicable section through Plan, its ticket links, criteria, todos, interface and ports. Keep the new request separate.
3. Prepare the snapshot below. Record source/interface/dependency inputs that determine the plan; omitting an input does not prove it stayed unchanged. The coordinator verifies completeness and authority. The gate validates hashes and structure; it cannot authenticate people or discover omitted dependencies.
4. Run `fast_gate.py start --from-plan <link> --plan-record <local.json>` with the normal key, request and scope flags. Both options are required together. The gate validates current tickets through its existing reader; unavailable access refuses reuse. A prewritten first-run work record conflicts with import: preserve or move it before retrying. Never forge a successful read or silently fall back to claiming reuse.
5. Start at Design for UI, Schema when still required, otherwise Build. Earlier steps are marked reused with provenance. Use a fresh checker before the build wave. Retain design coverage, current Show, likeness, security, tests and draft handoff. Never import old execution receipts or change an active pin.

## Snapshot

Version 1 JSON, at most 1 MiB; the planning record also at most 1 MiB. Paths stay inside the project, including through links. Unknown or duplicate fields fail. Hashes are lowercase SHA-256 of actual bytes. Store snapshots ignored, never in a public artifact.

```json
{
  "version": 1,
  "source": "https://tracker.example/plan#approved-section",
  "record": {"path": ".factory/approved/work-record.md", "sha256": "<record hash>"},
  "approval": {
    "actor": "<owner identity>",
    "source": "<approval message link>",
    "quote": "<actual approval quote covering this scope>",
    "plan_sha256": "<same approved record hash>"
  },
  "scope": {"kind": "change", "ui": false, "data": false, "auth": false, "design_port": false},
  "inputs": {"src/interface.py": "<current approved input hash>"},
  "proof_selection": {
    "version": 1,
    "tickets": [{"url": "https://tracker.example/issues/12", "body": "<complete issue body>",
                 "category": "logic", "reason": "<why these checks are owed>", "hidden": true}]
  }
}
```

- `scope` must exactly match the start's effective kind and flags. A changed scope needs a reconciled approval, not edited hashes.
- `inputs` names 1..1000 existing files. Bind actual source, interface and dependency inputs; do not use a placeholder file as proof of unchanged inputs.
- `proof_selection` uses the public [hidden-check selection](hidden-checks.md) shape. Each listed ticket must match the imported record; current criteria and integration ownership must agree with the pasted body. No `owed`, prepared checks, observations or prior results are imported.
- UI adds `show_plan`, the public `show --plan` object, including surfaces, full-suite argv and the planned window. It imports obligations only.
- Design ports add `design_input`, the existing coverage JSON's local path. Include that file and every reference image in `inputs`. Inventory, reference bytes and any owner cuts are validated and frozen; no old likeness review transfers.
- Research, kickoff, tickets, analysis and plan are validated once where applicable. Size, ticket links, todo IDs, port claims and integration ownership are frozen as in a normal run. Design and schema remain incomplete.
- Invalid data leaves the existing run, record and archives untouched. Correct every reported problem, resolve changed sources, then retry. Do not overwrite a rejected snapshot's hashes to manufacture approval.

## Record refusals

Read all diagnostics in one refusal. Local omissions do not hide independently readable ticket, coverage or PR problems. Unavailable sources block their dependent checks; they never prove missing criteria or success. Each source is read once per validation invocation, including failed reads; the next invocation refreshes it.

Only an explicit verdict field fails a rule: `U3 PASS Screen: the FAIL rule was exercised` remains PASS. `U3 FAIL Screen: overlap observed` blocks. UNKNOWN and N/A need reasons and never become PASS. Keep one final verdict per rule; duplicates and malformed fields are refused with a line example. Rule commentary and judge text cannot stand in for actual-use evidence.

Corrective examples name the expected structure, not a verdict to copy. Write actual observations. Missing draft PR proof still blocks handoff.
