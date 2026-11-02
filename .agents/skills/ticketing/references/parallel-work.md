# Parallel work

- One dedicated builder session per ticket, full cycle, small fixes included. Parent owns scheduling, shared decisions, tracker updates.
- Hand over: contract, authority and stops, decisions, current scope, checkout state, dependencies, evidence, unfinished phase, pending operations.
- Record real session, ticket revision, absolute checkout, base/head. A label is not a dispatched session. Missing capability stays explicit.
- Parallel tickets need disjoint files, runtime effects, acceptance, decisions. Isolate or serialize shared ports, databases, caches, services, build output.
- Fast run's tickets share its checkout, one writer per file. Parallel runs (lanes) on one epic: each own worktree, branch, dev ports, merging into the wave's integration branch. Safe tickets: own worktrees. Stop prior operations before handoff. Never overwrite or delete another ticket's state.
- Dependency in same run and branch (Fast): met once items it needs are ticked there. Across branches (every Safe ticket): met by its handed-off result: checked and reviewed commit in this ticket's base (branch from it or, with several dependencies, merge their delivered commits into this branch locally first) plus recorded delivery. No owner merge needed. Dependent ticket waits only for that, never for final proof of its criteria, which comes at the end. Closed status alone proves nothing. Parts without the dependency form own tickets, start at once. Changed dependency scope: revalidate affected analysis and evidence.
