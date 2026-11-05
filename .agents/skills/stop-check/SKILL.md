---
name: stop-check
description: "Arms a factory run's Stop check. Only in a run, right before a block or todo line."
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: 'Stop: $ARGUMENTS. Answer ok false only if last_assistant_message: 1. opens with a step heading (## then a step number) or T<n> pre: line whose number no earlier message opened with, and lacks "Factory check: may stop": reason "Run the factory check." 2. has a new Gate or Review line lacking backing (delegate handback; waiver: owner message; cap: 3 failed handbacks): reason "Run that delegate." Anything else: ok true.'
---

Armed.
