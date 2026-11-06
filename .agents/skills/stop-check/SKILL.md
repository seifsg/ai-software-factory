---
name: stop-check
description: "Arms a factory run's Stop check. Only in a run, before a block or todo line."
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: 'Stop: $ARGUMENTS. Answer ok false only if last_assistant_message opens with a step heading (## then a step number) or T<n> pre: line whose number no other message opened with, and lacks "Factory check: may stop": reason "Run the factory check." Anything else: ok true.'
        - type: prompt
          prompt: 'Stop: $ARGUMENTS. Answer ok false only if last_assistant_message has a new Gate or Review line lacking backing (only another message counts: delegate handback; waiver: user message granting it; cap: 3 failed handbacks): reason "Run that delegate."; or is backed and lacks "Factory check: may stop": reason "Run the factory check." Anything else: ok true.'
---

Armed.
