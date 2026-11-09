@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo   [PixVerse] Auto Account Creator - 1-Click
echo ========================================================
echo.

:: 1. Check if solver daemon is running on port 8191
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$conn = Get-NetTCPConnection -LocalPort 8191 -State Listen -ErrorAction SilentlyContinue; " ^
  "if (-not $conn) { " ^
  "  Write-Host '[*] Starting background solver daemon...' -ForegroundColor Cyan; " ^
  "  Start-Process -FilePath 'python.exe' -ArgumentList 'service.py' -WorkingDirectory (Join-Path (Get-Location).Path 'EzSolver') -WindowStyle Hidden; " ^
  "  Start-Sleep -Seconds 3; " ^
  "}"

:: 2. Ask user for email
set /p USER_EMAIL=">> Enter Email: "
if "%USER_EMAIL%"=="" (
    echo [X] Error: Email cannot be empty!
    pause
    exit /b
)

echo.
echo [*] Solving Turnstile and sending verification code...
echo.

python 02_pixverse_register.py "%USER_EMAIL%" "Password2026!"

echo.
echo ========================================================
echo Done! Press any key to close...
pause >nul

