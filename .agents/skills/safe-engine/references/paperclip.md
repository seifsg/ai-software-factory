# Paperclip binding

Verbs for the [orchestrated run](orchestrated-run.md) when Paperclip woke you. Its `paperclip` skill owns the API details (headers, payloads, checkout, statuses); follow it for every call below.

| Verb | Paperclip |
|---|---|
| TASK | The issue the wake payload names. Check it out first unless the payload says the harness already did. |
| ASK | One pending `ask_user_questions` interaction on the issue with `resolverPolicy: "human_only"` and `continuationPolicy: "wake_assignee"`, then status `in_review`. |
| OWNER | An interaction answer, or a comment with `authorUserId` set. A comment with `authorAgentId` is evidence. |
| REPORT | A comment on the issue. |
| HANDOFF | A `pull_request` work product on the issue. |
| WATCH | An issue monitor rechecking CI and review every 30 minutes, status `in_review`. A monitor wake with no change reschedules it and ends. |
| SPAWN | A new issue in this issue's project, no `parentId` (a child shares its parent's workspace), assigned to your own agent id, the session prompt as its description, an idempotency key. REPORT its link here. |
| BLOCK | Status `blocked` with `blockedByIssueIds`. Never a person as the unblock owner. |
| FINISH | Status `done` after the merge. |

- An answer that came as a comment: withdraw the pending interaction it covers.
- Skip Paperclip's commit attribution trailer; the run's commit rules apply.
- The wake ends when you exit. Leave the issue in the waiting status above, never `in_progress` without a live path.
