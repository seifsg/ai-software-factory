---
name: stop-check
description: "Arms a factory run's Stop check. Use only in a run, before each step."
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: 'Stop: $ARGUMENTS. Answer ok false only if last_assistant_message: 1. opens with a new step heading (## then a step number) or new T<n> pre: line, and lacks "Factory check: may stop": reason "Run the factory check in safe-factory." 2. has a new Gate or Review line lacking backing (delegate handback; waiver: owner message; cap: 3 failed handbacks): reason "Run that delegate." Anything else: ok true.'
---

Armed. Go on.
