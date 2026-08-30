$ErrorActionPreference = "SilentlyContinue"
$lab = "C:\Users\SV STORE\Downloads\Research SP500\lab"
$lock = Join-Path $lab "bo_nao.lock"
$py = "C:\Users\SV STORE\sp500_env\Scripts\python.exe"

# co daemon dang chay khong?
$alive = $false
if (Test-Path -LiteralPath $lock) {
    $pid_val = Get-Content -LiteralPath $lock -Raw
    $pid_val = $pid_val.Trim()
    if ($pid_val -match "^\d+$") {
        $alive = [bool](Get-Process -Id ([int]$pid_val) -ErrorAction SilentlyContinue)
    }
}
if ($alive) { exit 0 }

# chua chay -> khoi dong lai (detached)
$log = Join-Path $lab "bo_nao.log"
$err = Join-Path $lab "bo_nao.err"
if (-not (Test-Path -LiteralPath $lab)) { New-Item -ItemType Directory -Path $lab -Force | Out-Null }
Start-Process -FilePath $py -ArgumentList "bo_nao.py","--lien-tuc","--nghi","30" -WorkingDirectory $lab -WindowStyle Hidden -RedirectStandardOutput $log -RedirectStandardError $err
Add-Content -Path (Join-Path $lab "watchdog.log") -Value ("restart " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
exit 0
