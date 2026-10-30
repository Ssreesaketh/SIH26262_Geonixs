---
description: Regulatory safeguards and AICTE Approval Process Handbook conventions for SIH26262
always_on: true
---

# Product and Regulatory Rules

1. **Regulatory Reference Source**:
   - Reference the official AICTE Approval Process Handbook (APH) principles where verified.
   - Any rule, timeline, or escalation not directly sourced from published AICTE gazettes must be documented in `docs/REGULATORY_ASSUMPTIONS.md` as a configurable prototype parameter.

2. **No Statutory Presumption**:
   - Successfully completing scrutiny or an EVC stage does NOT equal statutory grant of approval. Approval requires authorized Standing Hearing Committee (SHC) / Executive Committee statutory decision recording.
   - An expired deadline or SLA breach flags an escalation or alert; it NEVER causes automated statutory rejection without due administrative process.

3. **Human In The Loop**:
   - Machine logic, timers, and automated checks cannot substitute for physical/virtual inspection findings or scrutiny officer sign-offs.
   - Document verification requires a human verifier ID and verification remarks.

4. **Workflow Immutability**:
   - An active application is bound to the version of the workflow template under which it was submitted (`workflow_version`). Updates to workflow templates do not retroactively invalidate or mutate historical transitions.
