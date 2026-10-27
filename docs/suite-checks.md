# Complete suites

New Fast runs declare a complete suite before `done plan`. UI runs include the
declaration in `show --plan`; other runs use `prove --plan <project-local.json>`:

```json
{"version":1,"full_suite":["python","tests/run.py"],"timeout_seconds":1800,
 "suite_inputs":{"files":[],"environment":[],
   "clock":{"instant":"2026-01-01T00:00:00Z","timezoneId":"UTC"}}}
```

List external input files and environment variable names explicitly. Empty arrays
assert there are no additional inputs. Source, executable bytes, arguments,
factory identity and relevant process paths are always included. Missing
`suite_inputs`, an unresolved executable/input, or an unborn Git HEAD means
unknown identity: the suite still queues and runs, but cannot reuse evidence.
The clock fields identify inputs; use the [browser helper](journey-clock.md) to
actually fix browser time.

Use the completed change manually, finish Build and, for UI work, complete Show.
Then run `prove --suite`. The current-policy hook directs raw invocations of the
declared suite to this command. `prove --suite --fresh` explicitly reruns it for
diagnosis; it still joins the queue.

The project-local `.factory/suite-cache` retains up to 256 completed results.
Reuse requires the same commit and effective inputs plus intact logs and output
hashes. An intact hit returns before queue admission after another input check.
Dirty source, changed arguments, environment, clock or declared files
invalidate reuse. A completed failure stays a failure when reused. Interrupted,
timed-out, truncated or tampered evidence cannot supply a passing result. Misses
enter the queue and recheck inputs and the cache after admission; executed
suites check inputs again afterward. Environment values are hashed, never stored
as plaintext.

New Safe states also reuse complete-profile `check` batches and queue misses;
`check --fresh` explicitly reruns them. Per-command IDs, artifacts, manual QA,
contract integrity and required checks still apply. Existing states retain their
saved policy. A partial test never replaces complete version acceptance.

New complete-cycle Safe runs allow `feature-check --checks <ids> --file <json>`
during Build after using the completed item. Select fewer than all configured
checks and record the changed-file mapping. The receipt uses the existing manual
observation shape, with these additional fields:

```json
{"version":1,"item":"T1","completed":true,
 "mapping":"changed parser -> parser-check",
 "candidate":"<status.feature_candidate>",
 "observations":[{"criterion":"A1","device":"local CLI",
   "action":"read a valid record","result":"the expected values appeared",
   "status":"PASS","evidence":[".factory/evidence/item.txt"]}]}
```

Supply actual observations and existing evidence. The gate checks current inputs,
criterion identity and evidence hashes; it cannot authenticate the observation.
Carried final-QA receipts are refused here. Partial feedback stays in Build and
does not supply final manual acceptance, seal a contract or satisfy full checks.
Failed feedback must be repaired before finishing implementation. Existing v2
states retain their prior prohibition on early feature checks.

Complete suites needing execution share one FIFO queue per machine, across
worktrees and gate homes. The queue uses `ProgramData` on Windows and `/tmp` on POSIX under
`ai-software-factory-suite-v1`; it has no per-run override. Permission failures
stop admission. At most 256 requests wait; cancellation removes only its own
request. A crashed worker's owned processes must be drained before replacement
admission. Internal test parallelism stays inside that one admission. Waiting
uses an OS-backed process wait; it does not promise a host-native agent wakeup.

Existing active bundles remain pinned. New Fast receipts adopt this behavior
from their selected methods; new Safe `init` states record it explicitly. Never
edit an active receipt to upgrade its policy.
