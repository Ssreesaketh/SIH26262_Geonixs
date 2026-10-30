---
name: sih-release-verification
description: End-to-end verification and quality audit checklist for the SIH26262 AICTE Approval & Compliance platform.
---

# SIH26262 Release Verification Skill

This skill guides verification of the SIH26262 platform before packaging and delivery.

## 1. Environment & Configuration Check
- Ensure `.env.example` exists and contains documented configuration options with placeholder values.
- Verify that no hardcoded credentials, production secrets, or private keys exist in version control.

## 2. Backend Automated Test Suite
- Run pytest suite:
  ```powershell
  pytest backend/tests -v
  ```
- Ensure 100% pass rate on workflow transitions, authorization checks, deficiency validation, and deadline calculations.

## 3. Frontend Production Build
- Run Vite production compilation:
  ```powershell
  cd frontend
  npm run build
  ```
- Verify zero TypeScript/JSX compilation errors and clean asset generation in `frontend/dist`.

## 4. Docker Environment Verification
- Inspect `compose.yaml` for:
  * Backend and Database services.
  * Health checks with `interval`, `timeout`, and `retries`.
  * Persistent volume bindings (`postgres_data`, `document_storage`).
  * Private network isolation.

## 5. Security & Boundary Audit
- Confirm that unauthenticated requests to `/api/v1/applications` receive HTTP 401.
- Confirm that cross-institution access is rejected with HTTP 403.
- Verify that document downloads require authenticated tokens.

## 6. Archive Integrity Check
- Generate ZIP at `dist/SIH26262_Local_Prototype.zip`.
- Inspect archive contents to confirm absence of `node_modules`, `.venv`, `.env`, and test artifacts.
