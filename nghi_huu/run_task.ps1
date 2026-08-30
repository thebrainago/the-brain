$ErrorActionPreference = "SilentlyContinue"
$lab = "C:\Users\SV STORE\Downloads\Research SP500\lab"
$xml = Join-Path $lab "BrainThorn.xml"
schtasks /create /tn "BrainThorn" /xml $xml /f
Write-Output ("create rc=" + $LASTEXITCODE)
schtasks /run /tn "BrainThorn"
Write-Output ("run rc=" + $LASTEXITCODE)
Start-Sleep -Seconds 12
schtasks /query /tn "BrainThorn" /fo list /v | Select-String -Pattern "Task To Run|^Status|Last Run Time|Last Result|Scheduled Task State|TaskName"
