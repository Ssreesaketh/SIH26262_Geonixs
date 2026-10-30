# Access-Control and Workflow Redesign — Upgrade Notes

## What changed

- Institution users now have a dedicated navigation set: **My overview**, **My applications**, and **Forms & documents**.
- Institution overview metrics, application lists, inspection schedules, document lists, application detail and audit timeline are tenant-scoped to the authenticated institution.
- Institution API responses conceal internal assignment roles, unfinished committee recommendations, private audit metadata and committee-member scheduling details.
- Application creation is restricted to institution users and the institution ID must match the authenticated user's institution.
- Institution document upload and renewal are institution-only; every document download remains authenticated and ownership-checked.
- All officer roles share the same five-case application registry and consistent operational dashboard. Write actions remain role- and stage-specific.
- EVC scheduling now has a UI. Submitting EVC findings advances a recommended application to **SAC_SHC / Bureau review**; deficient findings return the case to the institution for correction.
- Bureau review supports a required-rationale recommendation. System Administrator can record the final approval/rejection only after a bureau recommendation, and the application becomes completed.
- Four downloadable PDF working templates are included. Institution users can download the institution checklist and institution information form; officers receive only the templates permitted for their roles. They are clearly labeled demonstration templates, not official statutory forms.
- The seed dataset now creates exactly three institution users, three officer users, three institutions and five starter applications.

## Seeded demonstration accounts

All demo accounts use the demo-only password `Admin@AICTE2026!`.

| Role | Login |
|---|---|
| Regional Officer | `officer.north@aicte.gov.in` |
| Bureau Officer | `bureau.hq@aicte.gov.in` |
| System Administrator | `admin@aicte.gov.in` |
| Institution — Zenith | `principal@zenith.edu.in` |
| Institution — NIT | `principal@nit.edu.in` |
| Institution — Apex | `admin@apex.edu.in` |

## Existing database warning

Compose containers, networks and volumes are now project-scoped. Stop the old Compose stack from its previous project folder with `docker compose down` (do not add `-v`) before starting the new stack to free ports. The new project creates a fresh demo volume and leaves the older named volume untouched. If you deliberately configure the new project to reuse the old demo database, sign in as the System Administrator and use **Reset demo data** once. This clears and recreates the synthetic demo dataset; never use the reset against real user data.

## Validation performed in this environment

- Python source compilation: passed.
- Frontend TypeScript check (`tsc --noEmit`): passed.
- Backend pytest suite: **26 passed** using a temporary test-only bcrypt shim because the environment did not have the `bcrypt` package and external package downloads were unavailable. The shim was not included in the project; production password hashing code remains unchanged. Rerun `scripts/run-tests.ps1` on the target machine with the project requirements installed to validate against the real bcrypt dependency.
- A local Vite production build could not be completed because the uploaded `node_modules` directory lacked the Linux-specific Rollup optional dependency. The Dockerfile runs `npm install` inside its Linux build stage, so perform the full `docker compose up --build` on the target machine and inspect the result.
- A live browser review and full Docker integration run were not available in this environment.

## Run on Windows

From the project root:

```powershell
.\scripts\setup.ps1
docker compose config
docker compose up --build
```

Open `http://localhost:5173`. For an existing demo database, perform the one-time demo reset described above. Then test the three institution logins and all three officer logins, EVC scheduling, EVC findings, bureau recommendation, final decision and downloadable PDF forms.
