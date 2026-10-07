# KHÔI PHỤC DỮ LIỆU — HDD `E:` (còn cơ hội), SSD `C:`/`D:` (gần như không)

> Viết 02/10/2026 theo báo cáo của phiên Claude Code ở nhà. Máy: Windows 10 Pro, user `DUNG`; `C:` SSD 119 GB (hệ
> điều hành), `D:` SSD 119 GB (gần trống, có thư mục `Claude`), `E:` HDD 233 GB MBR (chỉ còn `Riot Games`).
> Đã biết: không có `Windows.old`, không có Shadow Copy / Restore Point, OneDrive trống, thùng rác chỉ có rác cài game.
> Mọi lệnh dùng được trên **PowerShell 5.1**, mở bằng *Run as administrator*. Lệnh `winfr` và các cờ của nó ghi theo
> hiểu biết của người viết, **chưa kiểm được từ cloud** (tài liệu Microsoft bị chặn ở đây): chạy `winfr /?` trên máy để
> đối chiếu trước khi chạy thật.

## 0. Bốn nguyên tắc

1. **Không ghi lên ổ nguồn.** Mọi thứ cài, tải, lưu kết quả, giải nén công cụ → ổ khác (`D:` hoặc ổ USB). Không cài
   gì vào `E:`; không phục hồi *vào chính* `E:`.
2. **Đọc trước, ghi sau.** TestDisk có chế độ phân tích chỉ đọc; `winfr` chỉ đọc nguồn. Không bấm `Write` trong TestDisk
   trước khi đã chép dữ liệu ra.
3. **Mọi thứ đang chạy trên `E:` có thể đè dữ liệu cũ** — Riot/Vanguard cập nhật game, và nhất là **Tối ưu hoá ổ đĩa
   (defrag) định kỳ hằng tuần** của Windows, vốn *di chuyển file vào đúng các cụm trống chứa dữ liệu đã xoá*. Tắt ngay (mục 2, bước 0).
4. **Kỳ vọng thực tế.** HDD: có cơ hội, tuỳ cách Windows đã được cài lại (mục 1). SSD: gần như không (TRIM).
   Mã nguồn **không nằm trong số cần cứu** — đã an toàn trên GitHub.

## 1. Ba câu hỏi quyết định "cứu được hay không"

**(a) Windows được cài lại bằng cách nào?** Câu trả lời đổi hẳn cơ hội:

| Cách | Hệ quả với `E:` / `D:` |
|---|---|
| USB cài mới, chỉ xoá/format phân vùng `C:` | `D:`/`E:` không bị đụng → dữ liệu cũ còn nếu chưa bị ghi đè sau đó |
| USB cài mới, xoá/tạo lại *cả* phân vùng ở `D:`/`E:` | bảng phân vùng đổi; nếu chỉ xoá bảng mà **chưa format** → TestDisk khôi phục trọn vẹn; nếu đã quick-format → quét theo nội dung |
| *Reset this PC* → *Remove everything* → **All drives** | xoá cả `D:`/`E:`; nếu bật **"Clean data"** thì ghi đè toàn bộ → **mất hẳn** (kể cả HDD) |

Nếu nhớ được, ghi lại đúng lựa chọn đã bấm. Nếu không nhớ: quét thử 20–30 phút (bước 4) — ra rất ít hay không ra gì ngoài file
Riot ⇒ nhiều khả năng đã bị ghi đè.

**(b) `E:` có từng chứa nhiều thứ không?** Chạy `khoi_phuc\kiem_o_dia.ps1` (chỉ đọc). Hai chỉ báo:
- "đã dùng" ≫ "file nhìn thấy" ⇒ còn dữ liệu ẩn / không có quyền xem (kiểm lại bằng `Get-ChildItem E:\ -Force`);
- **MFT thật ≫ MFT dự kiến** ⇒ bảng file (MFT) chưa bị tạo lại, bản ghi của file cũ còn ⇒ có thể khôi phục *kèm tên*. MFT thật
  ≈ dự kiến ⇒ ổ đã được format/tạo lại.

**(c) Dữ liệu cần cứu là loại gì?** Ảnh/tài liệu/video/zip cứu tốt bằng quét theo nội dung; file `.py/.json/.md` thì
đã có trên GitHub; `nao.db` / bảng giá `.parquet` / `ds/` bạn đã quyết định không cần (làm lại từ đầu) — trừ `ds/` nếu muốn giữ.

## 2. Quy trình cho `E:` (HDD), theo thứ tự

**Bước 0 — Đóng băng (làm ngay, 2 phút).**
```powershell
# thoát Riot Client / Vanguard; không mở game; không cài/cập nhật gì trên E:
Disable-ScheduledTask -TaskPath '\Microsoft\Windows\Defrag\' -TaskName 'ScheduledDefrag'   # tắt tối ưu/defrag định kỳ
powercfg /change standby-timeout-ac 0        # máy cắm điện không ngủ giữa chừng khi quét
powercfg /change disk-timeout-ac 0
```
Nếu `Get-PhysicalDisk` báo `HealthStatus` ≠ Healthy hoặc ổ kêu lạch cạch: **dừng**, đừng quét — ổ đang hỏng cần sao ảnh/ dịch vụ.

**Bước 1 — Thu thập sự thật (chỉ đọc).**
```powershell
powershell -ExecutionPolicy Bypass -File .\khoi_phuc\kiem_o_dia.ps1
```
Gửi kết quả cho phiên cloud (`/bao-len` hoặc dán) — chú ý: ổ `E:` là *Disk* số mấy, có khoảng `Unallocated` không, MFT.

**Bước 2 — Chuẩn bị chỗ chứa.** `D:\KhoiPhuc` (SSD, còn ~110 GB). Đủ cho quét *chọn loại file*; nếu phải cứu *mọi thứ* trên 233 GB,
dùng ổ USB/HDD ngoài ≥ 250 GB. **Chỗ chứa luôn khác ổ nguồn.**
```powershell
New-Item -ItemType Directory -Force -Path D:\KhoiPhuc\E | Out-Null
(Get-Volume -DriveLetter D).SizeRemaining / 1GB     # GB còn trống
```

**Bước 3 — Windows File Recovery (`winfr`, của Microsoft — không cài phần mềm bên thứ ba).** Cần Windows 10 bản 2004 trở lên.
```powershell
winget install --id 9N26S50LN705 -e --source msstore --accept-source-agreements --accept-package-agreements
# hoặc mở Microsoft Store, tìm "Windows File Recovery"
winfr /?                          # đọc lại cú pháp, các chế độ và cờ trên máy này
winfr /#                          # liệt kê nhóm "chữ ký" file dùng cho chế độ /x
```
Quét nhanh (NTFS, file còn bản ghi MFT → có tên và thư mục), lọc theo đuôi để đỡ rác:
```powershell
winfr E: D:\KhoiPhuc\E /regular /n *.docx /n *.xlsx /n *.pdf /n *.jpg /n *.png /n *.zip /n *.db /n *.py
```
`winfr` hỏi `Continue? (y/n)` rồi tạo thư mục `Recovery_<ngày giờ>` trong đích. Không ra gì → **chế độ mở rộng** (xoá lâu / đã format;
HDD 233 GB mất khoảng 1–3 giờ):
```powershell
winfr E: D:\KhoiPhuc\E /extensive /n *.docx /n *.xlsx /n *.pdf /n *.jpg /n *.png /n *.zip /n *.db /n *.py
```
Quét theo **chữ ký nội dung** (không cần tên; dùng khi ổ đã format hay hỏng):
```powershell
winfr E: D:\KhoiPhuc\E /x /y:PDF,JPEG,PNG,ZIP        # tên nhóm lấy từ `winfr /#`
```

**Bước 4 — TestDisk (bản zip chạy thẳng, KHÔNG cài đặt — giải nén vào `D:\Tools`).** Chỉ khi bạn đồng ý (đã từ chối cài lần trước).
Tải từ trang chủ nhà phát triển `cgsecurity.org` (mục TestDisk Download, bản Windows 64-bit `.zip`). Chạy `testdisk_win.exe` *as administrator*:
1. `Create` (tạo log, đặt ở `D:\Tools`) → chọn **đĩa** của `E:` (khớp dung lượng 233 GB) → kiểu bảng `Intel` (MBR) → `Analyse` → `Quick Search`.
2. Nếu hiện một phân vùng NTFS lớn đánh dấu `D` (Deleted) → bấm `P` để xem file. Thấy file cũ ⇒ bấm `c` (copy) và chọn đích `D:\KhoiPhuc\E_testdisk`.
   **Chưa bấm `Write`.** Chỉ ghi lại bảng phân vùng sau khi đã chép hết dữ liệu ra, và thường không cần.
3. Không thấy gì → `Deeper Search` (rất lâu). Vẫn không → sang bước 5.
4. Với phân vùng nhận được: `Advanced` → chọn phân vùng → `Undelete` liệt kê file đã xoá còn tên.

**Bước 5 — PhotoRec (cùng gói TestDisk; cắt file theo nội dung — phương án cuối).** `photorec_win.exe` as administrator →
chọn đĩa của `E:` → phân vùng (hoặc *Whole disk*) → `[File Opt]`: bỏ chọn hết (`s`) rồi tick loại cần (jpg, png, pdf, zip, sqlite…) →
`Whole` (quét cả vùng, dùng khi đã format) → đích `D:\KhoiPhuc\E_photorec`. Kết quả là hàng nghìn file **không tên** trong `recup_dir.N`.

**Bước 6 — Phân loại và kiểm.**
```powershell
Get-ChildItem D:\KhoiPhuc -Recurse -File | Group-Object Extension | Sort-Object Count -Descending | Select-Object -First 15 Name, Count
```
Mở thử vài file mỗi loại (ảnh mở được? PDF đọc được?). Copy phần cứu được ra **ổ khác nữa** (USB / Drive) ngay.

**Bước 7 — Dừng đúng lúc.** Quét `/extensive` + `/x` + PhotoRec xong mà chỉ ra file Riot / rác ⇒ ổ đã bị ghi đè sạch (xem 1a). Dừng, chuyển sang mục 4.

## 3. Chọn công cụ nào

| Công cụ | Cài đặt | Mạnh | Yếu | Dùng khi |
|---|---|---|---|---|
| `winfr` (Microsoft) | Store, Win10 ≥ 2004 | NTFS: kèm **tên + thư mục**; có quét theo chữ ký | chậm; không có giao diện; SSD kém | **đầu tiên** — hãng Microsoft, không thêm phần mềm lạ |
| TestDisk | zip, không cài | phân vùng bị xoá/đổi; khôi phục cả cấu trúc thư mục; `Undelete` | giao diện chữ; vô dụng nếu đã ghi đè | khi nghi chỉ *bảng phân vùng* bị đổi |
| PhotoRec | cùng gói TestDisk | chạy được trên ổ đã format/hỏng, mọi hệ tệp | mất tên + thư mục; ra rất nhiều file lộn xộn | phương án cuối, cho ảnh/tài liệu |
| Recuva | cài (có chào mời CCleaner) | dễ dùng | không hơn `winfr` | tuỳ chọn |

## 4. Hai ổ SSD (`C:`, `D:`)

- Windows 10 bật **TRIM**: khi xoá/format, ổ được báo vùng đó "trống" và tự dọn thành số 0 trong vài giây đến vài phút. `fsutil behavior
  query DisableDeleteNotify` = `0` nghĩa là TRIM đang bật (mặc định).
- `C:` đã bị ghi hàng chục GB khi cài Windows ⇒ coi như mất. `D:`: nếu bị quick-format hôm nay thì Windows thường gửi TRIM cả phân vùng ⇒ rất khó.
- **Thử một lần, rẻ:** quét `D:` 10–15 phút, ghi kết quả ra `C:\KhoiPhuc_D` (không phải `E:`), kỳ vọng ≈ 0:
  ```powershell
  New-Item -ItemType Directory -Force -Path C:\KhoiPhuc_D | Out-Null
  winfr D: C:\KhoiPhuc_D /x /y:PDF,JPEG,PNG,ZIP
  ```
  Không ra thì thôi. Dịch vụ cứu dữ liệu chuyên nghiệp với SSD đã TRIM hầu như không có kết quả; chỉ đáng nếu dữ liệu vô giá.

## 5. Nơi khác còn bản sao (kiểm theo thứ tự rẻ → đắt)

1. **GitHub** — toàn bộ mã (đã an toàn). **Phiên cloud claude.ai** — lịch sử thiết kế và kết quả.
2. **Ổ ngoài / USB / ổ cũ cắm lại.** Mã cũ trỏ `F:\TheBrain_luu` và `F:\TeraBoxDownload`: máy bây giờ không có `F:`, nên đó là **một ổ khác chưa cắm**
   (USB/HDD ngoài) *hoặc* `E:` HDD hiện tại từng mang chữ `F:`. Cắm mọi ổ ngoài bạn có và xem `Get-Volume`.
3. **Trình duyệt đồng bộ:** Chrome `chrome://settings/syncSetup`, Edge `edge://settings/profiles/sync`. Mật khẩu: `passwords.google.com`, `edge://wallet/passwords`.
4. **Google Drive / Gmail / Photos** — tìm tay: Drive (`drive.google.com`, lọc theo loại), Gmail (`has:attachment`, `from:me`). Bạn đã từ chối cho phiên làm việc
   tìm hộ; nếu đổi ý chỉ cần nói — mình tìm (chỉ đọc) từ phiên cloud, **chưa làm khi chưa có lệnh của bạn**.
5. **Telegram** (Saved Messages, chat với bot của lab — lưu vô hạn), **Zalo** ("Cloud của tôi" và chat với chính mình — file hết hạn sau một thời gian, kiểm ngay),
   **TeraBox** (lab từng dùng thư mục tải về của TeraBox).
6. **Điện thoại:** thư mục Download, ảnh, file nhận qua Zalo/Telegram.
7. **Môi giới / MT5:** lịch sử giá tải lại được; mở lại tài khoản **demo** XM (đặt lại mật khẩu bằng email). Không cần cứu.
8. **Email cũ** từng gửi file/mật khẩu cho chính mình.

## 6. Từ nay: để vụ này không lặp lại

- Mã: GitHub ✓. Sổ cái nghiên cứu: trong git (`so_cai/`) ✓. Bảng giá: dựng lại từ MT5 — không phải bản sao duy nhất.
- File cá nhân: bật **Sao lưu Windows / File History** ra ổ ngoài, hoặc đồng bộ OneDrive/Drive; quy tắc 3-2-1 (3 bản, 2 loại ổ, 1 bản ở nơi khác).
- Trước mọi lần cài lại Windows: chụp danh sách ổ, **rút ổ không cần format**, chọn đúng "chỉ ổ hệ điều hành".
