# Flask Server Startup Script
# Double-click this file to start the server

$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"

Write-Host "Starting Flask Book Sales Website..." -ForegroundColor Green
Write-Host "Server will be available at: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

Set-Location $PSScriptRoot
C:\Python313\python.exe -m flask run
