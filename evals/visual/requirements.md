# Rendered acceptance pilot

Deliver a complete learning page with Welcome, Learn, Progress and Contact
sections, in that order. Every section and its text must be visible. At widths
1280 and 390, sections stay inside the viewport without horizontal overflow,
occupy at least 65% of its width, have at least 100 pixels of height and do not
overlap. Different spacing, typography, borders and valid widths are allowed.

Clicking Complete lesson changes Not completed to Completed. Reload preserves
Completed. Each trial starts in a fresh browser context with empty storage.

- R1: required sections visibly render.
- R2: section geometry meets the stated bounds and order.
- R3: the button performs its stated action.
- R4: reload preserves completion.

The separate expected.json declares which criteria each synthetic candidate
violates. Observation checks receive a page, never candidate names or labels.
A candidate is accepted only when every criterion passes at both widths.
Calibration succeeds only when observed failures exactly match the labels.

This pilot checks specified DOM visibility, geometry and behavior. It does not
grade aesthetic quality, occlusion by arbitrary overlays, accessibility, model
performance or full production readiness. Browser/tool/capture errors are
errors, never acceptance. Screenshots and hashes accompany raw observations in
the output directory; they are evidence, not the acceptance decision.
