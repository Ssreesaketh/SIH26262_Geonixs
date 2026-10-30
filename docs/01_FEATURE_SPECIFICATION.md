# SIH26262 Feature Specification

---

## Feature A: Application Management & Workflow Engine
- **Purpose**: Manage end-to-end lifecycle of technical institution applications from initial drafting to final statutory committee disposition.
- **Primary Users**: Institution Users, Regional Officers, Bureau Officers.
- **Inputs**: Institution ID, Application Type (New Institution, Extension of Approval, Intake Variation), Configured Workflow Template ID, supporting statutory documents.
- **State Machine**:
  - Operational statuses: `DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `DEFICIENCY_RETURNED`, `STAGE_COMPLETED`, `WITHDRAWN`.
  - Statutory statuses: `NOT_RECORDED`, `RECOMMENDED_APPROVAL`, `RECOMMENDED_REJECTION`, `HEARING_SCHEDULED`.
- **Preconditions**:
  - Cannot transition without assigned actor possessing permitted role.
  - Return for deficiency requires non-empty `reason` string.
  - Advancing requires that all mandatory stage documents/checklists are fulfilled.
- **Acceptance Criteria**:
  - Application created with auto-generated unique identifier (e.g. `APP-2026-AICTE-1001`).
  - Stage entry updates `stage_entered_at` and computes `stage_due_at` based on workflow SLA configuration.
  - Every transition writes an audit record in the same atomic database transaction.

---

## Feature B: Control Tower Dashboard
- **Purpose**: Provide operational visibility into system-wide and regional throughput, bottlenecks, and overdue SLAs.
- **Primary Users**: Bureau Officers, Regional Officers, System Administrators.
- **Inputs**: Filter parameters (Region ID, Workflow Type, Date Range).
- **Outputs**:
  - Total Active Applications, Applications Approaching SLA, Applications Overdue.
  - Stage-wise distribution bar/count breakdowns (Scrutiny, Re-Scrutiny, EVC, SAC/SHC).
  - Regional pendency table showing pending counts and critical alerts.
  - Urgent Action Queue prioritized by SLA breach severity.
- **Acceptance Criteria**:
  - Metrics are computed on-the-fly from database records using SQL aggregations.
  - Regional Officers view aggregated numbers strictly scoped to their assigned jurisdiction.

---

## Feature C: Case Workbench
- **Purpose**: Unified workspace for inspecting and acting on a single application.
- **Primary Users**: Regional Officers, Scrutiny Committee, Institution Applicants.
- **Outputs**:
  - Header: Application No, College Name, Region, Current Stage, Days in Stage, SLA Countdown badge.
  - Procedural Stage Stepper: Visual representation of workflow progress with active/completed/returned markers.
  - Action Panel: Contextual buttons dynamically enabled based on user role and permitted transitions.
  - Tabbed Workspace:
    1. Documents (Upload, Review, Download).
    2. EVC Inspection (Scheduling, Roster, Findings).
    3. Undertakings (Time-bound conditions, Evidence).
    4. Audit Trail (Chronological, immutable timeline).
- **Acceptance Criteria**:
  - Unauthorized actions display clear explanatory messages rather than silently failing.
  - Returning a case triggers a modal requiring a deficiency explanation and updates status to `DEFICIENCY_RETURNED`.

---

## Feature D: Expert Visit Committee (EVC) Scheduling & Monitoring
- **Purpose**: Coordinate expert peer inspections, committee logistics, and inspection observation tracking.
- **Primary Users**: Regional Officers, EVC Committee Members.
- **Inputs**: Target Inspection Date, Assigned Experts (Chairman, Subject Experts), Inspection Mode (Physical / Virtual).
- **Outputs**:
  - EVC event schedule record with deadlines.
  - Observation logs, geo-tagged photograph references, and preliminary committee findings.
- **Acceptance Criteria**:
  - System enforces minimum advance notice window according to configured parameters.
  - Committee findings submission marks EVC stage as ready for regional scrutiny closure.

---

## Feature E: Time-Bound Undertakings & Compliance Evidence
- **Purpose**: Track institutional conditional commitments (e.g., land conversion, laboratory equipment delivery, faculty appointments).
- **Primary Users**: Institution Applicants (submitter), Regional Officers (verifier).
- **Inputs**: Condition description, mandatory due date, documentary proof attachment.
- **State Machine**: `PENDING` -> `SUBMITTED` -> `VERIFIED` or `RETURNED_FOR_CORRECTION`.
- **Acceptance Criteria**:
  - College submitting proof moves status to `SUBMITTED`; does NOT auto-verify.
  - Verification strictly requires an authenticated Regional Officer, recording `verified_by` and `verified_at`.

---

## Feature F: Lease & Prescribed-Document Validity Radar
- **Purpose**: Safeguard against expired registered land lease deeds, building safety certificates, and fire safety NOCs.
- **Primary Users**: Institution Applicants, Compliance Monitoring Cell.
- **Inputs**: Document Type, Registered Expiry Date, Issuing Authority.
- **Outputs**:
  - Validity status: `VALID`, `EXPIRING_SOON` (within warning window), `EXPIRED`.
  - Renewal chain linking new submission to prior document (`renewal_of_id`).
- **Acceptance Criteria**:
  - Document nearing expiry within 90/60/30 days automatically registers in Compliance Radar.
  - Renewal submission retains historical record without in-place overwrite.

---

## Feature G: Idempotent Automated Deadline Engine & Escalations
- **Purpose**: Proactively identify approaching and breached deadlines across application stages, EVC visits, undertakings, and document expiries.
- **Primary Users**: Background service / Bureau Officers.
- **Trigger**: Single-instance background loop OR authenticated endpoint (`POST /api/v1/alerts/check`).
- **Deduplication Strategy**: Unique composite key `deduplication_key` formatted as `{entity_type}:{entity_id}:{alert_type}:{escalation_level}`.
- **Escalation Hierarchy**:
  - Warning (Level 1): To Institution and Assigned Scrutiny Officer.
  - Overdue (Level 2): Escalated to Regional Director.
  - Critical SLA Breach (Level 3): Escalated to Bureau Officer / Central AICTE.
- **Acceptance Criteria**:
  - Executing deadline sweep 100 times in a row creates notifications exactly once per threshold tier.
  - Full acknowledgement and resolution workflow with recorded timestamps.

---

## Feature H: Immutable Transactional Audit Trail
- **Purpose**: Complete non-repudiation and accountability across all regulatory interactions.
- **Logged Events**: Creation, submission, transitions, deficiency returns, resubmissions, document uploads, verifications, EVC schedules, SLA alerts, administrative configuration adjustments.
- **Attributes**: `id`, `application_id`, `actor_user_id`, `actor_role`, `action`, `from_stage`, `to_stage`, `reason`, `metadata`, `created_at`.
- **Acceptance Criteria**:
  - Zero application-level delete or update endpoints.
  - Direct read access for authorized audit and review roles.
