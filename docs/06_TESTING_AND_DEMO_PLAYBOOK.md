# SIH26262 Testing and Demonstration Playbook

---

## 1. Five-Minute Executive Demonstration Script

### Minute 0:00 – 0:45: Control Tower (Operational Command)
- **Action**: Log in as Regional Officer (`officer.north@aicte.gov.in`).
- **Showcase**:
  - Live Control Tower KPIs showing total active applications, stage dwell times, and overdue cases.
  - Stage-wise pendency distribution highlighting Scrutiny and EVC backlogs.
  - Regional workload matrix demonstrating server-enforced geographical jurisdiction.
  - Urgent Escalation Queue highlighting applications breaching stage SLA windows.

### Minute 0:45 – 1:45: Case Workbench & Deficiency Workflow
- **Action**: Open application `APP-2026-AICTE-1002` (Northern Institute of Technology).
- **Showcase**:
  - Interactive Workflow Progression Stepper (Submission -> Scrutiny -> EVC -> SHC).
  - SLA timer badge showing remaining hours before Level 2 escalation.
  - Click `Return for Deficiency`. Note that submitting without remarks is rejected.
  - Enter: "Municipal Water NOC missing from Document Annexure IV; building plan lacks fire egress clearance."
  - Confirm return. Observe instant status change to `DEFICIENCY_RETURNED` and instant creation of an audit entry in the timeline.

### Minute 1:45 – 2:30: EVC Scheduling & Monitoring
- **Action**: Navigate to `EVC Schedule` (`/evc`).
- **Showcase**:
  - View application `APP-2026-AICTE-1004` requiring EVC inspection.
  - Schedule an inspection for a target date with an assigned committee (Chairman + 2 Subject Experts).
  - Submit preliminary committee observations and photographic verification evidence.

### Minute 2:30 – 3:30: Compliance Radar & Lease Expiry Tracking
- **Action**: Navigate to `Compliance` (`/compliance`) and `Documents` (`/documents`).
- **Showcase**:
  - Review an unfulfilled institutional undertaking (`UND-2026-001` - AI & Robotics Lab Setup).
  - Switch to Institution User session (`principal@zenith.edu.in`) and submit equipment invoices and geo-tagged lab photos. Status becomes `SUBMITTED` (demonstrating that submission DOES NOT auto-verify).
  - Switch back to Officer session and click `Verify Undertaking`. Enter official verification remarks to transition status to `VERIFIED`.
  - Open `Documents` view and inspect `Registered Land Lease Deed` expiring in 14 days (highlighted with Amber alert).
  - Execute `Renew Document` by uploading a renewed 30-year lease deed. Demonstrate that historical expired document is preserved as `SUPERSEDED` while the new deed enters the verification queue.

### Minute 3:30 – 4:30: SLA Engine & Hierarchical Escalations
- **Action**: Open `Alerts & Escalations` (`/alerts`).
- **Showcase**:
  - Trigger manual SLA sweep button (`POST /api/v1/alerts/check`).
  - Demonstrate idempotency: repeated clicks report 0 new alerts because identical alerts are deduplicated via composite key.
  - Review an escalated Level 3 Critical breach where an institution has been delayed past statutory notice windows.
  - Acknowledge and resolve an active alert with an administrative note.

### Minute 4:30 – 5:00: Accountability & Non-Repudiable Audit Journal
- **Action**: Navigate to `Audit Trail` (`/audit`).
- **Showcase**:
  - Filter events by application `APP-2026-AICTE-1002`.
  - Walk the evaluators through the chronological, non-repudiable audit journal capturing every action: creation, submission, scrutiny review, deficiency return, evidence upload, and official verification.
  - Highlight that there are zero update or delete endpoints for audit records, upholding administrative integrity.

---

## 2. Seeded Demonstration Scenarios

| Scenario # | Entity Reference | Initial Condition | Intended Demo Interaction |
| :--- | :--- | :--- | :--- |
| **Scenario 1** | `APP-2026-AICTE-1001` | Fresh submission in `SCRUTINY` stage | Advance to next stage (`EVC` or `APPROVAL_REVIEW`) |
| **Scenario 2** | `APP-2026-AICTE-1002` | Under review in `SCRUTINY` | Return for deficiency with mandatory remarks |
| **Scenario 3** | `APP-2026-AICTE-1003` | Resubmitted after deficiency correction | Finalize scrutiny signoff |
| **Scenario 4** | `APP-2026-AICTE-1004` | Awaiting EVC scheduling | Assign committee experts and scheduled inspection date |
| **Scenario 5** | `UND-2026-001` | Undertaking due in 48 hours | Submit evidence as institution; verify as officer |
| **Scenario 6** | `UND-2026-002` | Undertaking overdue by 5 days | Triggers Level 2 escalation alert to Regional Officer |
| **Scenario 7** | `DOC-2026-001` | Land lease expiring in 15 days | Displayed in Compliance Radar; upload renewal document |
| **Scenario 8** | `DOC-2026-002` | Fire Safety Certificate expired 10 days ago | Critical warning alert; trigger renewal workflow |

---

## 3. Automated Test Scenarios

### Workflow Engine Tests:
- Valid transition from `DRAFT` to `SUBMITTED`.
- Transition rejection if caller has unauthorized role.
- Deficiency return rejection if reason is blank or whitespace.
- Verification that advancing stage recalculates `stage_due_at` and appends an audit event atomically.

### Deadline Engine Tests:
- Correct classification into `ON_TRACK`, `UPCOMING`, and `OVERDUE`.
- Verification that running the evaluation check twice generates zero duplicate notifications.
- Escalation level incrementation upon repeated SLA breach.

### Security Boundary Tests:
- Institution User cannot read or modify another college's application.
- Regional Officer cannot access records belonging to another region.
- Unauthenticated requests receive HTTP 401 Unauthorized.
- Directory traversal attempts in file upload/download are blocked.
