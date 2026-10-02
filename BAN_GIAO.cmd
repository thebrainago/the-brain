@echo off
REM Mot lenh de vao phien: in ban ban giao + trang thai song cua he.
cd /d "%~dp0"
call "%~dp0_py.cmd"
"%PY%" "%~dp0BAN_GIAO.py"
pause
