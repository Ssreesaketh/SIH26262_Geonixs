# SIH26262 — Approval & Compliance Workspace Prototype

[![Prototype](https://img.shields.io/badge/Status-Hackathon%20Prototype-blue.svg)](#)
[![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20React%20%7C%20PostgreSQL-navy.svg)](#)
[![Security](https://img.shields.io/badge/Security-RBAC%20%7C%20Audit%20Trail%20%7C%20STRIDE-green.svg)](#)

An integrated, role-based, audit-traceable, and regulatory-safe platform for AICTE approval workflows, stage pendency monitoring, Expert Visit Committee (EVC) scheduling, time-bound compliance undertakings, document validity/expiry tracking (including lease monitoring), and automated deduplicated escalations.

---

## 🏛️ System Core Concepts
1. **Control Tower**: Regional and national operational dashboard tracking active applications, stage dwell times, overdue SLAs, and regional load.
2. **Case Workbench**: Comprehensive case management screen for an application featuring an interactive procedural stage stepper, contextual actions, deficiency return with mandatory justification, document vault, and an append-only audit trail.
3. **Compliance Radar**: Focused surveillance for expiring land leases, fire safety NOCs, time-bound institutional undertakings, and official verification workflows.

---

## 🚀 Quick Start (One-Click Docker Setup)

Read [`START_HERE_WINDOWS.md`](START_HERE_WINDOWS.md), [`RUN_CHECKLIST.md`](RUN_CHECKLIST.md), and [`docs/UI_UX_REFRESH.md`](docs/UI_UX_REFRESH.md) first. Use the cleaned package from a new folder; do not reuse a copied `.env` from the original working archive.

```powershell
# 1. Initialize environment & generate secure random keys
.\scripts\setup.ps1

# 2. Validate the Compose configuration before starting

docker compose config

# 3. Build and run containers
docker compose up --build
```
Open **http://localhost:5173** in your web browser. The Compose configuration binds the published ports to localhost only.

To stop the foreground services, press `Ctrl+C` and then run `docker compose down`. To restart in the background, use `docker compose up -d`.

### Pre-Seeded Demonstration Accounts:
| Role | Email | Password | Scope |
| :--- | :--- | :--- | :--- |
| **Regional Officer** | `officer.north@aicte.gov.in` | `Admin@AICTE2026!` | Shared view of all five seeded applications |
| **Bureau Officer** | `bureau.hq@aicte.gov.in` | `Admin@AICTE2026!` | Bureau review and recommendations |
| **System Administrator** | `admin@aicte.gov.in` | `Admin@AICTE2026!` | Final authority and system administration |
| **Institution — Zenith** | `principal@zenith.edu.in` | `Admin@AICTE2026!` | Zenith applications and documents only |
| **Institution — NIT** | `principal@nit.edu.in` | `Admin@AICTE2026!` | NIT applications and documents only |
| **Institution — Apex** | `admin@apex.edu.in` | `Admin@AICTE2026!` | Apex applications and documents only |



### Updating an existing installation

Before starting this draft, stop the old Compose stack from its previous project folder with `docker compose down` (do **not** add `-v`). This frees the local ports. Compose containers, networks and volumes are now project-scoped, so the new project creates its own seeded demo database while leaving the previous named volume untouched.

If you deliberately configure the new project to reuse an older demo database, sign in as `admin@aicte.gov.in`, open **Workflow configuration**, and choose **Reset demo data** once to remove legacy synthetic accounts and recreate the new dataset. This reset clears the demo data; never use it on a database containing real user data.

The refreshed seed contains exactly six demo accounts (three institution users and three officers), three institutions, and five starter applications. Newly created institution drafts will naturally increase the application count.
---

## 🛠️ Local Development (Native Mode)

### Backend (Python FastAPI):
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.initial_data
uvicorn app.main:app --reload --port 8000
```
Backend API docs available at: **http://localhost:8000/docs**

### Frontend (React + Vite):
```powershell
cd frontend
npm install
npm run dev
```
Frontend development server available at: **http://localhost:5173**

---

## 🧪 Running Automated Tests
```powershell
.\scripts\run-tests.ps1
```
Runs the full backend pytest test suite validating workflow transitions, deficiency validations, deadline calculations, and security boundaries.

---


## AI document review and regulatory RAG (new)

The project now includes an advisory PDF evaluation workflow and a regulatory retrieval assistant:

- In **Documents & forms**, users can run **AI review** on PDF documents they are authorized to access. The report shows text extraction/OCR status, any model-generated findings, source references, and limitations. It never changes the document's verification state or application workflow.
- In **Regulatory AI**, users can ask questions against the shared, administrator-curated source library. Answers include source title/version/page metadata when available. If no source matches, the assistant explicitly reports insufficient evidence.
- **System administrators** can index verified official PDF sources, record their source URL/version, and deactivate superseded sources. Institution submissions are never automatically added to the shared regulatory knowledge base.
- PDF extraction uses PyMuPDF; scanned pages can use Tesseract OCR when available. Processing is limited by `AI_MAX_PDF_PAGES` (default 60) and the configured file-size limit.

### Enable a local LLM (optional)

Without a local model configured, the application still extracts PDF text and retrieves relevant regulatory passages, but it does **not** claim to have performed LLM evaluation or generated a model answer. To enable local generation with Ollama:

1. Install and start Ollama on the host machine.
2. Pull a model suitable for your hardware, for example `ollama pull qwen2.5:7b`, and an embedding model with `ollama pull nomic-embed-text`.
3. In the project's private `.env`, set `OLLAMA_URL=http://host.docker.internal:11434`, `OLLAMA_MODEL=qwen2.5:7b`, and `OLLAMA_EMBED_MODEL=nomic-embed-text`. Keep the URL empty to disable model calls.
4. Rebuild/restart with `docker compose up --build`.

The Ollama endpoint is configured by the operator, not by end users. Keep it on a trusted local network and do not point it at an untrusted service. LLM calls can take time and are synchronous in this prototype. If the configured embedding model is available during source indexing, chunk vectors are stored and cosine similarity is used for retrieval; otherwise the service falls back to lexical ranking. The current vectors are stored as JSON and compared in application code. Moving them to `pgvector` is a planned scale/performance improvement.

### AI safety and evaluation limits

- Reports are advisory and require an authorized human reviewer. AI output never approves/rejects an application or advances a workflow.
- Source uploads are restricted to system administrators and must be verified/authorized before indexing.
- Only PDF documents are currently evaluated by the AI endpoint; JPEG/PNG remain uploadable for existing workflows but are not AI-evaluated.
- The prototype does not yet perform malware scanning, full PDF sanitization, or automated official-regulation verification. Vector retrieval requires a configured local Ollama embedding model; lexical retrieval remains the fallback. Do not use real student records until the security and privacy review is complete.

## 📖 Comprehensive Documentation Index
- [`docs/00_PRODUCT_DESIGN_BLUEPRINT.md`](docs/00_PRODUCT_DESIGN_BLUEPRINT.md)
- [`docs/01_FEATURE_SPECIFICATION.md`](docs/01_FEATURE_SPECIFICATION.md)
- [`docs/02_UX_FLOWS_AND_SCREEN_DESIGN.md`](docs/02_UX_FLOWS_AND_SCREEN_DESIGN.md)
- [`docs/03_SYSTEM_ARCHITECTURE.md`](docs/03_SYSTEM_ARCHITECTURE.md)
- [`docs/04_DATABASE_AND_API_SPECIFICATION.md`](docs/04_DATABASE_AND_API_SPECIFICATION.md)
- [`docs/05_BUILD_AND_SETUP_GUIDE.md`](docs/05_BUILD_AND_SETUP_GUIDE.md)
- [`docs/06_TESTING_AND_DEMO_PLAYBOOK.md`](docs/06_TESTING_AND_DEMO_PLAYBOOK.md)
- [`docs/REGULATORY_ASSUMPTIONS.md`](docs/REGULATORY_ASSUMPTIONS.md)
- [`docs/SECURITY_THREAT_MODEL.md`](docs/SECURITY_THREAT_MODEL.md)
- [`docs/AI_DOCUMENT_REVIEW_AND_RAG.md`](docs/AI_DOCUMENT_REVIEW_AND_RAG.md)
- [`docs/UI_UX_REFRESH.md`](docs/UI_UX_REFRESH.md)
- [`UI_REFRESH_CHECKLIST.md`](UI_REFRESH_CHECKLIST.md)

---

## ⚖️ Regulatory Notice
This system is a synthetic-data hackathon prototype built to demonstrate approval workflow governance, stage pendency monitoring, and compliance tracking. It is not an officially endorsed AICTE production deployment. Use only on localhost with synthetic data. The seeded accounts share a demo-only password and the current auth design needs further security hardening before any network or production deployment. See `SECURITY_REVIEW_PENDING.md`.


## Rule engine, escalation, and audit integrity

- Workflow configuration changes create a new numbered `WorkflowTemplate` version; active applications remain pinned to their existing version.
- Rule JSON supports `ordered_stages`, `stage_slas`, `warning_threshold_percent`, `reminder_windows_hours`, and `escalation_ladder`. The included values are illustrative demo assumptions, not official AICTE timelines.
- The deadline sweep emits an early warning at the configured percentage (seeded to 80%), configured near-deadline reminders, and deduplicated overdue escalation alerts.
- Institution accounts are scoped to their own application/document tenant; officer dashboards share the seeded application registry while actions remain role- and stage-authorized. The EVC inspection report and bureau review checklist are officer-only downloadable PDF templates; institution templates are visible only in the institution portal.
- Application events and consequential system events are snapshotted into a SHA-256 hash chain. Administrators can verify it through **Workflow configuration** or `GET /api/v1/config/audit/verify`. This is tamper-evident, not absolute immutability; production deployments should anchor hashes outside the application database.
- Document uploads validate file signatures and cross-check institution, application, undertaking, and renewal ownership. Alert lists and alert actions enforce role/object scoping.

For a walkthrough of these behaviors, see `DEMO_RUNBOOK.md`. After a clean checkout, run `scripts/setup.ps1`, then `docker compose up --build`. The UI/browser and real Docker build still need verification on the target Windows machine.


### Document uploads and review

Institution users can upload PDF, JPEG, or PNG files up to 10 MiB each. The server checks the declared type, extension, file signature, and basic file completeness; browser-side checks are only a convenience and are not relied upon for security. Uploaded files are private downloads and are not served inline.

New submissions appear as **SUBMITTED** until an authorized officer marks them **VERIFIED** or **RETURNED_FOR_CORRECTION** with review remarks. Institutions can upload a corrected replacement for a returned document; the previous version is retained as **SUPERSEDED**. These demo templates are not verified official AICTE statutory forms.
