# Playwright check helper

Use the bundle's `skills/safe-engine/scripts/playwright_checks.mjs` with an existing isolated page. It imports no browser package and launches nothing.

- `rendered(locator)` returns visible matches. `oneRendered(locator)` requires exactly one; it never selects the first duplicate. Scope by actual role/name and region from the runtime accessibility snapshot. Responsive copies hidden with CSS are excluded.
- `keyboardTarget(page, locator, maxTabs=20)` tabs from the current position until the unique target gets focus. Its result includes whether it reached the target and whether the focused geometry is on screen. A skip link normally hidden before focus is not itself a defect. Reset focus before each independent journey.
- `background(locator)` composites solid alpha backgrounds through ancestors. Unsupported images, filters, blending, group opacity or an unspecified canvas yield `known:false`; do not guess white or claim contrast passed.
- `iconPaint(locator)` reads masks, background images, colors and pseudo-element content. A mask can draw an icon with `background-image:none`. Inspect the rendered image; computed styles alone do not prove the asset looks correct.

Capture names with the runtime's accessibility snapshot, including viewport and state. Supply that raw snapshot to the checker. The helper neither computes accessible names nor judges their quality. A transparent overlay, clipping, occlusion or unsupported effect may still need direct inspection.
