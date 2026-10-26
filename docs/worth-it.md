# Worth-it rounds

Scores prioritize optional polish. Required criteria, mandatory accessibility, broken behavior, safety, data, legal duties, HIGH/CRITICAL findings and missing required proof remain mandatory. A score is neither evidence nor permission to defer.

Each review or check finding carries `location` (source), a plain `description`, `severity`, `disposition`, `exception` and:

```json
"worth": {"notice": 0, "harm": 1, "minutes": 90, "required": false, "reason": "Small visual detail; estimate includes layout checks"}
```

`notice`: 0 not visible in a normal demo, 1 maybe, 2 visible. `harm`: 0 none, 1 blemish, 2 confusion, 3 broken/wrong data/unsafe/illegal. `minutes`: nonnegative integer estimate, or `null` if unknown. Cost points: under 15 = 2, 15 to under 60 = 1, 60 or more = 0. Score = notice + harm + cost, out of 7; unknown cost means unknown score.

Mandatory findings go first regardless of score. Optional score 5+ goes now; 3–4 goes now under an hour, otherwise waits; 0–2 waits. Unknown optional cost needs an estimate before selecting a repair. Severity and authority are still independently checked.

## Fast and Lucky

Save a JSON object with a `findings` array. Finding IDs are `F1`, `F2`, etc. in that report's order. Keep all findings, not only the selected ones.

```text
python skills/safe-engine/scripts/fast_gate.py fix-round --project <project> --file <report.json> --finding F1 --finding F3
python skills/safe-engine/scripts/fast_gate.py fix-round --project <project> --file <report.json> --finding F2 --finishing-authority "<owner instruction and source>"
```

The command validates before writing, retains the report and selected IDs in the run's receipt, and reopens build while invalidating done-run/handoff completion. Low-value optional work is refused even beside mandatory fixes. Finishing selections must already have an authorized follow-ups entry.

New runs' final done-run records `**Findings:** none` only for clean checks without prior repair rounds, otherwise a scored report path. Remaining findings need authorized accepted-deferral. Every finding in every prior receipt, selected or not, needs exactly one reconciliation entry keyed by `report_sha256` and `finding`. Use `retained` with `current_finding` pointing to its unchanged final finding, `resolved` with actual `evidence`, or `cancelled` with `owner`, `authority` (instruction and source) and `reason`. Completion can retain only unselected findings; any selection of the same report/finding requires resolution evidence or owner cancellation. Foreign, duplicate, changed-retention and missing entries fail. Before-exposure obligations remain duties; Fast final reports only retain authorized accepted-deferral. Owner cancellation does not waive other criteria or alter the task contract. A clean marker cannot erase prior obligations. Old runs retain their recorded checks. The command validates declarations; it cannot prove a report is complete or authenticate an owner.

## Safe

New version 2 runs freeze worth scoring at initialization. Review reports use `safe_engine/review-schema-worth.json`; existing runs keep their original review schema and repair behavior.

```text
python -m safe_engine --project <project> --ticket <key> repair --reason "<why>" --finding F1
python -m safe_engine --project <project> --ticket <key> repair --reason "<why>" --findings <check-report.json> --finding F1
python -m safe_engine --project <project> --ticket <key> repair --reason "<why>" --finding F2 --finishing-authority "<owner instruction and source>"
```

After review select from the intact saved report; `--findings` cannot replace unresolved findings. After a clean review, a new scored failure report may start a correction. Before review, pass the complete scored failure report. Records-only corrections keep their existing proof restrictions. The selected fixes and report are retained before previous completion evidence is invalidated. Every subsequent review reconciles all receipt findings through the same retained/resolved/cancelled lists; a PASS cannot retain selected findings. A truthful FAIL may retain unresolved selections, remains in review and counts toward the failed-review limit; an unresolved required finding still blocks readiness.

## Finishing touches

Reuse the epic's one existing follow-ups ticket, retaining other deferred work. Each `accepted-deferral` finding needs `exception` fields `owner`, `reason`, `scope`, `revisit`, `authority`, `destination`; all parked entries in one report use the same destination. No tracker action occurs in scoring commands. The coordinator searches, appends once by source/finding identity, and records the remote result.

Parked reports say what waits, its score (or unknown), and why. Source/destination links stay separate. An explicit owner instruction starts the agreed entries as one finishing batch: complete it, use it, then run the final test pass on unchanged inputs. Failures and changed inputs require repair and fresh proof. Only the owner cancels work; Done still requires the merged PR.

`safe_engine/worth.py` is the shared evaluator. `scripts/package_skill_entries.py` generates its installed `fast_worth.py` copy; the installer ships it with the gate. No new dependency or background service is needed.
