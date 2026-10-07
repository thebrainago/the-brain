# Dia RAM R: (OSFMount) cho data nong + cache MT5 tester. Chu du an duyet 07/10/2026.
# - Ban goc nam o lab\data_goc va D:\MT5cache\*; lab\data va <slot>\Tester la JUNCTION sang R:.
# - Chay luc khoi dong (Task TheBrainRamdisk, SYSTEM) va dau khoi_dong_song_song.ps1; tu bo qua phan da xong.
# - -DongBo: chep nguoc R: -> ban goc (chi file moi hon, khong xoa) de ket qua khong mat khi tat may. Task TheBrainRamdiskDongBo 10 phut/lan.
# - Dia RAM chi gom ban sao; che_do_choi chi tam dung runner, KHONG go dia (can giu khi choi LoL).
param([switch]$DongBo, [int]$GB = 4)
$lab = "C:\Research SP500\lab"
$gocData = "$lab\data_goc"
$tester = @(
  @{ link = "C:\MT5slots\s1\Tester"; ten = "s1_Tester"; exe = "C:\MT5slots\s1\*" },
  @{ link = "C:\MT5slots\s2\Tester"; ten = "s2_Tester"; exe = "C:\MT5slots\s2\*" },
  @{ link = "C:\MT5slots\s3\Tester"; ten = "s3_Tester"; exe = "C:\MT5slots\s3\*" },
  @{ link = "C:\Users\DUNG\AppData\Roaming\MetaQuotes\Terminal\BB16F565FAAA6B23A20C26C49416FF05\Tester"; ten = "Tester_AppData"; exe = "C:\Program Files\XM Global MT5\*" }
)
function Log($m) { Add-Content "$lab\nhat_ky\ramdisk.log" "$(Get-Date -f 'yyyy-MM-dd HH:mm:ss') $m" }
function Copy-Dir($src, $dst) { robocopy $src $dst /E /MT:8 /R:0 /W:0 /NFL /NDL /NJH /NJS /NP | Out-Null }

if ($DongBo) {
  if (-not (Test-Path "R:\")) { exit 0 }
  if (Test-Path "R:\data") { robocopy "R:\data" $gocData /E /XO /R:0 /W:0 /NFL /NDL /NJH /NJS /NP | Out-Null }
  foreach ($t in $tester) { if (Test-Path "R:\MT5cache\$($t.ten)") { robocopy "R:\MT5cache\$($t.ten)" "D:\MT5cache\$($t.ten)" /E /XO /R:0 /W:0 /NFL /NDL /NJH /NJS /NP | Out-Null } }
  exit 0
}

# 1. Dia RAM
if (-not (Test-Path "R:\")) {
  Start-Process -FilePath "C:\Program Files\OSFMount\OSFMount.com" -ArgumentList "-a -t vm -s ${GB}G -m R: -o rw" -WindowStyle Hidden
  for ($i = 0; $i -lt 30 -and -not (Test-Path "R:\\"); $i++) { Start-Sleep 1 }
  Start-Sleep 2
  cmd /c "echo Y| format R: /fs:ntfs /q /y /v:RAMDISK" | Out-Null
  Log "tao dia RAM R: ${GB}GB"
}
if (-not (Test-Path "R:\")) { Log "LOI: khong co R:"; exit 1 }

# 2. data nong: lab\data -> junction R:\data (ban goc o data_goc)
$d = "$lab\data"
$laJunction = (Test-Path $d) -and ((Get-Item $d -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)
if (-not (Test-Path $gocData) -and -not $laJunction) {
  try { Rename-Item $d "data_goc" -ErrorAction Stop; Log "doi data -> data_goc" } catch { Log "KHONG doi duoc data (file dang mo): $_" }
}
if (Test-Path $gocData) {
  if (-not (Test-Path "R:\data")) { Copy-Dir $gocData "R:\data"; Log "chep data -> R:\data" }
  if (-not (Test-Path $d)) { cmd /c "mklink /J `"$d`" R:\data" | Out-Null; Log "junction data -> R:\data" }
}

# 3. cache MT5 tester: chi doi khi slot ranh (khong terminal64 nao dang chay trong slot)
foreach ($t in $tester) {
  $goc = "D:\MT5cache\$($t.ten)"; $ram = "R:\MT5cache\$($t.ten)"
  if ((Test-Path $goc) -and -not (Test-Path $ram)) { Copy-Dir $goc $ram }   # sau khoi dong junction cu tro vao R: chua co gi
  if (-not (Test-Path $t.link)) { continue }
  $it = Get-Item $t.link -Force
  if ($it.Target -and ($it.Target -join "") -like "R:*") { if (-not (Test-Path $ram)) { Copy-Dir $goc $ram }; continue }
  if (-not ($it.Attributes -band [IO.FileAttributes]::ReparsePoint)) { continue }
  $ban = Get-CimInstance Win32_Process -Filter "Name='terminal64.exe'" | ? { $_.ExecutablePath -like $t.exe }
  if ($ban) { Log "bo qua $($t.ten): slot dang chay"; continue }
  if (-not (Test-Path $ram)) { Copy-Dir $goc $ram }
  cmd /c "rmdir `"$($t.link)`"" | Out-Null
  cmd /c "mklink /J `"$($t.link)`" `"$ram`"" | Out-Null
  Log "junction $($t.ten) -> $ram"
}
