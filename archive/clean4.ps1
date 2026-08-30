$lab="C:\Users\SV STORE\Downloads\Research SP500\lab"
$du=@("_f.py","_c.py","_m.ps1","_i.py","_i2.py","_bm_err.txt","_bm_out.txt","fix_loisai.py")
foreach($f in $du){ $p=Join-Path $lab $f; if(Test-Path -LiteralPath $p){ Remove-Item -LiteralPath $p -Force } }
Write-Output "cleaned"
