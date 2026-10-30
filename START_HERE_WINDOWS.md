# Start SIH26262 on Windows

This guide is for the cleaned source package. It deliberately does not include your local `.env`, Python virtual environment, `node_modules`, database files or generated build outputs.

## Prerequisites

- Windows 10/11
- Docker Desktop installed and running (Linux containers enabled)
- Internet access for the first container build to download base images and dependencies
- PowerShell

You do not need to install PostgreSQL, Python or Node.js separately for the Docker-based app runtime. Python and Node.js are useful for the optional native test script.

## 1. Extract into a NEW folder

For example, extract the ZIP to `D:\Projects`. The ZIP contains a `SIH26262` folder, so the project root becomes `D:\Projects\SIH26262`. Do not extract over the original folder: a clean folder ensures an old `.env` does not carry over.

Open PowerShell in the folder containing `compose.yaml`.

## 2. Generate local environment values

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup.ps1
```

The setup script creates `.env` only if it does not already exist. It generates a random JWT secret and random PostgreSQL password. It does not print those values. Keep `.env` private and do not send it in a ZIP or commit it to Git.

## 3. Validate Compose configuration

```powershell
docker --version
docker compose version
docker compose config
```

Do not proceed if `docker compose config` reports an error. Save the complete error text for diagnosis, but redact passwords and secret values.

## 4. Build and start the app

```powershell
docker compose up --build
```

The first build needs internet access and may take several minutes. Wait for the database, backend and frontend services to start. Keep this terminal open for now.

## 5. Open the app

- Frontend: <http://localhost:5173>
- FastAPI docs: <http://localhost:8000/docs>
- Health endpoint: <http://localhost:8000/health>

Use the demo account table in `README.md`. Demo credentials are for this local synthetic-data prototype only. Change the design before exposing the application to any network beyond localhost.

## 6. Check container health

In a second PowerShell window, run:

```powershell
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend
```

All three services should be running/healthy. If a service exits, diagnose its logs before trying random changes.

## 7. Stop and restart

To stop the foreground run, press `Ctrl+C`, then:

```powershell
docker compose down
```

To start later in the background:

```powershell
docker compose up -d
```

To check the background services:

```powershell
docker compose ps
```

PostgreSQL data is stored in a named Docker volume and should remain after `docker compose down`. Avoid `docker compose down -v`; `-v` deletes the named volumes and can erase your local database/document data. If you previously ran an older version and see a PostgreSQL password-authentication error after changing `.env`, stop and report it before removing or replacing any volume. Only reset a volume when you confirm it contains disposable demo data.

## 8. Run tests (optional native toolchain)

Install Python 3.11+ and Node.js LTS if not already installed, then run:

```powershell
.\scripts\run-tests.ps1
```

The script creates a backend virtual environment and installs packages if needed, then runs pytest and a frontend production build. This is separate from the Docker startup test.

## 9. Reset demo data (destructive to local demo changes)

With the backend service running:

```powershell
.\scripts\reset-demo.ps1
```

This resets the database to the predefined synthetic demo scenario. It is not a general backup/restore tool.

## Troubleshooting information to capture

If it fails, send:

1. The command you ran.
2. The full error message with secrets removed.
3. The output of `docker compose ps`.
4. Relevant output from `docker compose logs --tail=100 backend` and/or `frontend`.

Never send `.env`, access tokens, passwords or private documents.


### If the backend fails at Uvicorn startup

Rebuild the backend image without using cached dependency layers, then start the stack:

```powershell
docker compose build --no-cache backend
docker compose up
```

The backend Dockerfile verifies the Uvicorn CLI import during image build.
