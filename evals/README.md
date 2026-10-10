# Evals

Score the factory against a plain agent on fixed sample requests, and catch drops after a model or harness update. Python 3.9+, standard library only. Run every command from the factory root.

## Run

```text
python -m evals check
python -m evals run --agent "<template>" [--factory-agent "<template>"] [--timeout 30] [--sample <id>] [--jobs 1] [--out <dir>] [--baseline <report.json>] [--keep]
python -m evals compare <baseline report.json> <report.json>
```

- `check` proves each rubric: every item fails on the untouched fixture and passes on the reference solution. Free; run it after editing a sample.
- `run` runs every sample (or each `--sample`) in both arms and writes `report.json` and `report.md` to `--out` (default `.factory/evals/<timestamp>/`, Git-ignored). Each agent's output goes to `logs/<sample>-<arm>.log` there.
- `compare` exits 1 and prints `DROP <sample>/<arm>: <old> -> <new>` for every pair whose delivered count fell below the baseline, or is missing. `run --baseline` does the same right after the run. A bad report exits 2.

## Agent command

`--agent` is a command template for your agent's non-interactive mode. It runs in the system shell, in the run's workspace, with the prompt on stdin. Placeholders, replaced already quoted (do not quote them again):

| Placeholder | Value |
|---|---|
| `{prompt_file}` | the prompt, outside the workspace |
| `{workdir}` | the workspace (also the current directory) |
| `{arm}` | `factory` or `plain` |
| `{sample}` | the sample id |
| `{factory}` | this checkout's root |

`--factory-agent` replaces `--agent` in the factory arm only, for agents that load the factory with a flag. Per-agent templates: `docs/hosts.md`, section Evals.

## Arms

Both arms get the same request, from `prompts/factory.md` or `prompts/plain.md`:

- **factory**: follow this checkout's `safe-engine` in Fast mode, offline, no tracker or pull request.
- **plain**: plan first, then build. The plain arm must run without the factory installed.

## Isolation and time limit

Each run gets a fresh temporary copy of the sample's `fixture/` (a new Git repository), never the rubric or reference. The run is stopped after `--timeout` minutes, with every process it started; a timed-out run counts every item as failed. The copy is deleted afterwards unless `--keep` is given (its path is then in the report).

## Report

Per sample and arm: `delivered` out of `total` items, `failing` checks with the reason, `minutes`, the agent's `exit` code and `timed_out`; `report.md` adds totals per arm.

## Baseline

After a run the owner trusts, copy its `report.json` to a stable path, for example `evals/baseline.json`, and commit it. Later runs pass `--baseline evals/baseline.json`.

## Samples

`samples/<id>/` holds:

- `request.md`: the request, one numbered item per requested outcome.
- `fixture/`: the starting project.
- `reference/`: files that, laid over the fixture, deliver every item.
- `rubric.py`: `CHECKS = {"R1": check, ...}`, one function per item, taking the workspace path and raising on failure. Each check runs in its own process with the workspace first on `sys.path`, so it can import the candidate's modules. Keep checks to a few seconds, without network.

## Real runs

Real runs call a paid model, take minutes per run and need the owner's approval of the cost. They never run in `python tests/run.py`; `tests/test_evals.py` drives the runner with a fake agent instead. Start with one sample and a short `--timeout`, read the logs, then run the set.
