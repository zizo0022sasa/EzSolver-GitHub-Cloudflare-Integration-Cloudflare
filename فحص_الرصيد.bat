@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo   💳 فحص رصيد حسابات PixVerse الحالية
echo ========================================================
echo.

python pixverse_creator.py --credits

echo.
echo اضغط أي مفتاح للإغلاق...
pause >nul

