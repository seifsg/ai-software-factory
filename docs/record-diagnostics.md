# Record diagnostics

## Local PR draft preflight

Before publishing a Fast/Lucky draft, run `python skills/safe-engine/scripts/fast_gate.py report --pr-body <project-local.md> --project <absolute-project>`. It applies the same proof, credit, effective PR policy and UI/journey structure checks as handoff to a local UTF-8 file (maximum 100,000 bytes). Existing authoritative run state is required; a legacy run needing migration is refused until its normal gate path resolves that state. Preflight changes no phase, proof receipt, ticket or PR. Success proves structure only; actual media access, observed behavior, current checks and the real published PR remain required at handoff. Invalid drafts fail locally before a network write.

## Completion diagnostics

Required independent review starts with source and affected manual evidence before the final complete suite. Keep the same reviewer for author-written repair deltas and unchanged observations; replace it if it wrote repairs or lost context. Final acceptance still needs current affected proof and inspection of the exact-candidate suite receipt. Combine related checking work instead of creating a new agent for every command.

`fast_diagnostics.py` shares ticket reads only during one validation, including read failures. Every new invocation refreshes sources. A refusal collects independently knowable local, ticket, checklist, coverage and PR errors with repair examples; inaccessible data remains explicitly unverified.

UX audits read explicit verdict fields. A PASS explanation can quote FAIL. Actual FAIL fields block, UNKNOWN/N/A need reasons, duplicate verdicts are refused, and rule/judge commentary cannot fake an actual-use PASS. Fix the finding and record its real result; examples never authorize inventing evidence.
