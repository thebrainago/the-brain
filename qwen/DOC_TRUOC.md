# qwen/ — hệ tự chạy của The Brain

**Một lệnh là đủ.** Mở terminal, gõ:

```
cd "C:\Users\SV STORE\Downloads\Research SP500\lab"
q
```

`q` nạp bảng việc, đo CPU, phóng việc, chấm kết quả, để qwen đọc và viết nhật ký,
rồi lặp lại — cho đến khi hết việc hoặc bạn gõ `q dung`. Tắt máy giữa chừng cũng
không sao: sổ tay ghi xuống đĩa sau mỗi thay đổi, chạy `q` lại là nó đi tiếp.

```
q                he chay lien tuc (nhieu ngay). Ctrl-C cung an toan.
q trang-thai     in bang viec + trang thai may, khong chay gi
q kiem           tu kiem ca duong: mo hinh, cong, bang, dieu toc
q dung           dat co dung -> vong lap thoat EM sau vong hien tai
q mot-vong       chay dung mot vong roi thoat (de thu)
q bao-cao        sinh BAO_CAO_<ngay>.md ngay bay gio
q de-xuat        xem viec qwen de xuat (chua chay, cho nguoi duyet)
q xong <ma>      danh dau mot viec `can_nguoi` la da lam xong
q giet           giet moi tien trinh con dang chay
```

---

## Hệ này chia việc thế nào

| | qwen (LLM) | code |
|---|---|---|
| chọn việc tiếp theo | ✗ | `bang_viec.py` đọc `NHIEM_VU.json` |
| chạy lệnh | ✗ | `tien_trinh.py`, chỉ lệnh có trong bảng |
| **chấm đạt/âm** | ✗ | `cong.py` |
| đọc kết quả, viết nhật ký | ✓ | |
| viết báo cáo ngày | ✓ | |
| đề xuất việc mới | ✓ (vào hàng chờ) | người duyệt |

Ranh giới này không phải vì sợ qwen phá. Nó đến từ một phép đo: **LLM điền trường
`co_che` cho 48 khai báo, bộ thẩm định bác 41, ròng cứu được 3.** Tỉ lệ đó không
dùng được cho một cổng. Nhưng nó dùng tốt cho khối lượng đọc — nên qwen gánh
đọc/bóc/viết, còn cổng thì để code.

## Giao việc VIẾT MÃ cho mô hình rẻ — `b tho`

Bảng trên nói qwen **không** viết mã. Từ 19/09/2026 nó viết được, nhưng chỉ
trong một khuôn rất chặt:

```
b tho don_hang.json          giao một đơn hàng cho mô hình rẻ
b tho don_hang.json --thu    chạy khô: in lời nhắc sẽ gửi, không gọi LLM
```

Chia việc:

| | ai làm |
|---|---|
| quyết định XÂY GÌ | người / mô hình mạnh |
| viết **bài test** (= đặc tả) | người / mô hình mạnh |
| gõ phần cài đặt cho đến khi test xanh | **mô hình rẻ** |
| chấm đạt/không | `pytest`. Không ai tự phán. |

Viết được bài test đúng là phần khó. Điền cho nó xanh là phần lặp lại — và đó
là phần đáng trả tiền cho một mô hình rẻ.

### Vì sao chia đúng chỗ đó

Phiên 19/09 tìm ra ba lỗi thật trong bộ mô phỏng. Cả ba **không** tìm ra bằng
cách gõ mã — chúng tìm ra bằng cách chạy thử rồi **nghi ngờ một kết quả đẹp**:

- 51/84 cấu hình được chấm "CHẠY ĐƯỢC" trên random walk → `cat_hoa` đang gặt
  biên độ trong nến;
- 12.805%/năm với sụt giảm 4,67 → cổng phân giải bỏ sót các nút khoảng cách;
- 50% lọt trên chuỗi đã phá edge → "chấm một đường không phân biệt được gì".

Một mô hình rẻ viết mã sẽ sinh ra đúng những dòng mã đó, và sẽ báo cáo "51 cấu
hình CHẠY ĐƯỢC" như một **thành công**. Nên ranh giới không phải "rẻ làm việc
dễ, đắt làm việc khó" — nó là: ai viết **cổng**, và ai đi qua cổng.

### Rào chắn quan trọng nhất: KHÔNG được sửa file test

Kiểu hỏng kinh điển của mọi vòng lặp "sửa đến khi xanh": mô hình thấy sửa test
dễ hơn sửa mã. Lúc đó bảng số vẫn xanh còn cái cổng thì biến mất.

Không phải nỗi lo lý thuyết. Chính trong phiên 19/09, bài
`test_ty_le_lot_tren_nhieu_phai_THAP` đỏ ở mức 50%, và cách dễ nhất là hạ
ngưỡng. Nếu hạ thì phát hiện lớn nhất phiên đó đã không bao giờ tồn tại.

Nên: để `file_test` vào `duoc_sua` là **lỗi đơn hàng** (ném `ValueError`), và
mọi khối mã trỏ tới file ngoài danh sách bị bỏ qua **trước khi ghi**. Hết vòng
mà chưa xanh thì mọi file được sửa trả về nguyên trạng.

Đã kiểm trên repo thật: mô hình cố sửa bài test và `b.py` → không đổi một byte.

### Đơn hàng gồm gì

`don_hang_mau.json` ở gốc `lab/` là mẫu chạy được. Các trường:
`ma` · `muc_tieu` · `file_test` (đặc tả) · `lenh_cham` · `duoc_sua` (danh sách
trắng) · `so_vong_toi_da`.

## Ba trạng thái, không phải hai

```
DAT            đo được và vượt ngưỡng
AM             đo được và không vượt ngưỡng
CHUA_DO_DUOC   khâu đo hỏng, chưa nói được gì
```

Trạng thái thứ ba là trạng thái quan trọng nhất của dự án này. Lịch sử lab đầy
những lần một khâu **hỏng** đọc y hệt một kết quả âm: 406 URL chết chiếm hàng đợi
→ làn bóc báo "hết tồn kho" khi kho còn 4.560 tài liệu; hết quota API → mẻ bóc
chạy 2 giây rồi báo "0/20 cơ chế"; lệch tên provider → mọi lời gọi trả "thiếu
OPENAI_API_KEY".

Nên `cong.py` trả `CHUA_DO_DUOC` cho tất cả những cái sau, **không bao giờ trả `AM`**:

- mã thoát ≠ 0
- không có file ra, hoặc file ra **cũ hơn lúc bắt đầu chạy**
- bảng kết quả có **phần lớn cột số chỉ một giá trị** (bẫy số 1 — dấu hiệu chung
  của 3 lỗi khác nhau trong một phiên 07/09)
- việc bị giết vì quá giờ

## Điều tốc CPU — vì sao không đặt cứng "8 tiến trình"

Đã đo trên đúng máy này hai bài cho hai kết luận ngược nhau:

```
quét bề mặt phễu D1 (một ô ~128 KB, nằm gọn trong cache)
    1 tiến trình 18,6 ô/giây · 8 tiến trình 70,6 (3,8 lần) · 16 tiến trình 79,0
bài mảng lớn (nghẹt băng thông RAM — máy chạy single-channel, 9,4 GB/s)
    1 luồng 8,9 GB/s · 20 luồng 9,4 GB/s → song song hoá KHÔNG ăn gì
```

Nên số tiến trình đúng **không suy ra được từ số nhân**. `dieu_toc.py` đo CPU thật
mỗi 5 giây và cộng/trừ slot theo phép đo, giữ **tổng CPU của cả máy** quanh 85%.
Mục tiêu là của cả máy, không của riêng hệ này — nên khi MT5 tester ăn 60% thì làn
CPU tự co lại. Đó là hành vi đúng.

Chỉnh mục tiêu: `config/qwen.json` → `"muc_tieu_cpu": 85` hoặc chạy một lần với
`QWEN_CPU=70 q`.

**Đo lại bộ điều tốc trên máy này** (12 việc đốt CPU thuần, ~3 phút, không đụng gì
đến nghiên cứu):

```
set QWEN_BANG=qwen\thu\BANG_TAI.json
set QWEN_SO_TAY=qwen\thu\so_tay_tai.json
q
```

Nhìn dòng `~ HH:MM:SS | san sang N | CPU xx% ...`. **Đạt** khi CPU ổn định trong
78-92% và số việc đang chạy *không* leo lên hết 12. Chạm 100% → hạ `nang_lan.CPU`;
dừng ở 60% → nâng lên.

## Làn (lane) — và ràng buộc vật lý không được phá

```
TESTER  tối đa 1     MT5 Strategy Tester
CPU     tối đa 8     tính toán thuần (numpy/pandas), OMP_NUM_THREADS=1
LLM     tối đa 4     gọi qwen hàng loạt (mỗi tiến trình tự mở 20 luồng)
MANG    tối đa 3     tải tài liệu / mã nguồn
NHE     tối đa 6     việc vặt vài giây
```

**`TESTER` = 1 là ràng buộc vật lý, không phải lựa chọn.** `chay_tester_kho` ghi đè
*cùng một* file `MQL5\Experts\<TEN_EA>.mq5`, *cùng một* `.ini`, *cùng một* `.xml`,
và máy chỉ có một `terminal64.exe`. Hai việc tester chạy cùng lúc thì kết quả của
nhau bị ghi đè — **và không ai báo lỗi**, bảng số đọc y hệt một kết quả thật.

Các làn còn lại chạy **đồng thời** với tester, vì chúng không tranh terminal64:
đo 30/08 cho thấy đọc trang qua trình duyệt 4,2% CPU và quét quantlab 10,1% trên
máy 20 luồng — hai trụ không tranh CPU của nhau.

## Đường LLM

Khoá đọc **tại chỗ** từ `~/.cc-switch/cc-switch.db` (bảng `providers`, khớp tên
bằng chuỗi con). Không chép sang dự án: một khoá API chỉ nên tồn tại ở một nơi.

Gọi **thẳng** `https://api.ai-box.vn/v1`, không qua cầu nối `127.0.0.1:8317` —
cầu nối đó dựng cho Codex CLI (Codex đòi `/v1/responses` mà AI Box không có).
LangChain nói `/chat/completions` sẵn. Đo 08/09: thẳng 2,1s, qua cầu nối 3,2s.

Kiểm nhanh: `q kiem`, hoặc `python -X utf8 -m qwen.mo_hinh`.

> Nếu `q kiem` báo *"không tìm thấy provider"*: mở cc-switch xem **tên thật** của
> profile rồi sửa `cc_switch_provider` trong `config/qwen.json`. Ngày 06/09 lệch
> tên đúng chỗ này làm **cả đường LLM tắt lặng lẽ** — mọi lời gọi trả "thiếu
> OPENAI_API_KEY" và không ai báo.

## Sửa việc của máy = sửa `NHIEM_VU.json`

```json
{"ma": "V1_dao_SPAIN35",
 "ten": "Dao chieu + ghep tren SPAIN35Cash",
 "vi_sao": "cau nay tra loi cau hoi gi, dua tren con so nao",
 "lan": "TESTER", "uu_tien": 1, "ngay": 2,
 "phu_thuoc": ["V1_dao_GER40"],
 "lenh": ["_dem_ghep.py", "SPAIN35Cash"],
 "cong": {"kieu": "chan_ban_tang", "file": "reports/DEM_CHAN_DUONG_SPAIN35Cash.json"},
 "toi_da_phut": 180}
```

Kiểu cổng có sẵn: `chay_duoc` · `khong_rong` · `so_lenh_du` · `truong_vuot` ·
`dem_dong_dat` · `chan_ban_tang` · `trong_log`.

`"can_nguoi": true` = hệ **không tự chạy**, chỉ in ra cho chủ dự án. Làm xong thì
`q xong <ma>` để mở khoá các việc phụ thuộc nó.

## File nào làm gì

| file | việc |
|---|---|
| `cau_hinh.py` | mọi hằng số, một chỗ |
| `dieu_toc.py` | giữ CPU ~85%, cấp phát lõi cho các làn |
| `bang_viec.py` | đọc `NHIEM_VU.json`, giải phụ thuộc, chọn việc |
| `tien_trinh.py` | phóng tiến trình con (BELOW_NORMAL, có hạn giờ, giết được cả cây) |
| `cong.py` | **chấm đạt/âm/chưa đo được — bằng code** |
| `so_tay.py` | trạng thái bền, resume được sau khi tắt máy |
| `mo_hinh.py` | đường LLM (cc-switch → LangChain) |
| `cong_cu.py` | bộ công cụ LangChain, danh sách trắng, không có vỏ shell |
| `tac_tu.py` | tác tử LangGraph + câu hệ thống (5 câu tự kiểm) |
| `chay.py` | vòng lặp điều phối + CLI |
| `NHIEM_VU.json` | **bảng việc — sửa ở đây** |

## Claude giao việc — qwen làm việc

Đây là nhịp làm việc từ nay, kể cả khi Claude có mặt.

**Khi Claude quay lại sau vài ngày**, đọc theo đúng thứ tự này:

```
q ban-giao        # ghi ra lab/BAN_GIAO_QWEN.md và in luôn
```

Nó xếp sẵn theo thứ tự người quay lại cần: `DAT` / `AM` / **`CHUA_DO_DUOC`**, việc
đang chờ chủ dự án, việc qwen đề xuất, nhật ký 30 mục cuối, các `BAO_CAO_*.md` đã
sinh. **Đọc mục `CHUA_DO_DUOC` trước mọi thứ khác** — đó là chỗ hệ không đo được,
không phải chỗ không có edge.

**Giao việc mới = sửa `qwen/NHIEM_VU.json`.** Không cần dừng đợt đang chạy: vòng
lặp thấy file đổi thì tự nạp lại (bảng hỏng thì nó giữ bản cũ và báo, chứ không
chết). Sau khi sửa nên `q kiem` để nó soát bảng — trùng mã, phụ thuộc treo, phụ
thuộc vòng tròn đều bị bắt lúc nạp.

Một việc tối thiểu cần: `ma` · `ten` · **`vi_sao`** · `lan` · `lenh` · `cong`.
Trường `vi_sao` không phải trang trí — nó đi vào lời nhắc của qwen khi qwen đọc
kết quả, nên viết nó như viết cho một người chưa đọc phiên trước.

**Việc thường trực** (`lap` > 1 + `cach_nhau_gio`) là thứ giữ cho một tuần không
cạn: bóc kho, bóc chỉ báo, săn nguồn, chạy bộ test. Chúng chạy lại khi hết chu kỳ,
và vòng lặp **không thoát** chỉ vì bảng trống một lúc.

**Phân vai:** Claude nghĩ ra *phép thử nào đáng chạy* và viết cổng cho nó. qwen
gánh khối lượng và viết lại những gì đo được. Ranh giới ở giữa là `qwen/cong.py`,
và nó phải luôn là code.

## Chạy nhiều ngày

Muốn nó sống qua đăng xuất: tạo Task Scheduler trỏ vào `lab\q.cmd` (giống 8 tác vụ
`.xml` sẵn có trong `lab/`), hoặc để cửa sổ terminal mở. Sổ tay bền nên cách nào
cũng resume được.

Mỗi ngày hệ tự sinh `Research SP500/BAO_CAO_<ngày>.md` — **bản nháp**: số do code
chấm, văn do qwen viết. Chủ dự án đọc lại trước khi tin.
