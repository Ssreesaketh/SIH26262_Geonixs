# SIH26262 Build, Setup, and Operations Guide

---

## 1. System Requirements & Prerequisites
- **Operating System**: Windows 10/11, macOS, or Linux.
- **Runtimes**:
  - Python 3.11+ / 3.13 (verified: Python 3.13.7 installed).
  - Node.js 18+ / 24+ (verified: Node v24.19.0, npm 12.0.2 installed).
  - Docker Desktop with Compose support (Docker 29.4.2 installed).

---

## 2. Directory Structure Overview
```
d:\SIH\
├── backend\
│   ├── app\
│   │   ├── api\               # REST endpoints (/v1/auth, /v1/applications, etc.)
│   │   ├── core\              # Config, Security, DB session, Auth middleware
│   │   ├── models\            # SQLAlchemy ORM models
│   │   ├── schemas\           # Pydantic v2 validation schemas
│   │   └── services\          # Workflow engine, SLA checker, Document vault
│   ├── alembic\               # Database migration versions
│   ├── tests\                 # Automated pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend\
│   ├── src\
│   │   ├── components\        # Common UI (Sidebar, Header, Stepper, StatusBadge)
│   │   ├── pages\             # Control Tower, Workbench, EVC, Compliance, Alerts
│   │   ├── services\          # Centralized API client & HTTP interceptors
│   │   └── types\             # TypeScript / data contracts
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   └── Dockerfile
├── docs\                      # Architecture, Specifications, Security Threat Model
├── scripts\
│   ├── setup.ps1              # One-click environment bootstrap
│   ├── reset-demo.ps1         # Safe deterministic database reset & reseed
│   └── run-tests.ps1          # Automated test runner
├── compose.yaml               # Docker Compose multi-service orchestrator
├── .env.example               # Environment variables template
├── AGENTS.md                  # Project rules & constraints
└── README.md                  # Master developer onboarding
```

---

## 3. Quick Start (Docker Orchestration)

### Step 1: Automated Setup
Run the setup script from the root of the project:
```powershell
.\scripts\setup.ps1
```
This script will:
1. Verify Docker, Node, and Python toolchains.
2. Generate a secure random 32-byte secret key and create `.env` from `.env.example` if absent.
3. Verify directory structures for secure document storage.

### Step 2: Build & Launch Containers
```powershell
docker compose build --no-cache backend
docker compose up --build
```
Services initialized:
- `db`: PostgreSQL 16 (Port 5432) with persistent volume `postgres_data`.
- `backend`: FastAPI API server on `http://localhost:8000`.
- `frontend`: React + Vite on `http://localhost:5173`.

### Step 3: Accessing the Application
Open your browser to:
```
http://localhost:5173
```
Login using seeded credentials:
- **Regional Scrutiny Officer**: `officer.north@aicte.gov.in` / `Admin@AICTE2026!`
- **Institution Applicant**: `principal@zenith.edu.in` / `Admin@AICTE2026!`
- **Bureau Officer**: `bureau.hq@aicte.gov.in` / `Admin@AICTE2026!`
- **System Administrator**: `admin@aicte.gov.in` / `Admin@AICTE2026!`

---

## 4. Local Development Without Docker (Native Mode)

### Backend:
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Run migrations / create tables
python -m app.initial_data
# Start API
uvicorn app.main:app --reload --port 8000
```

### Frontend:
```powershell
cd frontend
npm install
npm run dev
```

---

## 5. Safe Demo Reset
To restore the demonstration dataset back to pristine deterministic state without deleting container volumes:
```powershell
.\scripts\reset-demo.ps1
```
Or trigger the reset API as an authenticated Administrator:
`POST /api/v1/admin/reset-demo`
