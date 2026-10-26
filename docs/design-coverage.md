# Design coverage

For a design-port ticket, start a new run with `fast_gate.py start --design-port` plus the usual project, key, mode, kind and request arguments. It implies UI and cannot combine with `--no-ui`. Existing runs are unchanged.

Before plan, create the coverage artifact described in [the UX reference](../.agents/skills/ux-quality/references/coverage.md), then:

```text
python skills/safe-engine/scripts/fast_gate.py design --project <project> --input .factory/coverage.json
python skills/safe-engine/scripts/fast_gate.py design --project <project>
python skills/safe-engine/scripts/fast_gate.py design --project <project> --candidate
python skills/safe-engine/scripts/fast_gate.py design --project <project> --review .factory/likeness.json
```

The input freezes screen and element identities, the original denominator, builder identity and PNG reference hashes in the run. Keep JSON and captures under ignored `.factory/`; only statuses and owner decision records change in coverage. No row can disappear to raise the count. A changed reference requires a separately scoped run, not a rewritten ledger.

A fresh judge reads reference/current shots at the same pixel dimensions, theme and state. Its review names every element and its visible differences; it must not be the builder. The gate validates completeness, bytes and candidate freshness. It cannot determine likeness, authenticate identities, or prove an owner authorized a cut. The coordinator must inspect the cited owner answer and the independent judge's raw evidence.

`design --review` requires the build step. It accepts a truthful incomplete review so progress is preserved, but done-run, handoff and close refuse missing or partial elements. Done elements have no unresolved differences; cuts require an owner actor, source and quote. All original elements remain in the denominator. Source changes, including dirty and untracked non-ignored files, or changed reference/capture/review bytes invalidate acceptance. Candidate symlinks and directories such as submodules need explicit manual handling; this command refuses to claim a complete fingerprint for them.

Status cards show completed, partial, missing and cut counts. These are reported design elements, separate from task or goal completion. Status reads only image headers; final gates rehash the evidence. No automated pixel similarity score substitutes for the human comparison.

Safe runs keep their controller lifecycle: attach the inventory to the plan and fresh comparison/captures as candidate-bound manual evidence. This command controls Fast/Lucky runs only.
