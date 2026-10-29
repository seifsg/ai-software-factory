# Planned validation and reuse

Choose one affected validation command per coherent change. Full coverage is for shared boundaries, unknown impact or release/integration risk; a push or prose edit alone does not justify it. Report the actual scope, never call a partial pass a full-suite pass.

New Fast plans freeze argv/inputs before done plan: UI uses show --plan; others prove --plan <project-local.json>. The legacy full_suite field names the selected command:
```json
{"version":1,"full_suite":["python","tests/run.py","--changed","<run-base>"],"timeout_seconds":1800,"suite_inputs":{"files":[],"environment":[],"clock":{"instant":"2026-01-01T00:00:00Z","timezoneId":"UTC"}}}
```
Run prove --suite after real use/Build and UI Show. Old plans/pins keep their recorded requirements. Factory --changed follows named imports/loaders transitively; changed test helpers include consumers, unrelated sibling modules do not join merely by folder. Unknown/unmapped graphs fall back to all, explicitly reported. Use the actual run base; select named tests when finer coverage is established.

Receipts bind commit, source/factory files, argv, executable, declared files/environment and clock. Values are hashed. Intact same-input passes can be reused; no duplicate suite after an affected pass already satisfies the plan. Changed or unknown inputs, interrupted/timed-out/truncated/tampered proof cannot supply a pass. Failures remain failures. Each Fast execution has its own .factory/fast/prove/ log; the project .factory/suite-cache retains up to256 completed results.

Cache hits return before queue admission; misses recheck after admission and executions recheck inputs afterward. One machine FIFO spans worktrees/gate homes, using ai-software-factory-suite-v1 under ProgramData on Windows or /tmp on POSIX. No per-run override; permissions stop admission, maximum256 requests. Cancellation removes only its request; crashed owned processes drain before replacement. Internal parallel tests stay within one admission. OS waiting promises no host-native wakeup.

Completion updates only its own current receipt; preserve concurrent observations/owner controls. A conflicting receipt, closed run, changed source or changed inputs cannot complete as passed.

Safe keeps required complete-profile check/manual QA/contract integrity and per-command artifacts. check --fresh explicitly reruns; existing states retain their policy. Partial feedback cannot replace complete acceptance.

New complete-cycle Safe runs may feature-check --checks <ids> --file <json> during Build after actual completed-item use. Select fewer than all checks with a changed-file mapping:
```json
{"version":1,"item":"T1","completed":true,"mapping":"parser -> parser-check","candidate":"<status.feature_candidate>","observations":[{"criterion":"A1","device":"local CLI","action":"read valid record","result":"expected values","status":"PASS","evidence":[".factory/evidence/item.txt"]}]}
```
Use actual observations/evidence. The gate validates current inputs, criterion identity and hashes, not authenticity. Carried final-QA receipts refuse; feedback remains Build, seals no contract and satisfies no final manual/full check. Fix failed feedback before finishing. Existing v2 states still prohibit early feature checks.

Active bundles never auto-upgrade; new Fast methods and Safe init states select their policy. Never edit a receipt to change it.
