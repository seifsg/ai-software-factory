# Mandatory PR workflow

## Small direct changes

Seif selected [small-change](../.agents/skills/small-change/SKILL.md) on 3 October: six lightweight routines, careful implementation, focused checks and one narrow independent assessment. This route precedes the full version workflow described below. No automatic broad regression, full-suite reruns or five-artifact planning for a small fix. Accumulated changes may prompt an offer of affected-area validation; execution waits for the user. It is an agent-operated scoped handoff, not a new controller command or whole-version acceptance. Existing pinned runs retain their bundle/state; see the method for explicit local trials and evidence limits.

Seif's decision, 2 October 2026: **both original PR skills must execute for every factory-managed PR, in every project, without a workflow bypass.** Project-specific names/accounts/commands become bindings; the working method stays intact.

```text
Checked local candidate
  -> how-to-make-a-pr
       remote base + focused branch + actual gates
       task search/reuse + two-way links + awaiting-review status
       visual draft + human owner + notification
  -> how-to-review-a-pr [SEPARATE INSTANCE]
       original goal -> analyze-start -> three alternatives
       get-ready-to-code plan -> diagnosed in-scope corrections
       security + performance + journey + change-guard + compliance
       actual build gate -> additive fixes -> fresh assessment
       detailed PR comment for the current head
  -> DRAFT for the human
       missing step/settings/access -> BLOCK, never silently skipped
```

Canonical owners: [creation](../.agents/skills/how-to-make-a-pr/SKILL.md) and [review](../.agents/skills/how-to-review-a-pr/SKILL.md). [Provenance](skill-provenance.md) maps each source requirement to its generic adaptation. The rules apply outside a controller run too; a local `ready` phase is not PR acceptance.

## This repository's current bindings

| Binding | Evidence / status |
|---|---|
| Repository / base | Private `seifsg/ai-software-factory`; remote heads checked 2 October: `main` and `docs/skill-lifecycle-map`; no dev branch; verified default `main` is the source-procedure fallback |
| Initial factory PR | [Merged #1](https://github.com/seifsg/ai-software-factory/pull/1), 3 October, under Seif's direct merge instruction; preserve its published history |
| Task | Pending Seif's selection; this PR changes controller/application files and does not qualify for the routine-only exception |
| Review owner / notification | Seif explicitly requested a completion notification to himself through Slack for the reusable-skill delivery on 2 October; the connected profile resolves his personal DM. Record actual delivery in the PR. This does not select a permanent notification policy or resolve GitHub's author self-review restriction; formal reviewer/alternative handoff remains pending |
| Checks | Python controller suite, skill validation, local references, affected JavaScript syntax and rendered preview; no configured package build/typecheck/lint toolchain |
| Observability | No production session informed this local pilot |
| Ready / merge / release | Human decision; Seif directly authorized pending session merges on 3 October. No standing automatic merge or deployment policy is inferred |

## Pending binding choice

| Option | Setup | Benefit | Constraint |
|---|---|---|---|
| A — recommended | GitHub Issues, Seif as human owner, GitHub notification | Keeps task and review together with the existing repository | Must resolve exact awaiting-review representation and GitHub's author/reviewer limitations truthfully |
| B | Existing team tracker and chat, with named reviewer/destination | Fits an established team workflow | Needs the actual accounts, destination, status mapping and access |
| C | Leave bindings pending | Avoids inventing operational settings | Overall PR workflow stays blocked |

Recommendation: A for this repository because the work is already in GitHub. It is **not selected** until Seif chooses. These are project bindings, not alternatives to executing the skills.

Before escalating a missing binding, inspect actual project records, remote metadata and available authorized integrations. Pending bindings above remain pending until evidence or an actual owner decision resolves them; autonomous local delivery is not permission to invent a tracker, review recipient or notification substitute. These blockers affect PR completion, while independent local implementation, QA and owner testing may continue under the session contract.

## Actual enforcement boundary

The repository rules, coordinator and fresh-session starter require both procedures. The controller fingerprints packaged skills, so changes invalidate old local acceptance evidence. Its `review` remains a local candidate review; it does not open a PR or execute the full PR chain.

There is no host hook intercepting arbitrary PR commands and no protected remote merge check implemented here. An instruction can be missed by an agent; the factory must not claim technically universal enforcement. Missing external bindings and missing independent review remain explicit blockers, even when local validation passes. The first browser demo is historical evidence of the earlier local loop, not proof of the newly packaged PR workflow.
