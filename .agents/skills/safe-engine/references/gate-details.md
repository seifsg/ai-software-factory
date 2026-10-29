# Fast gate details

Contents: modules · run state · older gate · owed epic · scratch deletes · destructive guard · rehome · adopt PR proof · cleanup temp · recover baseline · shots · install · progress internals · live view internals

Read only the relevant section; normal flow: [fast-run](fast-run.md).

## Modules
fast_gate.py delegates state/registry to fast_ledger.py, checks to fast_record.py, skeleton hints to fast_hints.py, shell analysis to fast_shell.py, destructive protection to fast_rules.py/fast_guard.py, record facts to fast_progress.py, cards to fast_card.py, viewer to fast_view.py and view/index.html.

## Run state
start registers in gate-home active/ and stores state in runs/ with bundle/hook status. Git-info exclude protects .factory without changing project files; reverted ignores/clean -fd retain records. run.json is rewritten mirror, never fallback input. close moves state to runs/closed/ until next start.
Registration/state protect each other: missing registration restores from open state; missing/unreadable state keeps gate/destructive rules closed until owner closes it. An older open run.json migrates home on first use.

## Older gate
If installed gate refuses a light record, use full record until update: Epic holds ticket URL, analysis/full plan required; trivial work needs a ticket. Tell owner the copy is older.

## Owed epic
A run owes none of an epic's criteria only when every integration checklist item belongs to other runs. Handoff still owes items led by its own plan todos, frozen at done plan plus later ones.
- Integration item: `- [ ] T63 title → result (A1,A2)`; leading decorated todo IDs/lists count, later IDs and Proof tails do not.
- Parenthesized criterion groups are comma lists. `(#4 A1 to A8, #5 A1)` assigns following IDs to that ticket until next #.
- Other prose/group words such as `(needs #2 T29,A1)` are off-layout; gate names the item/form and requires whole epic. Otherwise the run holding integration work proves the epic whole.

## Scratch deletes
Scratch is derived scratch/<key>-<project-tag>-<start-time> in gate home. Stop processes holding it first. Guard allows only standalone literal paths(no variables, trailing slash or mid-path wildcard), with link-removing deleters: Bash rm -r with / separators and no backslash/quote, or cmd rd /s without quotes/spaces.
Never trust a replacement link/junction. close/abandon, including lost runs, removes scratch without following links and reports leftovers.

## Destructive guard
Active rules deny recursive deletes outside project except scratch, whole project, .factory/.factory/fast; deletes/moves/wildcards reaching run.json or .git except index.lock; git clean -x/-X, stash --all; force/mirror/prune/main/master-delete pushes; database DROP/TRUNCATE/wipes; writes to gate-home active/runs; migrations naming production env.
Rules inspect words through substitutions, groups, remote/container strings and piped SQL. Harmless commit/PR/search/echo/heredoc text does not fire. Brace/comma lists parse itemwise; unknown shell must pass both dialects. Exceptions require a proven harmless parse:
- Scratch uses the literal [delete form](#scratch-deletes).
- Root find requires name patterns excluding .git/.factory/fast/run.json, or both `-not -path './.git/*' -not -path './.factory/*'`.
- stash -u passes; force-with-lease passes only naming another branch, not HEAD.
- Wipes include dropdb, db:drop, migrate reset/fresh, ecto.reset and flush. Gate-home logs/bundles remain writable.
- Production env counts in command/earlier export, not inside a name such as add_prod_flag.
Hooks observe tool calls, not internals of scripts, interpreter snippets, xargs/piped deletes or commands piped into another shell. Those limitations grant no authority; record/done-run still carry obligations. A denial means find an authorized approach, not disable protection.

## Rehome
`python fast_gate.py rehome --project <abs> --from <recorded-folder>`
Owner instruction only, for an open run lost after moving machine/folder:
1. Bring project/.factory and its selected revision via resolve_bundle.py --ref. Missing old bundle path maps to gate home's same-revision copy.
2. Import open run.json once with steps/pause and normal Git exclusion.
3. Compare old/new status; owner retires old copy with close --abandon. One machine at a time.
No writes for closed/malformed/wrong-folder runs, overlapping held folders or existing registration; a held lost/closed run cannot be revived this way.

## Adopt PR proof
`python fast_gate.py adopt-pr-proof --project <abs> | --new-runs --method <absolute PR SKILL.md> --reason "<owner authority>"`
Explicit owner authority, with method/reason for either open-run or future-start form. Reviewed method must remain unchanged/available; source drift blocks dependent checks. Separate identity-bound policy preserves progress/pause/unrelated pins; status/hooks show source. Read method and recheck inventory with current installed gate; old binaries do not enforce overlay. Recorded handoff prevents adoption/reopening.

## Cleanup temp
`python fast_gate.py cleanup-temp --project <abs> --path <absolute temp child> --reason "<owner authority>" [--expect <preview SHA256>]`
Exact owner-authorized obsolete folders outside managed scratch only:
1. Confirm ownership/no users; retain reports.
2. Repeat path for each absolute direct system-temp child, using original temp environment, never global changes.
3. Inspect preview inventory; repeat with its digest.
Refuses links/special nodes, project/factory overlap and changed metadata. Saves private receipt first, reports leftovers. Keep targets quiescent; no hostile-race protection. Refusal requires cause correction/new preview, never a broader delete.

## Recover baseline
`python fast_gate.py recover-baseline --project <abs> --base <full-sha> --upstream refs/remotes/<remote>/<branch> --reason "<owner authority>" [--expect <preview SHA256>]`
Explicit owner instruction for stale start baseline; ancestry/dates alone prove no ownership.
1. Pause/checkpoint, stop writers, fetch actual upstream and preview.
2. Review each excluded commit/path against owned work, then repeat with digest; inspect receipt before explicit resume.
Requires ancestor of HEAD/upstream, pre-start commits, intact initial UI snapshots, no completed done-run and unchanged preview. Preserves original base/snapshot/pause/progress/audit; only later UI comparison changes, remaining edits still need proof. One correction/run; unknown ownership, repeated correction or later acceptance needs reviewed maintenance. Old gates remain conservative; no global install implied.

## Shots
`python fast_gate.py shots --phase before|after --serve "<dev command, {port}>" --path <view> [--path <view>] [--setup "<command>"] [--ports <before>,<after>] [--size 1280x800] [--browser <exe>] [--project <abs>]`
Capture Before before edits; After during final QA uses same out/paths/size/serve/setup/browser and checks retained Before bytes. Default .factory/fast/shots contains view-before.png, view-after.png, baseline.json; never replace early baseline during repair. Explicit --base creates labeled reconstruction, not a pre-edit capture. Browser flag or SAFE_ENGINE_BROWSER selects executable. Authenticated/seeded/native views use their capture route and Show before rows.

## Install
`python fast_gate.py install --host claude|codex|cursor|other [--project <abs>] [--no-auto-update] [--channel stable|edge]`
Wires supported hooks; host routes live in factory docs/hosts.md.

## Progress internals
Card shows step/time, ticket/todo counts, NOW/result and NEXT; before build it shows steps, paused state leads WAITING ON YOU/reason, finished state lists durations. Record supplies ticket titles, todo/result and last Now; valid Build-log line marks built.
Hooks atomically emit unseen cards/built todos/new NOW once, including parallel calls, then refresh view. Unchanged: one directory scan, no reads/network. Delegate calls show nothing until next main call. Claims live in .factory/fast/shown/<run>; start/close clear them and closed runs leave hooks.

## Live view internals
Busy port uses next free; existing server prints requested scoped URL. One server serves all project scopes through filters/details/reload. Worktrees of one local repo share scope; clones/submodules differ; non-Git scope is canonical folder. view --project --snapshot writes a marked static scoped page.
Only gate writes view/state.json on commands and changed hooks; unchanged polls cost304 every2s. Page leads selected goal/milestones/next test, then sessions, reported children and ticket activity; task progress differs from goal completion. Scope applies to details/thumbnails; empty project offers start. Now todos/background reports name agents; shots thumbnails are under .factory/fast/shots. First/every sixth prompt shares project link or says view is off/how to start.
