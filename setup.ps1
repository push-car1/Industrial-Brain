Write-Host "Industrial Knowledge Brain - Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
$dockerVersion = docker --version 2>$null
if (-not $dockerVersion) {
    Write-Host "ERROR: Docker is not installed. Please install Docker Desktop from:" -ForegroundColor Red
    Write-Host "  https://www.docker.com/products/docker-desktop/"
    exit 1
}
Write-Host "✓ Docker detected: $dockerVersion" -ForegroundColor Green

# Check Docker Compose
$composeVersion = docker compose version 2>$null
if (-not $composeVersion) {
    Write-Host "ERROR: Docker Compose is not available." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker Compose detected" -ForegroundColor Green

Write-Host ""
Write-Host "Building and starting services..." -ForegroundColor Yellow
Write-Host "This will take 2-5 minutes on first run (model download)." -ForegroundColor Yellow
Write-Host ""

# Start services
docker compose up --build -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to start services." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "✓ Services started!" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend:    http://localhost:8501" -ForegroundColor Cyan
Write-Host "API Docs:    http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Neo4j:       http://localhost:7474 (neo4j/password)" -ForegroundColor Cyan
Write-Host ""

$ingest = Read-Host "Load sample data? (Y/N)"
if ($ingest -eq "Y" -or $ingest -eq "y") {
    Write-Host "Loading sample data..." -ForegroundColor Yellow
    docker compose exec backend python ingest_sample_data.py
}

Write-Host ""
Write-Host "Setup complete! Open http://localhost:8501 in your browser." -ForegroundColor Green
