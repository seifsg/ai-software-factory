# Suite receipts

A receipt proves a test suite passed on an exact tree. The guard reads receipts before it accepts a Gate B or Gate C line; `scripts/check.sh` and the pro gate runner write them and reuse a passing one for an unchanged tree.

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
```

Readers ignore lines they do not know, so a writer may add its own (the pro gate runner adds `ref-tree`).

`tree` is what `git add -A` into a private copy of the index, then `git write-tree`, would print, with `.factory/` left out: `factory tree` prints it.

## Writing one

| Writer | Command |
|---|---|
| Any suite | `factory receipt run --suite full -- <full-suite command>`: runs it, writes the receipt, exits with the suite's code |
| A runner that ran the suite itself | `factory receipt write --cmd "<command>" --exit <code> [--log <path>] [--secs <n>]` (`--suite` defaults to `full`; `--result PASS|FAIL` in place of `--exit`) |
| This repository | `sh scripts/check.sh`: a full PASS writes `<tree>-full.txt`; the next run on the same tree prints nothing and exits 0 |

`factory` is `<plugin root>/scripts/factory.cmd` (sh or cmd), or a built `factory/target/release/factory`.

## What the guard accepts

A Gate B or Gate C line stands only with a receipt where `suite` is `full`, `result` is `PASS`, and `tree` equals the tree of the commit the gate line names (`@<sha>`). A receipt whose `head` starts with that sha and says `clean yes` matches without reading Git objects. An owner's waiver needs no receipt. `factory receipt check [--commit <sha>]` prints the receipt the guard would use, or why there is none.

A file that is untracked but not ignored is part of `tree`: commit or ignore it before the suite runs, or the receipt will not match the commit.
