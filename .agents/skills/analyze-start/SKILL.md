---
name: analyze-start
description: "Analyzes a feature, defect, refactor or PR before any coding: reads the actual code, explains purpose and success, maps every consumer and draws ASCII flow charts. Use when work starts on existing or new code, or when asked to analyze. Analysis only."
---

# Analyze Start

Analyze the feature in question thoroughly.
Do not code unless told.

Do a deep and thorough analysis to understand the feature provided. Educate yourself on it well. Then explain it back to me in full details.
Skim details that don't matter. Focus on core logic.
However, also focus on all other aspects linked to this feature and know everywhere else is being called or used.

Use ASCII charts to explain.

Explain what it does, why it exists, and what success means.

Name the next complete useful result, required dependencies and shared constraints. Keep the whole requested outcome visible.
Read actual code. Verify claims. Label guesses and unknowns.
Name where outside data enters, and which invariants are enforced or only assumed. Trace each defect or edge case to its design cause.
For a PR, check each claimed behavior against code and actual wiring.

For extensions, state what data can change and what needs code. Plan final proof with content absent from the build.

Do not code yet. This is fully analysis phase.
