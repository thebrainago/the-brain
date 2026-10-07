@echo off
rem _py.cmd - tim Python cho cac launcher; dat bien PY. Goi bang:  call "%~dp0_py.cmd"
rem Thu tu: .venv cua repo -> ban cu cua may nay -> bo chay `py` -> `python` tren PATH.
rem Khong dung WindowsApps\python.exe (stub cua Store). Doi ten nguoi dung hay cai lai Windows
rem khong con lam launcher gay: truoc day duong dan go cung C:\Users\SV STORE\...
set "PY="
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
if not defined PY if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" set "PY=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
if not defined PY for /f "usebackq delims=" %%I in (`py -3 -c "import sys;print(sys.executable)" 2^>nul`) do set "PY=%%I"
if not defined PY set "PY=python"
