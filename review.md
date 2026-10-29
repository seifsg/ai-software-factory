## Deep Review Report

Candidate: fbf00b444d9a27d59d5cc529bc52a164b37e72fa against origin/main 0425f8e. Read-only independent review of startup selection, canonical/generated resolvers, evaluation bootstrap/metadata, affected fixtures/tests, method sentence and documentation. Compliance, change, security, performance and journey lenses applied. No suites, model calls, browsers or live-project operations run during review.

### Findings

No demonstrated blocking or optional defect in this candidate.

### Verified behavior and scope

- `fast_entry.start` now reaches the existing locked selector for a valid receiptless fresh start. The selected gate creates state afterward; invalid request/open-run handling precedes selection. Resume routing and stored policies remain unchanged. The removed preliminary local inspection was duplicated by `select_locked`'s `inspect_bundle` before receipt publication.
- Canonical `select_locked` inspects retained pins, then returns explicit/legacy selections without remote discovery. Automatic new-run refresh, post-resolution receipt recheck and active-run race check remain. The notice says latest was not checked. Both generated resolver copies are byte-identical to the canonical source.
- Historical test setup explicitly constructs historical state through the internal command; subsequent commands/hooks remain real. These fixtures are not modern startup evidence. Six separate tests use actual public `main`, a real selected Git checkout and real state/receipts, replacing only remote discovery. They cover missing/corrupt/mismatched selection, explicit pin, automatic refresh and historical resume. No existing phase assertions or time limits were weakened.
- Evaluation exports are committed local Git snapshots before canonical explicit selection and model invocation. Snapshot SHA is actual local HEAD, distinct from originating checkout provenance and captured-byte hash. Plain arms receive no selection. Existing scorer/canary/process ownership paths are unchanged. Setup metadata does not affect product scores; `not_observed` remains possible. Matching gate-home records are observations, not authenticated enforcement proof or evidence that all factory steps ran.
- Both arms expose setup time separately; agent `minutes` semantics stay unchanged. Snapshot bootstrap has nonzero cost. Only explicit-pin remote lookup removal is demonstrated as reduced work; no universal startup or end-to-end speedup is established.
- Independent raw evidence in `.factory/checker213/acceptance.md` covers fresh current selection, corrupt/wrong-SHA rejection without state/replacement, zero explicit lookups, retained automatic refresh and old pins, real eval snapshot/gate observation, mirror-only unknown and independent scoring separation. Final CLI and eval replay identify this clean committed source.
- Committed startup guidance is shorter by 15 bytes and removes the redundant manual resolver instruction (compared Git blobs, avoiding working-tree CRLF differences). No new hook, gate phase, browser/reviewer cycle or skill was added. README, install/eval/host documentation and upgrade notes describe changed semantics.

### Limits

Final committed full suite, final criterion receipts, public proof publication and draft PR are parent-owned outstanding delivery steps. This review does not approve a release, installation/adoption, live-project change, model improvement or a general performance claim.

### Verdict

**PASS for the reviewed source, compatibility design and supplied manual evidence.** Overall delivery remains open until the required final suite and handoff evidence are recorded.

G1 PASS: no demonstrated current CLI silent-downgrade path; malformed selection fails before state, old contracts remain explicit.
G2 PASS: pinned/automatic semantics and truthful snapshot identity preserved.
G3 PASS: existing startup is consolidated and repeated explicit discovery removed; no new mandatory quality cycle.
G4 PASS for review scope; full-suite/handoff proof pending, never inferred from focused results.
