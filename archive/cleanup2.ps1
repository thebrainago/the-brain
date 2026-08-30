$ErrorActionPreference = "SilentlyContinue"
$lab = "C:\Users\SV STORE\Downloads\Research SP500\lab"
$du = @("_patch.py","_t.ps1","_m.ps1","reinstall_keeper.ps1","BrainThorn.xml","cleanup.ps1")
foreach ($f in $du) { $p = Join-Path $lab $f; if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force } }
Write-Output "temp cleaned"
