# Goal and session reporting

The preview presents saved facts, not process monitoring or an issue tracker mirror.
Keep the owner-facing facts below in the work record. Never invent dates or completion.

## Goal and next test

In Plan, record one JSON object per line:

```text
**Goal:** {"id":"editor","title":"Edit and export a document","milestones":[{"id":"edit","title":"Edit a document","done":false},{"id":"export","title":"Export a document","done":false}]}
**Next test:** {"title":"Edit a sample document","when":"After saving and recovery checks pass","estimate":"Not estimated","feedback":"Return to this session with what you tried, expected and saw."}
```

- Goal names the agreed outcome. Milestones cover its agreed scope, with stable IDs. Set `done` only after its outcome is demonstrated; reopen it when that result regresses. Keep proof in the build log. Do not add or remove agreed scope to improve the percentage.
- Each session shows its own recorded goal and milestone denominator. Sessions can share a goal; their task counts are never added into a project percentage. Keep shared goal reports consistent at coordination boundaries.
- A plain-text Goal is supported without a percentage. Missing milestones mean scope is unknown, not zero progress. Planned task completion remains a separate measure, never acceptance or release.
- Next test names a concrete result and its prerequisites. Estimate is optional and must carry its basis/window in plain text; missing means no estimate. A dependency is more useful than a guessed countdown.
- Update at plan changes and completed milestones. Record actual test targets with `fast_gate.py try` only; a milestone or completed plan alone never creates a runnable artifact.

## Subsessions

At delegation start, task changes and finish, append or update a JSON line in Build log:

```text
**Session:** {"id":"export-review","title":"Export review","task":"Check file recovery","status":"working","updated":"<ISO timestamp with timezone>"}
```

- Use the actual session ID and current timestamp. Status is `working`, `finished` or `blocked`. Optional `parent` names another reported child ID; absent means this coordinating session.
- Last line for an ID wins. Report every dispatched child, including blocked and completed work. Coordinator owns these lines; delegates report their state to it.
- These are last-reported states, not heartbeat guarantees. Do not refresh timestamps without observing the session. Missing or old reports stay visible as unknown/stale.
- When the host supplies agent snapshots, those also appear with their observation time. Use matching IDs to avoid duplicate reports. Historical hook connection counts are never active child sessions.
- Keep credentials, private content and raw errors out of titles/tasks. The preview rejects malformed metadata and gives a correction message without echoing it.

The overview covers sessions available in this local project's view. Closed sessions are retained for the current day; it is not a durable whole-product history or a remote session inventory. Existing sessions with no metadata remain visible with explicit gaps.

