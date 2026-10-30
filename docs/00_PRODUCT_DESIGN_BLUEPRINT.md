# SIH26262 Product Design Blueprint
**Platform**: AICTE Approval Workflow Automation & Institutional Compliance Governance Platform

---

## 1. Problem Definition
The All India Council for Technical Education (AICTE) receives thousands of annual applications across technical institutions across India for New Institution Approvals, Extension of Approval (EoA), Course Additions, Intake Variations, and Closure of Programs.
Currently, regional and central administrative handling faces severe operational challenges:
1. **Opaque Stage Pendency**: Lack of real-time visibility into application dwell time at individual approval stages (Scrutiny, Re-Scrutiny, Expert Visit Committee / EVC, Standing Hearing Committee / SHC, Standing Appellate Committee / SAC).
2. **Disconnected Compliance Governance**: Time-bound undertakings submitted by colleges (e.g., faculty recruitment deadlines, laboratory equipment installation, building completion certificates) often slip past unverified without automated alerting.
3. **Lease & Mandatory Document Expiries**: Land lease deeds, bank guarantees (FDRs), building safety certificates, and fire NOCs expire without proactive institutional and administrative early warning.
4. **Lack of Verifiable Auditability**: High dispute volume requires an immutable, non-repudiable audit trail of who reviewed, returned, verified, or approved each case, accompanied by mandatory recorded reasons for any deficiency.

---

## 2. Goals & Non-Goals

### Goals
- **Unified Workflow Engine**: Route applications dynamically according to configurable workflow templates (`ONLY_SCRUTINY`, `SCRUTINY_EVC`, `EVC_SAC_SHC`), maintaining versioned stage rules and strict preconditions.
- **Tripartite Operational Interface**:
  - **Control Tower**: High-level administrative radar tracking throughput, pendency bottlenecks, regional distribution, and SLA escalations.
  - **Case Workbench**: Action-oriented single-case workbench detailing stage timeline, assigned responsibility, contextual actions, deficiency log, and audit events.
  - **Compliance Radar**: Focused monitoring of time-bound undertakings and document expiry countdowns.
- **Idempotent Background Monitoring**: Automated deadline evaluation with multi-tiered escalations without duplicate notification spam.
- **Strict Role & Jurisdictional Access Control**: Enforce separation of duties (institutions, regional officers, bureau officers, EVC experts, system admins) with strict boundary isolation.
- **Security-by-Design**: Secure document handling (magic byte inspection, randomized storage IDs, protected streaming), CSRF protection, and audit immutability.

### Non-Goals
- **Replacing Legal Statutory Decision-Making**: The system automates workflows and tracks deadlines, but statutory grant of approval remains strictly a human committee determination.
- **Direct Real-World AICTE Gateway Integration**: This is a production-grade synthetic-data hackathon prototype, not an active endpoint on official AICTE national servers.
- **Unchecked Autonomous Statutory Approvals**: Applications cannot auto-approve upon timer expiry. Overdue SLAs escalate to officers rather than making statutory determinations.

---

## 3. Confirmed Hybrid Design Direction
We implement a hybrid architecture synthesizing three complementary paradigms:
```
+-------------------------------------------------------------------------+
|                          SIH26262 CONTROL TOWER                         |
|  - Real-time Stage Pendency   - Regional Heatmap   - Overdue SLA Queue  |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                           CASE WORKBENCH                                |
|  - Application Header & SLA        - Procedural Stage Progression       |
|  - Contextual Permitted Actions    - Mandatory Deficiency Recording     |
|  - Document & Undertaking Vault    - Append-only Audit Timeline         |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                          COMPLIANCE RADAR                               |
|  - Time-Bound Undertaking Tracker  - Lease & NOC Expiry Surveillance    |
|  - Multi-tier Escalation Engine    - Verification Two-Person Control    |
+-------------------------------------------------------------------------+
```

---

## 4. User Personas & Responsibilities

| Role | Operational Scope | Permitted Actions | Prohibited Actions |
| :--- | :--- | :--- | :--- |
| **Institution User** | Own Institution (`institution_id`) | Create & submit application; upload documents; submit undertaking evidence; upload renewed leases. | Access other colleges; approve/verify own filings; alter workflow configurations. |
| **Regional Officer** | Assigned Region (`region_id`) | Conduct scrutiny; record deficiencies; request resubmission; verify evidence; monitor regional pendency. | Access applications from outside assigned region; skip required inspection stages. |
| **Bureau Officer** | Central / Multi-Region Oversight | Cross-regional pendency monitoring; review high-tier escalations; manage inter-regional bottlenecks. | Modify institutional files directly without recorded audit reason. |
| **EVC Committee Member**| Assigned Cases (`application_id`) | Inspect assigned institutions; record scheduling; submit inspection findings and photographic evidence. | Perform scrutiny signoffs; verify land lease legalities. |
| **System Administrator**| Global System Governance | Manage users, regions, and workflow templates; tune SLA warning windows and escalation policies. | Unilaterally alter historical audit records or delete active cases. |

---

## 5. Information Architecture & Navigation

```
[Global Header: Brand, AICTE Seal, Authenticated User Identity, Role Badge, Notification Bell]
  |
  +-- /overview (Control Tower Dashboard: KPIs, Stage Pendency, Overdue Queue, Regional Matrix)
  +-- /applications (Registry Grid: Status, Stage, Region, SLA Countdown, Deep Search & Filters)
  +-- /applications/:id (Case Workbench: Header, Interactive Stepper, Action Panel, Tabbed Details)
  +-- /evc (EVC Operations Hub: Inspection Schedules, Committee Assignments, Findings Logger)
  +-- /compliance (Compliance Radar: Undertakings Ledger, Proof Submissions, Verification Drawer)
  +-- /documents (Document Vault: Lease Deeds, Fire NOCs, Expiry Radar, Renewal Lineage)
  +-- /alerts (Escalations Desk: Priority Triage, SLA Breach Ack/Resolve, Manual Sweep Trigger)
  +-- /audit (System-Wide Audit Journal: Chronological Non-Repudiable Event Stream)
  +-- /config (Administrative Console: Workflow Template Visualizer & SLA Window Editor)
```

---

## 6. Accessibility & Government Design System Principles
- **Color Contrast**: WCAG 2.1 AA compliant ratios across text and actionable elements.
- **Status Redundancy**: Information conveyed through clear semantic labels and distinct iconography, never color alone.
- **Keyboard Navigation**: Focus outlines, logical Tab order across tables and modal workflows.
- **Visual Tone**: Crisp, administrative dignity (Deep Navy `#0A2540`, crisp white backgrounds, subtle slate borders, vibrant status pills).
