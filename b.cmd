@echo off
chcp 65001 >nul
cd /d "%~dp0"
call "%~dp0_py.cmd"
"%PY%" "%~dp0b.py" %*
