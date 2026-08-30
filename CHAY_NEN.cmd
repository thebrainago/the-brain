@echo off
rem ============================================================
rem  THE BRAIN - watchdog ngoai tien trinh cho control plane 24/7.
rem  Watchdog restart ca khi supervisor thoat va khi lease bi treo.
rem ============================================================
cd /d "%~dp0"
set PY=C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PY%" set PY=python
if not exist "reports" mkdir "reports"

if exist "DUNG_LAI" goto het
echo [%date% %time%] khoi dong watchdog control plane >> "reports\dieu_phoi_nen.log"
"%PY%" giam_sat_dieu_phoi.py >> "reports\dieu_phoi_nen.log" 2>&1
set RC=%errorlevel%
echo [%date% %time%] watchdog thoat (ma %RC%) >> "reports\dieu_phoi_nen.log"
exit /b %RC%

:het
echo [%date% %time%] thay DUNG_LAI - khong khoi dong watchdog >> "reports\dieu_phoi_nen.log"
