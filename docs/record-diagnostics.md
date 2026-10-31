# Record diagnostics

## Local PR draft preflight

Before publishing a Fast/Lucky draft, run `python skills/safe-engine/scripts/fast_gate.py report --pr-body <project-local.md> --project <absolute-project>`. It applies handoff's PR body checks (proof, credit, effective PR policy, UI/journey) to a local UTF-8 file of at most 100,000 bytes. It needs a readable open run, refuses a legacy run that needs migration, and changes no state, ticket or PR. Success proves structure only; handoff still checks the published PR.

## Refusals

`fast_diagnostics.py` shares ticket reads only during one validation, including read failures. Every new invocation refreshes sources. A refusal collects independently knowable local, ticket, checklist, coverage and PR errors with repair examples; inaccessible data remains explicitly unverified.

UX audits read explicit verdict fields. A PASS explanation can quote FAIL. Actual FAIL fields block, UNKNOWN/N/A need reasons, duplicate verdicts are refused, and rule/judge commentary cannot fake an actual-use PASS. Fix the finding and record its real result; examples never authorize inventing evidence.
