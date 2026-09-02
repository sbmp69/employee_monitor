# Employee Monitor Agent - Build Script
# This script bundles the Python agent into a standalone executable using PyInstaller.

Write-Host "Checking for PyInstaller..."
if (!(Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "Installing PyInstaller..."
    pip install pyinstaller
}

Write-Host "Building EmployeeMonitorAgent.exe..."
# We use --onefile to create a single executable.
# We do NOT use --noconsole as per instructions to avoid stealth mechanisms, 
# providing a visible local console for basic local logging and transparency.
pyinstaller --onefile --name "EmployeeMonitorAgent" --icon=NONE main.py

Write-Host "Build complete! Check the 'dist' directory for EmployeeMonitorAgent.exe."
