---
name: database-schema
description: "Design or revise persistence from whole-product journeys, invariants and query workloads. Compare three viable designs, record the choice and audit it. Routine fixes stay scoped."
---

# Database Schema

Put the whole app in front of us. Get the model right before dependent features harden. No meaningless tables, missing relationships or quality cuts to save coding effort.

Optimize the real workload; plan safe evolution. No perfect-schema or universal O(1) promises.

## 1. Understand the whole picture

Read request, schema/migrations, queries, callers, product plan and settled decisions. Use [Analyze Start](../analyze-start/SKILL.md); reuse completed analysis. No coding here.

Map users/roles, ownership, journeys, state changes, business rules, data lifetime and consumers: clients, jobs, integrations, admin, search, reports. Include applicable game saves/inventory/progression and offline/sync. Invent no features to justify tables.

Record entities, cardinality, source of truth, tenant/access boundaries, volumes/growth/skew, read/write rates, concurrency, consistency and latency targets. Label assumptions; missing facts block dependent choices only. No persistence need? Say so; add no database.

Map `journey → invariant → read/write → filters/order/page → rows/size/rate → consistency → target → evidence/unknown`.

Include critical writes, failures and retries. Local fixes map affected paths/wider dependencies; whole-product awareness grants no redesign.

## 2. Plan and compare three designs

Use [Get Ready to Code](../get-ready-to-code/SKILL.md): files → original checkpoint → critique → phases → todos → whole plan. Stop unless continuation is already authorized. Reuse the delivery plan's five outputs; keep design and execution separate.

Research consequential unknowns through [Research Market](../research-market/SKILL.md), using current primary engine/version docs. The [source basis](../../../docs/skill-provenance.md#database-schema-method--4-october-2026) prescribes no stack.

For new substantive choices, compare three credible designs: modeling, ownership, access paths or consistency—not necessarily three brands. Preserve settled engine/product choices. If fewer are viable, explain rejected alternatives; invent none.

Compare correctness, complete journeys, read/write cost, consistency, security, storage, growth, operations and migration risk. Coding effort cannot justify weaker quality; runtime/operational costs still matter.

Recommend the best fit: why, tradeoff, revisit conditions, rejected options. Choose when delegated; resolve owner-reserved choices before dependent work. No repeated votes.

## 3. Write the selected schema

Apply [Application Security](../safe-engine/references/app-security.md) to database roles, row policies, bypass paths and tenant isolation. Verify actual application access; no blanket RLS mandate for unrelated local storage.

Keep one design record in the project's established location: access map, comparison, reasoned choice, ASCII ERD/equivalent, dictionary, index/query plan, migration plan, risks. No duplicate mutable specs.

Every table/collection, field, relationship, dataset, index and derived view needs a purpose/consumer. Remove unjustified copies/speculation. Keep necessary junctions, history, permissions and lookups; fewer tables alone proves nothing. Normalize/embed for the workload. Denormalization needs benefit, authoritative source, update/repair owner and freshness. No relational rules hidden in unbounded JSON.

Specify applicable:

- Keys/identity, cardinality, types/precision/units, timestamps/timezones, collation/case, required/null/default meaning, uniqueness/reference integrity. Enforce invariants in the database where supported; specify application enforcement otherwise.
- Ownership, tenant isolation, permissions, retention/deletion/cascades. Separate business history from debug logs. No orphans or accidental cross-tenant references.
- Transactions, isolation, idempotency, simultaneous writes, conflicts, retries/recovery. Show how invariants survive races.
- Predicates, projections, order/pagination, indexes/column order. Check selectivity, joins/N+1, scans/sorts, actual plans/row counts and index write/storage cost. Justify scans; never index every field.
- Partition/shard routing, hot keys, bounded documents/arrays and cross-partition work. Partitions/replicas/caches/materialized views need evidenced benefits and invalidation/refresh costs.
- Versioned migrations, dirty/duplicate/null data, backfill/batches, old/new clients, locks/downtime, rollout/recovery. Backups need usable restore. Destructive/production execution needs authority; reverse migrations cannot guarantee data recovery.

Keep the original O(1) question: avoid repeated work; can we get closer? Define N and result size K; distinguish expected/amortized/worst case. Indexes do not guarantee O(1); returning K records requires processing them. Measure latency/throughput at realistic size, skew, concurrency and cold/warm conditions. Label estimates/unmeasured targets.

Planning ends with the design. Authorized authoring uses Get Ready's full 0–4 loop for DDL/models/migrations. Keep them consistent; preserve unrelated data/changes. Written migrations grant no execution authority.

## 4. Audit it again

Read the written design/schema against access map/invariants. Walk critical input → stored state → query/output paths, including denial, retries, concurrent updates, deletion/recovery. Find unsupported assumptions, redundancy, missing constraints, wrong cardinality, costly access and migration hazards. Inspect emitted queries, not ORM names alone.

Reuse the factory's fresh independent reviewer: exact candidate, request, alternatives, choice, schema and raw evidence. Fix supported findings; reassess affected parts. Retain unresolved limits; missing independent review stays unverified. No extra fleet, early tests or implied production queries.

After implementation, manually use real app/CLI/API/database actions with harmless representative data in disposable development. Inspect [logs](../safe-engine/references/app-diagnostics.md), actual plans/results and [resource costs](../safe-engine/references/app-efficiency.md). Execution-based EXPLAIN runs queries: inspect side effects; rollback is no universal undo. Production probes/expensive workloads need authority.

After passing manual QA, author/polish/run final correctness, migration, isolation and performance checks under [tests-last order](../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests). No automated benchmarks/harnesses disguised as manual QA. Design-only ends with audited design and runtime unknowns.

Return choice/reason, schema location, audit findings/fixes, observed evidence and limits. Diagrams, optimizer estimates and tiny samples cannot prove production performance.
