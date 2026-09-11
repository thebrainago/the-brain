# KẾ HOẠCH XÂY NỐT THE BRAIN

> Chốt 11/09/2026. Tài liệu này **có quyền ưu tiên** hơn mọi kế hoạch cũ trong `lab/`.
> Đây là kế hoạch **xây năng lực**, không phải kế hoạch chạy nghiên cứu.
> Sáu khối, chạy nối tiếp. Mỗi khối có cổng nghiệm thu **chấm bằng code**, không chấm bằng cảm nhận.

---

## Cách dùng — mỗi phiên mở đầu bằng ba dòng

```
cd "C:\Users\SV STORE\Downloads\Research SP500\lab"
b vao                      # trạng thái sống + bàn giao hôm qua
python -c "import json;d=json.load(open('config/ke_hoach_xay.json',encoding='utf-8'));print(d['dang_o'], '|', d['khoi'][d['dang_o']]['trang_thai'])"
```

Rồi mở `q` ở một cửa sổ khác để qwen chạy nền suốt phiên:

```
q                          # chạy liên tục, Ctrl-C an toàn
q trang-thai               # xem bảng việc
q xong <ma>                # đánh dấu một việc `can_nguoi` đã xong
```

Kết phiên: `b ket "<tóm tắt>"` và cập nhật `config/ke_hoach_xay.json`.

---

## Phân vai Claude / qwen — ranh giới này đến từ một phép đo, không từ sở thích

**LLM điền trường `co_che` cho 48 khai báo, bộ thẩm định bác 41, ròng cứu được 3.**
Tỉ lệ 6% không dùng được cho một cổng, nhưng dùng rất tốt cho khối lượng đọc.

| Việc | Claude | qwen |
|---|:--:|:--:|
| Sửa `nhan/ngu_phap.py` (cửa duy nhất cho kiến thức mới) | ✓ | ✗ |
| Đụng schema `nao.db`, `plan_hash`, cổng | ✓ | ✗ |
| Thiết kế tầng chạm tiền, kill-switch | ✓ | ✗ |
| Đọc hàng nghìn tài liệu, bóc, phân loại | ✗ | ✓ |
| Dựng corpus nghiệm thu, viết ca kiểm | ✗ | ✓ |
| Chạy mẻ, chạy lặp, viết nhật ký | ✗ | ✓ |
| **Chấm đạt / âm** | ✗ | ✗ — `qwen/cong.py` chấm bằng code |

**Ba trạng thái, không phải hai.** `DAT` · `AM` · `CHUA_DO_DUOC`.
Mã thoát ≠ 0, thiếu file ra, file ra cũ hơn lúc bắt đầu chạy, hay bảng có phần lớn cột số
đứng im → **luôn là `CHUA_DO_DUOC`**, không bao giờ là `AM`.

**Ràng buộc vật lý:** làn TESTER tối đa 1 việc. Máy chỉ có một `terminal64.exe`,
hai việc tester cùng lúc ghi đè kết quả của nhau và **không ai báo lỗi**.

---

## Mốc đo đầu (11/09/2026) — dán vào mọi báo cáo để thấy dịch chuyển

```
NGỮ PHÁP          41 toán hạng · 187/383 giả thuyết là quay-về-trung-bình
BÓC TÁCH          327/9.419 tài liệu (3,5%)
SỔ CÁI            ket_qua 1.280 · PASS 14 · FDR 1.807 (bác 406)
KHO CƠ CHẾ        xé 4 mảnh: 383 / 32 / 75 / 192
CỔNG RA TIỀN      35.937 tổ hợp → train 50 → holdout 1
TẦNG CHẠM TIỀN    0 file
SỔ BÀI HỌC        0 file (đang sống trong 130 file memory ngoài repo)
VẬN HÀNH          control plane TẮT từ 01/09 · 243 script ngoài sổ · test 1.239 (4 hỏng)
```

---

# KHỐI 1 — CỬA VÀO TRI THỨC · trần của cả hệ

> **Đã đo baseline 11/09 bằng `_corpus_ngu_phap.py`. Kết quả sửa lại giả định ban đầu —
> đọc kỹ trước khi viết dòng mã nào.**

**Năng lực phải có:** một câu văn xuôi mô tả cơ chế thật đi được vào hệ thành khai báo chạy được.

### Baseline đo được (`reports/CORPUS_NGU_PHAP.json`)

```
TẦNG A — đo NGỮ PHÁP (150 câu `loai_cau` nhận là luật)
    NÓI_ĐƯỢC 0 · NÓI_MỘT_PHẦN 0 · KHÔNG_NÓI 150  (100%)

TẦNG B — đo KHÂU ĐỌC (150 câu có từ vựng phương pháp mà `loai_cau` từ chối)
    vùng 60 · sóng 46 · liên mã 22 · khối lượng 17 · hình học 13 · nến 3

TẦNG C — hình dạng THẬT của 689 cơ chế trong kho
    họ:        xu_huong 338 · quay_ve_trung_binh 142 · pha_vo 125 · bien_dong 54
    toán hạng: gia 1.159 · ema 334 · sma 233 · tre 228 · tb 159 · rsi 149
    CHƯA AI DÙNG (12/43): bollinger · cci · dem_lien_tiep · dong_luong · gann_sq9
                          obv · phuong_sai · smma · tong · trang_thai_lat
                          tuong_quan · wma
```

### Ba điều baseline này lật lại

1. **Kho không nghiêng về quay-về-trung-bình.** Con số 187/383 tôi trích lượt trước là của
   `nao.db/gia_thuyet` (giả thuyết đã đăng ký), không phải của kho cơ chế. Kho thật là
   **689 cơ chế và nghiêng về xu hướng** (338). Nhận định "hệ khám phá theo hình dạng từ vựng
   của chính nó" vẫn đúng — nhưng hình dạng đó là **trung bình động + giá**, không phải mean reversion.

2. **Thêm toán hạng chưa chắc là ràng buộc đang siết.** **12/43 toán hạng chưa ai dùng một lần nào** —
   kể cả `bollinger`, `tuong_quan`, `dong_luong`. Thêm `song.*` vào một hệ chưa từng gọi `bollinger`
   thì rất có thể nó cũng nằm im như 12 cái kia. **Phải trả lời "vì sao 12 cái đó chưa ai dùng"
   trước khi thêm cái thứ 44.** Cùng họ nghi ngờ với lỗi `closure DSL nuốt tham số` (152/170 mẫu điếc).

3. **Chỗ nghẽn trực tiếp là KHÂU ĐỌC, không phải từ vựng.** 150/150 câu tầng A ra 0 điều kiện,
   và lý do `doc_hieu` trả về là *"không tách được cặp (toán hạng, so sánh, ngưỡng)"* —
   vì `loai_cau` nhận cả câu kể chuyện: *"And if it's a bearish price movement, you go for a sell"*,
   *"how about buying a stock at an oversold (rsi) or at a support level"*.
   `loai_cau` có độ phủ cao và **độ chính xác gần bằng không**.

### Khối 1 tách làm hai, chạy theo thứ tự

**1A — KHÂU ĐỌC (làm trước, đây mới là chỗ nghẽn)**
- `loai_cau` phải trả thêm mức tin cậy, không chỉ nhãn; câu kể chuyện không được vào hàng đợi bóc.
- `dieu_kien_trong_cau` nuốt im lặng vế còn lại — phải trả phần bỏ sót ra ngoài để đo được.
- **Trả lời câu hỏi 12 toán hạng chết**: chúng không được sinh ra, hay sinh ra rồi bị loại?
- Cổng: tầng A từ **0%** lên **≥ 35% NÓI_ĐƯỢC**, và `NOI_MOT_PHAN` phải khác 0 —
  một bộ đọc lành mạnh phải có câu nói được một phần, 0 ở cả hai ô là dấu hiệu hỏng.

**1B — TỪ VỰNG MỚI (chỉ làm sau khi 1A đạt, và theo hàng đợi chứ không theo phán đoán)**
Thứ tự ưu tiên **do tầng B quyết định**, không do Claude chọn: `vung` (60) → `song` (46) →
`lien_ma` (22) → `hinh_hoc` (13) → `nen` (3).
`khoi_luong` (17) **không làm** — đã chứng minh CFD không có tape, mọi "delta" trên MT5 CFD
là hàm của chính giá.

### Toán hạng phải thêm

```
song.*      nguong (% hoặc bội ATR) -> dinh · day · bien_do_day · bien_do_hoi
            ti_le_hoi · so_nen_tu_dinh · so_nen_tu_day · chieu · so_song
nen.*       than · rau_tren · rau_duoi · nhan_chim · pinbar · trong · ngoai · doji
            (nhận `so_nen` để nói mẫu nhiều nến)
hinh_hoc.*  SỬA gann_sq9 (đang KeyError) · muc_gann · goc_gann · fibo (ăn theo song.*)
lien_ma.*   tuong_quan(ma_khac, n) · doi_pct(ma_khac) · dan_dat(ma_khac, tre)
```

### Hai cái bẫy phải chặn ngay trong thiết kế

1. **Zigzag nhìn trước.** Một đỉnh chỉ tồn tại sau khi giá đảo đủ ngưỡng. `song.dinh` phải trả
   `NaN` cho tới đúng bar xác nhận, không được lấp ngược về quá khứ. Đây là cùng họ lỗi
   `da_dich=True` đã sập 3 lần trong một phiên trước đây.
2. **`lien_ma` lệch hàng giá.** BTC bắt đầu 2014, ETH 2017, VNM 2009 — cắt chuỗi này bằng
   chỉ số của chuỗi kia là lệch hàng, **không báo lỗi**. Phải `concat(axis=1).dropna()` rồi mới
   lấy mảng.

### Cổng nghiệm thu

| Phép đo | Baseline 11/09 | Phải đạt |
|---|---:|---:|
| Tầng A · NÓI_ĐƯỢC | **0,0%** | **≥ 35%** |
| Tầng A · NÓI_MỘT_PHẦN | 0 | **> 0** (0 ở cả hai ô = bộ đo hỏng) |
| Toán hạng chưa ai dùng | **12/43** | **≤ 6**, và mỗi cái còn lại có lý do ghi ra |
| Tầng B · câu bị `loai_cau` từ chối | 158 | **≤ 80** |
| `gann_sq9` gọi được | KeyError | chạy, có ca kiểm |
| `b test` số fail | 4 | **≤ 4** (không thêm cái mới) |
| Ca kiểm nhìn trước cho `song.*` | — | có, và **fail khi cố tình lấp ngược** |

Đo lại bằng đúng một lệnh, hạt ngẫu nhiên cố định nên hai lần chạy lấy **cùng corpus**:

```
python _corpus_ngu_phap.py 150
```

**Claude làm:** `loai_cau` có độ tin cậy, `dieu_kien_trong_cau` trả phần bỏ sót, truy 12 toán
hạng chết, rồi mới đến toán hạng mới + ca kiểm nhìn trước + sửa `gann_sq9`.
**qwen làm:** dựng corpus có người/máy xác nhận là câu luật thật (`B1_corpus_vang`),
chạy lại bộ đo mỗi khi Claude sửa (`B1_do_corpus`), và bóc tiếp để kho câu dày lên.

**Prompt mở phiên:**
```
Khối 1 của lab/KE_HOACH_XAY.md. Trần của hệ là ngữ pháp: 41 toán hạng, và 187/383
giả thuyết là quay-về-trung-bình vì ngữ pháp giỏi nói cái đó nhất.
Thêm bốn nhóm song.* nen.* hinh_hoc.* lien_ma.* vào nhan/ngu_phap.py.
CHẶN TRƯỚC hai bẫy: zigzag nhìn trước (song.dinh phải NaN tới bar xác nhận) và
lien_ma lệch hàng giá (concat axis=1 dropna trước khi to_numpy).
Đo corpus TRƯỚC khi sửa để có baseline. Mỗi toán hạng mới phải có ca kiểm gọi thật.
Đừng thêm toán hạng nào không có trong kế hoạch — hàng đợi từ vựng của qwen sẽ nói
cái tiếp theo nên thêm gì.
```

---

# KHỐI 2 — VÒNG PHẢN HỒI · sổ bài học + tra cứu kết quả âm

**Năng lực phải có:** hệ tự trả lời được *"cái này đã thử chưa, thất bại thế nào, hướng nào nên tránh"*.

**Vì sao:** `hethong.txt` nêu đích danh *"bộ tổng kết để rút ra chiến lược… ghi lại hướng đi nên
tránh… AI giám sát tư duy để đúc rút"*. Grep toàn bộ `nhan/ tru/ qwen/` ra **0 file**.
Chức năng đó hiện sống trong 130 file memory của Claude — **ngoài repo, ngoài tầm với của hệ**.
Mất phiên là mất. Và 1.255 dòng FAIL trong `ket_qua` không tra cứu được.

### Phải tạo

```
bảng nao.db `bai_hoc`   (id, ma, loai, tieu_de, noi_dung, bang_chung, ngay, nguon, lien_quan)
   loai:  bay_do_luong | huong_nen_tranh | huong_dang_mo | quy_tac_nguoi_dung | su_that_tai_san
nhan/bai_hoc.py         them() · tra(cau_hoi) · lien_quan(gia_thuyet)
b da-thu "<mô tả>"      cửa tra cứu một dòng
lab/bai_hoc/*.md        bản người đọc, NẰM TRONG GIT
```

Và một móc nối bắt buộc: `quantlab` gọi `bai_hoc.lien_quan()` **trước khi đăng ký giả thuyết mới**,
cảnh báo nếu trùng hướng đã chết. Đây là chỗ vòng lặp khép lại.

### Cổng nghiệm thu

| Phép đo | Nay | Phải đạt |
|---|---:|---:|
| Thẻ bài học | 0 | **≥ 120** |
| 20 câu hỏi mẫu tra đúng | — | **≥ 16** |
| `evolution` báo cáo có mục "hướng nên tránh" | không | có |
| Giả thuyết mới trùng hướng đã chết bị cảnh báo | không | có, đo bằng ca kiểm |

**Claude làm:** schema, `nhan/bai_hoc.py`, móc vào `quantlab` và `evolution`, 20 câu hỏi mẫu.
**qwen làm:** phân loại 1.255 dòng FAIL + 192 JSON trong `reports/` thành thẻ (`B2_the_bai_hoc`).

---

# KHỐI 3 — ẢNH CHỤP DỮ LIỆU BẤT BIẾN

**Năng lực phải có:** một kết quả chạy hôm nay **tái lập được** sau ba tháng.

**Vì sao:** `kho()` chọn bản theo **độ phủ**. Thêm một file vào `data/` là đổi bản được chọn
của cả một mã, **không báo gì**. Với một hệ lấy holdout làm trọng tài, đây là lỗ hổng nền móng:
`plan_hash` đóng băng *kế hoạch* nhưng không đóng băng *dữ liệu*. Rẻ bây giờ, đắt dần theo thời gian.

### Phải tạo

```
bảng nao.db `anh_chup`  (ma, khung, ban, content_hash, so_bar, tu, den, ghim_luc)
nhan/anh_chup.py        ghim() · kiem() · liet_ke()
du_lieu.kho()           ưu tiên hash đã ghim; file đã ghim mà đổi -> NÉM LỖI, không im lặng đổi bản
quant_plan              plan_hash bao gồm anh_chup_hash
```

### Cổng nghiệm thu

| Phép đo | Phải đạt |
|---|---|
| Chạy lại 20 kết quả cũ | ra **đúng** số cũ |
| Thêm một file rác vào `data/` | kết quả **không đổi** |
| Sửa một file đã ghim | **lỗi rõ ràng**, không im lặng |

**Claude làm:** toàn bộ. **qwen làm:** chạy mẻ băm 518 bảng parquet (`B3_bam_kho`).

---

# KHỐI 4 — TẦNG CHẠM TIỀN

**Năng lực phải có:** một hệ qua cổng đi được tiếp — paper, live-shadow, hạn mức, kill-switch,
giám sát suy giảm — thay vì dừng lại ở một dòng `PASS` trong sổ.

**Vì sao:** `grep -E "paper|live_shadow|kill_switch|decay"` trên `nhan/ tru/ qwen/` = **0 file**.
Hệ tồn tại để ra tiền và **không có một dòng nào chạm tới tiền**. Kiến trúc V2 gọi đây là
"boundary riêng, chưa đạt" — nhưng để nó cuối cùng là sai thứ tự: **nó định nghĩa "xong" nghĩa là gì**.
Không có nó, cổng ra tiền đang chấm một thứ chưa ai nhận.

### Phải tạo

```
nhan/so_lenh.py    sổ paper chỉ-thêm: gt_ma, ma, chieu, luc_vao, gia_vao, lot,
                   luc_ra, gia_ra, phi, ly_do_ra
nhan/han_muc.py    kill-switch: trần sụt giảm · trần lệnh/ngày · trần phơi nhiễm · trần vốn
nhan/suy_giam.py   so chuỗi lệnh thật với phân phối kỳ vọng từ backtest; báo khi lệch quá ngưỡng
máy trạng thái     PAPER_CANDIDATE -> PAPER -> LIVE_SHADOW -> LIVE_CAP
```

**Luật cứng, không được nới:** không kết quả nào tự động giao dịch tiền thật chỉ vì có nhãn `PASS`.
Live chỉ mở sau paper period định trước, tick test, kill-switch đã **diễn tập**, và hạn mức vốn.

### Cổng nghiệm thu

| Phép đo | Phải đạt |
|---|---|
| Hệ `pine_cm_rsi_2 / TS_QQQ` (cái duy nhất qua holdout) chạy paper | sổ khớp tín hiệu backtest **100%** trên cùng cửa sổ |
| Diễn tập kill-switch | kích hoạt đúng, ghi sự kiện, không cần người |
| `suy_giam` trên một chuỗi cố tình bẻ hỏng | **bắt được**, không im lặng |

**Claude làm:** toàn bộ thiết kế và mã. **qwen làm:** chạy nhịp paper hằng ngày, ghi sổ (`B4_nhip_paper`).

---

# KHỐI 5 — CÁC CỬA VÀO CÒN THIẾU

**Năng lực phải có:** bốn cửa `hethong.txt` nêu mà hệ chưa có.

| Cửa | Hiện trạng | Phải tạo |
|---|---|---|
| video → cơ chế | 109 video mới dừng ở tải về | `nhan/doc_video.py` (yt-dlp + faster-whisper) |
| ảnh → cơ chế | chỉ có `doc_pdf` | `nhan/doc_anh.py` (OCR) |
| suy ngược từ sổ lệnh | `mimic` nằm trong `ds/` git riêng | `nhan/mimic_cau_noi.py` nối vào đường chạy |
| luồng ưu tiên của chủ dự án | `nap_tay/` có 5 repo, không có cửa | `b uu-tien <link\|file>` — trả kết quả **trong cùng phiên** |
| follow kênh/nhóm theo lịch | `theo_doi` 9 dòng | `nhan/theo_doi.py` — lịch đọc lại, không cần hằng ngày |

### Cổng nghiệm thu

| Phép đo | Nay | Phải đạt |
|---|---:|---:|
| Video có transcript | 0 | **≥ 80 / 109** |
| Cơ chế bóc được từ video | 0 | **≥ 20** |
| `b uu-tien` một link bất kỳ | không có | trả cơ chế + nhận định **cùng phiên** |
| Kênh đang theo dõi có lịch | 9 | **≥ 40** |

**Kiểm trước:** mạng máy này chặn một phần nguồn, DNS bị đầu độc với mql5.com —
chạy `b mang` và bật Cloudflare WARP trước khi kết luận "không tải được".

**Claude làm:** `b uu-tien`, cầu nối mimic, khung `doc_video` / `doc_anh`.
**qwen làm:** chạy mẻ transcript rồi bóc (`B5_transcript`, `B5_boc_video`).

---

# KHỐI 6 — QUẢN TRỊ ĐÈ LÊN HỆ NGOÀI + KHOÁ TESTER

**Năng lực phải có:** bộ quản lý lệnh chạy **đè lên một EA bất kỳ**, kể cả EA của người khác —
đúng ý `hethong.txt`: *"có thể quản trị độc lập hoặc làm 1 bộ quy tắc để tích hợp vào những hệ thống khác"*.

**Vì sao sau cùng:** nó ăn theo tầng chạm tiền ở khối 4. Đè quản trị lên một EA đang chạy tiền thật
mà không có kill-switch là đi ngược thứ tự an toàn.

### Phải tạo

```
EA giám sát hoàn chỉnh   (bản nháp đã biên dịch đạt 07/09, chưa đè thật lên EA ngoài)
nhan/khoa_tester.py      một cửa CÓ KHOÁ cho terminal64.exe
```

Khoá tester không phải tiện nghi: làn = 1 hiện đang dựa vào **kỷ luật con người**, và hai việc
cùng lúc ghi đè nhau **mà không ai báo lỗi** — đọc y hệt một kết quả thật.

### Cổng nghiệm thu

| Phép đo | Phải đạt |
|---|---|
| Đè quản trị lên 1 EA ngoài trong tester | **số lệnh đổi**, đo được |
| Hai việc tester phóng cùng lúc | việc thứ hai **bị chặn có thông báo**, không ghi đè |

---

# Bảng nghiệm thu toàn kế hoạch

| # | Khối | Chỉ số | Nay | Phải đạt |
|---|---|---|---:|---:|
| 1 | Ngữ pháp | toán hạng | 41 | ≥ 60 |
| 1 | Ngữ pháp | corpus diễn đạt được | baseline | ≥ 70% |
| 2 | Bài học | thẻ | 0 | ≥ 120 |
| 2 | Bài học | câu hỏi tra đúng | — | ≥ 16/20 |
| 3 | Ảnh chụp | kết quả cũ tái lập | không | 20/20 |
| 4 | Chạm tiền | file | 0 | sổ + hạn mức + suy giảm |
| 4 | Chạm tiền | paper khớp backtest | — | 100% |
| 5 | Cửa vào | video có transcript | 0 | ≥ 80 |
| 5 | Cửa vào | `b uu-tien` | không | trả cùng phiên |
| 6 | Quản trị | đè lên EA ngoài | nháp | số lệnh đổi |
| 6 | Tester | khoá thật | kỷ luật người | chặn được |

**Đừng đánh đồng "khối xong" với "hệ ra tiền".** Kế hoạch này xây *năng lực*.
Ra tiền là việc của những vòng chạy sau, trên năng lực đã có.

---

## Cập nhật trạng thái

`config/ke_hoach_xay.json` giữ khối đang làm và kết quả từng cổng.
Cập nhật lúc `b ket`, **không sửa tay** phần số — sửa tay thì mai hết so sánh được.

Khi một khối đạt cổng: đổi `trang_thai` sang `DAT`, ghi ngày, đẩy `dang_o` sang khối kế.
Khi một cổng trượt: ghi `AM` kèm số đo, hoặc `CHUA_DO_DUOC` kèm lý do khâu đo hỏng —
**và không được sang khối kế**.
