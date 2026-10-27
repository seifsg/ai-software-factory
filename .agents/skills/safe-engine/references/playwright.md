# Playwright check helper

Use `skills/safe-engine/scripts/playwright_checks.mjs` from the bundle with your browser/page. It imports no browser package and launches nothing.

- `rendered(locator)` returns visible matches; CSS-hidden copies are excluded. `oneRendered(locator)` requires exactly one, never the first duplicate. Scope by role/name and region from the runtime accessibility snapshot.
- `keyboardTarget(page, locator, maxTabs=20)` tabs from current focus to the unique target; reports whether it arrived and its geometry is on screen. A skip link hidden before focus is not a defect. Reset focus per journey.
- `background(locator)` composites ancestor solid alpha backgrounds. Images, filters, blending, group opacity or unknown canvas yield `known:false`; never guess white or claim contrast passed.
- `iconPaint(locator)` reads masks, images, colors and pseudo-elements. A mask can render with `background-image:none`. Inspect the image; computed styles do not prove appearance.
- `fixedBrowserPage(browser, {instant, timezoneId})` creates a context/page with fixed `Date` before navigation. Give an offset ISO instant and timezone; close the context. `fixedBrowserClock(page, instant)` needs a blank page with that timezone. Timers continue; install the clock before simulated timer controls.

Declare `{"version":1,"journey_tests":["tests/journey.spec.mjs"]}` in a project manifest. Run `node skills/safe-engine/scripts/journey_clock_lint.mjs <manifest.json>`. It rejects direct wall-time reads and missing fixtures; dynamic/ambiguous construction needs review. Only declared files are checked, not every runtime time source.

Give the checker the raw accessibility snapshot, viewport and state. The helper neither computes names nor judges their quality. Inspect transparent overlays, clipping, occlusion and unsupported effects directly.
