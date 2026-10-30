# Security review status — demo controls added; production review still pending

This is a local synthetic-data hackathon prototype, not a production AICTE service or a production security approval.

## Controls added in this revision

1. **Alert scoping and IDOR:** Alert listing now scopes institution users to notifications attached to their own institution, scopes regional officers to their assigned region, and limits EVC/bureau access by role/resource. Acknowledge/resolve endpoints apply the same object-level visibility checks; only operational officers/admin can resolve alerts. Regression test covers cross-institution alert listing and acknowledgement.
2. **Document associations:** Institution uploads and renewals are restricted to the authenticated institution account; application, undertaking, and renewal-document ownership are validated. Officer roles have read/download access according to role and region; they cannot upload institution-owned records through these endpoints.
3. **File content:** PDF/JPEG/PNG signature checks are applied in addition to client MIME and file-size checks. This is a basic type check, not malware scanning or full document validation.
4. **Audit integrity:** Consequential application and system actions are stored as SHA-256 hash-chain snapshots. Verification checks the chain and compares application-event source rows to their snapshots. The demo reset intentionally clears the demo chain.
5. **Rule history:** Workflow changes create new numbered versions and preserve the old version for applications already pinned to it.
6. **Local exposure:** Docker-published ports bind to localhost; Compose requires generated local secrets; the top-level `.env` is excluded from the release archive.

## Still required before wider-network use

- The frontend stores bearer tokens in `localStorage`; evaluate HttpOnly/Secure/SameSite sessions and XSS protections.
- Logout remains client-side/stateless; a copied token may remain valid until expiry.
- Add authentication rate limiting, comprehensive negative tests for every endpoint, dependency vulnerability scanning, and browser end-to-end testing.
- Add a separately protected audit checkpoint/anchor. A privileged attacker who can rewrite the database can potentially rewrite the entire chain; a hash chain alone is tamper-evident, not absolute immutability.
- Run the real bcrypt-backed backend test suite, production frontend build, and Docker Compose startup on the target Windows machine.
- Never use real institutional/personal data, publish seeded demo credentials, or expose the prototype publicly before review.

## Current verification evidence

The backend suite completed **30 tests passing** in the assistant execution environment using a temporary external bcrypt stub because network access prevented installation of the declared bcrypt dependency. This checks API/business logic but does not verify the real password-hashing dependency. The frontend TypeScript/build checks could not be rerun after the latest UI edits because dependencies are absent and npm offline installation failed due to uncached packages. Docker is unavailable in this environment.


## Document upload hardening added in the latest patch

- Only PDF, JPEG, and PNG uploads are accepted; extension, declared MIME type, and file signatures are checked.
- Default per-file upload limit is 10 MiB. The backend reads file content in bounded chunks and rejects oversized files; requests with a known excessive Content-Length are rejected before multipart parsing.
- Uploads are stored under random server-generated names, using exclusive file creation and canonical-path checks. User-provided filenames are not used as storage paths.
- Download responses are forced to attachment and include `nosniff` / private cache controls; the storage key is no longer exposed in document API responses.
- Documents enter `SUBMITTED`, and authorized officers can mark them `VERIFIED` or `RETURNED_FOR_CORRECTION` with required remarks. Correction uploads preserve the old record as `SUPERSEDED` and create a new submitted version.
- Regional authorization now fails closed if the officer has no region assignment or the target has no matching region. Regional document and undertaking lists are region-scoped, and alert visibility no longer treats a missing region assignment as unrestricted access.
- Added regression tests for spoofed file content, disallowed formats, review permissions, correction resubmission, and size-limit enforcement.

## Remaining production-hardening items

This remains a hackathon/demo application and has not undergone an independent penetration test. Before production use, add malware scanning / PDF sanitization, stronger document-content validation, formal schema migrations (for example Alembic), rate limiting and request throttling, security monitoring, backups/retention controls, and a legal/regulatory review of all official forms and workflows. The included PDF templates are explicitly demo templates, not verified official AICTE forms.


## AI / RAG controls added in this revision

- PDF evaluation checks document access before reading the stored file and persists an advisory report with the document content hash and engine mode.
- Regulatory source indexing and deactivation are restricted to `SYSTEM_ADMIN`; source chunks are page-aware and carry title/version/URL metadata.
- Shared RAG retrieval uses only active curated regulatory chunks. Institution-submitted documents are not automatically added to this shared corpus.
- AI outputs are explicitly marked advisory; no AI endpoint mutates document verification status or application workflow.
- Ollama is optional and disabled when `OLLAMA_URL` is blank. Configure only a trusted local Ollama endpoint.
- EVC schedule queries now filter regional officers to their assigned region. Alert direct-recipient visibility is checked in conjunction with the resource's institution/region scope.

## AI / RAG items still pending before production

- Local Ollama embedding generation and cosine-similarity retrieval are optional; lexical retrieval is the fallback. Vectors are currently stored as JSON and searched in application code; migrate to pgvector for larger corpora and test vector/model version consistency.
- No malware scanner or comprehensive PDF sanitization is integrated.
- OCR output and model findings require human review; test adversarial PDFs, prompt injection, corrupted PDFs, long-page/resource-exhaustion cases and model timeout behavior.
- The local model must be deployed and configured by the operator. The app must be tested with and without Ollama, including slow/unavailable model behavior.
- Add formal Alembic migrations rather than relying on `create_all()` for ongoing schema evolution.
- Complete full backend regression tests, frontend production build and Docker Compose startup on the target Windows environment before release.
