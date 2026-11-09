@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==================================================
echo   🚀 تشغيل سيرفر EzSolver في الخلفية (Daemon)
echo ==================================================

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$conn = Get-NetTCPConnection -LocalPort 8191 -State Listen -ErrorAction SilentlyContinue; " ^
  "if ($conn) { Write-Host '⚠️ السيرفر شغال بالفعل على البورت 8191! (PID: ' $conn.OwningProcess ')' -ForegroundColor Yellow; exit 0 } " ^
  "Start-Process -FilePath 'python.exe' -ArgumentList 'service.py' -WorkingDirectory (Get-Location).Path -RedirectStandardOutput 'daemon_out.log' -RedirectStandardError 'daemon_err.log' -WindowStyle Hidden; " ^
  "Start-Sleep -Seconds 3; " ^
  "$conn2 = Get-NetTCPConnection -LocalPort 8191 -State Listen -ErrorAction SilentlyContinue; " ^
  "if ($conn2) { Write-Host '✅ ممتاز! السيرفر شغال الآن في الخلفية على: http://127.0.0.1:8191' -ForegroundColor Green; Write-Host ('   رقم العملية (PID): ' + $conn2.OwningProcess) -ForegroundColor Cyan } " ^
  "else { Write-Host '❌ لم يبدأ السيرفر بعد، راجع ملف daemon_err.log' -ForegroundColor Red }"

echo.
echo اضغط أي مفتاح للإغلاق...
pause >nul
