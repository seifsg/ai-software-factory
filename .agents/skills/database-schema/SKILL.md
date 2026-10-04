---
name: database-schema
description: "Design or revise a database schema from whole-product journeys, invariants and query workloads. Compare three viable designs, record the choice and audit it. Use for new persistence models or material schema changes; keep routine fixes scoped."
---

# Database Schema

Put the whole app in front of us. Get the data model right before dependent features harden around it. No meaningless tables. No missing relationships. No cutting corners to save coding effort.

Optimize for the actual product and workload. A good first design still needs safe evolution. Do not promise a perfect schema or O(1) for every query.

## 1. Understand the whole picture

Read the request, existing schema/migrations, actual queries, callers, product plan and settled decisions. Use [Analyze Start](../analyze-start/SKILL.md). No coding during analysis. Reuse completed analysis; do not restart it for this skill.

Map users/roles, ownership, complete journeys, state changes, business rules, data lifetime and all consumers: clients, jobs, integrations, admin, search and reports. Include applicable game saves, inventory, progression and offline/sync behavior. Do not invent features to justify a table.

Record entities, relationships/cardinality, source of truth, tenant/access boundaries, volumes/growth/skew, read/write rates, concurrency, consistency and latency targets. Label assumptions. Missing facts block dependent choices, not unrelated work. No persistence need? Explain it; do not add a database to satisfy this skill.

Build a compact access map:

`journey → invariant → read/write → filters/order/page → expected rows/size/rate → consistency → target → evidence/unknown`

Cover critical writes and failure/retry paths, not just dashboard reads. An existing local fix maps its affected paths and wider dependencies; whole-product awareness does not authorize redesigning the whole database.

## 2. Plan and compare three designs

Use [Get Ready to Code](../get-ready-to-code/SKILL.md): files, original checkpoint, critique, phases, todos and whole plan. Honor the stop unless existing authority covers continuation. Keep design separate from execution. During factory delivery, reuse these five outputs inside the existing plan phase.

Research consequential unknowns in current primary documentation for the actual engine/version through [Research Market](../research-market/SKILL.md). Follow the [source basis](../../../docs/skill-provenance.md#database-schema-method--4-october-2026); it is not a fixed stack recommendation.

For a new substantive schema decision, compare three credible designs. Vary modeling, ownership, access paths or consistency where useful; do not force three database brands or add fake contenders. Preserve settled engine/product choices. If constraints leave fewer viable choices, show why others fail rather than inventing alternatives.

Compare correctness, complete journey support, read/write cost, consistency, security, storage, growth, operations and migration risk. Do not discount quality because implementation takes effort. Runtime cost and operational complexity still matter.

Recommend the best fit and explain why it wins, what it gives up and when the choice should be revisited. Record rejected options. Choose within delegated authority; otherwise present the recommendation and resolve the owner's choice before dependent work. No repeated vote on settled decisions.

## 3. Write the selected schema

Save one coherent design record in the project's established location: access map, three-way comparison, decision/reason, ASCII ERD or equivalent model, data dictionary, index/query plan, migration plan and open risks. Do not scatter duplicate mutable specifications.

Every table/collection, field, relationship, dataset, index and derived view needs a purpose and consumer. Remove unjustified copies and speculative flexibility. Fewer tables is not automatically better: retain junctions, history, permissions or lookup entities when they express real rules. Normalize or embed for the workload; denormalization needs a benefit, authoritative source, update/repair owner and freshness rule. Do not hide relational requirements in an unbounded JSON field.

Specify applicable:

- Keys/identity, cardinality, types/precision/units, timestamps/timezones, collation/case rules, required/null/default meaning, uniqueness and reference integrity. Enforce invariants in the database where supported; identify explicit application enforcement where not.
- Ownership, tenant isolation, permissions, retention/deletion and cascade behavior. Separate required business history from debug logs. No orphan records or accidental cross-tenant references.
- Transaction boundaries, isolation, idempotency, simultaneous writes, conflicts, retries and recovery. State how invariants survive races, not just sequential happy paths.
- Query predicates, projections, ordering/pagination and useful indexes, including column order. Account for selectivity, joins/N+1, scans/sorts, query plans, row count and index write/storage cost. Explain an intentional scan; do not index every field.
- Partition/shard routing, hot keys, bounded document/array growth and cross-partition work where relevant. Add partitions, replicas, caches or materialized views only for supported needs; include invalidation/refresh costs.
- Versioned migrations, existing dirty/duplicate/null data, backfill/batch strategy, old/new client compatibility, lock/downtime risk, rollout and recovery. Backups need a usable restore route; destructive changes and production execution need actual authority. A reverse migration does not guarantee lost data can be recovered.

Keep the original O(1) question: can we avoid repeated work and get closer? Name N and result size K; distinguish expected/amortized from worst-case cost. Indexed lookup is not automatically O(1); returning K records costs at least processing those records. Measure useful latency/throughput under realistic size, skew, concurrency and cold/warm conditions. Label estimates and unmeasured targets honestly.

Planning stops with the design. When schema authoring/implementation is authorized, write the chosen DDL, models and migrations using Get Ready's full 0–4 loop. Do not execute migrations merely because files exist. Keep migrations and models consistent; preserve unrelated data and changes.

## 4. Audit it again

Read the actual written design/schema against the full access map and invariants. Walk each critical journey from input to stored state to query/output, including denied access, retries, concurrent updates, deletion and recovery. Find unsupported assumptions, redundant structures, missing constraints, wrong cardinality, costly access paths and migration hazards. Verify emitted queries, not ORM names alone.

Obtain a fresh independent assessment of the exact candidate with request, alternatives, decision, schema and raw evidence. Reuse the factory's applicable reviewer; no extra review fleet. Correct supported findings, audit again and retain unresolved limits. Audit does not authorize early automated tests or production queries. Missing independent review remains unverified.

For implemented work, finish implementation first. Manually exercise real app/CLI/API/database actions in a disposable development environment with harmless representative data; inspect [mandatory logs](../safe-engine/references/app-diagnostics.md) and actual plans/results. Use [efficiency guidance](../safe-engine/references/app-efficiency.md). Execution-based EXPLAIN runs the query: inspect side effects first; rollback is not a universal undo. No production probes or expensive workload runs without authority.

Only after finished work and passing manual QA, author/polish/run automated correctness, migration, isolation and performance checks at the final pre-PR stage under [tests-last order](../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests). No automated benchmarks or test harnesses disguised as manual QA. A design-only request ends with an audited design and explicit runtime unknowns.

Return the selected design, why, schema location, audit findings/fixes, observed evidence and remaining limits. A diagram, optimizer estimate or tiny sample is not proof of production performance.
