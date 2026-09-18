@echo off
chcp 65001 >nul
cd /d "%~dp0"
taskkill /IM python.exe /F >nul 2>&1
echo ===== BAT DAU THE BRAIN 24/7 =====
echo Dang chay dieu phoi vien o cua so thu nho (minimized)...
start "TheBrain24h" /min python brain_24h.py
timeout /t 3 >nul
echo.
echo Trang thai (tom tat):
python brain_24h.py --tom-tat
echo.
echo Nhip tim: reports\BRAIN_nhip_tim.json
pause
