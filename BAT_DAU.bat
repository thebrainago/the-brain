@echo off
chcp 65001 >nul
title THE BRAIN - 24/7
cd /d "%~dp0"
set PY=C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PY%" set PY=python
if exist "DUNG_LAI" del "DUNG_LAI"
echo ================================================
echo   THE BRAIN - 5 tru, control plane song song
echo   SEEKER . QUANTLAB . NGHI . BANKER . EVOLUTION
echo ================================================
echo.
echo   Dung lai: chay DUNG_LAI.bat (hoac CTRL-C)
echo   Xem trang thai: TRANG_THAI.bat
echo.
"%PY%" giam_sat_dieu_phoi.py
pause
