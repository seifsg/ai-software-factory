# Fixed browser time

Use Playwright 1.45 or newer. Import `fixedBrowserPage` from the resolved bundle's
`skills/safe-engine/scripts/playwright_checks.mjs`. Supply the existing browser;
the helper creates an isolated context and fixes `Date` before navigation.

```javascript
const {context, page} = await fixedBrowserPage(browser, {
  instant: '2025-04-05T12:30:00Z', timezoneId: 'UTC'
});
try {
  await page.goto(appUrl);
  // Exercise the actual journey and assert its fixed expected state.
} finally {
  await context.close();
}
```

`fixedBrowserClock(page, instant)` supports an existing blank page whose context
already has the intended timezone. Both helpers reject navigation before setup.
Timers continue to run. Install Playwright's clock before timer-control calls
when a journey needs simulated timer progression. Never change the host clock.

Declare the journey source files relative to a project-local manifest:

```json
{"version":1,"journey_tests":["tests/shipment.journey.mjs"]}
```

From the factory checkout, run:

```text
node skills/safe-engine/scripts/journey_clock_lint.mjs <manifest.json>
```

The scoped lint rejects missing fixed-page fixtures and direct wall-time reads
such as `Date.now()` and `new Date()`. Literal fixed dates and monotonic duration
measurement remain valid. It inspects only declared files, not the application's
whole dependency graph. Unsupported dynamic construction requires manual review;
a passing static check does not prove every possible runtime time source.
Ambiguous slash contexts, nested templates/regex classes and Unicode regex sets
also require manual review. Simplify the expression before rerunning the lint.

During Look and fixes, first use the changed behavior, then run mapped affected
tests. Record the command and its changed-input mapping in the plan. If mapping
is unknown, choose the tests manually with a reason; `tests/run.py --changed` can
fall back to the complete suite, which is not narrow feedback. The declared full
suite remains in Prove after the current UI Show checkpoint and final manual use.
