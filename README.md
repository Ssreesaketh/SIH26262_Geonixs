# SIH26262 — AICTE Approval & Compliance Workflow Prototype

[![Status](https://img.shields.io/badge/Status-Hackathon%20Prototype-blue.svg)](#project-status)
[![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20React%20%7C%20PostgreSQL-navy.svg)](#technology-stack)
[![Security](https://img.shields.io/badge/Security-Review%20Pending-orange.svg)](#security-posture)

An integrated workflow workspace demonstrating role-aware AICTE approval case management, stage pendency monitoring, Expert Visit Committee (EVC) scheduling, compliance undertakings, document validity/expiry tracking, and operational alerts. This is a synthetic-data hackathon prototype, not an official AICTE service or a production security approval.

## Contents
- [Overview](#project-overview)
- [Capabilities](#core-capabilities)
- [Stack](#technology-stack)
- [Quick start](#quick-start--windows-and-docker)
- [Demo accounts](#demo-accounts)
- [Development and tests](#local-development-and-tests)
- [Security posture](#security-posture)
- [AI document review and RAG](#ai-document-review-and-regulatory-rag)
- [Deployment](#deployment-status)
- [Documentation](#documentation)
- [Limitations](#project-limitations-and-regulatory-notice)

## Project overview
AICTE FlowGuard is a prototype for improving visibility and consistency across approval workflows. It brings application status, document readiness, compliance checks, authorized review, regulatory references, and deadline alerts into one workspace.

The main user journey follows the sequence in the SIH presentation:

1. User login.
2. Application creation or selection.
3. Document upload.
4. OCR and field extraction.
5. Completeness and compliance validation.
6. Workflow routing and deadline engine.
7. Authorized scrutiny and EVC scheduling.
8. Decision or additional query.
9. Status update and deadline tracking.
10. Alerts, escalation, and audit log.

The case workflow represents scrutiny and re-scrutiny, deficiency returns, EVC observations, and SAC/SHC recommendations where applicable to the configured case path. These are workflow records/recommendations; the prototype does not replace the competent authority's statutory decision.

The regulatory assistant uses an approved/curated guideline repository as its retrieval source. AI assists with document understanding and regulatory information retrieval; deterministic rules manage workflow and deadlines; authorized officials retain approval authority.

## Core capabilities and implementation status
The table distinguishes the proposed SIH scope from the current prototype. “Prototype present” does not mean production-ready or officially integrated.

| SIH presentation capability | Current prototype status |
|---|---|
| Authentication, role-based access, application records and dashboards | Implemented as a prototype; role/object isolation still requires full negative testing. |
| Document upload and checklist/completeness workflow | Implemented in prototype form; validation and review coverage still require testing. |
| OCR, document parsing and structured field extraction | PDF text extraction/OCR path is present; extraction accuracy requires human verification and broader testing. |
| Compliance and configurable workflow rules | Configurable workflow/deadline logic is present; seeded rules are illustrative, not official AICTE timelines. |
| Authorized scrutiny, EVC scheduling, decision/additional query | Workflow stages and role-authorized actions are represented in the prototype; end-to-end role/stage validation remains a release task. |
| Alerts, escalation and audit log | Alert/deadline and hash-chain audit features are present; delivery/operational reliability and external audit anchoring remain outstanding. |
| RAG regulatory assistant | Curated-source retrieval is present; source currency, answer quality, citations and abstention need continued validation. |
| Live AICTE/system integration | Not implemented; the prototype uses synthetic/demo data and documented interfaces. |

The four implementation phases shown in the SIH presentation are reflected as follows:

- **Phase 1 — Authentication, application records, dashboard:** prototype implementation present.
- **Phase 2 — Workflow engine, document upload, checklist:** prototype implementation present.
- **Phase 3 — OCR, document extraction, regulatory RAG:** prototype capabilities present but limited; human verification and source validation are required.
- **Phase 4 — Alerts, audit trails, testing:** alert and audit features are present; full regression, browser, deployment and security testing remain incomplete.

These are prototype implementation notes, not a claim of production completion. Workflow thresholds and sample forms are demonstration material, not verified statutory AICTE requirements or official forms.

## Technology stack
| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| Runtime | Docker Compose, Nginx |
| Document processing | PyMuPDF, optional Tesseract OCR |
| Optional local LLM | Ollama |

## Quick start — Windows and Docker
Use a clean project folder. Do not copy an old `.env` into a fresh checkout without reviewing it. Read [START_HERE_WINDOWS.md](START_HERE_WINDOWS.md), [RUN_CHECKLIST.md](RUN_CHECKLIST.md), and [docs/UI_UX_REFRESH.md](docs/UI_UX_REFRESH.md).

```powershell
# Generate local environment secrets
.\scripts\setup.ps1

# Validate configuration
docker compose config

# Build and start
docker compose up --build
```

Open **http://localhost:5173**. The local Compose configuration binds application ports to localhost. Do not change this to a public bind address for an internet-facing deployment.

Stop with `Ctrl+C`, then `docker compose down`. Restart in background with `docker compose up -d`. Do not use `docker compose down -v` unless you intentionally want to delete the local database volume.

### Environment configuration
- Keep the real `.env` out of Git; `.env.example` is reference-only.
- Generate a unique high-entropy `SECRET_KEY` and strong database password per environment.
- Never use placeholder secrets, `postgres` as a production password, or shared demo credentials in deployment.
- Store production secrets in the hosting provider's environment/secret manager, never in source, README, screenshots, or slides.
- Set CORS to exact trusted frontend origins and keep PostgreSQL private.

## Demo accounts
The seeded development dataset includes these demo identities:

| Role | Demo email | Intended scope |
|---|---|---|
| Regional Officer | `officer.north@aicte.gov.in` | Officer registry and region-authorized work |
| Bureau Officer | `bureau.hq@aicte.gov.in` | Bureau review and recommendations |
| System Administrator | `admin@aicte.gov.in` | Demo configuration and administrative functions |
| Institution — Zenith | `principal@zenith.edu.in` | Zenith applications and documents |
| Institution — NIT | `principal@nit.edu.in` | NIT applications and documents |
| Institution — Apex | `admin@apex.edu.in` | Apex applications and documents |

**Passwords are intentionally omitted.** The seed dataset has historically used a shared demo-only password. Treat seeded credentials as public/compromised: use only on an isolated local synthetic-data instance, rotate them before any shared demo, and never reuse them elsewhere. Do not expose seeded accounts on a public deployment.

### Updating an existing installation
Stop the old Compose stack from its previous folder with `docker compose down` (without `-v`). If deliberately reusing an older demo database, follow [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md). Resetting demo data deletes/recreates synthetic records; never run it against important or real institutional data.

## Local development and tests

### Backend — FastAPI
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.initial_data
uvicorn app.main:app --reload --port 8000
```
API docs: **http://localhost:8000/docs**

### Frontend — React + Vite
```powershell
cd frontend
npm install
npm run dev
```
Frontend: **http://localhost:5173**

### Automated tests
Run from the project root:
```powershell
.\scripts\run-tests.ps1
```
The script runs backend pytest tests for workflow transitions, validation, deadlines, and security boundaries. Also run the frontend production build and full Compose startup before release.

### Verification evidence and gaps
The current security review records **30 backend tests passing in an assistant execution environment using a temporary external bcrypt stub**, because the declared bcrypt dependency could not be installed there. This is not equivalent to testing the real password-hashing dependency.

The review also records:
- Frontend production build/type checks could not be rerun after latest UI edits because dependencies were unavailable and offline installation failed.
- Docker was unavailable in that environment; a successful Docker build/start was not established there.
- Real bcrypt-backed tests, target-Windows Docker startup, browser E2E tests, and complete negative authorization tests remain outstanding.

Source inspection and partial tests do not prove that the complete application is operational or secure.

## Security posture

**Status: security review pending. This is not a production security certification.**

### Controls documented in the current codebase
- Institution uploads derive ownership from the authenticated account and validate associated application, undertaking, and renewal ownership.
- Institution application/document views and alert actions include tenant/object-level access checks.
- Regional access fails closed when an officer has no region assignment or the target does not match.
- Uploads accept PDF, JPEG, and PNG with extension, declared MIME, signature, completeness, and size checks; default per-file limit is 10 MiB.
- Files use generated storage names and guarded path handling. Downloads are attachment-only with `nosniff` and private-cache controls.
- Document review supports submitted, verified, and returned-for-correction states; correction uploads preserve the prior version as superseded.
- Workflow configuration changes create new numbered versions.
- Consequential events are snapshotted into a SHA-256 hash chain; verification is available in the application configuration screen and `GET /api/v1/config/audit/verify`.
- Curated regulatory sources are admin-managed; institution submissions are not automatically added to shared RAG.
- AI review is advisory and does not approve/reject applications or advance workflow state.

### Known findings and remaining work
| Priority | Area | Remaining concern / action |
|---|---|---|
| **P0 — before public/shared deployment** | Credentials | Replace/disable seeded shared credentials; generate environment-specific secrets; ensure no secrets or real data are committed. |
| **P0** | Authorization | Complete negative tests for cross-institution, cross-region, cross-role, and cross-application access. Review regional application registry/list filtering; detail/action checks alone do not establish list isolation. |
| **P0** | Authentication | Add login rate limiting and abuse protection. Frontend currently stores bearer tokens in `localStorage`; assess HttpOnly/Secure/SameSite sessions and XSS protections. Logout is client-side/stateless, so copied tokens may remain usable until expiry. |
| **P0** | Deployment | Enforce HTTPS, exact CORS origins, private DB access, private persistent document storage, managed secrets, backups/restore tests, and monitoring. Do not expose before review. |
| **P1** | File security | Add malware scanning and PDF sanitization; test malformed/adversarial PDFs, polyglot files, and resource exhaustion. Signature checks are not antivirus. |
| **P1** | Audit integrity | Anchor hashes in a separately protected external system. A privileged DB attacker may rewrite the database and chain; current chain is tamper-evident, not immutable. |
| **P1** | Database lifecycle | Add formal migrations (e.g. Alembic), least-privilege DB roles, retention controls, and tested backups/restores. |
| **P1** | Supply chain | Pin dependencies/base images; run `pip-audit`, `npm audit`, Bandit, and Trivy. Remediate findings; run containers non-root where practical and configure security headers/CSP. |
| **P1** | API/browser | Add E2E tests, request throttling, payload limits, safe errors, CSRF protection if cookie sessions are used, and mass-assignment/IDOR tests. |
| **P1** | AI/RAG | Test prompt injection, malicious/corrupt PDFs, OCR/model timeouts, long documents, and resource exhaustion. Enforce authorization before extraction/retrieval; keep humans responsible for decisions. |
| **P2** | Retrieval scale | Consider pgvector and explicit embedding/model version management before scaling beyond JSON-vector/lexical fallback. |

### Pre-release checklist
1. Rotate seeded passwords and verify demo accounts cannot be used publicly.
2. Run real bcrypt-backed backend tests in a clean environment.
3. Run frontend production build and inspect the generated bundle.
4. Build/start full Compose stack on target Windows; verify health checks and logs.
5. Test every role against sensitive list, detail, upload, download, update, decision, alert, and workflow endpoints.
6. Run dependency, static-analysis, container, and dynamic web scans (e.g. OWASP ZAP).
7. Verify HTTPS, CORS, secrets, DB isolation, file persistence, backups, and restore in deployment.
8. Obtain independent security, privacy, and legal/regulatory review before real-data or production use.

Passing this checklist is a release gate for this prototype, not proof of AICTE approval or statutory compliance.

## AI document review and regulatory RAG
- In **Documents & forms**, authorized users can request AI review of PDFs they can access. Reports may include text extraction/OCR status, model findings, source references, and limitations.
- In **Regulatory AI**, users can ask questions against the shared administrator-curated source library. Answers include source title/version/page metadata when available; insufficient evidence should be stated.
- Only system administrators can index/deactivate curated regulatory PDF sources. Institution submissions are not automatically added to shared knowledge.
- PDF extraction uses PyMuPDF; scanned pages may use Tesseract OCR. Processing is bounded by `AI_MAX_PDF_PAGES` and upload-size limits.
- AI findings are advisory and do not change document verification, approve/reject applications, or advance workflow.

### Optional local LLM with Ollama
Without a model configured, the application can extract text and retrieve passages but must not claim LLM evaluation/generation.

1. Install and start Ollama on the host.
2. Pull a model, e.g. `ollama pull qwen2.5:7b`, and embedding model, e.g. `ollama pull nomic-embed-text`.
3. In private local `.env`, set `OLLAMA_URL=http://host.docker.internal:11434`, `OLLAMA_MODEL=qwen2.5:7b`, and `OLLAMA_EMBED_MODEL=nomic-embed-text`.
4. Leave `OLLAMA_URL` empty to disable model calls; rebuild with `docker compose up --build`.

Use only an operator-controlled trusted Ollama endpoint. Calls are synchronous in this prototype. Embeddings are stored as JSON and compared in application code; lexical ranking is the fallback. pgvector is a future scale improvement.

### AI/RAG limitations
No malware scanning, comprehensive PDF sanitization, or automated verification of latest official regulations is currently provided. OCR and model output can be wrong or manipulated. Do not upload real student records, personal data, confidential institutional material, or sensitive documents before formal security/privacy review.

## Deployment status
**No production deployment URL is currently published.** The current documented run mode is local Docker Compose. Hosting, production configuration, persistent private storage, and external smoke tests have not been verified.

A publicly accessible live URL is not part of the technical architecture described in the SIH idea presentation itself. Whether a live URL is required for your particular submission round depends on the current SIH portal fields and your college/SPOC's instructions. The README and GitHub repository link should not be treated as a substitute for a required demo video or prototype demonstration.

Before any optional hosted demo:
- Replace seeded credentials and disable public access to demo accounts.
- Set unique production secrets in the hosting provider's environment settings.
- Use managed/private PostgreSQL and private persistent document storage.
- Configure exact frontend origins, HTTPS, health checks, logs, backups, and restore procedures.
- Verify uploads and generated files persist across restarts.
- Run role-based security/workflow smoke tests using synthetic data only.

Do not add a deployment URL, QR code, or hosting-success claim to a presentation until the deployed app has been tested outside the developer machine.

## Documentation
- [Product design blueprint](docs/00_PRODUCT_DESIGN_BLUEPRINT.md)
- [Feature specification](docs/01_FEATURE_SPECIFICATION.md)
- [UX flows and screen design](docs/02_UX_FLOWS_AND_SCREEN_DESIGN.md)
- [System architecture](docs/03_SYSTEM_ARCHITECTURE.md)
- [Database and API specification](docs/04_DATABASE_AND_API_SPECIFICATION.md)
- [Build and setup guide](docs/05_BUILD_AND_SETUP_GUIDE.md)
- [Testing and demo playbook](docs/06_TESTING_AND_DEMO_PLAYBOOK.md)
- [Regulatory assumptions](docs/REGULATORY_ASSUMPTIONS.md)
- [Security threat model](docs/SECURITY_THREAT_MODEL.md)
- [AI document review and RAG](docs/AI_DOCUMENT_REVIEW_AND_RAG.md)
- [UI/UX refresh](docs/UI_UX_REFRESH.md)
- [UI refresh checklist](UI_REFRESH_CHECKLIST.md)
- [Security review status](SECURITY_REVIEW_PENDING.md)
- [Demo runbook](DEMO_RUNBOOK.md)

## Project limitations and regulatory notice
This is a synthetic-data hackathon prototype, not an officially endorsed AICTE production deployment. It does not establish statutory compliance and must not be used to make real approval decisions. Workflow stages, SLA values, escalation thresholds, and sample forms are illustrative unless separately validated against current official requirements.

The SHA-256 audit chain is tamper-evident but not absolutely immutable. File signature checks are not malware scanning. AI/RAG outputs are advisory and can be inaccurate. Authentication, deployment, testing, and operational controls require further hardening and independent review.

**Use localhost and synthetic data only until outstanding security, privacy, legal, and operational reviews are complete.**
