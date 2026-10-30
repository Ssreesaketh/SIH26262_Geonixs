# SIH26262 Regulatory Assumptions and Safeguards

---

## 1. Official AICTE Regulatory Safeguards (Approval Process Handbook Principles)
1. **Separation of Workflow and Statutory Approval**:
   - In accordance with the AICTE Act (1987) and the Approval Process Handbook (APH), internal completion of Scrutiny, Re-Scrutiny, or Expert Visit Committee (EVC) verification constitutes procedural clearance, NOT statutory grant of approval.
   - Statutory approval can only be formally granted by the competent Executive Committee / Standing Appellate Committee (SAC) / Standing Hearing Committee (SHC) based on formal recommendation.
2. **Deficiency Hearing Rights (Natural Justice)**:
   - When an application is returned for deficiencies, institutions must be given formal notice and opportunity to rectify or present before SAC/SHC. The platform enforces this by recording exact deficiency reasons and supporting resubmission workflows.
3. **Mandatory Human Agency**:
   - Automated timers and deadline sweeps flag delays, send reminders, and escalate alerts. They NEVER execute autonomous statutory rejections or grants.

---

## 2. Configurable Prototype Assumptions (Synthetic Demonstration Baseline)
Where exact gazetted days vary across application categories (Technical, Management, Architecture, Pharmacy), the platform models these as configurable parameters within `workflow_templates` rather than hardcoding them:

| Parameter | Demonstration Value | AICTE Production Context |
| :--- | :--- | :--- |
| **Scrutiny Stage SLA** | 7 Days | Configured per annual approval calendar |
| **Deficiency Resubmission Window** | 10 Days | Standard institution rectification window |
| **EVC Scheduling Notice** | 5 Days | Minimum advance notification to college |
| **EVC Report Submission SLA** | 3 Days | Post-inspection committee report submission window |
| **Document Expiry Warning Window** | 30 & 60 Days | Warning threshold before land lease / NOC expiration |
| **SLA Warning Alert Threshold** | 48 Hours | Advance notice before stage deadline breach |
| **SLA Escalation Hierarchy** | Level 1: College/Officer<br>Level 2: Regional Director<br>Level 3: Central Bureau | Hierarchical administrative chain of command |

---

## 3. Unresolved Regulatory Questions & Future Work
- Integration with National Land Record Modernization Programme (NLRMP) for automated real-time verification of registered land lease deeds.
- Integration with Digilocker / NAD for digital certificate authentication.
- Cryptographic digital signing (DSC) of committee inspection reports.
