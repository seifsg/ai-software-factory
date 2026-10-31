# Plain progress reports

`python skills/safe-engine/scripts/fast_gate.py report --project <folder> --file <json>` validates and publishes the latest owner report. Use `--lint <body-file>` for standalone body prose or `--picture <png>` before sharing an image. Files must stay inside the project. Reports require an open run and tickets already recorded in its Tickets section. Invalid input preserves the last accepted report.

Each report has `version: 1` and `items` (1 to 100). An item has its HTTPS `ticket` URL, plain `feature`, `changed`, `next`, `waiting`, `time_left` (a stated estimate), boolean `visual`, `worth`, and `spend`. A visual item requires `picture: {"path":".factory/fast/shots/result.png","caption":"Shipment states are labelled"}`. The gate checks current bytes and copies scoped immutable previews for the view.

`worth` is the same finding input used by [worth-it assessment](worth-it.md), or `{"unavailable":"No assessment supplied"}`. Scores are out of seven; required work remains required.

`spend` has five entries: `elapsed_minutes`, `active_minutes`, `tokens`, `planned_minutes`, `planned_tokens`. Each has a `status` (measured, estimated, unavailable), `value`, and `source`. Available values are nonnegative finite numbers; add `scope` equal to the item's ticket URL and a stable `measurement` identity. Planned values must be estimated. The same measurement cannot be attributed to two tickets. Shared-session measurements must be reported as unavailable per ticket until actually attributable.

```json
{"status":"unavailable","value":null,"source":"Host supplies only a session total","reason":"Per-ticket usage is unavailable"}
```

An available measurement looks like this; the numbers are illustrative, not collected automatically:

```json
{"status":"measured","value":12,"source":"Dedicated ticket timer","scope":"https://example.com/issues/12","measurement":"ticket-timer-12"}
```

The command does not collect model telemetry or estimate missing consumption. Keep measured, estimated and unavailable values distinct. A report's timestamp is publication time. A current pause question or closed state takes priority over the last published report. Pending helpers or invalid wait receipts hide report directions. After completion, a newly published report restores its next action and waiting state; the helper result stays visible. Reused pictures appear only while their bytes match the accepted hash; a changed picture needs a fresh capture and report. Without a separate report or Try picture, the live view can show accepted Show captures while their source and report identities remain current.

Body lint detects issue/criterion/task codes, lane names, common branch prefixes and 7–40 character hexadecimal hashes. Optional top-level `literal_exceptions: [{"text":"A3","reason":"Exact product model name"}]` permits only that exact code-like literal. It does not authorize hiding internal references. References remain links at the end; raw provenance stays in the protected report record.

The dependency-free picture check supports static, non-interlaced 8-bit RGB, RGBA and grayscale PNGs, at most 16 MiB and 8 million pixels. It validates chunk checksums, bounded decompression and decoded contrast: at least 32 contrasting pixels and one per 10,000 canvas pixels. It rejects uniform, transparent, near-uniform and tiny-noise captures while retaining sparse real text. Unsupported palette/animation formats need conversion to a supported PNG. This is a content heuristic, not semantic validation, likeness review or accessibility approval. Human inspection still applies.

The same check protects Show/design pictures, screenshot capture, report publication and image Try targets. Supported image Try files are `.png`; JPEG, GIF, WebP, SVG, BMP, TIFF and AVIF extensions receive a conversion error. Existing non-image Try artifacts remain unchanged. Successful PNG checks may reuse a bounded, authenticated validation record under the local gate home when the current bytes, validator and dimensions agree. Missing, altered or unwritable cache data causes a full check. The cache cannot replace human inspection, report hash checks or independent likeness review. Remote images must be obtained through an authorized source and checked locally before sharing; the gate cannot intercept arbitrary external chat tools.
