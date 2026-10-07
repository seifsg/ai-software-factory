---
name: database-schema
description: "Designs or revises persistence from the whole product's journeys, invariants and query workloads: compares three designs, writes the schema, plans indexes and migrations, and audits the result. Use when adding or materially changing tables, collections, indexes or migrations. Routine fixes stay scoped."
---

# Database Schema

Put the whole product in front of us. Get the model right before dependent features harden.
No meaningless tables, missing relationships or quality cuts to save coding effort.
Optimize the measured workload. No perfect-schema or universal O(1) promises.
Do not code during design.

## 1. Map the whole product

Read the request, schema, migrations, queries, callers, product plan and settled choices. Reuse completed analysis (`analyze-start`).

- Map users and roles, ownership, journeys, state changes, business rules, data lifetime, consumers (clients, jobs, integrations, admin, search, reports). Include game saves, inventory, progression, offline sync where they apply. Invent no features to justify tables.
- Record entities, cardinality, source of truth, tenant and access boundaries, volumes, growth, skew, read and write rates, concurrency, consistency and latency targets. Label assumptions. Missing facts block dependent choices only.
- No persistence need? Say so. Add no database.
- Build the access map: `journey → invariant → read/write → filters/order/page → rows/size/rate → consistency → target → evidence/unknown`. Include critical writes, failures, retries.
- Local fix: map the affected paths and wider dependencies. Awareness grants no redesign.
- Required integrity and recovery come early. Speculative structures wait.

## 2. Compare three designs

- Plan with `get-ready-to-code`. Keep design and execution separate. Reuse the delivery plan.
- Research consequential unknowns in current primary docs for the engine and version. Settled engine choices stay.
- Compare three credible designs: modeling, ownership, access paths or consistency, not necessarily three brands. Judge correctness, complete journeys, read and write cost, consistency, security, storage, growth, operations, migration risk. Coding effort never justifies lower quality. Runtime and operating cost do count.
- Fewer than three viable: say why. Invent none.
- Choose one: why, tradeoff, revisit conditions, rejected options. Owner-reserved choices are settled before dependent work.
- Record: a 3-option table, a `**Chosen:**` line, a fenced ERD or DDL.

## 3. Write the schema

One design record in the project's usual location: access map, comparison, choice, ERD (ASCII or equivalent), data dictionary, index and query plan, migration plan, risks. No duplicate mutable specs.

- Every table, field, relationship, index and derived view has a purpose and a consumer. Remove speculation and unjustified copies. Keep needed junctions, history, permissions, lookups. Fewer tables alone proves nothing. Normalize or embed for the workload.
- Denormalize only with a benefit, an authoritative source, an owner for update and repair, and a freshness rule. No relational rules hidden in unbounded JSON.
- Keys, cardinality, types, precision, units, timestamps and timezones, collation, null and default meaning, uniqueness, referential integrity. Enforce invariants in the database where supported. Otherwise specify the application check.
- Ownership, tenant isolation, least-privilege roles, row policies, retention, deletion, cascades. Verify the real application access paths and any bypass. No orphans. No cross-tenant references. Business history is not debug logs.
- Transactions, isolation, idempotency, concurrent writes, conflicts, retries. Show how invariants survive races. Bound connections.
- Local commit plus remote effect (payment, email, webhook): name which side owns the truth and how they reconcile. No universal queue.
- Indexes come from the actual predicates, projections, order and pagination. Check selectivity, joins, N+1, scans, sorts, real plans and row counts, write and storage cost. Justify every scan. Never index every field.
- Partitions, shards, replicas, caches, materialized views need an evidenced benefit and a stated invalidation or refresh cost. Watch hot keys, unbounded documents and arrays, cross-partition work.
- Migrations: versioned. Handle dirty, duplicate and null data. Backfill in batches. Old and new clients. Locks and downtime. Rollout and recovery. Backups need a usable restore. A reverse migration does not guarantee data recovery. Writing a migration grants no right to run it. Destructive or production runs need authority.
- Complexity: define N and result size K. Say expected, amortized or worst case. Indexes do not guarantee O(1); returning K rows costs K. Measure latency and throughput at realistic size, skew, concurrency, cold and warm. Label estimates and unmeasured targets.

Authored DDL, models and migrations go through the `get-ready-to-code` 0–4 loop. Keep them consistent. Preserve unrelated data and changes.

## 4. Audit it again

1. Read the written schema against the access map and invariants.
2. Walk each critical path: input → stored state → query → output. Include denial, retries, concurrent updates, deletion, recovery.
3. Find unsupported assumptions, redundancy, missing constraints, wrong cardinality, costly access, migration hazards. Inspect the emitted queries, not ORM names.
4. Get an independent review when one is available. Give the reviewer the request, alternatives, choice, schema and raw evidence. Fix supported findings. Recheck affected parts. Unreviewed stays unverified.
5. After implementation, use the real app, CLI, API or database with harmless representative data in a disposable development environment. Read the logs, actual query plans and results, resource cost.
6. Execution-based query plans run the query. Check side effects. Rollback is no universal undo. Production probes and expensive workloads need authority.
7. After manual use passes, write and run correctness, migration, isolation and performance checks. Automated benchmarks are not manual QA.

Design-only work ends with the audited design and the runtime unknowns.
Return: choice and reason, schema location, audit findings and fixes, observed evidence, limits.
Diagrams, optimizer estimates and tiny samples prove no production performance.
