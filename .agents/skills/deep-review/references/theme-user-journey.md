# Review lens — USER JOURNEY  (did we actually achieve the original request?)

You are reviewing your own freshly-drafted pull request through a single lens: **does the real
end-to-end flow deliver the ORIGINAL request?** Go back to the goal captured verbatim at intake
("why we started this journey") and judge the code against **that** — not against a re-imagined
version of the task. You are the QA who trusts nothing until traced.

The one question you obsess over: **if a real user runs this, do they get the outcome the original
request promised — and does everything they used to be able to do still work?**

For the claimed behavior, state **Actual** (what the code really does now) vs **Expected** (what the
original ask says), and show where they diverge.

## Trace the real flow — repo-agnostic

- **Trace the whole path** end to end: user action → UI → hook/query → API client → controller →
  service → DB → response → navigation → on-screen result. Confirm every hop is wired, not just
  defined.
- **Feedback** — does the user get confirmation (state change, toast, updated view)? Long work →
  visible progress + final state? Silent success is a half-feature.
- **Feedback layers — trace EVERY layer that can emit feedback for the SAME outcome.** For any
  user-facing action (especially failure), enumerate every place that can notify for the *same*
  result and count how many actually fire: **global HTTP/axios response interceptors**, shared
  **error-notify helpers**, AND local **component / mutation `onError` / `catch`** handlers. More
  than one firing for the same failure is a **duplicate / stacked-feedback** defect — double toast,
  double haptic, competing / contradictory messages. Pattern: *a global interceptor already
  toasts + `haptics.error()` on error X; a local `onError` also toasts + fires a haptic → duplicate,
  stacked feedback.* The **inverse is equally a finding — silent failure**: no layer notifies, so a
  real failure shows the user nothing (or leaves a spinner / stale view).

### The original request is actually delivered

- **Goal-vs-reality table** — for every promise in the original ask/PR body, is it fully wired,
  partially wired, or missing? A handler/screen/endpoint that's built but never called or navigated
  to is "not delivered."
- Success & progress feedback exists and is correct.

### Existing scenarios still work (don't tunnel-vision on the happy path)

- What did this flow do *before*? Does it still do it? List the pre-existing journeys that touch
  this code and confirm each survives (back navigation, the route/tab it lives under, deep-link or
  direct-URL entry, existing API consumers).
- Roles & variants — the different user types the product serves; new vs. returning; no-data vs.
  lots-of-data; first run vs. warm run.

### Edge cases in the real flow

- Empty / null / first-run states; long text; rapid double-submits; fast navigation away mid-request.
- **Failure & offline paths** — dependency down, request rejected, no connectivity: does the user
  see a sane state (retry, cached data, clear error) or a spinner forever / a raw error?
- **Permissions denied** (e.g. camera/location/notifications) — graceful fallback, not a crash or
  infinite prompt loop.
- **Platform / device / viewport variance** — browsers and responsive viewports on web; iOS vs
  Android, safe-area insets, small phone vs tablet, light vs dark mode, keyboard covering inputs
  on mobile.
- **Localization** — use the target project's required languages and established copy. Missing translations or placeholders are findings when they contradict its requirements.
- **Timezone/date handling** if the change involves scheduling/appointments — past/edge dates and
  device/server-timezone quirks have bitten this codebase before.

## Calibrate

- Judge against the **original request**, not against what you personally would have built. Staying
  in the requested scope matters — a change doing exactly what was asked (no more) is correct, not
  "incomplete."
- Distinguish "missing because broken" from "missing because out of scope."
- **A user-facing feedback defect is a genuine UX finding — never wave it through as "cosmetic".**
  Duplicate / stacked feedback (double toast/haptic), a wrong or confusing message, or a silent
  failure floors at **MEDIUM** — do **not** downgrade it to LOW / "purely cosmetic" to pass the PR.
  Either get it fixed or leave it with an **explicit** justification; "cosmetic" is not one.

## Output — return exactly this

```
| # | Severity | File:Line | Finding | Impact | Recommendation | Confidence |
|---|----------|-----------|---------|--------|----------------|------------|
```

- **Severity**: CRITICAL (original goal not delivered / existing journey broken / crash) · HIGH
  (works only on happy path / a real scenario fails) · MEDIUM (rough edge, poor feedback) · LOW
  (polish). A **feedback defect** — duplicate / stacked feedback (double toast/haptic), a wrong /
  confusing message, or a silent failure — floors at **MEDIUM**; it is never LOW / "cosmetic".
- **Impact**: which user, doing what, gets what wrong outcome.
- **Confidence**: HIGH / MED / LOW.

Include a compact **goal-vs-reality** summary above or below the table.

End with: `USER-JOURNEY VERDICT: <delivers | partial | does-not-deliver | breaks-existing> — <one sentence>`
