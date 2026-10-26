# Hidden checks and proof selection

New Fast/Lucky runs record a per-ticket choice before plan. Visual-only ports default to independent likeness plus their required suite; logic, data, safety and mixed work keep independent checks. Existing runs and Safe's sealed-check lifecycle retain their obligations. Install updated launchers after release; never rewrite an active run's state.

All JSON files below are local to the project. Run the selected bundle's gate, with `--project <absolute project>` on each command:

```text
python fast_gate.py checks --plan plan.json --project <absolute project>
python fast_gate.py checks --prepare checks.json --project <absolute project>
python fast_gate.py checks --runtime runtime.json --project <absolute project>
python fast_gate.py checks --observe observation.json --project <absolute project>
python fast_gate.py checks --run --project <absolute project>
python fast_gate.py checks --brief --project <absolute project>
python fast_gate.py checks --status --project <absolute project>
```

Plan: `version:1`, `tickets` array. Each row has `url`, full pasted `body`, `category` (`visual-port`, `logic`, `data`, `safety`, `mixed`), and `reason`. `hidden` defaults false for visual-port and true otherwise; only visual-port may be false. A visual-port true needs `owner_request`. False requires `start --design-port`, current likeness and the Show suite. The list must match the run's tickets. A ticketless trivial run uses an empty list and `none_reason`. Requirements are frozen; checklist ticks and activity do not change their identity. Changed criteria require a new confirmed run.

Only the documented plan and ticket-row fields are accepted; ownership fields are computed by the gate. Listed HTTPS tickets from other trackers keep the gate's offline/unverified path. At done plan, the gate freezes run todo ownership and excludes an epic's integration criteria only when the ticket layout assigns all that work to another run. Online verification compares that ownership with the live ticket. The owning run still owes it; child tickets and off-layout ownership stay owed here.

Prepared set: `version:1`, `checker` identity/source, `interface`, `ports`, and `checks` array. Each check names `criterion` as the full issue URL followed by `#A1`. Executable rows have `files` (first is the executed check; others are declared dependencies), `argv` explicitly naming the first file, `timeout_seconds` (1..3600), and optional `environment` variable names. Python, JavaScript and JSON inputs use native syntax parsing. JavaScript needs Node on PATH. Unsupported languages use their real project tool as a written manual procedure, with honest observation rather than a fake automated receipt. A manual row supplies `manual` instead of files/argv.

`--prepare` parses every declared source and preserves logs; it does not run assertions against an unfinished build. Re-prepare after editing checks. `--run` is allowed only after build and applicable Show. It parses again, executes each check through the bounded runner, and records start/duration/exit/timeout, logs and identities. Failure is retained; an interrupted or changed run cannot count.

Runtime JSON: `candidate` from `fast_design.candidate(project)` (UI runs may use `show --candidate`), `source`, and for UI a local `path` to a nonempty actual accessibility snapshot. Include viewport/state in the source record and hand the raw file to the checker. Non-UI supplies `not_applicable`. The command records hashes, not an assertion that a file came from the browser.

Manual observation: `criterion`, current `candidate`, `source`, `observation`, and `verdict` (`PASS`, `FAIL`, `DEFERRED`). DEFERRED also needs `reason` exactly `DEFERRED (owner: why)` or `DEFERRED (hardware: why)`. The coordinator verifies that authority. Manual observations do not pretend to be executable checks.

Completion requires a current successful execution receipt plus the checker's written criterion verdicts. It checks source, input files, commands, executable, declared environment (always PATH/PYTHONPATH/NODE_PATH) and log hashes. Declare every relevant input; undeclared external services are not automatically fingerprinted. It does not prove independent authorship or sandbox an arbitrary command.

Verdicts use `#<issue number> <criterion>: PASS|FAIL|DEFERRED` where the number is unambiguous. Use `<ticket URL>#<criterion>: ...` for other trackers or colliding issue numbers. Offline completion remains visibly unverified and still needs every owed criterion's actual proof.

For Playwright, import `skills/safe-engine/scripts/playwright_checks.mjs` from the selected factory bundle. `rendered`/`oneRendered` handle responsive copies without first-match guesses; `keyboardTarget` observes focus-only skip links; `background` composites supported alpha layers; `iconPaint` includes masks and pseudo-elements. Unsupported rendering effects stay unknown. The module uses the caller's page/locator and never launches a browser.
