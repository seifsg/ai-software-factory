# PR layout

Use the project's template first. Include applicable blocks below; keep purpose, context and progress outside Before/After. A cold reader must understand the result without the chat or diff.

**Title:** `<type>(<scope>): <concrete change and outcome>` in the reader's language; explain necessary jargon.

## Sections

```text
<header: requester, deciders, real author; original or adaptation>
## 🎯 Purpose & goal      problem, intended result, clickable ticket
## 🎬 Before & after      one ### per outcome, observed proof
## 📍 Context             base/branch, sources, prior work, unknowns
## 🔧 What & why          approach and reason
## 🔀 Flow                branches, failure, recovery
## 🧩 Design / files      options; NEW/M/D paths and purpose
## 🧱 Guards / scope      findings, limits, follow-ups
## ✅ Verification        criterion, change, exact-candidate proof, gap
## 🚦 Progress / next     done, blockers, review state, human step
## 📝 Adjustment history  append WHAT / WHY / WHO / result
---
<last line from credit.md>
```

## Outcome proof

Before/After follows purpose. Name outcomes by their effect, never a file/path. Every changed view/state and affected journey maps to an outcome; shared proof uses captions or timestamps.

```text
### <outcome>
**Visual:** yes
**Journey:** yes
**Before:** <observed condition, base sha>
![before](https://<host>/before.png)
**After:** <observed result, head sha, criterion>
![after](https://<host>/after.png)
**Video:** [<journey, 00:00-00:35>](https://<host>/journey.mp4)
```

- Each outcome declares `**Visual:** yes` or `**Visual:** no (<reason>)`, and `**Journey:** yes` or `**Journey:** no (<reason>)`. A UI run needs a visual outcome. Shared backend changes still show affected UI journeys.
- Visual yes: distinct Before/After screenshots under those labels, or a two-column `| Before | After |` image table. Captions name state, base/head and criterion. New UI uses the prior entry/empty state labeled "did not exist". Prose/video never replaces a required pair.
- Journey yes: `**Video:**` with an HTTPS mp4/webm/mov link or HTML video for an extensionless upload. Shared clips name each journey's start/end timestamps; GIF/still previews do not suffice.
- `**Media waiver:** screenshots | <exact owner request> | <source>` applies only to its outcome. Scope is screenshots, video or all; no implied waiver of other media or truthful proof.
- Nonvisual: matched request/response, status, log or command output under Before/After, or `**Before → After:** <same input, base/head, criterion>` and a diff block. A new result says "did not exist". No waiver for server/internal work without affected UI journeys.
- Demo context states candidate, isolated fixture/reset, viewport/environment, coverage and limits. Media access and full capture rules: [media proof](media-proof.md).

```diff
  200 OK
- {"theme":"light"}
+ {"theme":"dark"}
```

## Verification and writing

- Map every confirmed criterion and checklist item to proof or a gap. Include confirmed ticket revision/digest, dependencies and integration state; bind evidence to the pushed candidate. Name unverified work.
- Link the triggering discussion. Give needed request, decisions/reasons, current state, remaining work and blockers inline; links are an audit trail, not missing context.
- Checked, reviewed, merged and released remain distinct. Name the next visible result; acceptance stays open. Keep adjustment history for the PR's life.
- Use measured facts, active verbs, consistent terms, short bullets and narrow tables. Diagrams use code blocks; variant comparisons use tables. Emojis label sections; fold long machine data.
- No em dashes, filler, slogans, invented benefits, tests, visuals, authorship or consent. Verify names, numbers and units. Never copy example results.
- Final read: can a new reviewer explain what/why/before/after/next, open every outcome's proof and find each requested detail?
