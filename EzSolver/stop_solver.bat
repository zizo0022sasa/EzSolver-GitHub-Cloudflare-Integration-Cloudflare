@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo جاري إيقاف سيرفر EzSolver وعمليات الخلفية...

powershell -NoProfile -Command "
$conns = Get-NetTCPConnection -LocalPort 8191 -ErrorAction SilentlyContinue
if ($conns) {
    foreach ($c in $conns) {
        $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
        if ($p) {
            Write-Host ('[+] إيقاف العملية: ' + $p.ProcessName + ' (PID: ' + $p.Id + ')') -ForegroundColor Yellow
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host '✅ تم إيقاف سيرفر EzSolver بنجاح!' -ForegroundColor Green
} else {
    Write-Host 'ℹ️ السيرفر مش شغال حالياً.' -ForegroundColor Cyan
}
"

pause

