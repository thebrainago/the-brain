$ErrorActionPreference = "SilentlyContinue"
$lab = "C:\Users\SV STORE\Downloads\Research SP500\lab"
$du = @("_shot.ps1","_add.py","_r.ps1","_keys.py","_n.ps1","_t.ps1","_cap.png")
foreach ($f in $du) { $p = Join-Path $lab $f; if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force } }
Write-Output "cleaned"
