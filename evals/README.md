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
- `compare` exits 1 on a drop in delivered items, a pair missing from the new report, or a changed item total (not comparable); a pair new since the baseline is only noted. A malformed or interrupted report exits 2.

## Agent command

`--agent` is a command template for your agent's non-interactive mode. It runs in the system shell, in the run's workspace, with the prompt on stdin. Placeholders, replaced already quoted (do not quote them again):

| Placeholder | Value |
|---|---|
| `{prompt_file}` | the prompt, at `../prompt.md` from the workspace |
| `{workdir}` | the workspace (also the current directory) |
| `{arm}` | `factory` or `plain` |
| `{sample}` | the sample id |
| `{factory}` | factory arm: a fresh export of the factory bundle; plain arm: empty |

`--factory-agent` replaces `--agent` in the factory arm only, for agents that load the factory with a flag. On Windows the shell is `cmd`: values are always double-quoted, and one containing `%` (expanded even inside quotes) or `"` is refused. Per-agent templates: `docs/hosts.md`, section Evals.

## Arms

Both arms get the same request, from `prompts/factory.md` or `prompts/plain.md`:

- **factory**: follow the exported `safe-engine` in Fast mode, offline, no tracker or pull request.
- **plain**: plan first, then build. It must run without the factory installed.

## Isolation

- Before any agent starts, the runner reads into memory the chosen samples (request, fixture, rubric) and the check program, `rubric_tools.py` and `harness.py`. Item ids come from the rubric's syntax tree; the runner never runs rubric code itself.
- Each check is a child process (`python -I -B -c`) that gets all of that over a stdin pipe, with a random token, and works outside the workspace. No file the agent can reach is read for scoring, and no path to those sources is passed.
- Candidate code runs only in further child processes: the harness (imports the candidate module, returns plain typed data) or `run_python` (runs a candidate program). The check compares results type-strictly, so custom objects, an early exit or a shadowed module fail.
- Each run gets a fresh temp folder: `work/` (the fixture, a new Git repository with the fixture committed), `prompt.md`, the factory export, and its own temp and gate home (`TEMP`, `TMP`, `TMPDIR`, `SAFE_ENGINE_HOME`).
- Every agent and check runs as a process tree that is stopped when it ends, normally or at the time limit: a Windows job object, a process group elsewhere. A timed-out run counts every item as failed.
- A run is **void** when the checkout's `evals/` files changed during it: every item fails with the reason. Rerun from a clean checkout.
- New entries in the system temp folder during a run are reported as possible escapes: other programs write there too, and with `--jobs` above 1 an entry shows on every run active at the time.
- The run folder is deleted afterwards unless `--keep` (its path is then in the report); a folder that cannot be deleted is reported. `--out` inside `evals/` is refused.

## Report

Per sample and arm: `delivered` out of `total` items, `failing` checks with the reason, `minutes`, the agent's `exit` code, `timed_out`, `void`, `possible_escapes`, and `error` or `cleanup` when a run broke or left a folder. A broken run fails all its items and the others continue. `report.md` adds totals per arm. A report marked interrupted cannot be a baseline or be compared.

## Baseline

After a run the owner trusts, copy its `report.json` to a stable path, for example `evals/baseline.json`, and commit it. Later runs pass `--baseline evals/baseline.json`.

## Samples

`samples/<id>/` holds:

- `request.md`: the request, one numbered item per requested outcome.
- `fixture/`: the starting project.
- `reference/`: files that, laid over the fixture, deliver every item.
- `rubric.py`: `CHECKS = {"R1": check, ...}` as a dict literal, one function per item, taking the workspace path and raising on failure; optional `KEEP = {"R4"}` for preserved behavior. `FIXTURE` maps the fixture's file names to their original text.

Rubrics use `evals.rubric_tools`: `call` with `op` or `request` runs the candidate module in the harness, `expect` and `same` compare type-strictly, `run_python` runs a candidate program with output through files, and `scratch` gives a temp folder. Keep checks to a few seconds, without network.

## Real runs

Real runs call a paid model, take minutes per run and need the owner's approval of the cost. They never run in `python tests/run.py`; the tests drive the runner with a fake agent. Start with one sample and a short `--timeout`, read the logs, then run the set.
