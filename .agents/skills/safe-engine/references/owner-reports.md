# Plain owner reports

Use for every coordinator progress update and delegate handback to the owner. Records and tickets retain their identifiers.

1. Name the page or feature, what changed in user words, the next action, worth-it score, estimated time left and who waits on whom. No ticket/criterion codes, lane or branch names, hashes or unexplained abbreviations in the body. Put reference links last.
2. For every reported ticket, show elapsed time, active work and tokens used against planned time/tokens. Label measured, estimated or unavailable with the source. Never allocate a shared session total to individual tickets or invent missing telemetry. Unknown estimates stay unknown.
3. Visual change: include the current picture. Run `report --picture <png>` before sharing any picture, then inspect it. A content check rejects blank/near-blank or corrupt pixels; it cannot judge whether this is the right screen. Convert unsupported images to a supported PNG; never bypass the check with a different extension.
4. Publish through `report --file <json>`. It refuses codes and invalid pictures before replacing the last accepted report. `report --lint <body-file>` checks standalone prose. Validate before sending through the owner's channel; command output alone is not proof of delivery.
5. Exact code-like product names may use a narrow `literal_exceptions` entry with exact text and reason. Never exempt internal references or whole paragraphs. Current pause or terminal state takes priority over the last published report. Reuse pictures only while their current bytes match the accepted identity; changed pictures need a new capture and report. The live view can show current accepted Show captures when no report or Try picture exists.

Input and measurement shapes: the factory's report command documentation. Use `deep-review` worth inputs; no duplicate score formula. Missing worth inputs show unavailable with a reason. Keep raw measurement IDs and provenance in the record; reference links end the owner report.
