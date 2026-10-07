# cai_git.ps1 - PowerShell 5.1. Cai Git for Windows khi GitHub tai cham / winget treo.
# Tai tu cac MIRROR truoc (co resume, tu bo neu cham), kiem SHA-256 chinh thuc roi cai im lang.
#   powershell -ExecutionPolicy Bypass -File cai_git.ps1
# Luu y: URL mirror viet theo hieu biet, CHUA kiem duoc tu cloud - mirror nao hong thi script tu chuyen sang cai ke tiep;
# SHA-256 la rao cuoi: file sai hash bi xoa, khong bao gio duoc chay.
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProgressPreference = 'SilentlyContinue'
$dich = 'D:\Tai'
New-Item -ItemType Directory -Force -Path $dich | Out-Null

# 0. Dung moi winget dang treo (hai ban winget cung luc de dung nhau - mot nguyen nhan "treo")
foreach ($ten in @('winget', 'WindowsPackageManagerServer')) { Get-Process -Name $ten -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue }

# 1. Ban moi nhat + SHA-256 chinh thuc tu github.com / api.github.com (file nho, khong phai CDN cham)
$rel = Invoke-RestMethod 'https://api.github.com/repos/git-for-windows/git/releases/latest' -Headers @{ 'User-Agent' = 'cai_git' }
$asset = $rel.assets | Where-Object { $_.name -match '^Git-.*-64-bit\.exe$' } | Select-Object -First 1
if (-not $asset) { throw 'Khong tim thay Git-*-64-bit.exe trong ban phat hanh moi nhat' }
$ten = $asset.name
$tag = $rel.tag_name
$sha = $null
if ($asset.PSObject.Properties['digest'] -and $asset.digest -match 'sha256:([0-9a-fA-F]{64})') { $sha = $Matches[1] }
elseif ($rel.body -match ([regex]::Escape($ten) + '\s*\|\s*([0-9a-fA-F]{64})')) { $sha = $Matches[1] }
if (-not $sha) { throw "Khong lay duoc SHA-256 chinh thuc cua $ten - mo trang release tren github.com, chep hash vao bien `$sha roi chay lai" }
$sha = $sha.ToLower()
Write-Host "Ban: $tag  file: $ten  SHA-256: $sha"

# 2. Danh sach nguon: mirror -> chinh thuc (cuoi cung, chap nhan cham)
$nguon = @(
    @{ url = "https://registry.npmmirror.com/-/binary/git-for-windows/$tag/$ten"; toiThieu = 100000; giay = 15 },
    @{ url = "https://cdn.npmmirror.com/binaries/git-for-windows/$tag/$ten"; toiThieu = 100000; giay = 15 },
    @{ url = "https://mirrors.huaweicloud.com/git-for-windows/$tag/$ten"; toiThieu = 100000; giay = 15 },
    @{ url = $asset.browser_download_url; toiThieu = 5000; giay = 90 }
)
$out = Join-Path $dich $ten
$xong = $false
foreach ($n in $nguon) {
    Write-Host ("Thu: " + $n.url)
    # curl.exe co san tu Windows 10 1803. -C - = tiep tuc file do; bo neu toc do < toiThieu byte/giay trong `giay` giay.
    $a = @('-L', '--fail', '--silent', '--show-error', '--retry', '2', '--retry-delay', '2', '--connect-timeout', '10',
           '--speed-limit', [string]$n.toiThieu, '--speed-time', [string]$n.giay, '-C', '-', '-o', $out, $n.url)
    & curl.exe @a
    if ($LASTEXITCODE -ne 0) { Write-Host "  -> bo (ma $LASTEXITCODE), thu nguon ke"; continue }
    $h = (Get-FileHash $out -Algorithm SHA256).Hash.ToLower()
    if ($h -eq $sha) { $xong = $true; break }
    Write-Host "  -> SAI hash ($h), xoa file va thu nguon ke"
    Remove-Item $out -Force -ErrorAction SilentlyContinue
}
if (-not $xong) { throw 'Khong nguon nao tai duoc file dung hash. Dung clone_khong_can_git.ps1 de lay ma truoc, cai Git sau.' }

# 3. Cai im lang, roi lam moi PATH ngay trong cua so nay (khong can mo terminal moi)
Start-Process -FilePath $out -ArgumentList '/VERYSILENT', '/NORESTART', '/SUPPRESSMSGBOXES', '/NOCANCEL', '/SP-' -Wait
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
git --version
