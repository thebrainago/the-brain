@echo off
chcp 65001 >nul
title BROWSER DAILY SCAN
cd /d "C:\Users\SV STORE\Downloads\Research SP500\lab"
set PY=C:\Python314\python.exe
if not exist "%PY%" set PY=python
echo ================================================
echo   BROWSER DAILY SCAN - Quet tu dong hang ngay
echo   Ket hop: Browser Agent (Profile 16) + Seeker
echo ================================================
"%PY%" -c "import sys; sys.path.insert(0, r'C:\Users\SV STORE\Downloads\Research SP500\ds'); from browser.scanner import main; import sys as s; s.argv = ['scanner', '--daily']; main()"
echo.
echo Xem bao cao: reports/browser_scan_*.json
echo.
pause
