# setup_vps.ps1 - Cai dat toan bo phong lab + bot tren VPS Windows moi
# Chay MOT LAN sau khi thue VPS (PowerShell as Administrator):
#     powershell -ExecutionPolicy Bypass -File setup_vps.ps1
# ==========================================================================
$ErrorActionPreference = "Stop"
$GOC = "C:\lab"
Write-Host "=== THE BRAIN — cai dat VPS ===" -ForegroundColor Cyan

# --- 0. kiem tai nguyen ---
$ram = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)
$disk = [math]::Round((Get-PSDrive C).Free/1GB,1)
$core = (Get-CimInstance Win32_Processor | Measure-Object NumberOfLogicalProcessors -Sum).Sum
Write-Host "  CPU logic: $core core · RAM: $ram GB · Disk trong: $disk GB"
if($disk -lt 40){ Write-Warning "Disk < 40GB — cache MT5 se day nhanh. Can >= 100GB." }
if($ram -lt 4){ Write-Warning "RAM < 4GB — chi chay duoc 2-3 terminal MT5 song song." }

# --- 1. Python ---
Write-Host "`n[1/6] Python..." -ForegroundColor Yellow
if(-not (Get-Command python -ErrorAction SilentlyContinue)){
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    $env:Path += ";$env:LOCALAPPDATA\Programs\Python\Python312;$env:LOCALAPPDATA\Programs\Python\Python312\Scripts"
}
python --version
python -m pip install --quiet --upgrade pip requests yt-dlp MetaTrader5 pandas numpy pyarrow

# --- 2. thu muc lab ---
Write-Host "`n[2/6] Thu muc lab..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force $GOC,"$GOC\data","$GOC\prompts","$GOC\reports" | Out-Null
Write-Host "  Copy toan bo thu muc 'lab\' + 'LuoiDoiXung.mq5' + cac file *.py can dung vao $GOC"
Write-Host "  (lab.py, PROMPT_DEEPSEEK.md, prompts\*, soi_tk_ultima.py, EA...)"

# --- 3. MetaTrader 5 ---
Write-Host "`n[3/6] MetaTrader 5..." -ForegroundColor Yellow
Write-Host "  Tai MT5 tu sàn ban dung (XM cho V6, Exness cho EURCAD cent)."
Write-Host "  Cai it nhat 2 terminal: 1 chay BOT that, 1 chay LAB tester."
Write-Host "  Sau khi cai: mo MetaEditor, bien dich LuoiDoiXung.mq5 -> .ex5"
Write-Host "  Roi tai lich su M1: mo chart EURCAD M1, keo ve 2013 (hoac dung nap_m1_*.py)"

# --- 4. LLM config (aibox box API cong ty HOAC DEEPSEEK_API_KEY) ---
Write-Host "`n[4/6] LLM config..." -ForegroundColor Yellow
Write-Host "  Neu neu may nha da co lay config.toml (provider aibox) -> copy vao .codex\"
Write-Host "  Neu dung key chinh chu:"
if(-not $env:DEEPSEEK_API_KEY){
    $k = Read-Host "  Dan DEEPSEEK_API_KEY (sk-...) [Enter de bo qua]"
    if($k -and $k -ne ""){
        [Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY",$k,"Machine")
        Write-Host "  Da luu DEEPSEEK_API_KEY. Mo lai PowerShell de co hieu luc."
    }
}

# --- 5. dieu chinh duong dan trong lab.py ---
Write-Host "`n[5/6] Sua duong dan trong lab.py cho khop VPS..." -ForegroundColor Yellow
Write-Host "  Mo $GOC\lab.py, sua:"
Write-Host "    MT5      = duong dan terminal64.exe cua terminal LAB"
Write-Host "    MT5_DATA = thu muc du lieu cua terminal do (%APPDATA%\MetaQuotes\Terminal\<hash>)"
Write-Host "    Tim hash: dir `$env:APPDATA\MetaQuotes\Terminal"

# --- 6. task tu dong chay 24/7 ---
Write-Host "`n[6/6] Lap lich chay 24/7..." -ForegroundColor Yellow
$batBot = "$GOC\chay_bot.bat"
@"
@echo off
REM Bot that: mo cac terminal MT5 co EA gan san (V6, EURCAD). MT5 tu chay theo lich EA.
start "" "C:\Program Files\Exness MT5\terminal64.exe"
"@ | Out-File $batBot -Encoding ascii

$batLab = "$GOC\chay_lab.bat"
@"
@echo off
cd /d $GOC
:loop
python bo_nao.py --lien-tuc --nghi 60
timeout /t 60
goto loop
"@ | Out-File $batLab -Encoding ascii

# Task Scheduler: chay lab khi khoi dong, tu bat lai neu tat
schtasks /Create /TN "TheBrain_Lab" /TR "$batLab" /SC ONSTART /RU SYSTEM /RL HIGHEST /F | Out-Null
schtasks /Create /TN "TheBrain_Bot" /TR "$batBot" /SC ONSTART /RU SYSTEM /RL HIGHEST /F | Out-Null
schtasks /Create /TN "BrainWatchdog" /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File $GOC\watchdog_brain.ps1" /SC MINUTE /MO 3 /F | Out-Null
Write-Host "  Da tao 3 task: TheBrain_Lab + TheBrain_Bot + BrainWatchdog (chong dừng)."

Write-Host "`n=== XONG. Buoc cuoi lam TAY: ===" -ForegroundColor Green
Write-Host "  1. Copy file lab (da huong dan o buoc 2)"
Write-Host "  2. Cai + dang nhap MT5, bien dich EA, tai lich su M1"
Write-Host "  3. Sua duong dan trong lab.py (buoc 5)"
Write-Host "  4. Kiem duong ong:  cd $GOC ; python lab.py --kho --vong 1"
Write-Host "  5. Chay that:        python lab.py --lien-tuc --nghi 1800"
Write-Host "  6. Xem thu vien:     python xem_thu_vien.py"
