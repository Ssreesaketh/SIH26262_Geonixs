# SIH26262 Run & Verification Checklist

**Project source reviewed:** uploaded `SIH.zip` and its clean release archive.

**Status key:** `[x]` verified from the package or completed in this cleaned copy; `[ ]` still needs execution/evidence. A source file or cached artifact does not count as a passing runtime test.

## A. Package and files

- [x] React/TypeScript frontend source is present.
- [x] FastAPI backend source and API endpoint modules are present.
- [x] PostgreSQL/Docker Compose configuration is present.
- [x] Product and implementation documentation is present.
- [x] Backend test files are present.
- [x] Windows setup, test and demo-reset scripts are present.
- [x] This cleaned delivery excludes the top-level `.env`, Python virtual environment, `node_modules`, database files and generated build outputs.
- [x] Compose CORS setting changed to a JSON array so Pydantic Settings can parse its `List[str]` field.
- [x] Published frontend/backend ports are bound to `127.0.0.1` in the cleaned copy.
- [x] Setup script generates a random JWT secret and random PostgreSQL password in `.env` without printing the values.
- [x] Test script no longer silently skips backend tests merely because a bundled virtual environment is absent.
- [x] Demo-reset script now runs through the active Docker Compose backend.

## B. Must be completed on your computer

- [ ] Docker Desktop installed and running.
- [ ] Extracted the cleaned ZIP into a new folder (not over the old folder).
- [ ] `.\scripts\setup.ps1` ran successfully and created `.env`.
- [ ] `docker compose config` completed without errors.
- [ ] `docker compose up --build` completed successfully.
- [ ] `docker compose ps` shows `db`, `backend` and `frontend` running/healthy.
- [ ] `http://localhost:5173` opens in the browser.
- [ ] `http://localhost:8000/health` reports healthy.
- [ ] `http://localhost:8000/docs` opens the API docs.
- [ ] Login succeeds with a documented demo user.
- [ ] Dashboard metrics load from the backend.
- [ ] Application list and application detail load successfully.
- [ ] A valid workflow transition succeeds.
- [ ] An invalid transition is rejected.
- [ ] A deficiency return requires a reason and appears in history.
- [ ] EVC scheduling/status is visible and works for an authorized role.
- [ ] Undertaking evidence can be submitted and then verified by an authorized user.
- [ ] Document upload/renewal/expiry screens work with synthetic sample data.
- [ ] Manual deadline check creates expected notifications.
- [ ] 80% stage warning and configured reminder windows behave as expected.
- [ ] Overdue escalation ladder reaches each configured role at its configured threshold.
- [ ] Running the deadline check twice does not create duplicate notifications.
- [ ] Alert acknowledgement/resolution works as intended.
- [ ] Audit history shows the relevant actions.
- [ ] Administrator hash-chain verification succeeds after actions.
- [ ] Audit verification reports tampering in the automated test.
- [ ] Data persists after `docker compose down` and `docker compose up -d`.
- [ ] `.\scripts\run-tests.ps1` passes on a machine with internet/dependencies available.
- [ ] Browser end-to-end demo passes from a clean startup.
- [ ] Clean package runs from the exact extracted ZIP folder.

## C. Security review — not yet release-approved

- [x] Institution notification listing is scoped to the authenticated institution; cross-institution listing, acknowledgement and resolution are covered by regression tests.
- [x] Alert acknowledgement and resolution enforce object-level visibility checks.
- [x] Institution document uploads and renewals are restricted to the authenticated institution account; target institution/application/undertaking/renewal ownership checks are implemented.
- [ ] Replace or explicitly accept/document the bearer-token-in-`localStorage` design; it increases token exposure risk if an XSS bug exists.
- [ ] Validate uploaded file content/signature in addition to the client-provided MIME type.
- [ ] Test authentication rate limiting and logout/token invalidation behavior; logout currently appears client-side/stateless rather than revoking an issued token.
- [ ] Review all APIs for institution/region object-level access and add negative tests.
- [ ] Review dependency vulnerabilities and update/fix actionable findings.
- [ ] Do not expose the app beyond localhost until the above items are addressed and verified.

## D. Rules for marking completion

- Mark a runtime item `[x]` only after you personally see the expected result or have an actual test result.
- If an item fails, leave it unchecked and record the error below.
- Do not mark the security review complete based on a successful Docker build alone.

### Run log

| Date/time | Command or action | Result | Evidence / error |
|---|---|---|---|
| Not run on user's computer yet | — | Pending | Fill in after first startup |

### Known constraints

- Docker is not installed in the assistant's execution environment, so the Docker build and local browser run have **not** been verified here.
- Network access was unavailable for installing the declared bcrypt dependency and frontend npm dependencies in this execution environment. The backend tests were run with a temporary external bcrypt test stub (not included in the release): **26 passed**; real bcrypt and the production frontend build remain to be verified locally.
- Existing pytest cache/build files in the original archive are not sufficient evidence that the current clean package passes its tests.
- This is a synthetic-data hackathon prototype, not an AICTE production deployment.

## E. UI/UX refresh status

- [x] Refreshed shared header, sidebar, login and design-system styles in the source package.
- [x] Updated selected page headings and labels for clearer administrative language.
- [x] Removed the non-official text-only `AICTE` logo block; the refreshed product uses a neutral prototype mark and a clear non-affiliation notice.
- [x] Added a dedicated UI refresh note and checklist.
- [ ] Rebuild the frontend Docker image on Windows and visually review the result.
- [ ] Confirm the existing login, live dashboard data and core workflows still work after rebuilding.
- [ ] Review responsive layout, keyboard focus and visible error states in the browser.

See [`docs/UI_UX_REFRESH.md`](docs/UI_UX_REFRESH.md) and [`UI_REFRESH_CHECKLIST.md`](UI_REFRESH_CHECKLIST.md).

## D. AI document review and regulatory RAG — added in 1.1.0

- [ ] Rebuild backend/frontend with `docker compose up --build` on the target machine.
- [ ] Confirm `/docs` lists the `/api/v1/ai` endpoints.
- [ ] Sign in as an institution user and evaluate a synthetic PDF belonging to that institution.
- [ ] Confirm an institution user cannot evaluate another institution's document by changing the document ID.
- [ ] Confirm JPEG/PNG uploads remain supported by the existing vault but the AI evaluator returns 415 for them.
- [ ] Confirm the evaluation report says advisory-only and does not change document verification status or application stage.
- [ ] Sign in as `SYSTEM_ADMIN`, index a verified synthetic/officially authorized PDF, and verify the catalogue records source title, version and page-aware chunks.
- [ ] Confirm non-admin source upload and deactivation are rejected.
- [ ] Ask a question and confirm the response returns retrieved source metadata/page references; without Ollama it must explicitly say retrieval-only.
- [ ] If using Ollama, pull both configured models, set `OLLAMA_URL`, `OLLAMA_MODEL`, and `OLLAMA_EMBED_MODEL` in the private `.env`, then verify model-backed answers and vector retrieval.
- [ ] Deactivate a source and verify it is no longer retrieved while historical evaluation reports remain available.
- [ ] Test scanned, malformed, encrypted, empty-text, maximum-page and oversized PDFs.
- [ ] Run the full backend pytest suite, TypeScript/Vite build and Docker/browser end-to-end tests on the target machine.
