# KHÔI PHỤC MÁY NHÀ + LÀM LẠI TỪ ĐẦU (02/10/2026)

> Người đọc: chủ dự án, và phiên Claude Code sẽ chạy trên máy nhà (phiên **[GHI]**).
> Viết bởi phiên cloud sau khi máy nhà cài lại Windows. Cập nhật mục 8 mỗi khi xong một việc.

## 0. Đọc 1 phút

- **Chuyện gì đã xảy ra:** máy nhà cài lại Windows → mất mọi thứ nằm ngoài git. Chủ dự án quyết định
  **làm lại từ đầu, bài bản và khoa học hơn**. Kết quả cũ (SP500 đã test, bot V6, Ultima AUDCAD) *không phải
  bằng chứng*; chủ dự án cũng nhận xét chúng không hiệu quả. Mất `nao.db` vì thế **không phải mất mát cần cứu**.
- **Mã nguồn còn đủ** ở GitHub `thebrainago/the-brain`, nhánh `claude/autonomous-trading-system-rzzt7h`.
  Nhánh này đã **gộp hai dòng việc cloud**: `trading-system-optimization` (45 commit 19–22/09: HEPHAESTUS, cầu git
  hai máy, MT5 trên Actions) và nhà nghiên cứu AI + tiêu chí tiền (25–29/09). `main` vẫn dừng ở 19/09 — gộp
  vào `main` là việc của chủ dự án (nói với phiên cloud thì nó mở PR).
- **MỘT kênh:** chủ dự án chat ở phiên cloud; máy nhà và VPS là tay chân, nói chuyện qua `b cau` (mục 6).
  `b tram` đã bị gỡ — gộp vào đây.
- **Phiên Claude Code trên máy nhà là [GHI]** (CLAUDE.md "QUY TAC PHIEN"): duy nhất được dùng MT5 tester, ghi
  `nao.db`/`nc.db`, sửa `config/*.json`. Phiên cloud là [DOC] với dữ liệu, nhưng là nơi duy nhất ra đơn.
- **Việc đầu tiên:** mục 2 (tìm bản sao) — *trước* khi cài hay ghi bất cứ gì lên ổ.

## 1. Cái gì còn, cái gì mất

| Thứ | Ở đâu (máy cũ) | Số phận |
|---|---|---|
| Mã nguồn, tài liệu, báo cáo `.md/.json`, `nhat_ky/` | GitHub | **còn đủ** |
| Kho giá `data/`, cache `data_khung/` | `F:\TheBrain_luu\` từ 12/09 | **có thể còn** (ổ F: thường không bị format) |
| `nao.db` (1,6 GB: sổ FDR, ứng viên, tài liệu đã đọc) | `lab\` trên C: | mất, trừ khi còn trong `Windows.old`. Không cần cứu: làm lại |
| `nc.db` (sổ tay nhà nghiên cứu AI) | `lab\` | gần như rỗng: nhà nghiên cứu mới chạy trên cloud |
| Khoá API: `config/api_keys.json`, `gh_token.txt`, `passview.json` | `lab\config` (gitignore) | mất — nhập lại bằng tay. **Không dán khoá vào chat** |
| `ds/` — kho DeepSeek, git riêng 56 commit, 799 test | `Research SP500\ds` | **không có repo trên GitHub** → mất nếu không tìm được bản sao. Lab chỉ cần nó ở 2 chỗ: `nhan/doc_lenh_tester.py`, `test_mimic_ban_do.py` |
| MT5: cài đặt, đăng nhập XM demo, EA, profile | `C:\Program Files\XM MT5`, `AppData\Roaming\MetaQuotes` | mất — cài lại, mở demo mới |
| cc-switch (provider DeepSeek), Telegram, phiên trình duyệt CDP | profile người dùng | mất — làm lại khi cần |
| `Desktop\hethong.txt`, `../AGENTS.md` | Desktop, `Research SP500\` | bản chép `SO_DO_HE_THONG.txt` và `CLAUDE.md` (rút gọn) còn trong repo |

Lệnh `b khoi-phuc` in đúng bảng này cho *máy đang chạy* (có/thiếu/mất thật) và danh sách "BƯỚC TIẾP".

## 2. TÌM BẢN SAO TRƯỚC (có hạn chót)

1. **`C:\Windows.old`** — nếu bạn cài *chồng* lên bản cũ (không format ổ C:), thư mục người dùng cũ còn ở
   `C:\Windows.old\Users\<tên>\Downloads\Research SP500\` (`lab\nao.db`, `ds\`, `lab\config\api_keys.json`) và
   `...\AppData\Roaming\MetaQuotes\Terminal\`. **Windows tự xoá nó sau khoảng 10 ngày.** Đừng chạy Disk Cleanup /
   Storage Sense mục "Previous Windows installation". Copy sang ổ khác trước.
2. **`F:\TheBrain_luu\data` và `data_khung`** — `nhan/duong_dan.py` tự nhận nếu thư mục tồn tại; không cần cấu hình.
3. **Bản sao khác:** OneDrive/Google Drive (Desktop có đồng bộ không?), USB, ổ ngoài, `F:\TeraBoxDownload`.
4. Báo kết quả cho phiên cloud: *còn / mất* từng mục.

## 3. Cài công cụ (khoảng 20–30 phút)

PowerShell, không cần quyền Administrator:

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
irm https://claude.ai/install.ps1 | iex
```

Đóng PowerShell, mở cửa sổ mới (để nhận PATH), rồi `git --version; python --version; claude --version`.
Không có `winget` (Windows 10 cũ): tải Git từ git-scm.com, Python 3.12 từ python.org (tick "Add to PATH"), và dùng
lệnh `claude` ở trên.

MT5: cài **XM MT5** từ trang XM, mở **tài khoản DEMO** (máy chủ `XMGlobal-MT5 10`). Repo chỉ dùng demo.

## 4. Kéo mã về và nối Claude Code

```powershell
mkdir "C:\Research SP500"; cd "C:\Research SP500"      # giữ bố cục cũ: ..\lab, ..\ds
git clone https://github.com/thebrainago/the-brain.git lab
cd lab
git checkout claude/autonomous-trading-system-rzzt7h
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
claude                       # đăng nhập ĐÚNG tài khoản claude.ai đang chạy phiên cloud
```

Thư mục phải tên `lab` và `ds` nằm cạnh nó: code tính `GOC = LAB.parent` và tìm `GOC/ds`. Mọi launcher
(`b.cmd`, `q.cmd`) tự tìm Python theo `.venv` → bản cũ → `py -3` → `python` (`_py.cmd`), không còn dính
`C:\Users\SV STORE\...`.

Để Claude trên máy **hiểu việc**, chọn một trong hai:
- **Phiên mới (nhẹ token):** gõ `claude` trong `lab`, bảo "đọc `tai_lieu/KHOI_PHUC_MAY_NHA.md` rồi `b nc`".
- **Nạp cả cuộc trò chuyện của phiên cloud:** `claude --teleport session_01ER1xpfauUywJ6smLMSZmHW`. Kéo đúng
  nhánh và toàn bộ lịch sử; phiên cục bộ là bản sao riêng (việc làm ở đó không hiện trên phiên cloud). Nặng token hơn.

Điều khiển từ điện thoại/trình duyệt: trong phiên cục bộ gõ `/remote-control`.

## 5. Chẩn đoán và dựng lại trạng thái

```powershell
.\b.cmd khoi-phuc      # còn gì, thiếu gì, thiếu cái nào là MẤT THẬT, bước tiếp
.\b.cmd vao            # trạng thái sống
.\b.cmd nc             # hồ sơ nghiên cứu (sổ tay) — lần đầu sẽ rỗng
.\b.cmd test           # cần: pip install pytest pytest-xdist (đã có trong requirements.txt)
```

**Dữ liệu giá.** Nếu `F:\TheBrain_luu\data` còn → xong. Nếu mất: tập lệnh xuất M1 cũ (`*_M1_mq.parquet`, trần 5
triệu bar/cặp của terminal) **không nằm trong repo** (nằm ở `sp500_phase1/` hoặc ngoài). Phiên Claude Code trên máy nhà
viết lại bộ xuất bằng `copy_rates_range` — đọc `_tai_chi_so_xm.py` để tránh các bẫy đã biết (gọi đầu sau
`symbol_select` trả thiếu bar → thử lại 4 lần; phải dùng mốc RẤT XA; đếm bar mỗi năm để bắt đoạn bị dồn từ khung
khác; bar D1 của XM có `spread = 0`) và `CLAUDE.md` mục "Bẫy đã sập thật". Dữ liệu dựng lại phải theo giao thức mục 7
(hộ chiếu + đóng băng đoạn).

## 6. Kênh cloud ↔ máy (MỘT kênh, nhiều máy)

```
 PHIÊN CLOUD (nơi bạn chat) ── b cau giao ──► git: viec/cho ──► MÁY NHÀ / VPS   b cau chay (lịch 5 phút)
        ▲                                                         │  kéo → nhận việc → chạy → đẩy kết quả
        ├──────── git: viec/xong, viec/may (nhịp tim) ◄───────────┘
        └──── claude -p … --cloud  (tuỳ chọn, TẮT mặc định) ◄── máy gọi ngược để đánh thức phiên này
```

Bạn chỉ cần nói với phiên cloud: *"chạy nc tu-lai AUDCAD H4 trên máy nhà"*. Phiên cloud ra đơn (`b cau giao`), máy
tự kéo về, chạy, đẩy kết quả; phiên cloud đọc (`b cau lay`). Cloud không với tới máy nhà nên **máy tự đi lấy việc**:
không mở cổng nào, phiên chat tắt thì đơn vẫn nằm chờ.

**Cài trên máy nhà** (sau mục 4):

```powershell
.\b.cmd cau cai https://github.com/thebrainago/the-brain.git claude/autonomous-trading-system-rzzt7h --ten nha --kha-nang windows,mt5,data
.\b.cmd cau chay        # thử một lượt: đơn cau-kiem (ping) phải DAT
# rồi dán dòng schtasks mà lệnh `cau cai` in ra (chạy mỗi 5 phút)
```

`cau cai` tạo **hộp thư riêng** (một bản clone chỉ để đồng bộ `viec/`), nên máy vẫn kéo việc ngay cả khi bạn đang
sửa code trong `lab` (cầu cũ không kéo khi cây làm việc đang dở). Lệnh vẫn chạy ở `lab` thật (dữ liệu, config, MT5).
Cloud kiểm: `b cau lay` → bảng đơn + bảng máy (nhịp tim: máy nào đang bật, đang làm gì, mã bản nào).

**VPS Linux** — cùng lệnh, chỉ khác tên/khả năng và dòng cron thay cho schtasks:
`python b.py cau cai <url> <nhánh> --ten vps --kha-nang linux,24x7`. Đơn có `can: ["mt5"]` sẽ tự bỏ qua VPS.
Nhiều máy cùng kéo một hàng đợi **không chạy trùng**: máy nào push *phiếu nhận việc* (`viec/dang/<mã>.json`)
trước là máy làm.

**Gọi ngược về phiên này (tuỳ chọn):** phiên cloud *ngủ* giữa các lượt; không ai đánh thức nó khi máy xong việc.
Bật: `b cau cai ... --session session_01ER1xpfauUywJ6smLMSZmHW --bao-cloud` (máy cần có `claude` đã đăng nhập).
Máy chạy `claude -p "[CAU-NOI may=nha] 3 don xong: ..." --cloud <session>`. Mỗi lần đánh thức tốn token của bạn nên:
tắt mặc định, tối thiểu 30 phút giữa hai lần (việc **cần cloud trả lời** được ưu tiên), tối đa 12 lần/ngày, và tin
chỉ gồm *mã đơn + trạng thái* đã lọc ký tự — nội dung log (có thể chứa chữ lấy từ web) không bao giờ đi ngược lên.

**An toàn.** Mỗi đơn là lệnh thật chạy trên máy có khoá API, dữ liệu, MT5:
- chỉ chạy lệnh trong **danh sách trắng** (`qwen/cau_trang.py`): phải bắt đầu `{py}`, rồi khớp một hình đã khai
  báo (`b.py <lệnh b>`, `-m pytest …`, vài module/script). Ngoài danh sách → **không chạy**, ghi `CHUA_DO_DUOC` và hỏi
  cloud; chủ dự án duyệt đúng đơn đó trên máy: `b cau xem MA` (in lệnh + vân tay) rồi `b cau duyet MA VAN_TAY`;
- danh sách nằm trong mã nên chặn **lỗi và lệnh bị tiêm vào phiên cloud**, không chặn kẻ đã đẩy được lên nhánh (họ
  sửa được cả file này) → **để repo private + bật xác thực hai lớp cho tài khoản GitHub** (repo đang public);
- dừng khẩn: file `CAU_DUNG` ở gốc `lab` (tại máy, không cần mạng) hoặc `b cau dung` / `b cau tiep` (từ xa qua git);
- mỗi kết quả mang **phiên bản mã** đã chạy (commit, `+sua` nếu cây dở) và bản sao các báo cáo mới ra.

Đơn cũ 20/09 (đòi `data/` + `nao.db`, vd `hepha-nap --that` ghi kho cơ chế sản xuất) đã chuyển vào
`viec/luu_tru/` để khỏi tự chạy khi vừa cài; chỉ còn `cau-kiem` (ping) trong `viec/cho/`.

## 7. Làm lại từ đầu: giao thức khoa học

*(đang dựng — mục này được viết nốt khi các phần dưới đây xong; xem `git log` để biết phần nào đã có)*

## 8. Việc kế tiếp (theo thứ tự)

1. Máy nhà: mục 2 → 3 → 4, `b khoi-phuc`, `b cau cai`, thấy ping `DAT` (kênh thông).
2. Chủ dự án: đổi repo sang **private**, bật 2FA; quyết định gộp nhánh vào `main` (PR).
3. Tìm bản sao `ds/` (mục 1); nếu không còn, ghi nhận mất và bỏ 2 chỗ phụ thuộc.
4. Dựng lại kho giá (mục 5) theo giao thức mục 7.
5. Đo hiệu năng máy nhà vs VPS vs container cloud (bench), rồi quyết thuê VPS.
