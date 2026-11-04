---
name: analyze-start
description: "Analyzes a feature, defect, refactor or PR before any coding: reads the actual code, explains purpose and success, maps every consumer and draws ASCII flow charts. Use when work starts on existing or new code, or when asked to analyze. Analysis only."
---

# Analyze Start: understand it fully, write no code

Analysis only. Learn the feature, task or PR end to end, then explain it so a teammate or future agent can pick it up cold. No code changes: read, search, diagram.

> **Grounding rule.** Read the real code, never guess from a diff or a filename. A skimmed claim is a hypothesis until read enough to know what it means. Keep verified facts and hypotheses apart.

## Instructions

0. **Start from the inputs.** Read the ticket (requested items, criteria), any kickoff research and an owner-named size; know which step this is and what comes next.
1. **Learn it.** Read the feature or PR and everything it touches. Follow the code, not the summary. Skim what doesn't matter; focus on core logic.
2. **Explain it back in full detail.** Own words: what it does, why it exists, what success means. New product or feature: who uses it, the jobs they need done, each requested item mapped to what it needs, and the non-functional needs (speed, accessibility, security). Why stated nowhere: say so; no rationale is a finding.
3. **Map every call site.** Everywhere this code is called, used or depended on: callers, consumers, route/DTO/schema references, event names, storage keys, tests. List with paths; regression review builds on it. Prefer search and reading over assumption.
4. **Draw ASCII charts.** Flow and architecture, trigger → layers → data/persistence → result; mark where the change sits.

   ```
   Web example:
     request → controller → service → ORM/DB
                                 └→ external API / queue → response
                                 ↑ frontend: user action → component → hook/query → API client

   Mobile example:
     user action → screen/route → hook/context/query cache
                 → API client | direct-to-storage upload → local persistence
                 → navigation + UI result
   ```

5. **Trace the risky edges.** Where outside data enters; invariants enforced vs only assumed. Trace each defect or edge case to its design cause.
6. **Claim vs code** (a PR or a bug report). Each claimed behavior: where delivered, whether wired up:

   | Claimed behavior | Where in the code | Delivered? (YES / PARTIAL / NO) | Note |
   |---|---|---|---|

7. **Extensions.** What changes through data or config, what needs code. Plan the final proof with content absent from the build.
8. **Scope.** Next complete useful result, its required dependencies, shared constraints. Keep the whole requested outcome visible.
9. **Open questions and hypotheses.** Collect the ambiguous, the risky, what needs outside context. Label hypotheses; never a hunch as fact.

Docs or method changes: map readers, links and canonical owners instead of inventing code consumers.

## Hard rule

No code in this phase: no edits, fixes, quick changes. Coding only in a later, explicit build phase.

## Output contract

The block `## 1 Analyze` holds, in this order:

- [ ] **Inputs:** ticket link, requested-item and criteria ids, research summary, owner-named size or `none`; `step 1, next: Recommend`
- [ ] **Purpose:** what it does, why it exists, what success means; a missing why is named as a finding
- [ ] **Flow:** at least one ASCII diagram with the change located on it
- [ ] **Used by:** every caller, consumer and dependent, with paths
- [ ] **Edges:** outside-data entry points; invariants enforced vs assumed
- [ ] **Claims:** the claim-vs-code table, or "no claims to check"
- [ ] **Scope:** next complete useful result and its dependencies
- [ ] **Unknowns:** open questions and labeled hypotheses, or "none"
- [ ] **For Recommend:** the decisions step 2 must make
- [ ] No file changed during this step

A small `change` keeps every line, each one short.
