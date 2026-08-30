schtasks /create /tn "BrainSweep" /xml "C:\Users\SV STORE\Downloads\Research SP500\lab\BrainSweep.xml" /f 2>$null
schtasks /run /tn "BrainSweep" 2>$null
Write-Output ("sweep launched rc=" + $LASTEXITCODE)
