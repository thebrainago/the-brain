@echo off
REM ============================================================================
REM  THE BRAIN - goi CHU DONG (da go auto-chay-cung-may: khong phai ngay nao
REM  cung co nguon moi, chay khong cung chi ton dien)
REM
REM    BRAIN.bat            chay day du : thu thap nguon + chay cua ai
REM    BRAIN.bat nhanh      chi chay cua ai (bo qua thu thap nguon)
REM    BRAIN.bat nguon      chi thu thap nguon moi (arXiv + GitHub + nap_tay)
REM    BRAIN.bat bao-cao    in lai bao cao tu so dang ky, khong chay gi
REM
REM  Dung 10 luong (may co 20). Doi so luong: sua --processes duoi day.
REM ============================================================================
cd /d "%~dp0"

if "%1"=="nhanh" (
    python brain_daily.py --khong-fetch --processes 10
    goto :end
)
if "%1"=="nguon" (
    python brain_sources.py arxiv --so 15
    python brain_sources.py github --so 20
    python brain_sources.py nap-tay
    goto :end
)
if "%1"=="bao-cao" (
    python the_brain.py bao-cao
    goto :end
)

python brain_daily.py --processes 10

:end
echo.
echo Ket qua: reports\THE_BRAIN.md ^| Nguon: reports\BRAIN_nguon.md ^| Nhat ky: reports\BRAIN_nhat_ky.md
pause
