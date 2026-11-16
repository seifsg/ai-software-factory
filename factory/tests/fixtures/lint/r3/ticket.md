# slugify maxLength and uniqueSlug

### 📥 Request
> `slugify(title, { maxLength })` in `src/slug.js`: optional `maxLength` (positive integer). Cut the slug to at most `maxLength` chars without leaving a trailing dash, and cut at a dash boundary when one exists inside the limit. Bad `maxLength` (0, negative, non-integer, non-number) throws `RangeError`. No option = today's behaviour.
> New `uniqueSlug(title, existing, options)` in the same file: returns `slugify(title, options)`, or the first of `slug-2`, `slug-3`, ... not in `existing` (an array or a Set). With `maxLength`, the suffix must fit inside the limit too. Empty slug (e.g. title `"!!!"`) throws `RangeError`.
> Tests for every case in `test/slug.test.js`; `npm test` green. (the owner, chat, 2026-11-16)
> Owner on delivery: "This repo has no remote: stop after verify and review (no PR step)." Commit on a branch, never on main.

### 🎯 Purpose & goal
**Purpose:** slugs need a length cap and collision-free variants.
**Goal:** both functions behave as the request says, each case tested.

### ✅ Definition of done
- **A1 (R1):** `slugify` cuts to at most `maxLength`, at a dash boundary when one fits, never ends in a dash.
- **A2 (R1):** `maxLength` of 0, negative, non-integer or non-number throws `RangeError`.
- **A3 (R1):** no option or no `maxLength` gives today's output.
- **A4 (R2):** `uniqueSlug` returns the base slug when free, else first free `slug-N` (N from 2); `existing` is an array or a Set.
- **A5 (R2):** with `maxLength`, base plus suffix fits the limit.
- **A6 (R2):** empty slug throws `RangeError`.
- **A7 (R3):** every case above has a test in `test/slug.test.js`; `npm test` green.

### ☑️ Checklist
- [x] T1 slugify accepts {maxLength} and cuts at a dash boundary (A1 A2 A3 A7)
- [x] T2 uniqueSlug returns a free slug that fits maxLength (A4 A5 A6 A7)

### 🚦 Progress / next
Status: Dev done. Priority: P2. Local only, no remote.

### 📝 Activity
- 2026-11-16 Claude: created, local ticket (no tracker, no remote).
- 2026-11-16 Claude: To do -> In progress, build starts (branch feat/slug-maxlength-unique).
- 2026-11-16 Claude: In progress -> Dev done, all items ticked, A1 to A7 proven at 3c57049; no PR (owner: no remote, stop after verify and review).
- 2026-11-16 Claude: step 8 review fix round R1 (tests only) at 2ffc440; non-object options stay a TypeError (decision F2, reversible by owner).

### 🗂 Deferred (pending owner)
LOW findings left after step 8 review (@2ffc440). Owner: the owner. Revisit: next change to src/slug.js.
- Merge the 3 message tests that repeat existing calls into the existing assertions; move the slugify test next to the other slugify tests.
- Assert the D3 and title messages (`options must be an object`, `title must be a string`).
- Split the 112-character slugify comment line (src/slug.js:13) into two lines, and the 135-character line at test/slug.test.js:96.
- Decision F2 (reversible): non-object options stay a TypeError, so arr.map(slugify) throws; owner may choose to treat them as none.
