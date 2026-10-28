# Independent worktree enrollment

```text
python fast_gate.py enroll-worktree --project <new-worktree> --source <original-worktree> --bundle <reviewed-factory> --reason "<owner authority>"
```

Only on the owner's instruction, for an independent run in a distinct Git worktree inheriting tracked legacy run files. The source keeps its registered open run. Enrollment validates the shared repository, unchanged tracked mirror/receipt/record and source identity, including recorded moves. Local active, lost, closed or unknown state and unrelated receipts refuse.

The command archives every inherited byte and hashed lineage under `.factory/fast/archive/`, records `.factory/worktree-enrollment.json` and selects the explicit factory. Read them back, then use ordinary `start` with a new key and request. Accepted progress never carries into the new run. No source files or source state change. Interrupted enrollment retains evidence: preserve it and diagnose the partial transition before retrying. Never hand-edit lifecycle files or use `rehome` to take over a source that must stay active.
