$lab = "C:\Users\SV STORE\Downloads\Research SP500\lab"
$arc = Join-Path $lab "archive"
New-Item -ItemType Directory -Force -Path $arc | Out-Null
# 1) xoa __pycache__ (an toan, tu dung lai)
Get-ChildItem -LiteralPath $lab -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
# 2) gom temp/scratch + log rac vao archive (khong xoa)
$gom = @("_c.py","_e.py","_q.py","_s.ps1","_chup_darwinex.ps1","_chup_manhinh.ps1","_ocr.ps1",
         "clean3.ps1","clean4.ps1","cleanup2.ps1",
         "bo_nao.err","bo_nao.log","epxung.err","mt5_run.err","mt5_run.out",
         "thorn.err.log","thorn.out.log","watchdog.log","snap_log.txt",
         "da_nhiem_banker.log","da_nhiem_quantlab.log","da_nhiem_seeker.log")
foreach($f in $gom){ $p=Join-Path $lab $f; if(Test-Path -LiteralPath $p){ Move-Item -LiteralPath $p -Destination $arc -Force } }
# 3) xoa .lock rac (da het dung)
foreach($f in @("bo_nao.lock","thorn.lock")){ $p=Join-Path $lab $f; if(Test-Path -LiteralPath $p){ Remove-Item -LiteralPath $p -Force } }
Write-Output ("archived count=" + @(Get-ChildItem -LiteralPath $arc -File).Count)
