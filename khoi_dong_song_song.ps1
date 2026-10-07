# Chay sau khi dang nhap (Task Scheduler "TheBrainSongSong"): go CAU_DUNG, mo N bo chay CPU song song (hop thu cau_hop_thu_pN)
# + 3 bo TESTER-ONLY m1..m3 (hop thu cau_hop_thu_mN, moi bo 1 slot MT5; CAU_CHI_LAN=TESTER). Bo chinh 'nha' (TheBrainCauChay) cung TESTER-only.
# Moi bo: CAU_HOP_THU / CAU_TEN=nha-pN / CAU_KHA_NANG=windows,data. Dieu toc: config\dieu_toc.json.
param([int]$N=18)
$lab="C:\Research SP500\lab"
& "$lab\ramdisk_khoi_dong.ps1"   # dia RAM R: + junction data/cache (idempotent)
Start-Sleep 60
[IO.File]::Delete("$lab\CAU_DUNG")
# sau restart khong con tester nao song -> go khoa tester cu
Get-ChildItem "C:\Research SP500" -Directory -Filter "cau_hop_thu*" | % { [IO.File]::Delete("$($_.FullName)\viec\.khoa_tester") }
function Mo($id,$kn,$chi){
  $d="C:\Research SP500\cau_hop_thu_$id"
  if(Test-Path "$d\.git"){
    $env:CAU_HOP_THU=$d; $env:CAU_TEN="nha-$id"; $env:CAU_KHA_NANG=$kn
    if($chi){$env:CAU_CHI_LAN=$chi}else{$env:CAU_CHI_LAN=""}
    Start-Process -WindowStyle Hidden -FilePath "$lab\.venv\Scripts\python.exe" -ArgumentList "b.py","cau","chay","--lien-tuc","--nghi","20" -WorkingDirectory $lab -RedirectStandardOutput "$lab\nhat_ky\chay_$id.log" -RedirectStandardError "$lab\nhat_ky\chay_$id.err"
    Start-Sleep 5 } }
1..3 | % { Mo "m$_" "windows,mt5,data" "TESTER" }
1..$N | % { Mo "p$_" "windows,data" $null }
