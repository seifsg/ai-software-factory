# Approved plans and record diagnostics

Use `fast_gate.py start --from-plan <link> --plan-record <project-local.json>` with the usual `--project`, `--key`, `--kind`, request and UI/data flags. Both new options must be supplied together. The source must identify an actual approved plan section; a bare URL or `approved: true` is insufficient.

The coordinator resolves the source and approval, records the exact plan and its source/dependency inputs, then prepares the [bounded snapshot](../.agents/skills/safe-engine/references/approved-plans.md). The gate checks scope, hashes, current ticket requirements and existing planning validators before writing run state or archiving a prior record. Unavailable current ticket access refuses reuse; it does not count an old pasted body as a fresh read. The gate cannot authenticate an approver or prove omitted dependencies are unchanged.

On the first run, a prewritten `.factory/fast/work-record.md` conflicts with imported planning. The gate refuses the import before changing the record or run; preserve or move that record and retry. A normal start still keeps a prewritten record.

Current non-UI runs with the suite policy require `suite_plan` in the snapshot, using the same validation as public `prove --plan`, for example `{"version": 1, "full_suite": ["python", "tests/run.py"], "timeout_seconds": 1800}`. Optional `suite_inputs` declares effective files, environment names and clock inputs; their actual values are checked when proof runs. Missing or invalid plans refuse reuse. UI uses `show_plan`; UI and older non-UI methods reject `suite_plan`. This imports only suite obligations, never prior execution or approval results.

UI starts at Design. Data work retains Schema; other non-UI work starts at Build. Reused steps record their source link. Ticket coverage, size, todos, ports, fresh check preparation, current Show, likeness, security, the required suite and draft PR handoff retain their normal obligations. No prior execution result, identity or bundle pin transfers. Existing runs keep their selected factory; normal starts and legacy records keep their contracts.

`fast_plan_reuse.py` owns bounded import validation. `fast_diagnostics.py` shares ticket reads only during one validation, including read failures. Every new invocation refreshes sources. A refusal collects independently knowable local, ticket, checklist, coverage and PR errors with repair examples; inaccessible data remains explicitly unverified.

UX audits read explicit verdict fields. A PASS explanation can quote FAIL. Actual FAIL fields block, UNKNOWN/N/A need reasons, duplicate verdicts are refused, and rule/judge commentary cannot fake an actual-use PASS. Fix the finding and record its real result; examples never authorize inventing evidence.
