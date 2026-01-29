# Install Tesseract OCR for Windows
Write-Host "Downloading Tesseract-OCR installer..." -ForegroundColor Cyan

$installerUrl = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
$installerPath = "$env:TEMP\tesseract-installer.exe"

# Download installer
Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath

Write-Host "`nInstaller downloaded. Starting installation..." -ForegroundColor Green
Write-Host "Please follow the installation wizard." -ForegroundColor Yellow
Write-Host "IMPORTANT: Install to the default location: C:\Program Files\Tesseract-OCR" -ForegroundColor Yellow

# Run installer
Start-Process -FilePath $installerPath -Wait

Write-Host "`n✅ Installation complete!" -ForegroundColor Green
Write-Host "`nPlease restart the Flask server for changes to take effect." -ForegroundColor Cyan

# Clean up
Remove-Item $installerPath -ErrorAction SilentlyContinue
