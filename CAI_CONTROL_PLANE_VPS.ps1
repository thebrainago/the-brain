# Cai control plane thanh Scheduled Task chay tu luc boot, khong can dang nhap.
# Chay PowerShell as Administrator:
#   powershell -ExecutionPolicy Bypass -File .\CAI_CONTROL_PLANE_VPS.ps1
param(
    [string]$TaskName = "TheBrainControlPlane",
    [string]$PythonPath = "C:\Users\SV STORE\AppData\Local\Python\pythoncore-3.14-64\python.exe",
    [string]$Account = "$env:USERDOMAIN\$env:USERNAME"
)

$ErrorActionPreference = "Stop"
$Lab = Split-Path -Parent $MyInvocation.MyCommand.Path
$Watchdog = Join-Path $Lab "giam_sat_dieu_phoi.py"

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principalNow = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principalNow.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Can mo PowerShell bang Run as administrator."
}
if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Khong tim thay Python: $PythonPath"
}
if (-not (Test-Path -LiteralPath $Watchdog)) {
    throw "Khong tim thay watchdog: $Watchdog"
}

Write-Host "Task se chay duoi tai khoan $Account." -ForegroundColor Cyan
Write-Host "Dung tai khoan Windows rieng, khong co quyen admin, neu dua len VPS." -ForegroundColor Yellow
$Credential = Get-Credential -UserName $Account -Message "Nhap mat khau de Task Scheduler chay khi chua dang nhap"

$Action = New-ScheduledTaskAction -Execute $PythonPath `
    -Argument ('"{0}"' -f $Watchdog) -WorkingDirectory $Lab
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Trigger.Delay = "PT30S"
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
    -Settings $Settings -User $Credential.UserName `
    -Password $Credential.GetNetworkCredential().Password -Force | Out-Null

Write-Host "Da cai task $TaskName." -ForegroundColor Green
Write-Host "Kiem: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Trang thai: & '$PythonPath' '$Lab\dieu_phoi.py' --trang-thai"
