# Stop on any error
$ErrorActionPreference = "Stop"

Write-Host "Starting build process..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "Virtual environment already exists" -ForegroundColor Yellow
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create icons
Write-Host "Creating icons..." -ForegroundColor Yellow
python create_icons.py

# Build executable
Write-Host "Building executable..." -ForegroundColor Yellow
pyinstaller whisper_gui.spec

# Check if build was successful
if (Test-Path "dist\WhisperGUI.exe") {
    Write-Host "`nBuild completed successfully!" -ForegroundColor Green
    Write-Host "The executable can be found at: $((Get-Item "dist\WhisperGUI.exe").FullName)" -ForegroundColor Green
} else {
    Write-Host "`nError: Build failed - executable not found" -ForegroundColor Red
    exit 1
}

# Keep console window open
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 