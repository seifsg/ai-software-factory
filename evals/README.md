# Evals

Score the factory against a plain agent on fixed sample requests, and catch drops after a model or harness update. Python 3.9+, standard library only. Run every command from the factory root. This folder is in the factory repository only; installed copies leave it out.

## Run

```text
python -m evals check
python -m evals run --agent "<template>" [--factory-agent "<template>"] [--timeout 30] [--sample <id>] [--jobs 1] [--out <dir>] [--baseline <report.json>] [--keep]
python -m evals compare <baseline report.json> <report.json>
```

- `check` proves each rubric: every item fails on the untouched fixture and passes on the reference solution; a `KEEP` item (preserved behavior) passes on both. Free; run it after editing a sample.
- `run` runs every sample (or each `--sample`) in both arms and writes `report.json` and `report.md` to `--out` (default `.factory/evals/<timestamp>/`, Git-ignored), with each agent's output in `logs/<sample>-<arm>.log`. A `--baseline` is read first, so a bad one fails before any paid run.
- Ctrl-C cancels queued runs, stops running agents with every process they started, writes a partial report marked interrupted and exits 130.
- `compare` exits 1 on a drop in delivered items, a pair missing from the new report, or a changed item total (not comparable); a pair new since the baseline is only noted. A malformed report exits 2.

## Agent command

`--agent` is a command template for your agent's non-interactive mode. It runs in the system shell, in the run's workspace, with the prompt on stdin. Placeholders, replaced already quoted (do not quote them again):

| Placeholder | Value |
|---|---|
| `{prompt_file}` | the prompt, at `../prompt.md` from the workspace |
| `{workdir}` | the workspace (also the current directory) |
| `{arm}` | `factory` or `plain` |
| `{sample}` | the sample id |
| `{factory}` | factory arm: a fresh export of the factory bundle; plain arm: empty |

`--factory-agent` replaces `--agent` in the factory arm only, for agents that load the factory with a flag. On Windows the shell is `cmd`, which expands `%` even inside quotes: a placeholder value containing `%` or `"` is refused. Per-agent templates: `docs/hosts.md`, section Evals.

## Arms

Both arms get the same request, from `prompts/factory.md` or `prompts/plain.md`:

- **factory**: follow the exported `safe-engine` in Fast mode, offline, no tracker or pull request.
- **plain**: plan first, then build. It must run without the factory installed.

## Isolation

- Before any agent starts, the chosen samples are copied to a private temp folder. Fixtures, rubrics and references are read only from that copy.
- Each run gets a fresh temp folder: `work/` (the fixture, a new Git repository with the fixture committed), `prompt.md`, the factory export, and its own temp and gate home (`TEMP`, `TMP`, `TMPDIR`, `SAFE_ENGINE_HOME`).
- A run is **void** when the checkout's `evals/` files or the private copy changed during it: every item fails with the reason. Rerun from a clean checkout.
- New entries in the system temp folder during a run are reported as escapes. With `--jobs` above 1, an escape shows on every run active at the time.
- `--timeout` minutes per run; a timed-out run is stopped with every process it started and counts every item as failed. The run folder is deleted afterwards unless `--keep` (its path is then in the report).

## Report

Per sample and arm: `delivered` out of `total` items, `failing` checks with the reason, `minutes`, the agent's `exit` code, `timed_out`, `void` and `escapes`. `report.md` adds totals per arm.

## Baseline

After a run the owner trusts, copy its `report.json` to a stable path, for example `evals/baseline.json`, and commit it. Later runs pass `--baseline evals/baseline.json`.

## Samples

`samples/<id>/` holds:

- `request.md`: the request, one numbered item per requested outcome.
- `fixture/`: the starting project.
- `reference/`: files that, laid over the fixture, deliver every item.
- `rubric.py`: `CHECKS = {"R1": check, ...}`, one function per item, taking the workspace path and raising on failure; optional `KEEP = {"R4"}` for preserved behavior.

Each check runs in its own process with a time limit and file output. The rubric loads before the workspace joins `sys.path`, and an item passes only when a per-check token is printed after the check returns, so an early exit or a shadowed module fails. Start candidate programs with `evals.rubric_tools.run_python`, never through a pipe. Keep checks to a few seconds, without network.

## Real runs

Real runs call a paid model, take minutes per run and need the owner's approval of the cost. They never run in `python tests/run.py`; the tests drive the runner with a fake agent. Start with one sample and a short `--timeout`, read the logs, then run the set.
