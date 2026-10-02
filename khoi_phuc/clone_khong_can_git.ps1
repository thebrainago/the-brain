# clone_khong_can_git.ps1 - PowerShell 5.1. Lay repo ve KHONG can Git: dung Dulwich (Git viet bang Python, tai tu PyPI).
# Repo chi ~17 MB nen xong nhanh ke ca khi GitHub cham. Ket qua la repo git THAT: sau nay cai Git xong thi `git status` dung ngay.
#   powershell -ExecutionPolicy Bypass -File clone_khong_can_git.ps1
#   (them -Nong de chi lay commit moi nhat; sau do `git fetch --unshallow` neu can lich su)
# Luu y: repo phai dang PUBLIC. Neu da chuyen private thi clone an danh se bi tu choi - dung Git + dang nhap GitHub.
param(
    [string]$Nhanh = 'claude/autonomous-trading-system-rzzt7h',
    [string]$Dich = 'C:\Research SP500\lab',
    [switch]$Nong
)
$ErrorActionPreference = 'Stop'
$cha = Split-Path $Dich -Parent
New-Item -ItemType Directory -Force -Path $cha | Out-Null      # Dulwich khong tu tao thu muc cha
if (Test-Path $Dich) { throw "$Dich da ton tai - doi ten hoac xoa truoc." }
# Tim Python that (khong dung ban WindowsApps - stub cua Store). PATH cua cua so nay co the chua co Python moi cai.
$py = $null
$lenh = Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1
if ($lenh) { $py = $lenh.Source }
if (-not $py) {
    $ungVien = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
    if (Test-Path -Path $ungVien) { $py = $ungVien }
}
if (-not $py) { throw 'Khong tim thay Python that. Cai Python 3.12 truoc (python.org) roi chay lai.' }
& $py -m pip install --user --quiet dulwich
$tam = Join-Path $env:TEMP 'clone_dulwich.py'
@'
import sys
from dulwich import porcelain
url, dich, nhanh, nong = sys.argv[1:5]
kw = {"branch": nhanh}
if nong == "1":
    kw["depth"] = 1
porcelain.clone(url, dich, **kw)
print("xong:", dich)
'@ | Set-Content -Path $tam -Encoding ASCII
$nongArg = '0'
if ($Nong) { $nongArg = '1' }
& $py $tam 'https://github.com/thebrainago/the-brain.git' $Dich $Nhanh $nongArg
