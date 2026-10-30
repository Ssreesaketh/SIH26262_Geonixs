# Reset SIH26262 synthetic demonstration data. This deletes demo records in the configured database.
$ErrorActionPreference = "Stop"
Write-Host "Resetting SIH26262 synthetic demo data..." -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[FAIL] Docker CLI is not available." -ForegroundColor Red
    exit 1
}

$services = docker compose ps --status running --services 2>$null
if ($LASTEXITCODE -ne 0 -or -not ($services -contains "backend")) {
    Write-Host "[FAIL] The backend container is not running. Start the app with: docker compose up -d" -ForegroundColor Red
    exit 1
}

$pythonCode = "from app.core.database import SessionLocal; from app.seed_data import seed_database; from app.services.sla_engine import SLAEngine; db = SessionLocal(); seed_database(db, reset=True); SLAEngine.evaluate_all(db); db.close(); print('Demo database reset and reseeded.')"
docker compose exec -T backend python -c $pythonCode
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Demo reset did not complete." -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "[PASS] Synthetic demo data reset and reseeded." -ForegroundColor Green
