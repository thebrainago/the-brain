# dung_slot_mt5.ps1 - dung N terminal MT5 PORTABLE (ban sao cua XM Global MT5 DEMO) de chay tester song song.
# Moi slot ~0,85 GB: cai dat (0,3 GB) + MQL5 + config + lich su CHI cua cac symbol can (mac dinh GOLD.i#).
# Dung:  powershell -File dung_slot_mt5.ps1 -N 3 [-Symbols 'GOLD.i#','AUDCAD#']
param([int]$N = 3, [string[]]$Symbols = @('GOLD.i#'))
$ErrorActionPreference = 'Stop'
$cai = 'C:\Program Files\XM Global MT5'
$dat = Join-Path $env:APPDATA 'MetaQuotes\Terminal\BB16F565FAAA6B23A20C26C49416FF05'
$gocSrv = Join-Path $dat 'bases\XMGlobal-MT5 10'
for ($i = 1; $i -le $N; $i++) {
    $d = "C:\MT5slots\s$i"
    if (Test-Path "$d\terminal64.exe") { "slot $i da co" ; continue }
    New-Item -ItemType Directory -Force $d | Out-Null
    robocopy $cai $d /E /NFL /NDL /NJH /NJS /NP | Out-Null
    robocopy (Join-Path $dat 'MQL5') "$d\MQL5" /E /NFL /NDL /NJH /NJS /NP | Out-Null
    robocopy (Join-Path $dat 'config') "$d\config" /E /NFL /NDL /NJH /NJS /NP | Out-Null
    robocopy (Join-Path $dat 'bases\Default') "$d\bases\Default" /E /NFL /NDL /NJH /NJS /NP | Out-Null
    robocopy (Join-Path $dat 'bases\Custom') "$d\bases\Custom" /E /NFL /NDL /NJH /NJS /NP | Out-Null
    $s = "$d\bases\XMGlobal-MT5 10"
    foreach ($sub in 'mail','news','subscriptions','symbols','trades','ticks') {
        if (Test-Path "$gocSrv\$sub") { robocopy "$gocSrv\$sub" "$s\$sub" /E /NFL /NDL /NJH /NJS /NP | Out-Null }
    }
    Copy-Item "$gocSrv\tickers.dat" $s -ErrorAction SilentlyContinue
    foreach ($sy in $Symbols) { robocopy "$gocSrv\history\$sy" "$s\history\$sy" /E /NFL /NDL /NJH /NJS /NP | Out-Null }
    "slot $i dung xong: $d"
}
