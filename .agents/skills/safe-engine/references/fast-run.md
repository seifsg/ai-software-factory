# Fast run: record and gate

Contents: kickoff questions · light lane · work record · briefs · the gate · hooks · progress · live view · keep it fast

Steps: research, kickoff, tickets, analysis, plan, design, schema, build, show, done-run, handoff. New UI runs use [Look, Show, Prove, Ship](show.md); others skip Show. Reasoned proof selection: [hidden checks](hidden-checks.md). Refusals: [record diagnostics](record-diagnostics.md).

## Kickoff questions

After research, product/feature only: one POC round; MVP/production until launch-baseline decisions close. Ask gaps with choices, recommendation/tradeoff first, via question tool or one short message:
1. Size first: POC(requested behavior works), MVP(real test users), production slice.
2. Features: requests are fixed. POC extras go to follow-ups; MVP offers researched launch gaps with evidence, at most four options/question.
3. Approach: three delivery routes.
4. Stack: three product-bar options, recommendation first.
5. Shape: name; MVP/production also public landing/private-only and who signs in.
6. Tracker: only when no repository exists; answer binds the run.

Over four gaps: another call in the same round. Pause while waiting. Record answer/source; Features lists requests then additions. Later changes enter epic activity; unanswered suggestions follow [sizes](sizes.md).

## Light lane

A change records tickets, plan, build, done-run, handoff; --ui adds design/Show, --data schema. --design-port implies UI and frozen reference coverage.
- Follow existing ticket; new only for a new outcome, none(reason) when trivial.
- No analysis step; Success/Todos suffice. Unknown cause/multiple consumers: analyze-start first, in Plan. Continue todo numbering and0–4; tick after use. [Older gate](gate-details.md#older-gate) may require full record.

## Work record

start writes .factory/fast/work-record.md. Sections follow step order; labels put colon inside bold, e.g. **Epic:**. New runs record **Findings:** none only for clean checks, else scored JSON; [fix rounds](worth-it.md) precede repairs. [Sample](work-record-sample.md) illustrates syntax, never facts to copy.

| Section | Required content |
|---|---|
| Research | ≥3 competitor subsections with source URLs, feature table, Opportunities; product also Stack options with3 rows |
| Kickoff | Features, Approach, Answered by; product/feature Size begins POC/MVP/production, or none(reason) for small features; Lucky keeps Size in Tickets. Product also Stack |
| Tickets | **Epic:** URL/title(change: **Ticket:**), Backlog with owned/affected/untouched. Product/feature also Sub-issue URLs and Requested R-ids for every request/addition; owner-deferred ids keep links. Online tickets open with Definition of done and criteria covering nondeferred R-ids |
| Analysis | Success and fenced ASCII flow; product/feature only |
| Plan | Files, Critique, Phases, Todos, Whole plan; Logging, Efficiency; light uses Success/Todos. Todo: T1 title → what the owner can do once it is done (#ticket,A1). **Ports:**, full-plan Interface, UI UX rules U1–U10. Online Checklist maps planned todos/criteria/nondeferred R-ids; exclude Blocked/not-planned |
| Design | Four hex colors; UI kit, Font, Logo, Icons, Layout, Theme(light), Journeys(counts/minimum), Map, Hierarchy(primary actions), Labels |
| Schema | Three-option table, Chosen, fenced ERD/DDL |
| Build log | Each todo starts its own T1 pre: … do: … post: … line. **Now:** names active todos. Only try writes **Try:** lines |
| Done-run | Real-use PASS and Logs. UI/touched UI: existing .factory/fast/shots/ image, one U1–U10 verdict each, UX judge identity; PASS/FAIL/UNKNOWN/N/A with evidence/reason, no open FAIL/duplicates. MVP/production: **Secrets:**, Dependencies, Static with tool/command/result([security](product-bar.md#security)) |
| Handoff | Run, owned-ticket Statuses, Unverified, Follow-ups, Deferred; sign-in: Dev sign-in. `**PR:**` draft URL/body passing how-to-make-a-pr. Online checklists complete except eligible deferrals; epic only this run's integration todos. Explicit scoped media waivers only; gate checks declarations/links, not content/access/authority |

**Hidden checks:** contains criterion verdicts only, one per line or comma-separated: #2 A1: PASS, or #2 A1: DEFERRED (owner|hardware: reason), optional parenthesized note. No other text/FAIL. Online every owed planned criterion not Blocked/Backlog needs a verdict; offline at least one. [Owed epic](gate-details.md#owed-epic) excludes another run's integration criteria.
Delegates return log lines; coordinator writes record. Copy design/schema decisions into product docs during build.

## Briefs

- Interface: exact exports, shapes, labels/test IDs, routes, commands/flags and committed source paths. none(reason) only if nothing public; light plan includes it when delegating.
- Ports: this checkout's started/reserved services, or none(reason). Referenced previews belong in ordinary plan context. Lane0 uses defaults; extra lane n uses project rule, else defaults+100×n, fixed for its life. Add two shots spares. Real collisions refuse plan. Authorized inspection permits no other-lane start/stop/reset/mutation.
- Own stacks with fast_gate.py lane start / lane stop; brief generation/resources and verify cache writes. Isolate sample mode/data roots from live preview. Await producer exit0 before consumers; yielded sessions are pending.
- UI UX rules: U1–U10 plus project rule-file paths. Host limits: factory docs/hosts.md.
- Every delegate gets Interface/Ports verbatim and applicable UX rules. Checker reads named committed interfaces, never implementation. Missing name: read source; still absent, return blocked:name, update Interface and rebrief.

Owner/hardware-only work ends DEFERRED (owner|hardware: reason) on its unticked item, hidden verdict and handoff Deferred. Supply a written manual check; finish executable work first. FAILs, unsought access and available work cannot defer. Deferred-only runs close, tickets Ready for QA naming them.

## The gate

Python3.9+ standard library; fast_gate.py beside installed launcher or in bundle skills/safe-engine/scripts. [Modules](gate-details.md#modules).
Before product start, resolve_bundle.py --project <abs> writes .factory/entry-bundle.json; maintenance uses improve-factory. Git starts fetch upstream, preserve dirty work; start commit anchors UI proof.

```text
python fast_gate.py start --project <abs> --key <slug> --mode fast|lucky --kind product|feature|change [--[no-]ui] [--[no-]data] [--auth] --request-file <file>
python fast_gate.py done <step> --project <abs> [--offline "<reason>"]
python fast_gate.py status | scratch | pr-proof-method | pause --reason "<why>" | resume | close [--abandon "<reason>"]
python fast_gate.py try T3 --cmd "<command>" | --url <http(s)> | --file <project path> --project <abs>
python fast_gate.py view --project <abs> [--port 8765] [--snapshot <file>]
python fast_gate.py view --all-projects [--port 8765] [--snapshot <file>]
```

- Always pass --project; request file is verbatim. start records state in SAFE_ENGINE_HOME(default ~/.safe-engine), creates record/scratch and excludes .factory from Git unless tracked; git init first. run.json is read-only mirror, never input. [Missing state](gate-details.md#run-state); [moved run](gate-details.md#rehome).
- Product defaults UI/data; no-ui/no-data only if true, auth for sign-in/roles. Decide before start; flags freeze.
- Scratch holds throwaways/profiles/caches; set TMPDIR/TEMP/TMP and lane resources. Stop owned processes before [cleanup](gate-details.md#scratch-deletes).
- Steps run in order. Tickets/plan/handoff and selected-check done-run refresh online tickets; handoff reads PR. Other tracker/offline requires --offline reason, stays unverified and names PR body as **PR:** URL (body:file); readable supported tickets cannot use offline.
- Older runs keep policy unless explicit adoption. pause for owner; done/resume clears it. close needs handoff or owner-reason abandon, including missing-state recovery.
- [shots](gate-details.md#shots): Before before edits, After during QA, retained baseline; --base is disclosed reconstruction. Only explicit owner authority permits rehome/adopt-pr-proof/cleanup-temp/recover-baseline([details](gate-details.md)); [install](gate-details.md#install) wires hooks.

## Hooks

**One full suite per effective version** when broad/shared risk or unknown impact requires it; otherwise one affected pass. Declare argv/file/environment/clock before done plan via show --plan(UI) or prove --plan. After use/Build/UI Show, prove --suite queues and reuses intact matching proof. Old runs keep policy.
- Before build prerequisites pass, deny source edits, shell writes/redirections/tee and scaffold/install commands. Quoted/heredoc/here-string text is not executable; .factory stays writable except run.json.
- Active-run destructive denial covers recursive deletes outside project except scratch, entire project, .factory/fast, protected run.json/.git paths; clean -x/-X, stash --all; force/mirror/prune/default-branch-deletion pushes; database DROP/TRUNCATE/wipes; writes to gate-home active/runs; production-env migrations. Owner chooses an authorized alternative. [Exact exceptions/limits](gate-details.md#destructive-guard).
- Stop reminds once; repeated/paused/closed stops pass. Finite helpers use wait --add with a valid wakeup per owned run([waiting](waiting.md)); servers never qualify; helpers do not pause the gate.
- Prompt/session start shows run/next/pause. No active run: hooks exit. Without hooks, preserve order yourself.

## Progress

[Plain owner reports](owner-reports.md) govern updates. Gate commands print cards first; relay unseen cards only. Hooks show unseen cards, built todos and new NOW once, including parallel calls; delegates emit through next main call. [Internals](gate-details.md#progress-internals).

## Live view

view --project serves its open/today-closed runs at http://127.0.0.1:8765/; omitted project means current repository, never all. Background it; share link once/run. Only gate writes state. [Internals](gate-details.md#live-view-internals).
- try records usable ticked-todo results; unknown todo/target refuses with expected form.
- Dispatch/task-change/finish reports goal, next test and child sessions via [preview reporting](preview-reporting.md).

## Keep it fast

One record, boundary status. No controller capture/seal or routine independent code review in Fast/Lucky. Required PR media/UI UX verdicts stay. verify adds manual QA/tests; promote moves to Safe. Optional visual reuse follows [Show](show.md): proven nonvisual exceptions/input identity retain original captures and compatible owner delivery/reply. Unknown/relevant changes refresh affected After; full-candidate checks stay strict.
