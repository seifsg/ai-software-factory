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

- Before any agent starts, the runner reads into memory the chosen samples (request, fixture, rubric, reference solution), the check program, the modules it ships (`rubric_tools.py`, `harness.py`, `proc.py`, `winjob.py` and the canonical `safe_engine/windows_job.py` helper) and the factory bundle. Item ids come from the rubric's syntax tree; the runner never runs rubric code itself.
- Each check is a child process started without site hooks (`python -I -S -B -c`). It gets everything over a stdin pipe, with a random token, and answers over a stdout pipe only the runner holds; nothing is written to the run folder. No file the agent can reach is read for scoring, and no path to those sources is passed.
- Candidate code runs only in further child processes, each in its own process tree that stops when it ends: the harness (`-I -S`, imports the candidate module, returns plain typed data) or `run_python` (a candidate program without environment or site hooks, with the host's own text defaults). The harness opens a dedicated result pipe before any candidate code loads and must send exactly one record from a clean exit; its stdout and stderr are only logs, so a forged result line counts for nothing.
- Each run gets a fresh temp folder: `work/` (the fixture, a new Git repository with the fixture committed), `prompt.md`, the factory export, and its own temp and gate home (`TEMP`, `TMP`, `TMPDIR`, `SAFE_ENGINE_HOME`; `PWD` and `OLDPWD` dropped).
- Every agent and check runs as a process tree that is stopped when it ends, normally or at the time limit: a Windows job object, a process group elsewhere. A timed-out run counts every item as failed. On Windows, failed ownership setup or resume kills and reaps the suspended command before returning an error. Cleanup seals membership and confirms owned process handles have exited; an unconfirmed stop raises instead of claiming success. There is no PID-tree fallback. Every registered tree is attempted even if one stop fails. Unconfirmed ownership remains registered for retry; partial interrupt/taint reports retain cleanup errors.
- The interpreter guard records, before any agent starts, the files behind every module that real checks and harnesses load (by scoring each chosen sample's reference once), the interpreter, and the listings of every folder they search plus the site folders. It is checked after each agent and before scoring. Each scoring also runs a canary item with a random id and no rubric, which must fail. A change or a passing canary voids the run and stops the whole eval (exit 3), and a canary passing before any agent refuses the eval: the change outlives the run. Agents must install packages into their own environment, never the shared interpreter.
- A run is **void** when the checkout's `evals/` files changed during it. Scoring no longer reads them, so this flags tampering with the checkout, not a wrong score.
- New entries in the system temp folder during a run are reported as possible escapes: other programs write there too, and with `--jobs` above 1 an entry shows on every run active at the time.
- The run folder is deleted afterwards unless `--keep` (its path is then in the report); a folder that cannot be deleted is reported. `--out` inside `evals/` is refused.

## Threat model

The guards stop the common ways an agent games its score: editing rubrics, shadowing modules, planting site hooks or bytecode, returning look-alike objects, exiting early, forging results, hardcoding the answers to known inputs (random inputs need real answers). They do not make a hostile agent safe. Agents run as the same user as the runner, so a determined one can still read or attach to the runner's processes, use whatever that user can reach, and start processes through operating system services (WMI, Task Scheduler, COM servers, launchd or systemd user services) that escape the job object or process group. Evals of agents that may act adversarially belong on a machine that holds nothing else of value.

**Isolated machine:** use a disposable virtual machine or container the host already supports, or at least a separate operating system user with no access to your files. Install only Python 3.9+, Git and the agent CLI there, copy in a clean checkout of the factory, supply only the agent's own credentials, run `python -m evals run`, copy `report.json`, `report.md` and `logs/` out, then discard the machine or user.

## Report

Per sample and arm: `delivered` out of `total` items, `failing` checks with the reason, `minutes`, the agent's `exit` code, `timed_out`, `void`, `possible_escapes`, and `error` or `cleanup` when a run broke or left a folder. A broken run fails all its items and the others continue. `report.md` adds totals per arm. A report marked interrupted or stopped cannot be compared, and a baseline also needs every row clean (no error, void or timeout); `compare` labels broken rows. Exit codes: 0 done, 1 a drop, 2 bad input, 3 the eval stopped on a guard, 130 interrupted.

## Baseline

After a run the owner trusts, copy its `report.json` to a stable path, for example `evals/baseline.json`, and commit it. Later runs pass `--baseline evals/baseline.json`.

## Samples

`samples/<id>/` holds:

- `request.md`: the request, one numbered item per requested outcome.
- `fixture/`: the starting project.
- `reference/`: files that, laid over the fixture, deliver every item.
- `rubric.py`: `CHECKS = {"R1": check, ...}` as a dict literal, one function per item, taking the workspace path and raising on failure; optional `KEEP = {"R4"}` for preserved behavior. `FIXTURE` and `REFERENCE` map the fixture's and the reference solution's file names to their text.

Every check runs its fixed regression cases plus fresh random inputs drawn from `rubric_tools.RANDOM` (operating system randomness), so a candidate passes only by computing the right answers. Expected answers for random inputs come from the reference solution, run inside the check process from memory and never written to disk: `agree` runs the same operations on both and compares type-strictly, and `run_program` runs a reference program in process. Also in `evals.rubric_tools`: `call` with `op`, `request` or `tests` (a unittest source) runs operations against the candidate module in the harness, `expect` and `same` compare type-strictly, `run_python` runs a candidate program, `scratch` gives a temp folder. Keep checks to a few seconds, without network.

## Real runs

Real runs call a paid model, take minutes per run and need the owner's approval of the cost. They never run in `python tests/run.py`; the tests drive the runner with a fake agent. Start with one sample and a short `--timeout`, read the logs, then run the set.
