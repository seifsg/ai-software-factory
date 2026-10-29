# Delegate: roles, briefs and gates

Delegate only worthwhile jobs; use the cheapest capable role. Host models/overrides: factory docs/hosts.md.

| Role | Tier | Edits | Work | Handback |
|---|---|---|---|---|
| runner | light | no | commands, search, inventories, comparisons/logs | `<step or path:line>: <result>` per step or hit, then `PASS`, `FAIL <step>` or `<n> hits` |
| analyst | standard | no | research, area analysis, single-lens/UX reviews, method walkthroughs, spec scouting | `<path:line or URL>: <finding>` per finding, then `<n> findings` |
| maker | standard | yes | planned/mechanical edits, specified fixes, executable walkthroughs/checker | `<path:lines>: <change>` per change, then `T<n> pre: <before> do: <change> post: <check>` per todo |
| builder | deep | yes | architecture, schema, security, unclear bugs | `<path:lines>: <change>` per change, then `decision: <choice> because <reason>` per call made and `T<n> pre: <before> do: <change> post: <check>` per todo |
| reviewer | deep | no | final/independent deep-review and read-only design decisions | `<path:line or URL> <severity>: <problem>. <fix>.` most severe first, then `verdict: ready`, `ready after fixes` or `not ready: <why>`; with no diff, `decision: <choice> because <reason>` instead |

Keep the role's tier/access and method reports. Every handback then adds:

- `G<n> PASS <evidence>` or `G<n> FAIL <evidence>` per gate in the brief;
- `left: <item>: <what it learned>` per unfinished item, when it stops early;
- at most one refusal, as its last line: `too-big. split: <one-line jobs>`, `needs-confirm. op: <command>` or `ambiguous. ask: <one question>`.

## Brief
Carry goal, role, absolute paths, edit bounds, branch, handback and [scratch](fast-run.md#the-gate). Quote relevant rules; whole methods only for walkthrough/review. End with verifiable gates per required outcome:
```text
G1 outcome CHECK: command EXPECT: observed output
G2 NEG outcome CHECK: save fix as patch, set aside, run test, restore EXPECT: failure
G3 MANUAL outcome: reviewer judgment
```
Every fix claimed pinned by a test needs NEG; use a patch, never stash. A check unable to fail proves nothing.
- Fresh context: request, decisions, interface, stops, evidence. Full chat needs a reason. Keep bulky returns local, emit needed fields/errors/paths, read targeted ranges; no repeated unchanged methods/transcripts or nested dumps.
- Verify lane cwd before writes; use its resources and [quiet waits](waiting.md). Isolate sample data/mode from live preview; authorized inspection grants no other-lane service mutation/start/stop.
- Maker ends with narrow affected check. Slow checks run once locally or on useful runner after wave, source frozen, command/output saved; diagnose failures before choosing repair/delegation.
- Preserve full command/session/exit. Pending/missing exit is no PASS and never releases a dependent consumer. Reuse PASS only for matching source/command/runtime/environment and intact evidence; changed/failed/untrusted proof reruns. Delegate verdict is not independent acceptance; inspect logs and give MANUAL to reviewer.

## Size and tier
- One coherent job/context; combine related checks, separate useful disjoint work. Smaller-than-brief jobs stay local. Split over3 outcomes, multiple commits or unrelated documents; one change across files counts once.
- Large spec: analyst returns focused briefs/rules/paths. Only coordinator spawns; extra helpers require too-big. split. Carry left groundwork forward.
- Lowest passing role; reduce effort before tier. After2 failed rounds, same job/handbacks go one tier up with same edit access: runner→analyst, analyst→reviewer, maker→builder. Deep twice-failed work returns for shared-cause diagnosis.
- Session model is ceiling. Owner override wins; never change owner's session model/effort.

## Rounds
Keep delegated maker and independent reviewer through a coherent repair batch; review deltas. Replace for lost context or reviewer-written repairs. Reviewer gets requirements, plan, rules, diff and raw proof, never builder reasoning/verdict; no self-approval.
