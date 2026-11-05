---
name: stop-check
description: "Arms a factory run's Stop check. Only in a run, right before a block or todo line."
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: 'Stop: $ARGUMENTS. Answer ok false only if last_assistant_message: 1. has a new Gate or Review line lacking backing before it (delegate handback; waiver: owner message; cap: 3 failed handbacks): reason "Run that delegate." 2. opens with a step heading (## then a step number), Gate line or T<n> pre: line whose number or letter no message before it opened with: reason "Run the factory check." Anything else: ok true.'
---

Armed.
