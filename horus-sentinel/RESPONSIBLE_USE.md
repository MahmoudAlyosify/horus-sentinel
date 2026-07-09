# Responsible Use

HORUS Sentinel is a **defensive, passive open-source intelligence (OSINT) platform**
built for **authorized** analysis only: your own assets, publicly available data,
or subjects you have explicit written permission to assess.

## Design commitments

- **Passive by default.** The platform consumes already-public data. It does not
  attack, exploit, brute-force, deliver payloads, or establish access to any system.
- **Authorization is enforced, not assumed.** Every job runs under a signed
  Rules-of-Engagement (RoE) record validated by the Scope & Authorization Engine.
- **Third-party terms respected.** All external sources are accessed through a
  central Tool Abstraction Layer that enforces rate limits and caching.
- **Chain of custody.** Every finding is traceable to a source and a timestamp.
- **Human-authoritative.** The AI augments an analyst; a human validates every
  report before it is marked final. The system stops at *recommendation*.

## What this tool is NOT

It is not an attack tool, an exploitation framework, or a substitute for expert
judgment in security-critical or life-critical contexts. Outputs are decision
support, not decisions.

Use it to help defenders understand and reduce their own exposure.
