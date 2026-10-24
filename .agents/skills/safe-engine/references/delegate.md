# Delegate: roles, briefs and gates

Each delegated job runs on the cheapest role that can pass its gates. Your agent's role names, models and override routes: the factory's `docs/hosts.md`.

## Roles

| Role | Tier | Edits | Jobs | Hands back |
|---|---|---|---|---|
| runner | light | no | scripted commands with a pass/fail (tests, builds, the full suite), searches, inventories, comparisons, log reading | `<step or path:line>: <result>` per step or hit, then `PASS`, `FAIL <step>` or `<n> hits` |
| analyst | standard | no | research, per-area analysis, one-lens reviews, UX verdicts, scouting a large spec | `<path:line or URL>: <finding>` per finding, then `<n> findings` |
| maker | standard | yes | planned or mechanical edits, fix rounds that spell out each fix, walkthroughs, the checker | `<path:lines>: <change>` per change |
| builder | deep | yes | edits that need design calls: architecture, schema, security, unclear bugs | `<path:lines>: <change>` per change, then `decision: <choice> because <reason>` per call made |
| reviewer | deep | no | final and independent review (`deep-review`), judgement calls that change no file: unclear bugs, architecture | `<path:line> <severity>: <problem>. <fix>.` most severe first, then `verdict: ready`, `ready after fixes` or `not ready: <why>` |

A todo runs on the role its tier and edit access give. A method that names its own report (hidden checks, UX verdicts, `deep-review`) keeps it. Every handback then adds:

- `G<n> PASS <evidence>` or `G<n> FAIL <evidence>` per gate in the brief;
- `left: <item>: <what it learned>` per unfinished item, when it stops early;
- at most one refusal, as its last line: `too-big. split: <one-line jobs>`, `needs-confirm. op: <command>` or `ambiguous. ask: <one question>`.

Read the last line first. A refusal is never done: split, confirm or ask the owner, then brief again.

## Brief

Carry what the delegate cannot infer: the goal, its role, absolute paths, read-only or not, the conventions in play, the branch it owns, its handback shape and, in Fast and Lucky, the run's scratch folder ([fast-run](fast-run.md#the-gate)). Quote the paragraphs a job needs; never "read the whole document first". End with one gate per required outcome:

```text
G1 <outcome> CHECK: <command> EXPECT: <text its output must show>
G2 NEG <outcome> CHECK: <set the fix aside as a patch file, run its test, restore the fix> EXPECT: <the failure>
G3 MANUAL <outcome>: <what the reviewer judges>
```

- Every fix a test is said to pin gets a NEG gate. Set it aside with a patch file, never a stash. A gate that cannot fail proves nothing.
- A maker's last gate is the narrow test for its change. Slow checks (the full suite, long builds) run once on a runner after the wave, writing their output to a file in the scratch folder; a red run goes to a fresh maker with the failures.
- On handback, re-run every runnable gate yourself before accepting; for a slow check, read the end of its output file instead. MANUAL gates go to the reviewer.

## Size

- One job per agent: one item, or one cluster of findings in one area. Independent items get separate agents.
- Split a brief with more than three deliverables (separate outcomes; one change repeated across many files is one), more than one commit, or a whole document to read.
- A large spec: an analyst scouts it first and returns one brief per job, with the rules it needs quoted and the files and lines it touches.
- Below the overhead line, do it yourself: a change smaller than its brief.
- A delegate that stops early hands back groundwork (`left:`); the next brief quotes it.

## Tier

- Pick the lowest role that can pass the gates. To spend less, lower effort before tier.
- Escalate, don't coach: after two failed gate rounds, the job and its handbacks go to a fresh delegate one tier up with the same edit access (runner to analyst, analyst to reviewer, maker to builder). A deep job that fails twice comes back to you (Authority and stops, rule 4).
- Your session is the ceiling: a role above your session's tier runs on your session's model.
- The owner's override beats every role. Never change the owner's session model or effort.

## Rounds

- A fresh delegate per review or fix round. Never resume one across rounds: it re-sends its whole history. Resume only for a quick follow-up while its context is small.
- A review goes to a fresh reviewer with the requirements and the diff only, never the plan or a verdict.
