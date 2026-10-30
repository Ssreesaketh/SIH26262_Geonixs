# SIH26262 Application Security Threat Model

---

## 1. Threat Modeling Methodology
We adopt the **STRIDE** methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) tailored to a multi-tenant government administrative platform.

---

## 2. Threat Analysis & Mitigations

### A. Spoofing (Identity & Authentication)
- **Threat**: Attacker brute-forces officer passwords or impersonates another user via manipulated tokens.
- **Mitigations**:
  - Passwords hashed using modern key derivation functions (bcrypt with work factor >= 12 or Argon2id).
  - Cryptographically signed JWT tokens with standard expiry (`exp`) and issuer claims.
  - Constant-time password comparisons to prevent timing side-channels.
  - Generic error messages for failed authentication without username enumeration.

### B. Tampering (Unauthorized Data Alteration)
- **Threat 1**: Institution modifies internal workflow state or approves their own undertaking.
- **Mitigation**: Server-side state machine strictly controls allowed transitions; institution role lacks `VERIFY` and `ADVANCE_STAGE` permission.
- **Threat 2**: Officer alters historic audit events to hide delayed scrutiny.
- **Mitigation**: Database audit logs are append-only; application layer exposes no `UPDATE` or `DELETE` endpoints on `application_events`.

### C. Repudiation (Disputing Prior Actions)
- **Threat**: Official denies returning an application or an institution claims they never received a deficiency notice.
- **Mitigations**:
  - Every transition requires non-empty user context (`actor_user_id`, `actor_role`).
  - Deficiency reasons are stored immutably in both `application_events` and `applications`.
  - Notification generation logs `deduplication_key` and exact timestamp.

### D. Information Disclosure (Data Leakage & Cross-Tenant Access)
- **Threat 1**: College A views applications and financial disclosures of College B by guessing `id`.
- **Mitigation**: Object-level access control queries enforce `institution_id == current_user.institution_id`.
- **Threat 2**: Regional officer snoops on colleges in another geographical jurisdiction.
- **Mitigation**: Regional filter middleware enforces `institution.region_id == current_user.region_id`.
- **Threat 3**: Arbitrary file download via path traversal (`../../etc/passwd`).
- **Mitigation**: File storage uses isolated volume paths with sanitized random UUID filenames (`storage_key`), streaming via authenticated endpoints only.

### E. Denial of Service (System Availability)
- **Threat 1**: Repeated file uploads exhausting container disk space.
- **Mitigations**: Explicit file size ceiling (10 MB per file) enforced at both reverse proxy and Pydantic validation layers; permitted file extensions restricted to PDF, PNG, JPG.
- **Threat 2**: Repeated deadline check loops causing high CPU and duplicate notifications.
- **Mitigations**: Idempotent deadline sweeps utilizing composite unique key constraints on `deduplication_key`.

### F. Elevation of Privilege (Unauthorized Administrative Action)
- **Threat**: Institution user passes `role: "SYSTEM_ADMIN"` in registration or update payload.
- **Mitigation**: User creation strictly restricted to administrative routes; Pydantic update schemas forbid mass assignment of `role`, `is_active`, or `region_id`.
