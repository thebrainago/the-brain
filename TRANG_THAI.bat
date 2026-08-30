@echo off
chcp 65001 >nul
title THE BRAIN - trang thai
cd /d "%~dp0"
set PY=C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PY%" set PY=python
"%PY%" bang_dieu_khien.py
echo.
pause
