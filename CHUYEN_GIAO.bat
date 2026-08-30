@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ===== THE BRAIN - CHUYEN GIAO / SAO LUU CUOI PHIEN =====
python chuyen_giao.py
echo.
echo Ban giao: lab\BAN_GIAO_HOM_NAY.md  |  Snapshot: lab\reports\chuyen_giao\<ngay>
echo.
pause
