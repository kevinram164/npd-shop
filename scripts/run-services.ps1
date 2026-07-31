# Start all NOLI microservices locally (shared SQLite for lab).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$svc = Join-Path $root "services"
$venvPython = Join-Path $root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
  Write-Host "Creating venv..."
  python -m venv (Join-Path $root "backend\.venv")
  $venvPython = Join-Path $root "backend\.venv\Scripts\python.exe"
  & $venvPython -m pip install -r (Join-Path $svc "requirements.txt")
}

$db = Join-Path $svc "noli-shared.db"
$dbUrl = "sqlite:///" + ($db -replace '\\', '/')
$env:DATABASE_URL = $dbUrl
$env:JWT_SECRET = "noli-dev-secret-change-me"
$env:INTERNAL_TOKEN = "noli-internal-dev"
$env:CORS_ORIGINS = "http://127.0.0.1:5173,http://localhost:5173"
$env:AUTH_URL = "http://127.0.0.1:8001"
$env:CATALOG_URL = "http://127.0.0.1:8002"
$env:ORDER_URL = "http://127.0.0.1:8003"
$env:PAYMENT_URL = "http://127.0.0.1:8004"
$env:PYTHONPATH = $svc
$env:SEED_ON_STARTUP = "true"

$jobs = @()
$jobs += Start-Process -PassThru -NoNewWindow -FilePath $venvPython -ArgumentList "-m","uvicorn","main:app","--host","127.0.0.1","--port","8001" -WorkingDirectory (Join-Path $svc "auth-service")
Start-Sleep -Seconds 1
$jobs += Start-Process -PassThru -NoNewWindow -FilePath $venvPython -ArgumentList "-m","uvicorn","main:app","--host","127.0.0.1","--port","8002" -WorkingDirectory (Join-Path $svc "catalog-service")
Start-Sleep -Seconds 1
$jobs += Start-Process -PassThru -NoNewWindow -FilePath $venvPython -ArgumentList "-m","uvicorn","main:app","--host","127.0.0.1","--port","8003" -WorkingDirectory (Join-Path $svc "order-service")
Start-Sleep -Seconds 1
$jobs += Start-Process -PassThru -NoNewWindow -FilePath $venvPython -ArgumentList "-m","uvicorn","main:app","--host","127.0.0.1","--port","8004" -WorkingDirectory (Join-Path $svc "payment-worker")
Start-Sleep -Seconds 1
$jobs += Start-Process -PassThru -NoNewWindow -FilePath $venvPython -ArgumentList "-m","uvicorn","main:app","--host","127.0.0.1","--port","8090" -WorkingDirectory (Join-Path $svc "gateway")

Write-Host "Started PIDs: $($jobs.Id -join ', ')"
Write-Host "Gateway: http://127.0.0.1:8090/api/health"
Write-Host "Press Ctrl+C in this window will NOT stop children — stop via Task Manager or Stop-Process."
