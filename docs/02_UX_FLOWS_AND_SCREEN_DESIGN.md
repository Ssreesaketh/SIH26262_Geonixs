# SIH26262 UX Flows and Screen Design

---

## 1. Global Navigation Architecture
The interface implements an accessible administrative layout consisting of:
- **Top Bar**: Government AICTE Emblem, Portal Title, Regional Scope Indicator, System Date (UTC/IST), Notification Indicator with unread badge, User Profile menu with active role badge.
- **Sidebar**:
  - `Overview` (Control Tower)
  - `Applications` (Master Registry & Workflows)
  - `EVC Schedule` (Inspection Operations)
  - `Compliance` (Undertakings & Evidence)
  - `Documents` (Leases, Certificates & Expiry Radar)
  - `Alerts & Escalations` (SLA Triage Desk)
  - `Audit Trail` (Append-Only Event Stream)
  - `Workflow Config` (Admin Rules & Deadlines)

---

## 2. Text-Based Wireframes

### Screen 1: Control Tower (`/overview`)
```
+--------------------------------------------------------------------------------------------------+
| AICTE Portal Header  | Scope: Northern Region  | Current Time: 27 Oct 2026, 19:15 | User: R. Sharma |
+--------------------------------------------------------------------------------------------------+
| [NAV] Overview | Applications | EVC | Compliance | Documents | Alerts (3) | Audit | Config        |
+--------------------------------------------------------------------------------------------------+
| CONTROL TOWER OPERATIONAL RADAR                                            [Trigger SLA Sweep]    |
|                                                                                                  |
| [ TOTAL ACTIVE: 42 ]   [ STAGE OVERDUE: 4 ]   [ UPCOMING SLA (48h): 7 ]   [ EXPIRED LEASES: 2 ]   |
|                                                                                                  |
| +-----------------------------------------------+ +---------------------------------------------+ |
| | STAGE-WISE PENDENCY                           | | REGIONAL WORKLOAD BREAKDOWN                 | |
| | Scrutiny:       ========== (18)               | | Northern Region:   ======== (14)            | |
| | Re-Scrutiny:    ===== (7)                     | | Western Region:    ========== (18)          | |
| | EVC Scheduled:  ==== (6)                      | | Southern Region:   ===== (10)               | |
| | SAC / SHC:      === (3)                       | |                                             | |
| +-----------------------------------------------+ +---------------------------------------------+ |
|                                                                                                  |
| URGENT ESCALATION QUEUE (PRIORITY TRIAGE)                                                        |
| [Level 3 - Critical] APP-2026-1002 | Scrutiny overdue by 4 days | Assigned: NRO Scrutiny Cell    |
| [Level 2 - Warning]  APP-2026-1007 | EVC visit unscheduled (24h left) | Target: Apex Tech Inst  |
| [Level 2 - Warning]  DOC-EXP-0881  | Land Lease Deed expired 12 days ago | Inst: Zenith Inst   |
+--------------------------------------------------------------------------------------------------+
```

### Screen 2: Case Workbench (`/applications/:id`)
```
+--------------------------------------------------------------------------------------------------+
| APPLICATION WORKBENCH: APP-2026-AICTE-1002                                        [Back to List] |
| Institution: Northern Institute of Technology (NIT-402) | Region: Northern | Type: Extension (EoA)|
| Current Stage: SCRUTINY | Status: UNDER_REVIEW | Stage Due: 28 Oct 2026 (18 hrs remaining)       |
+--------------------------------------------------------------------------------------------------+
| WORKFLOW PROGRESSION STEPPER:                                                                    |
| (1) Submission [DONE] -> (2) Scrutiny [ACTIVE] -> (3) EVC [PENDING] -> (4) Committee [PENDING]   |
+--------------------------------------------------------------------------------------------------+
| PERMITTED CONTEXTUAL ACTIONS:                                                                    |
| [ Advance to EVC Stage ]  [ Return for Deficiency (Requires Reason) ]  [ Upload Supporting Note] |
+--------------------------------------------------------------------------------------------------+
| [TAB 1: Application Data] | [TAB 2: Documents (8)] | [TAB 3: Compliance] | [TAB 4: Audit Trail]  |
|                                                                                                  |
| +----------------------------------------------------------------------------------------------+ |
| | AUDIT TIMELINE (NON-REPUDIABLE JOURNAL)                                                      | |
| | 27 Oct, 14:00 - Officer R. Sharma opened scrutiny review.                                     | |
| | 25 Oct, 09:30 - System auto-escalated warning: Scrutiny due in 72 hours.                      | |
| | 21 Oct, 11:15 - Institution submitted application (Template: SCRUTINY_EVC v1).               | |
| +----------------------------------------------------------------------------------------------+ |
+--------------------------------------------------------------------------------------------------+
```

### Screen 3: Compliance & Lease Expiry Radar (`/compliance` & `/documents`)
```
+--------------------------------------------------------------------------------------------------+
| INSTITUTIONAL COMPLIANCE & DOCUMENT VALIDITY RADAR                                               |
| Filter: [ All Statuses v ] [ Expiring in 30 Days v ] [ Search Institution... ]                   |
+--------------------------------------------------------------------------------------------------+
| Entity / Document       | Institution             | Expiry / Due  | Status         | Action      |
|-------------------------+-------------------------+---------------+----------------+-------------|
| Registered Lease Deed   | Zenith Polytechnic      | 15 Oct 2026   | EXPIRED        | [Renew]     |
| Fire Safety Certificate | Horizon College of Eng  | 12 Nov 2026   | EXPIRING_SOON  | [Renew]     |
| Undertaking: AI Lab Eq  | Apex Institute of Tech  | 30 Oct 2026   | SUBMITTED      | [Verify]    |
| Undertaking: PhD Fac.   | Metro State University  | 05 Nov 2026   | PENDING        | [Notify]    |
+--------------------------------------------------------------------------------------------------+
```

---

## 3. Key User Journeys

### Journey 1: Regional Scrutiny Officer Deficiency Return Flow
1. Officer opens `/applications`, filters by `Region: Assigned` and `Stage: Scrutiny`.
2. Selects application `APP-2026-1002`, opening Case Workbench.
3. Reviews uploaded land title and building plan; notes missing Municipal Water NOC.
4. Clicks `Return for Deficiency`.
5. System displays modal:
   - Mandatory field: `Deficiency Remarks` ("Municipal Water NOC missing from Document Annexure IV").
   - Target Resubmission Stage: `SCRUTINY_RESUBMISSION`.
6. Officer confirms. System atomically:
   - Updates workflow status to `DEFICIENCY_RETURNED`.
   - Records audit event with actor ID, timestamp, and deficiency reason.
   - Dispatches in-app notification to the institution.

### Journey 2: Institution Renewal of Expired Lease
1. Institution user logs in; Compliance Radar flags expired Lease Deed.
2. Navigates to `/documents`, clicks `Renew Document` on expired lease `DOC-102`.
3. Selects new valid PDF, enters new registered expiry date (e.g. 2036-10-15).
4. Submits form. Backend stores new document linking `renewal_of_id = DOC-102`.
5. Historical document remains intact with status `SUPERSEDED`; new document enters `PENDING_VERIFICATION`.

### Journey 3: Official Verification of Undertaking Evidence
1. Institution submits geo-tagged laboratory photographs and invoices for `UND-201`. Status transitions to `SUBMITTED`.
2. Scrutiny Officer opens Workbench -> Compliance tab.
3. Clicks `Review Submitted Evidence`, inspects PDF.
4. Clicks `Verify Undertaking`. Modal prompts for official verification notes.
5. On submit, status changes to `VERIFIED`, setting `verified_by = officer_id` and creating an audit record.
