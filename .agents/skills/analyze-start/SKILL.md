---
name: analyze-start
description: "Analyzes a feature, defect, refactor or PR before any coding: reads the actual code, explains purpose and success, maps every consumer and draws ASCII flow charts. Use when work starts on existing or new code, or when asked to analyze. Analysis only."
---

# Analyze Start: understand it fully, write no code

Deep, thorough, analysis-only phase. Educate yourself on the feature, task or PR until you understand it end to end, then explain it back so a teammate or a future agent could pick it up cold. Do not write or change code.

> **Grounding rule.** Read the real code, never guess from a diff or a filename. A claim you only skimmed is a hypothesis until you have read enough to know what it means.

## Instructions

0. **Start from the inputs.** Read the ticket (requested items, criteria), any kickoff research and the size; know where the run stands.
1. **Educate yourself thoroughly.** Read the feature or PR and everything it touches. Follow the code, not the summary. Skim details that don't matter; focus hard on the core logic.
2. **Explain it back in full detail:** what it does and why it exists. Define what success means. New product: its users and their jobs, what each requested item needs, non-functional needs (speed, accessibility, security). If the why is stated nowhere, say so: a change with no rationale is itself a finding.
3. **Map every call site.** Find everywhere else this code is called, used or depended on: callers, consumers, route/DTO/schema references, event names, storage keys, tests. List them with paths. Regression review builds on this map. Prefer search and reading over assumption.
4. **Draw ASCII charts.** Show the flow and the architecture, trigger → layers → data/persistence → result, and mark where the change sits.

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

5. **Trace the risky edges.** Name where outside data enters, which invariants are enforced and which are only assumed. Trace each defect or edge case to its design cause.
6. **Claim vs code** (a PR or a bug report). For each claimed behavior, point to where it is delivered and whether it is actually wired up:

   | Claimed behavior | Where in the code | Delivered? (YES / PARTIAL / NO) | Note |
   |---|---|---|---|

7. **Extensions.** State what can change through data or config and what needs code. Plan the final proof with content absent from the build.
8. **Scope.** Name the next complete useful result, its required dependencies and shared constraints. Keep the whole requested outcome visible.
9. **Open questions and hypotheses.** Collect anything ambiguous, risky or needing outside context. Label hypotheses; never present a hunch as a fact.

Docs or method changes: map readers, links and canonical owners instead of inventing code consumers.

## Output contract

The block `## 1 Analyze` holds, in this order:

- [ ] **Inputs:** ticket link, requested-item and criteria ids, research summary, size; `step 1, next: Recommend`
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
