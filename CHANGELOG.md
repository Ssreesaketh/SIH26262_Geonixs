# SIH26262 Implementation Changelog

## [1.0.0-prototype] - 2026-10-27
### Architecture & Design
- Established project foundation conforming to official SIH26262 requirements.
- Selected Modular Monolith architecture: FastAPI (Python 3.13) + React 19 / Vite + PostgreSQL 16.
- Finalized hybrid design paradigm: Control Tower, Case Workbench, Compliance Radar.
- Authored full design documentation suite under `docs/` (`00_PRODUCT_DESIGN_BLUEPRINT.md` through `06_TESTING_AND_DEMO_PLAYBOOK.md`, `REGULATORY_ASSUMPTIONS.md`, and `SECURITY_THREAT_MODEL.md`).
- Established Antigravity workspace rules and skills under `AGENTS.md` and `.agents/`.

### Backend Foundation
- Configured FastAPI application structure with `/api/v1` REST routes.
- Implemented SQLAlchemy 2.0 ORM schemas for Regions, Institutions, Users, Workflow Templates, Applications, Audit Events, EVC, Undertakings, Documents, and Notifications.
- Implemented JWT-based authentication with Argon2/bcrypt password hashing.
- Implemented role-based and jurisdictional object-level access controls.
- Implemented state machine engine with transactional audit trail and mandatory deficiency remarks.
- Implemented idempotent deadline evaluation service with unique deduplication keys.
- Implemented secure file storage manager with randomized UUID keys and MIME/magic validation.

### Frontend Implementation
- Configured React + Vite application with Indian Government Administrative Portal design system.
- Built Control Tower dashboard with live backend aggregations, stage pendency charts, and priority escalation queue.
- Built Case Workbench with interactive workflow stepper, contextual action controls, tabbed detail views, and chronological audit timeline.
- Built EVC inspection management and scheduling interface.
- Built Compliance Radar for time-bound undertakings and document expiry surveillance.
- Built Alerts & Escalation desk with manual SLA sweep trigger.

### Packaging & Delivery
- Authored Docker multi-container configuration (`compose.yaml`, `Dockerfile.backend`, `Dockerfile.frontend`).
- Authored automated Windows PowerShell scripts (`scripts/setup.ps1`, `scripts/reset-demo.ps1`, `scripts/run-tests.ps1`).
- Created deliverable packaging script targeting `dist/SIH26262_Local_Prototype.zip`.

## [1.0.1-ui-refresh] - 2026-10-27
### User interface
- Reworked the header, sidebar, login view and shared design tokens for a calmer administrative workspace.
- Improved card, table, form, button, status badge and responsive styling.
- Added visible prototype and synthetic-data disclosures; removed the text-only `AICTE` square that could be mistaken for an official logo.
- Simplified operational copy, including deadline-check actions and screen headings.
- Added `docs/UI_UX_REFRESH.md` and `UI_REFRESH_CHECKLIST.md` with changes and remaining local verification.
### Validation note
- TypeScript source check completed successfully in the available environment.
- The Vite production bundling step was not verified here because the available dependency archive lacked the Linux Rollup optional package and fresh dependency installation timed out. Rebuild in Docker on Windows before marking release verification complete.

## [1.0.2-live-demo] - 2026-10-28
### Multi-role demo synchronization
- Added automatic polling refresh for the Operations Overview, application registry, open case workbench, EVC, compliance, documents, alerts and audit trail.
- Added periodic unread-alert badge refresh so separately logged-in role sessions reflect server-side changes without a manual reload.
- Background refresh runs only while the browser tab is visible and avoids resetting loading states on every poll.
- Added `DEMO_RUNBOOK.md` with a two-browser, institution-to-officer case lifecycle demonstration and troubleshooting steps.
### Validation
- Source changes reviewed. Full frontend TypeScript build and backend test suite could not be completed in this packaging environment because dependency installation was unavailable (`npm` registry/cache missing packages; Python environment missing `bcrypt`). Rebuild and run the provided checks on the user's Docker setup before the live presentation.


## Rule-engine and audit-integrity upgrade

- Workflow edits now create a new active version rather than mutating the selected version.
- Added validation for stage sequence, integer durations, warning threshold, reminder windows, and escalation ladder.
- Added 80% early-warning logic, configured reminder windows, and per-level overdue escalation deduplication.
- Added SHA-256 audit-chain entries for application events and consequential system actions, plus an admin-only verification endpoint.
- Added admin JSON editor and audit verification action to Workflow configuration.
- Tightened alert object authorization and document upload/renewal ownership and file-signature validation.
- Added regression tests for rule versioning, audit tampering, warning threshold, and escalation levels.

## [1.1.0-ai-document-review-rag] - 2026-10-29
### AI document review and regulatory retrieval
- Added bounded PDF text extraction with optional Tesseract OCR for scanned pages.
- Added persisted advisory document evaluation reports, content SHA-256 fingerprints, evaluator metadata and report history endpoints.
- Added administrator-only regulatory PDF indexing with page-aware chunks, source URL/version metadata, duplicate-source checks and source deactivation.
- Added optional Ollama LLM generation and embedding support. When embeddings are available, retrieval uses cosine similarity; otherwise it uses lexical ranking. When the LLM is unavailable, the UI/API explicitly reports retrieval-only or deterministic pre-check mode.
- Added Regulatory AI navigation, source catalogue/question UI, admin source curation, and PDF AI-review actions in Documents & forms.
- Kept AI strictly advisory: no AI endpoint changes document verification status or application workflow.
- Restricted regional-officer EVC schedule queries to the officer's assigned region and strengthened alert direct-recipient scoping.
### Validation status
- Python source compilation, ORM mapper/table creation, PDF extraction, advisory fallback, cosine helper, lexical retrieval and TypeScript checks passed in the available environment.
- Full pytest execution remains unverified because `bcrypt` (declared in requirements) is missing in the build environment and package installation was blocked by unavailable network access.
- Vite production build remains unverified because the supplied `node_modules` lacks the Linux-specific Rollup optional dependency. Build from a clean Docker image on the target Windows machine.
- Real Ollama inference and Docker end-to-end tests were not run.
