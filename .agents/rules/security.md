---
description: Application security standards, RBAC, access boundaries, upload controls, and audit integrity
always_on: true
---

# Application Security Standards

1. **Authentication & Password Protection**:
   - Store passwords using Argon2id or bcrypt with work factor >= 12.
   - Session tokens must be signed JWTs or cryptographically secure session IDs.
   - Authentication errors must return generic failure messages without revealing account existence.

2. **Authorization & Boundary Enforcement**:
   - Enforce RBAC at the backend service layer on every single route. Never trust frontend state, role query parameters, or client headers.
   - Check institutional tenancy: an institution user may only query and modify applications matching their `institution_id`.
   - Check regional scope: regional officers may only access applications matching their assigned `region_id`. Bureau officers and system admins have broader oversight as explicitly defined.

3. **Input Validation & Parameter Tampering**:
   - Use Pydantic models for strict payload validation.
   - Forbid arbitrary field updates; protected fields (`status`, `workflow_status`, `stage_due_at`, `verified_by`) can only be modified through dedicated state machine transition methods.

4. **Document Storage & File Uploads**:
   - Restrict uploads to approved MIME types: `application/pdf`, `image/jpeg`, `image/png`.
   - Validate file size limits (default max 10MB).
   - Generate cryptographically random UUID storage keys. Never use user-provided filenames on the filesystem.
   - Prevent directory traversal: isolate files in dedicated non-executable storage volumes outside web roots.
   - Serve files only through authenticated and authorized streaming endpoints (`/api/v1/documents/{id}/download`).

5. **Audit Trail Integrity**:
   - Audit logs are append-only. No application API or user interface shall allow modification or deletion of `application_events` / `audit_logs`.
   - Each state change and audit event must be persisted in the same atomic database transaction.
