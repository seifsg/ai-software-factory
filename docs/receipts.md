# Suite receipts

A receipt proves a test suite passed on an exact tree. The guard reads receipts before it accepts a Gate C or final review line; `scripts/check.sh` and the pro gate runner write them and reuse a passing one for an unchanged tree.

## File

`<checkout>/.factory/receipts/<tree>-<suite>.txt`, LF line endings, written to a temporary file and renamed into place. One file per tree and suite: an older gate keeps its receipt when a later run writes another.

```text
factory-receipt 1
suite full                 `full` = the project's full suite; any other name for a narrower suite
tree <sha>                 the work tree: tracked and untracked files, .factory/ left out
head <sha>                 HEAD when the suite started
clean yes                  yes when tree equals HEAD's tree
result PASS                PASS when the suite exited 0, else FAIL
cmd <command line>
runtime <stamp>            optional; the writer's own stamp (tools, platform)
secs <n>
at 2026-11-16T18:30:00Z    UTC
log <path>                 optional: where the suite's output was saved
runs 1                     full runs of this suite recorded on this tree; absent counts 1
passes 1                   passing runs among them; absent: 1 for a PASS, 0 for a FAIL
inert <glob>               optional, repeatable: paths the suite never reads (`--inert`)
```

Readers ignore lines they do not know, so a writer may add its own (the pro gate runner adds `ref-tree`).

`tree` is what `git add -A` into a private copy of the index, then `git write-tree`, would print, with `.factory/` left out: `factory tree` prints it.

## Writing one

| Writer | Command |
|---|---|
| A suite that does not write its own receipt | `factory receipt run --suite full -- <full-suite command>` runs it and writes the receipt. Exit 0 requires both a passing suite and a saved or reused PASS receipt. `--again` runs it and counts a repeat. |
| A suite to start in the background | `factory receipt start --suite full -- <full-suite command>` starts the command on the clean final head and returns the launch receipt path, or reuses an existing PASS. |
| A runner that ran the suite itself | `factory receipt write --cmd "<command>" --exit <code> [--log <path>] [--secs <n>]` (`--suite` defaults to `full`; `--result PASS` or `--result FAIL` in place of `--exit`) |
| This repository | `sh scripts/check.sh`: a full PASS on a clean tree (`<ref>` is the work tree) writes `<tree>-full.txt`; the next run on that tree prints nothing and exits 0 |

`factory` is `<plugin root>/scripts/factory.cmd` (sh or cmd), or a built `factory/target/release/factory`.

`receipt start` returns after the command process starts. Its `<tree>-<suite>.launch.txt` records the head, tree, command, start time, process ID with its start time (`owner`) and log path. The usual completion receipt records the exit result. Expect a FAIL if the tracked or untracked tree at completion differs from the starting commit. Foreground and background native runners share a reservation for each tree and suite. If a terminated supervisor leaves a `.running` file, confirm the suite process has stopped before removing that reservation and retrying. While a started suite is live, the Stop guard refuses a turn end that nothing would wake ([time blocks](time-blocks.md#detached-suites)); every suite run also stamps its span on the run's clock.

## What the guard accepts

Gate B can pass while the suite runs. Gate C and the final review stand only with a receipt where `suite` is `full`, `result` is `PASS`, and `tree` equals the tree of the commit the gate line names (`@<sha>`); Gate C, on the final head, only with one whose `passes` is 1: the full suite passes once per run. The Stop hook flags, once, each tree whose receipt counts a second run, failed or not. Reviewers and checkers read receipts and never run the suite. A receipt whose `head` starts with that sha and says `clean yes` matches without reading Git objects. An owner's waiver needs no receipt. `factory receipt check [--commit <sha>] [--wait <secs>]` prints the receipt the guard would use, or why there is none; `--wait` keeps checking inside the call until one lands. A PASS receipt with `inert` lines also stands for a later tree whose change from its own touches only paths those globs match (read from Git); `receipt check` names it as carried ([parallel runs](parallel-runs.md)).

A file that is untracked but not ignored is part of `tree`: commit or ignore it before the suite runs, or the receipt will not match the commit.

If the Git directory is read-only, the receipt command can use HEAD's tree after Git confirms the checkout is clean without taking an index lock. A dirty or unreadable checkout still needs the normal snapshot.
