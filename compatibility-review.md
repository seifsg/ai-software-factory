# Scoped presentation compatibility review

Verdict: PASS. Scope: two uncommitted production lines and three matching expected-output literals in one test module over `c9cf0b7c71300ce40146fee337364cb3a4e6eb53`; the earlier message-delta PASS remains the foundation. No code edits or test execution occurred during this independent review.

## Resolved compatibility finding

The initial two-line proposal made `fast_card.card` render `repr(key)`. For validated run keys this adds exactly two single quotes, restoring the quoted-key substring required by `tests/test_fast_state.py:253`. It initially conflicted with three unquoted-card expectations at `tests/test_fast_progress.py:68`, `:89` and `:197`. The parent subsequently changed exactly those three expected-output literals to quoted keys. I read the resulting complete delta: full-line equality and prefix assertions, all other expected fields and the test execution paths are unchanged.

This deliberate visual-only string update preserves assertion strength and retains one identity occurrence. Accepted keys match `[a-z][a-z0-9-]{0,63}`, so repr introduces no escaping or ambiguous syntax. No remaining supported blocking finding in the reviewed delta.

## Scratch decision

PASS: `fast_setup.TEXT` again contains the exact delimiter ` (the run's` used by the scratch-path extractor in `tests/test_fast_gate.py:549`. That extractor serves the scratch deletion/close tests; the path remains before the delimiter and is not truncated at spaces. `the run's temp` has the same byte length as `throwaway data` and accurately describes the run-owned scratch directory. All three temp environment variables, literal-path-only deletion instruction, standalone deletion forms, Bash separator guidance and close cleanup remain. No cleanup or permission logic changed.

The quoted card adds two bytes wherever the ordinary card occurs. Relative to the reviewed saved capture this predicts start 759/771, done 220/242, status 262/266; other measured fields are unaffected. This is an arithmetic implication, not a fresh measurement or suite result. The owner-report branch returns before the edited card head and is unchanged.

Read the parent's saved manual selected-snapshot output in `.factory/eval-selection-proof/compat-manual/start.txt` and `result.json`: it shows the quoted key, restored scratch delimiter and full version/SHA; the result labels source checkout dirty and separately identifies the selected snapshot with check-selection and suite policies active. Parent reports current measurement total 5,719 bytes with caps unchanged. Targeted suites and final full suite remain parent-owned; this review does not claim their results.

## Reviewed identities

- fast_setup.py SHA256: `B90C8422DF1F214CED339A4EBB31A4F39FB6D73000D32E32D422FCD9508CE326`
- fast_card.py SHA256: `FB1BD2F3B91682B888D91F4E4407E04F5AD20A59C2C5BDDCD9529DE6A047B798`
- tests/test_fast_progress.py SHA256: `5F48D9EB997D869CCF40AC77A9AF3116D600BF9D544438C20879FC6F9377A6D9`

Read the complete changed card function and scratch constant, key validation, status/rehome call sites, scratch parser and its cleanup consumers, and all searched card-prefix assertions. No broader review loop or new mandatory check was introduced.
