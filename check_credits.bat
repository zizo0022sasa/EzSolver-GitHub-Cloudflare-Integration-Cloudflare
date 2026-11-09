@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo   [PixVerse] Check Credits
echo ========================================================
echo.

python pixverse_creator.py --credits

echo.
pause

