---
name: how-to-make-a-pr
description: "Prepares and opens a draft pull request for human review, linked to its ticket and backed by before/after proof. Use when creating, updating or correcting a pull request."
---

# How to make a PR

Open drafts; humans decide ready, merge and release. Analysis/review-only grants no push, PR or comment.

## 1. Bind project and ticket

Find repository, branches, release/template/signing rules, checks, tracker and review owner from actual rules, manifests, CI and remote metadata. Ask consequential gaps only; a missing binding blocks its dependent step.

- Search existing tickets by symptom, area, files and branch/title; none: `ticketing`. No ticket only under a whole-diff exemption or a retained trivial change with the reason in the body.
- Refresh confirmed scope before opening/updating; drift, pending scope or failed refresh blocks acceptance. A draft/pass cannot replace current owner intent.
- Link both ways: ticket in PR, PR in ticket activity. Open finished work is Ready for QA; Done follows merge.

## 2. Branch

- Own branch, never base; protect dirty/foreign work with isolation. Base is integration branch, else default; explain exceptions.
- Epic wave: share integration branch/draft, incorporate finished lanes, resolve/recheck and push without force. Independently complete UI tickets may ship after Show/Prove with checked dependencies; never wait for unrelated tickets or merge without human authority.
- Check remote branches; shallow clones hide them. Dependent Safe tickets, wrong base and hotfixes: [cases](references/pr-cases.md).

```text
git ls-remote --heads origin
git ls-remote --symref origin HEAD
git fetch origin
git switch -c <scope>/<short-name> origin/<base>
```

## 3. Plan proof before edits

Every outcome needs observed Before/After. API: matched status/body; CLI/gate: command output; method/prose: walkthrough result plus key text. Use diff blocks; speed/size/cost compares the same workload. Prove internal changes through their screen/endpoint/command; new output says "did not exist". Declare **Visual:** and **Journey:** per [layout](references/pr-layout.md). Changed visuals, states, motion or UI journeys require [media proof](references/media-proof.md) before editing, including shared-backend effects.

## 4. Change and check

- One outcome per PR; unrelated finds become follow-ups. Stage owned filenames, never `git add .` or `git add -A`.
- Branch follows project convention, else `<scope>/<short-name>`. Commit `<type>(<scope>): <imperative subject>`; explain why in body. Honor signing; never invent identity or bypass permission/gates.
- No AI/tool attribution in commits. PR ends exactly with [credit](references/credit.md).
- Use real behavior before writing/adjusting tests. Test-discovered production fixes return through use and affected tests; no tests that restate code.
- Required local checks pass before push; unrun checks stay unverified. CI is extra evidence, never required, waited on or rerun; list local commands/results.

## 5. Draft

1. Write [layout](references/pr-layout.md) to a file. Fast/Lucky: `fast_gate.py report --pr-body <file> --project <abs>` before publication; structure-only success replaces no observed proof or handoff check.
2. Push and open draft against the actual base ([commands](references/github.md)). Closing keyword only for completed sub-issues/change tickets; epic gets a plain link.
3. Request review from the actual configured owner through the supported route. Notify only authorized recipients/channels; reminders only when asked.
4. Share authorized, sanitized observations with source/limits; no foreign session IDs or secrets.

## 6. Review and handoff

- Required independent review: frozen source/manual/affected checks first; resolve source findings before planned validation. Source-only review advances no controller phase. Same reviewer checks author deltas and carried findings/observations; changed inputs need fresh affected proof. After the suite, inspect exact-candidate receipt/log before verdict. Reviewer-written repairs require a fresh independent assessment.
- Own draft: `deep-review` in Safe; Fast/Lucky's optional Safe check covers it. Skip an already independently reviewed exact head. Own-branch fixes/comments are authorized; post open questions in the PR instead of stopping. Another author's PR keeps every checkpoint. Remote/cloud review: [cases](references/pr-cases.md).
- Fast/Lucky opens one draft per run, or updates its wave draft with outcomes, criteria, remaining work and refreshed summary. Safe checks run only on request; reuse completed current QA/tests/review. Variations get separate branches/drafts.
- Name missing baseline/tests/review and link the epic. Draft/review grants no merge/release. After merge, new work branches from current base. No force push, rewrite or unrequested notification.
