# SIH26262 test and build verification script for Windows PowerShell
$ErrorActionPreference = "Stop"
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host " SIH26262: Backend tests + frontend production build" -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[FAIL] Python was not found. Install Python 3.11+ and reopen PowerShell." -ForegroundColor Red
    exit 1
}

$venvDir = ".\backend\venv"
$pyExe = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path $pyExe)) {
    Write-Host "[SETUP] Creating backend virtual environment..." -ForegroundColor Yellow
    python -m venv $venvDir
    if ($LASTEXITCODE -ne 0) { throw "Could not create backend virtual environment." }
    & $pyExe -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Could not upgrade pip." }
    & $pyExe -m pip install -r .\backend\requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Could not install backend dependencies. Check network access and requirements.txt." }
}

Write-Host "`n[1/2] Running backend unit, workflow, deadline and security tests..." -ForegroundColor Yellow
& $pyExe -m pytest -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Backend tests failed. Fix the reported failures before claiming verification." -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "[PASS] Backend test suite passed." -ForegroundColor Green

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "[FAIL] npm was not found. Install Node.js LTS and reopen PowerShell." -ForegroundColor Red
    exit 1
}

Push-Location .\frontend
try {
    if (-not (Test-Path ".\node_modules")) {
        Write-Host "`n[SETUP] Installing frontend dependencies with npm ci..." -ForegroundColor Yellow
        npm ci
        if ($LASTEXITCODE -ne 0) { throw "npm ci failed. Check network access and package-lock.json." }
    }
    Write-Host "`n[2/2] Running frontend production build..." -ForegroundColor Yellow
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] Frontend production build failed." -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "[PASS] Frontend production build passed." -ForegroundColor Green
} finally {
    Pop-Location
}

Write-Host "`n[NOTE] This script verifies tests/builds, not the full Docker/browser demo." -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan
