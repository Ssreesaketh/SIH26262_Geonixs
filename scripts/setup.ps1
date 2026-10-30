# SIH26262 Setup and Verification Script for Windows PowerShell
param (
    [switch]$Force = $false
)

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "  SIH26262 AICTE Approval & Compliance Platform - Environment Setup" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan

# 1. Check Prerequisites
Write-Host "`n[1/5] Checking System Prerequisites..." -ForegroundColor Yellow

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $pyVer = python --version
    Write-Host "  [OK] Python: $pyVer" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Python not found on PATH." -ForegroundColor DarkYellow
}

$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCmd) {
    $nodeVer = node --version
    Write-Host "  [OK] Node.js: $nodeVer" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Node.js not found on PATH." -ForegroundColor DarkYellow
}

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
    $dockerVer = docker --version
    Write-Host "  [OK] Docker: $dockerVer" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Docker CLI not found." -ForegroundColor DarkYellow
}

# 2. Check and generate .env
Write-Host "`n[2/5] Configuring Environment Secrets..." -ForegroundColor Yellow
$envPath = ".\.env"
$envExamplePath = ".\.env.example"

if (-not (Test-Path $envPath) -or $Force) {
    if (Test-Path $envExamplePath) {
        $envContent = Get-Content $envExamplePath -Raw
        
        # Generate cryptographically secure random values. Hex keeps the database URL safe from URI-escaping issues.
        $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        $secretBytes = New-Object byte[] 32
        $rng.GetBytes($secretBytes)
        $secretKey = -join ($secretBytes | ForEach-Object { "{0:x2}" -f $_ })

        $dbBytes = New-Object byte[] 32
        $rng.GetBytes($dbBytes)
        $dbPassword = -join ($dbBytes | ForEach-Object { "{0:x2}" -f $_ })

        $envContent = $envContent.Replace("change-this-to-a-secure-random-32-byte-hex-string", $secretKey)
        $envContent = $envContent.Replace("POSTGRES_PASSWORD=GENERATED_BY_SETUP_SCRIPT", "POSTGRES_PASSWORD=$dbPassword")
        $envContent = $envContent.Replace("DATABASE_URL=postgresql+psycopg2://postgres:GENERATED_BY_SETUP_SCRIPT@localhost:5432/aicte_workflow", "DATABASE_URL=postgresql+psycopg2://postgres:$dbPassword@localhost:5432/aicte_workflow")
        Set-Content -Path $envPath -Value $envContent
        Write-Host "  [OK] Generated .env with random SECRET_KEY and database password (values hidden)." -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] .env.example not found." -ForegroundColor Red
    }
} else {
    Write-Host "  [OK] Existing .env file found. Preserving current secrets." -ForegroundColor Green
}

# 3. Create Document Storage Directory
Write-Host "`n[3/5] Initializing Secure Storage Directory..." -ForegroundColor Yellow
$storageDir = ".\document_storage"
if (-not (Test-Path $storageDir)) {
    New-Item -ItemType Directory -Path $storageDir | Out-Null
}
$sampleFiles = @("sample_lease_deed_nit402.pdf", "sample_fire_noc_zen801.pdf")
foreach ($sf in $sampleFiles) {
    $targetFile = Join-Path $storageDir $sf
    if (-not (Test-Path $targetFile)) {
        Set-Content -Path $targetFile -Value "%PDF-1.4`r`n%SIH26262 Synthetic Sample Document`r`n%%EOF"
    }
}
Write-Host "  [OK] Secure document storage directory ready." -ForegroundColor Green

# 4. Summary & Execution Instructions
Write-Host "`n[4/5] Setup Completed Successfully!" -ForegroundColor Cyan
Write-Host "---------------------------------------------------------------------" -ForegroundColor Gray
Write-Host "To launch with Docker Compose (Recommended):" -ForegroundColor White
Write-Host "  docker compose up --build" -ForegroundColor Yellow
Write-Host "`nTo run natively for local development:" -ForegroundColor White
Write-Host "  Backend:  cd backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000" -ForegroundColor Yellow
Write-Host "  Frontend: cd frontend; npm run dev" -ForegroundColor Yellow
Write-Host "`nAccess Portal URL:  http://localhost:5173" -ForegroundColor Green
Write-Host "Backend API Docs:   http://localhost:8000/docs" -ForegroundColor Green
Write-Host "---------------------------------------------------------------------" -ForegroundColor Gray
Write-Host "`nSeeded demo identities use a legacy shared password that is public/compromised." -ForegroundColor Yellow
Write-Host "Use seeded accounts only on an isolated synthetic-data instance; rotate or disable them before any shared deployment." -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Cyan
