# Fast gate details

Contents: modules · run state · older gate · owed epic · scratch deletes · destructive guard · rehome · adopt PR proof · cleanup temp · install · progress internals · live view internals

Read only the section your situation needs. The rest of the gate is in [fast-run](fast-run.md).

## Modules

`fast_gate.py` keeps run state and the run registry in `fast_ledger.py`, checks in `fast_record.py`, the record skeleton's hints in `fast_hints.py`, shell analysis in `fast_shell.py`, the destructive guard in `fast_rules.py` and `fast_guard.py`, record facts in `fast_progress.py`, the owner's dashboard in `fast_card.py`, the live view in `fast_view.py` and `view/index.html`.

## Run state

- `start` registers the run, keeps its state in the gate home and notes the bundle and hook status. It keeps `.factory/` out of Git in the clone's `.git/info/exclude`: no project file changes; a reverted `.gitignore` and `git clean -fd` leave the records.
- `.factory/fast/run.json` is a mirror the gate rewrites on every change.
- `close` moves the run's state to `runs/closed/` until the next `start`.
- The registration (`active/`) and the state (`runs/`) guard each other: a deleted registration comes back from the open state, and a deleted state never falls back to `run.json`.
- A registered run whose state in the gate home is missing or unreadable keeps the gate closed and every destructive rule on until the owner closes the run.
- A run started by an older gate moves its open `run.json` home on first use.

## Older gate

An older installed gate refuses a light record: record the run the full way until the installed copy updates. `**Epic:**` carries the ticket's URL; a trivial change opens one first. Then the analysis and the full plan. Tell the owner the copy is older.

## Owed epic

Another run owes an epic (a change: its ticket) when its checklist holds integration todos and each one is another run's. An integration todo is an item in the ticket layout, `- [ ] T63 <title> → <result> (A1, A2)`: its own todo IDs lead it (decoration and lists like `🤝 **T63** / T64` allowed), and a group in parentheses names the epic's criteria. A group is a comma list of IDs; a part led by `#<n>`, as in `(#4 A1 to A8, #5 A1)`, gives its IDs and the ones after it to ticket n, until the next `#`. IDs later in an item never claim it; a `Proof:` tail is not read.

- Then this run owes none of the epic's criteria and, at handoff, only the epic's items its own plan todos lead (the todos pinned at `done plan`, plus later ones).
- An item that names the epic's criteria any other way (in prose, or in a group with other words such as `(needs #2 T29, A1)`) is off the layout: every run owes the epic whole, and the gate refuses the step naming the item and the form to use.
- Otherwise the epic is owed whole, so the run holding its integration todo proves it.

## Scratch deletes

The scratch folder is `scratch/<key>-<project tag>-<start time>` in the gate home, derived from the run, never stored. Stop the processes that hold files there first. Deletes of it and inside it pass the guard when they:

- name a plain literal path (the hook does not see your variables; no trailing slash, no wildcard mid-path);
- use a deleter that removes a link as a link: `rm -r` where the host names its shell as Bash, the path written with `/` separators and no backslash or quote; or `rd /s` (cmd) with no quote or space in the path;
- stand alone in their command.

A link or junction put in the folder's place is never trusted. `close` (also `--abandon`, also for a lost run) removes the folder without following links and names anything left.

## Destructive guard

The rules are listed in [fast-run](fast-run.md#hooks). A rule fires when its words appear anywhere in the command, whatever the shell structure (substitutions, groups, `ssh` or container strings, piped `.sql` files). Commit, PR and search text, and echo or heredoc text that only reaches a file or the terminal, never fire one. Brace and PowerShell comma lists count item by item; an unknown shell must pass both the Bash and the PowerShell reading. A fired rule is denied unless the parse proves it harmless:

- Recursive deletes inside the run's scratch folder pass with the [deleters](#scratch-deletes).
- A `find` from the root passes only with `-name` patterns that cannot match `.git`, `.factory`, `fast` or `run.json`, or with `-not -path './.git/*' -not -path './.factory/*'`.
- `git stash -u` passes; `--force-with-lease` naming another branch, not `HEAD`, passes.
- Database wipes include `dropdb`, `db:drop`, `migrate reset`, `migrate:fresh`, `ecto.reset`, `flush`.
- Writes to the gate home cover redirects and edit tools; its logs and bundles pass.
- A production env value counts in the command or an earlier `export`; `prod` inside a name such as `add_prod_flag` is none.

Hooks see tool calls, not intent: files written and destructive commands run from inside scripts, `xargs rm`, piped deletes (`Get-ChildItem | Remove-Item`), commands piped into a shell from a file or program, and inline interpreter code (`python -c`, `node -e`) pass; the record and the done-run carry the rest.

## Rehome

```text
python fast_gate.py rehome --project <abs> --from <the folder its run.json records>
```

The owner's step, run only on their instruction. It brings in an open run from another machine or folder, which reads as lost in this gate home; `status` then names the command.

1. First bring the project with its `.factory/` and the run's bundle (the launcher's `resolve_bundle.py --ref <revision in .factory/entry-bundle.json>`). When the receipt's old bundle path is missing here, `rehome` points it at this gate home's copy of the same revision.
2. `rehome` takes the open `run.json` home once, with its steps and pause, and keeps `.factory/` out of Git as `start` does.
3. One machine at a time: check the card against `status` on the old machine, then the owner retires the copy there with `close --abandon`.

It refuses, writing nothing, when the run is closed, malformed or records another folder, or when this gate home holds a run for either folder or one around or inside it. A run this gate home holds as lost or closed never comes back through it.

## Adopt PR proof

```text
python fast_gate.py adopt-pr-proof --project <abs> | --new-runs --method <absolute PR SKILL.md> --reason "<owner authority>"
```

Only on explicit owner authorization. `--project` adopts for an open run, `--new-runs` for future starts; pass `--method` and `--reason` with either form.

- The method must remain available and unchanged in its reviewed bundle; a changed or missing source blocks dependent checks.
- A separate identity-bound policy preserves progress, pauses and unrelated pins; status and prompt hooks show its source.
- Read that method and recheck the proof inventory; use the current installed gate at handoff. Older gate binaries do not enforce this overlay.
- A recorded handoff prevents adoption; no silent reopening of completed work.

## Cleanup temp

```text
python fast_gate.py cleanup-temp --project <abs> --path <absolute temp child> --reason "<owner authority>" [--expect <preview SHA256>]
```

Obsolete fixtures outside managed scratch, only on the owner's explicit instruction for those exact folders. Normal QA still uses managed scratch.

1. Verify ownership and that no process uses them; preserve needed reports.
2. Repeat `--path` for each absolute direct child of the system temp folder. Run with the original temp environment, not a QA scratch override; do not change global settings.
3. Preview, inspect the inventory, then repeat with its `--expect` digest.

The command refuses links, special nodes, protected project or factory overlap and changed metadata; it saves a private receipt before removal and reports leftovers. Keep targets quiescent: this is no protection against hostile concurrent filesystem changes. A refusal never authorizes a wider delete or disabling the guard; correct the cause and preview again.

## Install

```text
python fast_gate.py install --host claude|codex|cursor|other [--project <abs>] [--no-auto-update] [--channel stable|edge]
```

Wires the hooks for agents that need it; the factory's `docs/hosts.md` lists each agent's route.

## Progress internals

The run card:

```text
🏭 portal-poc · 🔨 build · step 6/8 · ⏱️ 42m total, 5m in step
🎫 #12 Download & SEO   ▰▰▱ 2/3 · run 5/9
✅ SEO: title and description on every page
🔨 NOW  Download button
     → click it and the PDF saves
⏭️ NEXT Contact form
```

- Before the build it shows the steps done, current and left. A paused run leads with `⏸️ WAITING ON YOU: <reason>` and shows what is on hold. Once every step is done, it lists each step's duration.
- The facts come from the record: ticket titles after their URLs, each todo's title and result, and the Build log's last `**Now:**`. A todo counts as built once its Build log line passes the `build` check.
- Unseen progress rides along with each hook's answer, once each, even under parallel calls: the card after each step, pause or resume; `✅ <title> done → <result>` per newly built todo, then the new NOW and the ticket bar; the new NOW when `**Now:**` changes. The same check refreshes the live view.
- Nothing changed: one directory scan, no reads, no network. Hook calls your agent marks as a delegate's (the factory's `docs/hosts.md`) show nothing; the next main-thread call does.
- Claims live in `.factory/fast/shown/`, one folder per run; `start` and `close` clear them. A closed run leaves the hooks.

## Live view internals

- One server shows every run. `view --snapshot <file>` writes the page with the current state, without live updates.
- The gate is the only writer of its data, `view/state.json` in the gate home: at each gate command, and at each hook whose file-time check saw the run state or record change, from delegates and on every host. Nothing changed: no extra work. The page polls every 2 s; an unchanged file costs one 304.
- It shows each run's steps, its todos (done, now, next, later, counted as the card counts), its agents and sessions, the owner's open question and Ready to try. Agents: the todos in `**Now:**`, plus the background agents your agent reports at a stop (the factory's `docs/hosts.md`). Screenshots under `.factory/fast/shots/` show as thumbnails.
- On the first prompt and every sixth after, the prompt hook's message to the owner carries the view's link, or says the view is off and how to start it.
