# Worktree enrollment

```text
python fast_gate.py enroll-worktree --project <new-worktree> --source <original-worktree> --bundle <reviewed-factory> --reason "<owner authority>"
```

Owner instruction only, for a new Git worktree that inherited the source's tracked run files while the source keeps its open run. It refuses on any local run state, changed inherited files or a source run they do not match.

It archives the inherited files under `.factory/fast/archive/`, writes `.factory/worktree-enrollment.json` and selects the given factory. Then `start` a new key and request; the run links the archive as `inherited` and carries no progress. The source is never written. If enrollment stops midway, keep the archive and diagnose before retrying. Never use `rehome` here.
