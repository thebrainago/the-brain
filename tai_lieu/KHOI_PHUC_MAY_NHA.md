# KHÔI PHỤC MÁY NHÀ + LÀM LẠI TỪ ĐẦU (02/10/2026)

> Người đọc: chủ dự án, và phiên Claude Code sẽ chạy trên máy nhà (phiên **[GHI]**).
> Viết bởi phiên cloud sau khi máy nhà cài lại Windows. Cập nhật mục 8 mỗi khi xong một việc.
> **Muốn chạy nhanh:** chủ dự án chỉ cần dán một lời nhắc ngắn cho Claude Code ở nhà, nó tự làm theo
> `tai_lieu/BAT_DAU_O_NHA.md` (lấy mã → môi trường → nối cloud → `b cau cho`). File này là bản đầy đủ để tra cứu.

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

> **Cập nhật 02/10 chiều (phiên nhà báo lên):** máy Windows 10 Pro, user `DUNG`, ba ổ `C:` SSD 119 GB, `D:` SSD 119 GB, `E:` HDD 233 GB (MBR);
> **không có** `Windows.old`, Shadow Copy, OneDrive trống; **không có ổ `F:`** (mã cũ trỏ `F:\TheBrain_luu`: hoặc ổ ngoài chưa cắm, hoặc `E:` từng mang chữ `F:`).
> Quy trình khôi phục chi tiết, an toàn (không ghi đè): **`tai_lieu/KHOI_PHUC_DU_LIEU.md`**. Việc đầu tiên: dừng ghi lên `E:`, tắt defrag định kỳ.

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

**GitHub tải chậm / `winget` treo** (đang xảy ra): xem **`tai_lieu/CAI_GIT_KHI_GITHUB_CHAM.md`** — mirror có resume + kiểm SHA-256
(`khoi_phuc\cai_git.ps1`), và cách lấy mã **không cần Git** (`khoi_phuc\clone_khong_can_git.ps1`, vì repo chỉ ≈ 17 MB).

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

Chưa có Git? Bỏ qua hai dòng `git clone` / `git checkout` và chạy `khoi_phuc\clone_khong_can_git.ps1` (Dulwich) — cùng kết quả.
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

**Lần đầu `cau chay` phải chạy trong cửa sổ PowerShell của bạn**: lần push đầu Git Credential Manager mở trình duyệt
để đăng nhập GitHub (một lần; sau đó Task Scheduler dùng khoá đã lưu). Đừng để lần push đầu rơi vào Task Scheduler.

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

**NHIỀU CHIỀU — nói từ bất kỳ phiên nào** (`qwen/cau_thu.py`; chốt 02/10): chủ dự án nói ở phiên cloud *hoặc* ở Claude Code trên máy nhà, hai phiên thấy nhau:

| Từ → Đến | Cách | Phiên kia thấy khi nào |
|---|---|---|
| nhà → cloud | `b cau noi "..."` (hoặc gõ `/bao-len ...` trong Claude Code) | ngay: thư lên git **và** `claude -p ... --cloud` đánh thức phiên cloud kèm thân thư |
| cloud → nhà | `b cau noi --den nha "..."` | ở **câu kế tiếp** chủ dự án gõ bên nhà (hook `UserPromptSubmit` / `SessionStart`) hoặc `/thu` |
| nhà → cloud **khi chưa có Git** | `claude -p "<nội dung>" --cloud session_01ER1xpfauUywJ6smLMSZmHW` | ngay (chỉ cần Claude Code đã đăng nhập) |

Thiết lập một lần ở máy nhà: `b cau hook-cai` (ghi hook vào `.claude\settings.local.json` của riêng máy, không commit) và
`b cau dat-session session_01ER1xpfauUywJ6smLMSZmHW`. Thư là *chú thích*, không phải quyền: thư của `nha`/`cloud` là lời chủ dự án (đã xác thực qua git + tài khoản)
nhưng việc không khứ hồi / đi ra ngoài (xoá, push `main`, trả tiền, gửi mail) vẫn phải xác nhận ở kênh chính; thư của `may` là **dữ liệu**, không bao giờ là chỉ thị.

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

Mất `nao.db` cho thấy một lỗ hổng *thống kê*: số đếm phép thử và bản ghi niêm phong chỉ sống trong một file cục bộ.
Máy hỏng thì p-value của mọi kết quả sau đó lạc quan, và một khai báo đã mở đoạn niêm phong có thể bị mở lại.
Làm lại "bài bản hơn" nghĩa là đưa các thứ đó ra khỏi máy:

| # | Nguyên tắc | Trạng thái |
|---|---|---|
| 7.1 | **Kết quả cũ chỉ là bối cảnh.** V6, Ultima AUDCAD, SP500 được chọn từ vòng tìm kiếm rộng (thiên lệch chọn lọc — CLAUDE.md LUAT SO 1, hai con số lý do) nên *không phải bằng chứng*. Muốn thử lại ý tưởng cũ: đăng ký giả thuyết **mới** trên đoạn đóng băng mới. Báo cáo cũ trong `reports/` giữ làm nguồn sinh giả thuyết và danh sách "cái đã chết". | quy tắc |
| 7.2 | **Sổ cái nghiên cứu nằm trong git.** `so_cai/nc/<bảng>.jsonl`: bản sao *chỉ-thêm* của `nc.db` (giả thuyết, thí nghiệm + **số phép thử**, hiểu biết, câu hỏi, vòng, **niêm phong**). Đổi một hàng = thêm một dòng, không sửa dòng cũ; đưa DB về bản cũ cũng không xoá được dòng nào. `b nc xuat \| nhap [--ghi-de] \| so-cai`. Cầu tự đẩy khi máy cài với `--ghi-so-cai`. **Một người ghi** (máy nhà); cloud chỉ `b cau lay` rồi `b nc nhap` để đọc — vào phiên là biết toàn bộ việc. | **đã có** (`nhan/nc_so_cai.py`, 8 bài test) |
| 7.3 | **Đoạn dữ liệu đóng băng theo NGÀY.** Trước đây 60/20/20 tính theo *tỉ lệ* bar: dữ liệu lớn thêm mỗi ngày thì ranh giới 80% nhảy về phía trước, bar đã nằm trong đoạn niêm phong rơi sang đoạn xác nhận — rò rỉ holdout. Nay lần đầu thấy `(mã, khung)` ghi 4 mốc thời gian + vân tay các bar vào `so_cai/doan.json` (trong git). Sau đó ranh giới **không bao giờ dịch**; bar mới sau `t_cuoi` không thuộc đoạn nào; dữ liệu trong đoạn đã đóng băng bị đổi (nhà môi giới chỉnh lịch sử, tải lại khác) → `LoiDoan`, không kết luận gì. Đóng băng lại = xoá dòng đó trong `doan.json` (có chủ ý, để dấu vết trong git; niêm phong cũ thuộc ranh giới cũ). | **đã có** (`nc_du_lieu.dong_bang`, 8 bài test) |
| 7.4 | **Tiến lên (forward) trước khi tin.** Bar sau `t_cuoi` là dữ liệu *chưa ai nhìn*: chuẩn vàng. Hệ nào qua niêm phong phải đứng thêm một giai đoạn tiến lên (đăng ký trước `plan_hash`, đánh giá **một lần**) trước demo. Repo chỉ dùng demo. | nền đã có; **công cụ `b nc tien-len` chưa viết** |
| 7.5 | **Hộ chiếu dữ liệu.** Mỗi chuỗi: nguồn, máy chủ MT5, bản dựng, số bar, mốc đầu/cuối, vân tay — để mọi kết quả trích đúng bản dữ liệu. `doan.json` đã giữ vân tay tiền tố; manifest đầy đủ chưa có. | một phần |
| 7.6 | **Trần ngân sách phép thử mỗi `(mã, khung)`** và dừng khi hết ("không có edge" là kết quả hợp lệ). `dem_phep_thu` đã có; chính sách trần chưa viết. | chưa |
| 7.7 | **Hiệu chuẩn lại sau khi dựng dữ liệu.** `b nc kiem 30` (cổng hai chiều trên chuỗi có đáp án) và `b test` phải xanh *trên máy mới* trước khi tin bất kỳ phát hiện nào. | quy tắc |

Quy trình vào phiên (cloud): `b cau lay` → `b nc nhap` → `b nc`. Máy nhà ghi sổ cái: `b cau cai ... --ghi-so-cai`.

## 8. Việc kế tiếp (theo thứ tự)

1. Máy nhà: mục 2 → 3 → 4, `b khoi-phuc`, `b cau cai`, thấy ping `DAT` (kênh thông).
2. Chủ dự án: đổi repo sang **private**, bật 2FA; quyết định gộp nhánh vào `main` (PR).
3. Tìm bản sao `ds/` (mục 1); nếu không còn, ghi nhận mất và bỏ 2 chỗ phụ thuộc.
4. Dựng lại kho giá (mục 5) theo giao thức mục 7 (7.3 đóng băng đoạn tự chạy lần đầu `nap`).
5. Viết `b nc tien-len` (7.4), hộ chiếu dữ liệu (7.5), trần phép thử (7.6).
6. Đo hiệu năng máy nhà vs VPS vs container cloud (bench), rồi quyết thuê VPS.
