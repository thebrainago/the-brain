$ErrorActionPreference = "SilentlyContinue"
$lab = "C:\Users\SV STORE\Downloads\Research SP500\lab"
# kill python cũ
Get-CimInstance Win32_Process -Filter "Name like 'python%'" | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
schtasks /end /tn "BrainThorn" | Out-Null
schtasks /delete /tn "BrainThorn" /f | Out-Null
Start-Sleep -Seconds 2
# tao va chay lai
$xml = Join-Path $lab "BrainThorn.xml"
schtasks /create /tn "BrainThorn" /xml $xml /f | Out-Null
schtasks /run /tn "BrainThorn" | Out-Null
Write-Output ("create+run done rc=" + $LASTEXITCODE)
