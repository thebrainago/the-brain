# kiem_o_dia.ps1 - CHI DOC, khong ghi len bat ky o nao. PowerShell 5.1. Chay bang "Run as administrator".
# Muc dich: truoc khi khoi phuc du lieu, biet RO tung o dia la gi va tren o co con dau vet du lieu cu khong.
#   powershell -ExecutionPolicy Bypass -File kiem_o_dia.ps1
$ErrorActionPreference = 'Continue'
function Tieu($s) { Write-Host ''; Write-Host ('=== ' + $s) -ForegroundColor Cyan }
$gb = @{ n = 'GB'; e = { [math]::Round($_.Size / 1073741824, 1) } }
$trong = @{ n = 'ConTrongGB'; e = { [math]::Round($_.SizeRemaining / 1073741824, 1) } }

Tieu '1. O DIA VAT LY (MediaType: SSD hay HDD; BusType: USB = o ngoai)'
$c1 = @('DeviceId', 'FriendlyName', 'MediaType', 'BusType', $gb, 'HealthStatus')
Get-PhysicalDisk | Select-Object -Property $c1 | Format-Table -AutoSize

Tieu '2. KIEU BANG PHAN VUNG + PHAN VUNG (co khoang trong / UNALLOCATED khong?)'
$c2 = @('Number', 'FriendlyName', 'PartitionStyle', 'OperationalStatus', $gb)
Get-Disk | Select-Object -Property $c2 | Format-Table -AutoSize
$c3 = @('DiskNumber', 'PartitionNumber', 'DriveLetter', 'Type', $gb, 'Offset')
Get-Partition | Select-Object -Property $c3 | Format-Table -AutoSize
$c4 = @('DriveLetter', 'FileSystemLabel', 'FileSystem', $gb, $trong)
Get-Volume | Where-Object { $_.DriveLetter } | Select-Object -Property $c4 | Format-Table -AutoSize

Tieu '3. TRIM (SSD): DisableDeleteNotify = 0 nghia la TRIM BAT -> du lieu SSD da xoa gan nhu khong khoi phuc duoc'
fsutil behavior query DisableDeleteNotify

Tieu '4. GOC D: va E: (ke ca file an / he thong)'
$c5 = @('Mode', 'LastWriteTime', 'Name')
foreach ($o in 'D:', 'E:') {
    $goc = $o + '\'
    if (Test-Path -Path $goc) {
        Write-Host ('--- ' + $o)
        Get-ChildItem -Path $goc -Force -ErrorAction SilentlyContinue | Select-Object -Property $c5 | Format-Table -AutoSize
    }
}

Tieu '5. DUNG LUONG DA DUNG vs FILE NHIN THAY, va MFT (ban ghi file cu con luu o day)'
foreach ($ch in 'C', 'D', 'E') {
    $v = Get-Volume -DriveLetter $ch -ErrorAction SilentlyContinue
    if (-not $v) { continue }
    $dung = $v.Size - $v.SizeRemaining
    $goc = $ch + ':\'
    $ds = Get-ChildItem -Path $goc -Recurse -Force -File -ErrorAction SilentlyContinue
    $soFile = @($ds).Count
    $thay = ($ds | Measure-Object Length -Sum).Sum
    $mft = $null
    $t = (fsutil fsinfo ntfsinfo ($ch + ':') 2>$null) -join "`n"
    if ($t -match 'Mft Valid Data Length\s*:\s*0x([0-9a-fA-F]+)') { $mft = [math]::Round([Convert]::ToInt64($Matches[1], 16) / 1048576, 1) }
    $mftDuKien = [math]::Round($soFile / 1024, 1)
    $dongKq = '{0}:  da dung {1} GB | file nhin thay {2} file / {3} GB | MFT that {4} MB, du kien cho so file nay ~{5} MB'
    $dongKq -f $ch, [math]::Round($dung / 1073741824, 1), $soFile, [math]::Round($thay / 1073741824, 1), $mft, $mftDuKien
}
Write-Host ''
Write-Host 'Doc ket qua:' -ForegroundColor Yellow
Write-Host " - 'da dung' >> 'file nhin thay'  : con du lieu AN (quyen / he thong) - xem ky muc 4."
Write-Host " - 'MFT that' >> 'du kien'        : o nay TUNG chua rat nhieu file va bang file chua bi tao lai -> khoi phuc co TEN file co the duoc."
Write-Host " - 'MFT that' ~ 'du kien'         : bang file moi -> o da bi FORMAT/tao lai; chi con cach quet theo noi dung (PhotoRec / winfr /x)."
Write-Host ' - Day chi la dau hieu, khong phai ket luan.'
