@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo   🎬 مصنع إنشاء حسابات PixVerse التلقائي بنقرة واحدة
echo ========================================================
echo.

:: 1. فحص هل سيرفر الحل المحلي شغال؟ لو مش شغال، نشغله فوراً في الخلفية
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$conn = Get-NetTCPConnection -LocalPort 8191 -State Listen -ErrorAction SilentlyContinue; " ^
  "if (-not $conn) { " ^
  "  Write-Host '[*] جاري تشغيل سيرفر الحل المحلي في الخلفية...' -ForegroundColor Cyan; " ^
  "  Start-Process -FilePath 'python.exe' -ArgumentList 'service.py' -WorkingDirectory (Join-Path (Get-Location).Path 'EzSolver') -WindowStyle Hidden; " ^
  "  Start-Sleep -Seconds 3; " ^
  "}"

:: 2. طلب الإيميل من المستخدم
set /p USER_EMAIL=">> ادخل الإيميل اللي عايز تسجل بيه: "
if "%USER_EMAIL%"=="" (
    echo [X] لم يتم إدخال إيميل!
    pause
    exit /b
)

echo.
echo [*] جاري الاتصال وتوليد التوكن وإرسال كود التفعيل...
echo.

python 02_pixverse_register.py "%USER_EMAIL%" "Password2026!"

echo.
echo ========================================================
echo انتهت العملية. اضغط أي مفتاح للإغلاق...
pause >nul

