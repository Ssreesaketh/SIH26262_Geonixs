# SIH26262 UI/UX Refresh

## Design intent

The interface has been refined into a restrained administrative workspace rather than a generic dashboard. It uses a light content canvas, a deep-navy navigation rail, a white utility header, quieter borders, more consistent spacing, readable data tables, and clear status treatments.

The design keeps the approved three-part information model:

- **Overview / Control Tower** for operational visibility.
- **Case Workbench** for processing one application at a time.
- **Compliance and Alerts** for obligations, deadlines, and exceptions.

The refreshed styling is shared across all screens so cards, forms, tables, controls, and status badges behave consistently. Responsive breakpoints collapse the sidebar into a horizontal navigation strip on smaller screens.

## Brand and identity

The previous header displayed the letters `AICTE` inside a blue square, which was not an actual verified organization logo and could imply official affiliation. The refreshed interface uses a neutral ShieldCheck product mark and labels the product as an independent SIH26262 demonstration prototype. The Government of India’s UXDT catalogue lists an AICTE logo asset pack (https://www.uxdt.nic.in/documents/council/all-india-council-of-technical-education/), but the direct downloadable asset could not be reliably retrieved in this environment. Rather than approximate or distort an official mark, this package does not embed it. If an authorized asset is supplied later, it can replace the neutral product mark without changing the application functionality.

The notice “Not an official AICTE service · Synthetic demonstration data” is intentional. Do not remove it unless the prototype's status changes and any necessary authorization is confirmed.

## Main files changed

- `frontend/src/styles/index.css` — added a consistent design-token layer, header/sidebar styling, card/table/form/button treatments, responsive behavior, reduced-motion handling, and missing utility classes used by the existing JSX.
- `frontend/src/components/Navbar.tsx` — refreshed workspace identity, demo disclosure, clock, notification control, profile display and accessible labels.
- `frontend/src/components/Sidebar.tsx` — clearer navigation groups, active state, alert count, compact demo footer and small-screen behavior.
- `frontend/src/pages/LoginPage.tsx` — redesigned sign-in and demo-persona selection while preserving the existing login API behavior.
- `frontend/src/App.tsx` — added semantic layout class names for the new shared design layer.
- `frontend/src/pages/ControlTowerPage.tsx` — simplified operational terminology and primary deadline action copy.
- `frontend/src/pages/ApplicationsPage.tsx`, `CaseWorkbenchPage.tsx`, `CompliancePage.tsx`, `DocumentsPage.tsx`, `AlertsPage.tsx`, `WorkflowConfigPage.tsx` — simplified selected headings and action labels.
- `frontend/index.html` — updated the document title, description and theme color to identify the independent prototype.

## What this refresh does not change

This is a presentation and UX copy refresh. It does not intentionally change database schema, workflow rules, API endpoints, authentication behavior or authorization logic. Existing security-review findings remain open and must be handled separately.

## Local validation status

- [x] Source-level UI changes applied.
- [x] TypeScript check passed in the available dependency environment before the frontend bundle step.
- [x] Corrected project retains the existing Docker Compose configuration and API wiring.
- [ ] Vite production bundle completed in this environment.
- [ ] Docker image rebuilt on the user's Windows machine.
- [ ] Refreshed interface opened and visually reviewed in the user's browser.
- [ ] All functional flows retested after the UI refresh.

The production bundle could not be completed in this environment because the uploaded Windows `node_modules` did not contain the Linux-specific Rollup optional dependency and a clean dependency installation timed out. This is an environment limitation, not evidence that the project bundle succeeds. Rebuild in Docker on the user's Windows environment and inspect any reported error.

## Apply the refresh to an existing local installation

1. Stop the running foreground `docker compose up` with `Ctrl+C`.
2. From the current project folder, run `docker compose down` **without** `-v`. This stops containers but preserves named PostgreSQL and document-storage volumes.
3. Extract the refreshed ZIP into a new folder such as `D:\Projects\SIH26262_UI_Refresh`.
4. Copy the existing local `.env` from the working project into the new folder. The archive intentionally does not contain `.env`. Keep this file private. Reusing the environment is important when reusing the existing database volume because the stored PostgreSQL password must match the configured password.
5. Start PowerShell in the new folder and run:

   ```powershell
   docker compose config -q
   docker compose up --build
   ```

6. Open `http://localhost:5173` and sign in with the same local demo account.
7. Check the dashboard, applications list, case detail, compliance, documents, alerts and audit trail.
8. If any service fails to start, capture `docker compose ps` and the relevant `docker compose logs --tail=100 frontend` or `backend` output, with secrets removed.

Do not run `docker compose down -v` when you want to preserve existing demonstration data.
