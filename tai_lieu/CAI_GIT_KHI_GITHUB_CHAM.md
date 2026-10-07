# CÀI GIT KHI GITHUB TẢI CHẬM / WINGET TREO (PowerShell 5.1)

> Viết 02/10/2026. Bối cảnh: `winget install --id Git.Git -e` tải khoảng 27 KB/s rồi treo; `github.com`, `python.org`, `claude.ai`
> vẫn vào bình thường. Script trong `khoi_phuc\` đã qua bộ phân tích cú pháp PowerShell (tree-sitter) nhưng **chưa chạy trên Windows thật**;
> URL mirror viết theo hiểu biết, chưa kiểm được từ cloud — mirror nào hỏng script tự bỏ qua, và file sai SHA-256 không bao giờ được chạy.

## 0. Hiểu vấn đề trước khi thử (30 giây)

`winget` lấy file cài Git từ **kho phát hành (release assets) của GitHub**, nằm trên CDN khác với trang `github.com`. Trang web nhanh không có nghĩa file nhanh.
File cài ≈ 65 MB; ở 27 KB/s mất ≈ 40 phút và hay treo. **Đừng chờ Git để bắt đầu làm việc**: toàn bộ repo chỉ ≈ **17 MB** (gói git) nên lấy
thẳng được bằng cách không cần Git (mục 1), và Git cài song song sau.

## 1. Lấy mã NGAY, không cần Git (Dulwich — Git viết bằng Python, tải từ PyPI)

```powershell
powershell -ExecutionPolicy Bypass -File .\khoi_phuc\clone_khong_can_git.ps1
# hoặc dán trực tiếp (không cần repo): xem tin nhắn hướng dẫn; thêm -Nong để chỉ lấy commit mới nhất
```
Kết quả là repo git **thật** ở `C:\Research SP500\lab` (đã checkout nhánh `claude/autonomous-trading-system-rzzt7h`). Cài Git xong thì `git status`,
`git pull`, `git push` chạy ngay trên chính thư mục đó (đã kiểm: Git thật đọc được repo do Dulwich tạo, kể cả clone nông + `git fetch --unshallow`).
Lưu ý: clone ẩn danh chỉ chạy khi repo **public**; nếu sau này chuyển private thì cần Git + đăng nhập GitHub (hãy clone *trước* khi đổi).

## 2. Cài Git nhanh bằng mirror (có resume, tự bỏ nếu chậm, kiểm SHA-256)

```powershell
powershell -ExecutionPolicy Bypass -File .\khoi_phuc\cai_git.ps1
```
Việc nó làm: (0) dừng mọi `winget` đang treo (hai bản winget cùng lúc có thể giẫm nhau); (1) hỏi `api.github.com` bản mới nhất và **SHA-256 chính thức**;
(2) thử lần lượt `registry.npmmirror.com` → `cdn.npmmirror.com` → `mirrors.huaweicloud.com` → nguồn chính thức, bằng `curl.exe -C -` (tiếp tục file dở) và
`--speed-limit/--speed-time` (bỏ nguồn nào dưới 100 KB/s trong 15 giây; nguồn chính thức chấp nhận chậm tới 5 KB/s); (3) so SHA-256 — sai thì xoá, thử nguồn kế;
(4) cài im lặng `/VERYSILENT /NORESTART`, rồi **làm mới PATH ngay trong cửa sổ này** (không cần mở terminal mới):
```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
git --version
```
Làm bằng tay (nếu muốn): vào trang liệt kê bản phát hành của mirror (`npmmirror.com/mirrors/git-for-windows/`), tải `Git-<ver>-64-bit.exe` bằng trình duyệt,
rồi so `Get-FileHash <file> -Algorithm SHA256` với hash ghi trên trang release **trên github.com** trước khi chạy.

## 3. Sửa `winget` treo (nếu vẫn muốn dùng winget)

```powershell
# a) dừng bản đang treo, đừng chạy hai bản cùng lúc
Get-Process winget -ErrorAction SilentlyContinue | Stop-Process -Force
# b) đổi bộ tải: mở `winget settings` và đặt  "network": { "downloader": "wininet" }   (hoặc "do" = Delivery Optimization, có resume)
winget settings
# c) chạy có giới hạn thời gian, chỉ nguồn winget (bỏ msstore), không hỏi
$p = Start-Process winget -PassThru -NoNewWindow -ArgumentList 'install','--id','Git.Git','-e','--source','winget','--silent','--disable-interactivity','--accept-source-agreements','--accept-package-agreements'
if (-not $p.WaitForExit(900000)) { $p.Kill(); 'winget treo > 15 phut, da dung' }
```
Giới hạn thẳng: `winget` vẫn tải từ GitHub nên **mirror (mục 2) mới là cách tăng tốc thật**; các bước trên chỉ giúp nó đỡ treo và không đứng vô hạn.

## 4. Các phương án còn lại

| Phương án | Cách | Ghi chú |
|---|---|---|
| MinGit (zip, không cài) | tải `MinGit-<ver>-64-bit.zip` từ mirror ở mục 2, giải nén `D:\Tools\mingit`, thêm `...\cmd` vào PATH | nhỏ hơn (~45 MB), đủ cho clone/pull/push; **không có Git Credential Manager** → push cần token (PAT) |
| ZIP nhánh | `curl.exe -L -C - -o D:\Tai\lab.zip https://github.com/thebrainago/the-brain/archive/refs/heads/claude/autonomous-trading-system-rzzt7h.zip` rồi `Expand-Archive` | lấy được mã nhưng không có `.git`; chỉ khi Dulwich không chạy |
| Git qua `scoop`/`choco` | — | vẫn tải từ GitHub CDN, không nhanh hơn |

## 5. Sau khi có mã (và Git)

```powershell
cd "C:\Research SP500\lab"
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt     # bị vướng gói nào thì cài nhóm tối thiểu:
# .\.venv\Scripts\python -m pip install numpy pandas scipy requests psutil pyarrow MetaTrader5 pytest pytest-xdist
.\b.cmd khoi-phuc
.\b.cmd cau hook-cai                                           # Claude Code ở nhà tự hiện thư từ cloud ở câu kế tiếp
.\b.cmd cau dat-session session_01ER1xpfauUywJ6smLMSZmHW       # để /bao-len đánh thức được phiên cloud
claude
```
`git push` lần đầu: Git Credential Manager mở trình duyệt đăng nhập GitHub một lần.
Báo lên cloud ngay cả **khi chưa có Git**: `claude -p "<nội dung>" --cloud session_01ER1xpfauUywJ6smLMSZmHW`.
