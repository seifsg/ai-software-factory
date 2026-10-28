# Delegate: roles, briefs and gates

Use the cheapest capable role; host models/overrides: `docs/hosts.md`.

## Roles

| Role | Tier | Edits | Jobs | Hands back |
|---|---|---|---|---|
| runner | light | no | scripted commands with a pass/fail (tests, builds, the full suite), searches, inventories, comparisons, log reading | `<step or path:line>: <result>` per step or hit, then `PASS`, `FAIL <step>` or `<n> hits` |
| analyst | standard | no | research, per-area analysis, one-lens reviews, UX verdicts, read-only method walkthroughs, scouting a large spec | `<path:line or URL>: <finding>` per finding, then `<n> findings` |
| maker | standard | yes | planned or mechanical edits, fix rounds that spell out each fix, walkthroughs that run the change, the checker | `<path:lines>: <change>` per change, then `T<n> pre: <before> do: <change> post: <check>` per todo |
| builder | deep | yes | edits that need design calls: architecture, schema, security, unclear bugs | `<path:lines>: <change>` per change, then `decision: <choice> because <reason>` per call made and `T<n> pre: <before> do: <change> post: <check>` per todo |
| reviewer | deep | no | final and independent review (`deep-review`), judgement calls that change no file: unclear bugs, architecture | `<path:line or URL> <severity>: <problem>. <fix>.` most severe first, then `verdict: ready`, `ready after fixes` or `not ready: <why>`; with no diff, `decision: <choice> because <reason>` instead |

Use the role's tier/edit access; keep method reports (hidden checks, UX, `deep-review`). Every handback then adds:

- `G<n> PASS <evidence>` or `G<n> FAIL <evidence>` per gate in the brief;
- `left: <item>: <what it learned>` per unfinished item, when it stops early;
- at most one refusal, as its last line: `too-big. split: <one-line jobs>`, `needs-confirm. op: <command>` or `ambiguous. ask: <one question>`.

Read refusals first: split, confirm or clarify before briefing again. Owner handbacks use [plain reports](owner-reports.md).

## Brief

Carry goal, role, absolute paths, edit limits, branch, handback and [scratch folder](fast-run.md#the-gate). Quote needed rules; whole methods only for walkthroughs/reviews. End with a gate per required outcome:

Fresh context: request, decisions, interface, stops, evidence paths. Full chat needs a reason. Store bulky returns locally; emit needed fields/diagnostics and paths. Never dump nested results or resend unchanged methods/transcripts. Read needed ranges/log tails. Host controls: adapter.

Verify lane cwd before writes; stop on mismatch. Pass its resources to commands/browsers. Use [quiet waits](waiting.md).

```text
G1 <outcome> CHECK: <command> EXPECT: <text its output must show>
G2 NEG <outcome> CHECK: <set the fix aside as a patch file, run its test, restore the fix> EXPECT: <the failure>
G3 MANUAL <outcome>: <what the reviewer judges>
```

- Every fix a test is said to pin gets a NEG gate. Set it aside with a patch file, never a stash. A gate that cannot fail proves nothing.
- A maker's last gate is the narrow test for its change. Slow checks (the full suite, long builds) run once on a runner after the wave, on files nobody edits until they end, writing the command and its output to a file in the scratch folder; a red run goes to a fresh maker with the failures.
- Keep the full tool return, command, session ID and exit result. Pending or missing exit is no PASS. Reuse PASS only with matching source, command, runtime/environment and intact evidence; changed, failed or untrusted receipts need execution. A delegate verdict is not independent acceptance. Read slow-check logs; MANUAL goes to the reviewer.

## Size

- One job per agent: an item or related findings. Separate useful independent jobs.
- Split briefs with over three outcomes, multiple commits or a whole unrelated document; one change across files counts once.
- Large spec: an analyst returns focused briefs with required rules and affected paths.
- Changes smaller than their brief stay local.
- Only the coordinator spawns; extra agents need `too-big. split:`.
- Preserve early groundwork (`left:`) in the next brief.

## Tier

- Pick the lowest role that can pass the gates. To spend less, lower effort before tier.
- Escalate, don't coach: after two failed gate rounds, the job and its handbacks go to a fresh delegate one tier up with the same edit access (runner to analyst, analyst to reviewer, maker to builder). A deep job that fails twice comes back to you (Authority and stops, rule 4).
- Your session is the ceiling: a role above your session's tier runs on your session's model.
- The owner's override beats every role. Never change the owner's session model or effort.

## Rounds

- Keep one focused maker through a coherent repair batch; start fresh when its context is stale or unrelated. Independent reviewers are fresh and never approve their own repairs.
- A review goes to a fresh reviewer with the baseline its method names (requirements, plan, rules, the diff and raw evidence such as logs, transcripts and QA notes), never the builder's reasoning or a verdict.
