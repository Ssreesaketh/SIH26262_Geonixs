# SIH26262 Live Multi-Role Demo Runbook

## What this demo proves

This prototype uses a shared PostgreSQL database and role-scoped FastAPI endpoints. A change saved by one logged-in role becomes visible to other authorized sessions through automatic UI refresh (about 4–8 seconds depending on the page). This is periodic synchronization, not WebSocket push. Workflow actions are persisted server-side and the application timeline records actions.

Use synthetic demo data only. This is a hackathon prototype, not an official AICTE production service. Treat configured workflow timings and seeded data as demonstration assumptions, not official regulatory rules.

## Start

From PowerShell in the project root:

```powershell
docker compose up --build
```

Keep this terminal open. Open the portal at http://localhost:5173 and API docs at http://localhost:8000/docs.

## Demo accounts

Password for all seeded accounts: `Admin@AICTE2026!`

| Persona | Email | Demonstrates |
|---|---|---|
| Institution — Zenith | `principal@zenith.edu.in` | Manage Zenith applications and documents only |
| Institution — NIT | `principal@nit.edu.in` | Manage NIT applications and documents only |
| Institution — Apex | `admin@apex.edu.in` | Manage Apex applications and documents only |
| Regional Officer | `officer.north@aicte.gov.in` | Scrutiny, EVC scheduling/findings and authorized workflow actions |
| Bureau Officer | `bureau.hq@aicte.gov.in` | Review EVC reports and record recommendations |
| System Administrator | `admin@aicte.gov.in` | Final decision and system configuration |

## How to demonstrate cross-role updates

For two simultaneous personas on one computer, use separate browser profiles (for example, Edge normal window and Chrome, or a private/incognito window). Each browser stores its own authentication token. Do not sign both users into the same browser profile, because the second login replaces the first session's token.

1. Open two browser profiles. In profile A, sign in as the Institution user. In profile B, sign in as the Regional Officer.
2. Keep the officer's Operations Overview open in profile B.
3. In profile A, open **Applications** → **New Application Draft**. Create an application using the configured `SCRUTINY_EVC` workflow.
4. Open the new case and submit it from the institution session. If the workflow UI shows a confirmation or required document prompt, follow that on-screen requirement.
5. Within a few seconds, the officer's Applications registry / Operations Overview should refresh from the shared API. Open the new case as the officer and inspect its stage and history.
6. As the officer, return it for deficiency using a specific reason. The reason must not be blank. Example: `Municipal Water NOC is missing from the submitted annexure; please upload the current certificate.`
7. Switch to the institution session and wait for the case to refresh. Open the same case and use the available resubmission action after adding the required evidence/remarks supported by the UI.
8. Return to the officer session, review the updated case, and advance it only when the workflow permits. Use the seeded EVC case for the EVC scheduling demonstration.
9. Open **Audit Trail** in the officer session to show the chronological actions. The page refreshes automatically.
10. For compliance, use **Compliance** to submit evidence as the institution user and then verify/reject it as an authorized officer. Submission must not automatically mark an undertaking verified.

## What should update automatically

- Operations Overview KPIs, stage pendency, and unread alert count
- Applications registry and current stage/status
- Open Case Workbench status and event history
- EVC schedule, compliance obligations, documents, alerts, and audit trail

Most views refresh every 5–8 seconds while their browser tab is visible. Refreshing manually remains available by navigating away/back or reloading the page.

## Verify health / troubleshoot

```powershell
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend
```

- If all services are healthy but another browser does not show a change, wait up to 8 seconds or reload that view.
- If the application does not appear for an officer, confirm that the officer has the correct regional jurisdiction and the institution belongs to that region. Server-side access scope is intentional.
- If a workflow action is rejected, read the error. The backend enforces role permissions and configured state transitions; do not bypass these checks for the demo.
- Do not run `docker compose down -v` unless you intend to delete the persisted database and document-storage volumes.

## Suggested narration

"The institution submits the case once. The API commits it to the shared database. The regional officer's separate session refreshes and sees the same case. Each authorized decision is persisted, the status advances through configured workflow transitions, and the audit trail makes the sequence reviewable. Access remains role- and jurisdiction-scoped."


## Demonstrate the three rule-engine upgrades

### 1. Edit a versioned rule (administrator)

1. Sign in as `admin@aicte.gov.in` and open **Workflow configuration**.
2. Edit the JSON for `SCRUTINY_EVC`. Example: change `warning_threshold_percent` from `80` to `75`, or change a stage's integer value under `stage_slas`.
3. Keep `COMPLETED` as the last stage, use known stage codes, and keep each SLA a non-negative integer.
4. Edit `escalation_ladder` to set day thresholds and recipient roles. The first level must begin at day `0`; supported roles are `INSTITUTION_USER`, `REGIONAL_OFFICER`, `BUREAU_OFFICER`, `EVC_MEMBER`, and `SYSTEM_ADMIN`.
5. Click **Validate & save new version**. The API creates a new version and keeps the old version for applications already using it. No code change or redeploy is required.

### 2. Demonstrate the 80% warning and escalation ladder

1. Open **Alerts** as an authorized officer.
2. Trigger the manual deadline check from the available control (or use `POST /api/v1/alerts/check` in `/docs`).
3. A stage warning is generated after the configured percentage of the stage's elapsed allowance. Configured reminder windows are deduplicated separately.
4. After a deadline, each eligible escalation level gets a separate, repeat-safe alert. Running the check again should not duplicate alerts for the same stage instance and level.
5. The seed ladder (day 0 regional officer, day 3 bureau officer, day 7 system administrator) is an illustrative demo policy, not an official AICTE timeline.

### 3. Verify the hash chain

1. Perform a workflow action, acknowledge an alert, or save a new rule version.
2. As administrator, open **Workflow configuration** and click **Verify audit chain**.
3. The API checks each hash link and compares application-event snapshots against their source rows. It reports the first detected mismatch or a valid entry count.
4. The endpoint is `GET /api/v1/config/audit/verify` and is administrator-only. The chain is tamper-evident, not a substitute for a separately protected production audit archive; a privileged database attacker could rewrite an entire chain without an external checkpoint.

**Demo reset warning:** **Reset demo data** deliberately clears synthetic records and the demo audit chain before reseeding. Do not use it if you need to preserve the current demo history.
