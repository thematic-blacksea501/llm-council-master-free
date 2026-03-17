# LLM Council - Windows Start Script (PowerShell)

Write-Host "Starting LLM Council..." -ForegroundColor Cyan

# Check if .venv exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment and installing dependencies..." -ForegroundColor Yellow
    uv sync
}

# Start backend in a new background job or process
Write-Host "Starting backend on http://localhost:8001..." -ForegroundColor Green
$backendProcess = Start-Process uv -ArgumentList "run", "python", "-m", "backend.main" -PassThru -NoNewWindow

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start frontend
Write-Host "Starting frontend on http://localhost:5173..." -ForegroundColor Green
Set-Location frontend
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}

# Run frontend (this will stay in the current window)
Write-Host " "
Write-Host "LLM Council is running!" -ForegroundColor Green
Write-Host "Backend:  http://localhost:8001 (running in background)"
Write-Host "Frontend: http://localhost:5173"
Write-Host " "
Write-Host "To stop, close this window or press Ctrl+C."

npm run dev

# Cleanup on exit
if ($backendProcess) {
    Write-Host "Shutting down backend..." -ForegroundColor Yellow
    # Kill the process tree (including python children)
    taskkill /pid $backendProcess.Id /t /f | Out-Null
}
