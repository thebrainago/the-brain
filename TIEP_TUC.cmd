@echo off
rem ============================================================
rem  TIEP_TUC.cmd - MOT LENH "TIEP TUC" NGAY KHI MO TERMINAL
rem  Cach dung: mo terminal trong thu muc lab, go:   TIEP_TUC
rem  No: (1) mo lai Chrome bot + CDP 9224, (2) in tinh trang,
rem      (3) chay supervisor (SEEKER/QUANT/BANKER/EVO/COMPUTE).
rem  Ho so lam viec tiep: lab\GHI_NHO_LAM_VIEC.md
rem ============================================================
cd /d "%~dp0"
set PY=C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PY%" set PY=python
chcp 65001 >nul

echo === [1/3] MO TRINH DUYET BOT + CDP 9224 ===
"%PY%" mo_chrome_cdp.py

echo.
echo === [2/3] TINH TRANG HIEN TAI ===
"%PY%" tinh_trang.py

echo.
echo === [3/3] TIEP TUC HE (supervisor) - Ctrl-C de dung an toan ===
"%PY%" dieu_phoi.py

echo [supervisor da dung] De chay nen 24-7: CHAY_NEN.cmd
pause >nul
