@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Tat THE BRAIN 24/7 (doc pid tu nhiem tim)...
powershell -NoProfile -Command "$j = Get-Content 'reports\BRAIN_nhip_tim.json' -Encoding UTF8 | ConvertFrom-Json; if ($j.pid) { Stop-Process -Id $j.pid -Force -ErrorAction SilentlyContinue; Write-Host ('Da tat pid ' + $j.pid) } else { Write-Host 'Khong co pid' }"
pause
