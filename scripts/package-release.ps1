# SIH26262 Release Packaging Script
Write-Host "Packaging clean release deliverable..." -ForegroundColor Cyan

$distDir = ".\dist"
if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir | Out-Null
}

$zipPath = Join-Path $distDir "SIH26262_Local_Prototype.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

# Temporary staging directory
$stageDir = Join-Path $distDir "staging"
if (Test-Path $stageDir) {
    Remove-Item $stageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $stageDir | Out-Null

Write-Host "Copying project files to staging..." -ForegroundColor Yellow

# Copy root files
$rootFiles = @(
    "compose.yaml",
    ".env.example",
    ".gitignore",
    ".dockerignore",
    "pytest.ini",
    "README.md",
    "CHANGELOG.md",
    "AGENTS.md",
    "START_HERE_WINDOWS.md",
    "RUN_CHECKLIST.md",
    "SECURITY_REVIEW_PENDING.md"
)
foreach ($f in $rootFiles) {
    if (Test-Path $f) {
        Copy-Item $f -Destination $stageDir
    }
}

# Copy directories
Copy-Item ".\docs" -Destination (Join-Path $stageDir "docs") -Recurse
Copy-Item ".\scripts" -Destination (Join-Path $stageDir "scripts") -Recurse
Copy-Item ".\.agents" -Destination (Join-Path $stageDir ".agents") -Recurse

# Copy Backend
$stageBackend = Join-Path $stageDir "backend"
New-Item -ItemType Directory -Path $stageBackend | Out-Null
Copy-Item ".\backend\*" -Destination $stageBackend -Recurse -Exclude "venv", ".venv", "*.db"

# Copy Frontend
$stageFrontend = Join-Path $stageDir "frontend"
New-Item -ItemType Directory -Path $stageFrontend | Out-Null
Copy-Item ".\frontend\*" -Destination $stageFrontend -Recurse -Exclude "node_modules", "dist", ".vite"

# Create document_storage placeholder in staging
$stageDocStorage = Join-Path $stageDir "document_storage"
New-Item -ItemType Directory -Path $stageDocStorage | Out-Null
Set-Content -Path (Join-Path $stageDocStorage ".gitkeep") -Value ""

# Strip any build caches, pycache, .pyc, node_modules from staging
Get-ChildItem -Path $stageDir -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $stageDir -Filter ".pytest_cache" -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $stageDir -Filter "node_modules" -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $stageDir -Filter "dist" -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $stageDir -Filter "*.pyc" -Recurse -File | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $stageDir -Filter "*.db" -Recurse -File | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $stageDir -Filter ".env" -Recurse -File | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "Compressing archive to $zipPath..." -ForegroundColor Yellow
Compress-Archive -Path "$stageDir\*" -DestinationPath $zipPath -CompressionLevel Optimal

# Clean up staging directory
Remove-Item $stageDir -Recurse -Force

$zipItem = Get-Item $zipPath
$sizeMb = [math]::Round($zipItem.Length / 1MB, 2)
Write-Host "[OK] Clean release deliverable created at $zipPath ($sizeMb MB)." -ForegroundColor Green
