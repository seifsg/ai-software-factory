# Delegate: roles, briefs and gates

Cheapest capable role; models, overrides: `docs/hosts.md`.

## Roles

| Role | Tier | Edits | Jobs | Hands back |
|---|---|---|---|---|
| runner | light | no | scripted commands with a yes/no (tests, builds, the full suite), searches, inventories, comparisons, log reading | `<step or path:line>: <result>` per step or hit, then `PASS`, `FAIL <step>` or `<n> hits` |
| analyst | standard | no | research, per-area analysis, one-lens reviews, UX verdicts, read-only method walkthroughs, scouting a large spec | `<path:line or URL>: <finding>` per finding, then `<n> findings` |
| maker | standard | yes | planned or mechanical edits, fix rounds that spell out each fix, walkthroughs that run the change | `<path:lines>: <change>` per change, then `T<n> pre: <before> do: <change> post: <check>` per todo |
| builder | deep | yes | edits that need design calls: architecture, schema, security, unclear bugs | `<path:lines>: <change>` per change, then `decision: <choice> because <reason>` per call made and `T<n> pre: <before> do: <change> post: <check>` per todo |
| checker | light | its gate line only | gate checks ([checker](checker.md)) | its handback |
| reviewer | deep | no | final and independent review (`deep-review`), judgement calls that change no file: unclear bugs, architecture | `<path:line or URL> <severity>: <problem>. <fix>.` most severe first, the factory `verdict:` line of `how-to-review-a-pr` last; with no diff, `decision: <choice> because <reason>` instead |

Use the role's tier/edit access; keep method reports (UX, `deep-review`, checker). Every handback except the checker's (its lines only) then adds:

- `G<n> PASS <evidence>` or `G<n> FAIL <evidence>` per gate in the brief;
- `left: <item>: <what it learned>` per unfinished item, when it stops early;
- at most one refusal, as its last line: `too-big. split: <one-line jobs>`, `needs-confirm. op: <command>` or `ambiguous. ask: <one question>`.

Refusals first: split, confirm or clarify, then brief again.

## Brief

Carry goal, role, absolute paths, edit limits, branch, handback and a scratch folder under `.factory/`. Quote needed rules; whole methods only for walkthroughs/reviews. Fresh context: request, decisions, interface, stops, evidence paths; full chat needs a reason. Keep bulky returns in files; give needed fields and paths. Never resend unchanged methods or transcripts. Host controls: adapter.

Verify working folder before writes; stop on mismatch. Background delegates: set `Waiting: jobs: <what>` in the run file before ending turn; result comes back. End with a gate per required outcome:

```text
G1 <outcome> CHECK: <command> EXPECT: <text its output must show>
G2 NEG <outcome> CHECK: <set the fix aside as a patch file, run its test, restore the fix> EXPECT: <the failure>
G3 MANUAL <outcome>: <what the reviewer judges>
```

- Every fix a test is said to pin gets a NEG gate. Set it aside with a patch file, never a stash. A gate that cannot fail proves nothing.
- A maker's last gate is the narrow test for its change. Slow checks (full suite, long builds) run once on a runner after the wave, on files nobody edits until they end, writing command and output to a file in scratch folder; diagnose a red run before fixing or delegating it.
- Keep the full tool return, command, session ID and exit result. Pending or missing exit is no PASS. Reuse PASS only with matching source, command, runtime/environment and intact evidence; changed, failed or untrusted receipts need execution. A delegate verdict is not independent acceptance. Read slow-check logs; MANUAL goes to the reviewer.

## Size

- One coherent job per agent. Combine related checks; separate only useful independent jobs.
- Split briefs with over three outcomes, multiple commits or a whole unrelated document; one change across files counts once.
- Large spec: analyst returns focused briefs with required rules and affected paths.
- Only the coordinator spawns, and a reviewer its lens agents; extra agents need `too-big. split:`.
- Keep early groundwork (`left:`) in next brief.

## Tier

- Lowest role that can clear the gates. To spend less, lower effort before tier.
- Escalate, don't coach: after two failed gate rounds, job and handbacks go to fresh delegate one tier up, same edit access (runner to analyst, analyst to reviewer, maker to builder). A deep job that fails twice comes back to you (Authority and stops, rule 4).
- Session is ceiling: a role above session tier runs on session model.
- Owner's override beats every role. Never change owner's session model or effort.

## Rounds

- One maker, one independent reviewer per repair batch; reviewer checks deltas. Replace either on lost context, and a reviewer that repaired.
- First review goes to fresh reviewer with baseline its method names (requirements, plan, rules, diff, raw evidence: logs, transcripts, QA notes), never builder's reasoning or a verdict.
