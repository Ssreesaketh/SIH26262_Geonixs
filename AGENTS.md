# AGENTS.md — SIH26262 AICTE Approval & Compliance Platform

## 1. Project Context & Goals
SIH26262 is an integrated, secure, configurable, and audit-traceable workflow automation platform designed for AICTE approval processing and institutional compliance governance.
It addresses:
- Configurable approval routing across statutory and administrative stages (Scrutiny, Re-Scrutiny, EVC, SAC/SHC).
- Stage-wise pendency and SLA tracking to eradicate administrative gridlocks.
- Expert Visit Committee (EVC) scheduling, observation logging, and deadline management.
- Time-bound institutional undertakings, compliance evidence submission, and formal verification by authorized officials.
- Proactive lease and prescribed-document expiry radar with automated renewal tracking.
- Idempotent automated reminders and hierarchical overdue escalations.
- Region-wise and role-based operational dashboards (Control Tower, Case Workbench, Compliance Radar).
- Append-only transactional audit trail guaranteeing accountability and non-repudiation.

## 2. Confirmed Architectural Decisions
- **Architecture**: Modular Monolith.
- **Backend**: Python 3.11+ / 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0 (PostgreSQL primary with automatic SQLite test/fallback compatibility).
- **Frontend**: React 18/19, Vite, Lucide Icons, Modern High-Density Administrative Portal Design System.
- **Database**: PostgreSQL with Alembic migration versioning.
- **Security Baseline**: Argon2/bcrypt password hashing, HttpOnly session/JWT tokens, server-enforced role and regional/institutional data boundary authorization, secure file upload validation (MIME, size, magic signature), path traversal prevention, zero client-trust principles.
- **Background Engine**: Idempotent deadline monitoring engine running either via internal scheduler or via deterministic authorized API trigger (`/api/v1/alerts/check`).

## 3. Regulatory Safeguards & Principles
1. **Never Invent Regulations**: Explicitly distinguish verified AICTE Approval Process Handbook (APH) guidelines from synthetic prototype assumptions.
2. **Separation of Workflow and Statutory Decisions**: Administrative completion of a stage does not automatically grant statutory approval; an overdue deadline does not arbitrarily cancel an institution's application.
3. **Preservation of Authorized Human Agency**: AI and automation assist and notify; they never usurp legally mandated scrutiny, verification, or statutory committee votes.
4. **Separation of Duties**: Institutional users cannot verify their own undertakings or alter workflow rules; regional officers cannot manipulate applications outside their geographical jurisdiction.

## 4. Coding & Verification Standards
- Maintain strict type hints in Python and comprehensive schemas in Pydantic.
- Every state transition must update application state, calculate stage deadlines, and append an audit event in an atomic transaction.
- Returns for deficiency must mandate an explicit recorded reason.
- Frontend must never fake backend metrics; all KPI cards and charts must bind directly to `/api/v1/dashboard/*`.
- Run tests and verify real endpoints before claiming completion.
