# Fresh startup-method walkthrough

Read-only walkthrough by a fresh non-builder agent. Read only `safe-engine/SKILL.md` and the relevant startup section of `references/fast-run.md`. No implementation or other agents' reports were read. No workflow, command, test, network call or live-project action was executed.

Reviewed instruction:

> `start` resolves missing selections. Use `resolve_bundle.py --project <abs> --bundle <root>` for an explicit pin; maintenance: `improve-factory`.

## Ordinary new CLI project

After confirming the first commit/feature branch and writing the verbatim request, issue:

```text
python "<gate>" start --project "<project>" --key cli --mode fast --kind product --no-ui --request-file "<project>/.factory/request.md"
```

A separate resolver call is unnecessary for a missing selection. Confirm persistence before choosing `--no-data`, because startup flags are fixed. Tracker, research, kickoff and subsequent required steps remain applicable.

## Explicit pin and maintenance

The reviewed instruction supplies the explicit selection form:

```text
python "<resolver>" --project "<candidate>" --bundle "<immutable-runner>"
```

Maintenance routes to `improve-factory`; read that method before issuing its detailed sequence. It was outside this walkthrough's permitted reads. Use the selected runner's gate for the candidate only after satisfying that method. Do not substitute the editable candidate for the immutable runner, change an active receipt, adopt a version or touch the application.

## Verdict and limits

- G1 PASS: ordinary startup and explicit selection decisions derive from the supplied methods. Detailed maintenance sequencing remains unverified.
- G2 PASS: no installation, adoption, merge or live-project authority was assumed.
- G3 PASS: persistence, initial repository state and the maintenance method remain explicit prerequisites.

This records the prior walkthrough only. It does not demonstrate runtime selection, compare a fabricated Before run, prove a code repair, measure latency or replace tests.
