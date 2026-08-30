@echo off
chcp 65001 >nul
title BROWSER DAILY SCAN - CDP Mode
cd /d "%~dp0"
set PY=C:\Python314\python.exe
if not exist "%PY%" set PY=python

echo ================================================
echo   BROWSER DAILY SCAN v2 - CDP Mode
echo   Profile: .browser_darwinex (port 9224)
echo   Ket hop: CDP Browser + Seeker + SocialDiscoverer
echo ================================================
echo.

echo Kiem tra CDP port 9224...
"%PY%" -c "import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:9224/json/version',timeout=3); print('CDP SAN SANG:',r.status)"
if %ERRORLEVEL% NEQ 0 (
    echo Chrome CDP chua chay. Vui long chay: python mo_chrome_cdp.py
    echo Hoac tu dong chay: python mo_chrome_cdp.py 9224 .browser_darwinex
    pause
    exit /b
)

echo.
echo Chon che do:
echo   1. Daily Scan (quet + kham pha)
echo   2. Scan-only (chi quet lai)
echo   3. Discover-only (chi kham pha nguon moi)
echo   4. Stats (xem thong ke)
echo.
set /p C="Chon (1-4): "
if "%C%"=="" set C=1
if "%C%"=="1" set MODE=daily
if "%C%"=="2" set MODE=scan-only
if "%C%"=="3" set MODE=discover-only
if "%C%"=="4" set MODE=stats

"%PY%" -c "import sys; sys.path.insert(0, r'C:\Users\SV STORE\Downloads\Research SP500\ds'); from browser.scanner import main; import sys as s; s.argv=['scanner','--%MODE%','--cdp','9224']; main()"
echo.
pause
