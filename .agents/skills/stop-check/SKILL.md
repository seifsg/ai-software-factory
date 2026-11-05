---
name: stop-check
description: "Arms a factory run's Stop check for this session. Use when `safe-factory` says to, before each step."
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: 'Stop: $ARGUMENTS. Read last_assistant_message. Answer ok false only in two cases. One: it opens with a step heading (## then a step number) or a T<n> pre: line, that text did not end an earlier turn, and it lacks "Factory check: may stop": reason "Run the factory check in safe-factory." Two: it has a Gate or Review line not seen earlier and lacking backing (delegate handback; waiver: owner message; cap: 3 failed handbacks): reason "Run that delegate." Anything else: ok true.'
---

Stop check armed. Go on with the step.
