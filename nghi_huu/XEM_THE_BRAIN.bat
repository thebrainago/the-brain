@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ===== THE BRAIN - TRANG THAI =====
python brain_24h.py --tom-tat
echo.
pause
