---
description: Release packaging, security stripping, reproducible scripts, and delivery standards
always_on: true
---

# Release and Packaging Standards

1. **Clean Deliverable Packaging**:
   - Deliverable ZIP must be output to `dist/SIH26262_Local_Prototype.zip`.
   - Strictly exclude `.env`, `.git/`, `__pycache__/`, `.pytest_cache/`, `node_modules/`, `venv/`, `.venv/`, and temporary uploaded binary storage files.
   - Include `.env.example`, Docker manifests, setup scripts, database migration files, seed scripts, documentation, and test suites.

2. **Setup Script Hygiene**:
   - `scripts/setup.ps1` must be self-contained:
     * Check prerequisites (Docker, Node, Python).
     * Generate secure, random cryptographic keys (SECRET_KEY) for `.env` if `.env` does not already exist.
     * Configure default test administrative credentials safely.
     * Provide clear next-step instructions.

3. **Deterministic Reset Procedure**:
   - `scripts/reset-demo.ps1` must safely reset database state and re-seed the standard deterministic demonstration dataset without manual SQL intervention.
