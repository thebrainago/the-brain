# KẾ HOẠCH HOÀN THIỆN THE BRAIN

> **Nguồn duy nhất của cấu trúc: `Desktop/hethong.txt` (chủ dự án, 11/09/2026).**
> Bản trước của tài liệu này dựng theo `KE_HOACH_XAY.md` và sổ `van_de` của lab —
> **sai cấu trúc**, đã chuyển vào `nhat_ky/KE_HOACH_HOAN_THIEN_SAI_CAU_TRUC_12_09.md`.
> Lab đã mọc thêm BANKER và NGHI, hai thứ **không có trong sơ đồ**, và tôi đã
> xếp chúng vào việc phải làm.

---

## 0. Hai điều chỉnh về TINH THẦN — đọc trước khi đọc việc

**(a) Mục tiêu là TIỀN, không phải chặt chẽ học thuật.** Chủ dự án viết:

> *"mục tiêu là lợi nhuận còn lại không phải những mô hình kinh tế hay quản trị
> quỹ để mà cần đề cao quá nhiều tiêu chí học thuật hay các chỉ tiêu chặt chẽ.
> Mục đích cuối cùng là có tiền chấp nhận cả chi phí và rủi ro cao"*

Phiên 12/09 tôi làm ngược: lấy **MDE / FDR / placebo làm tường chặn** rồi lần
lượt tuyên bố trailing, ghép, z5, quantora là ÂM. Những phép đo đó **không sai**,
nhưng dùng làm **cổng chặn** thì sai vai. Vai đúng là **nhãn cảnh báo** — *"cái
này mỏng, vào tiền thì size nhỏ"* — chứ không phải *"cấm cửa"*.

Hệ quả cụ thể: một cơ chế dưới MDE **vẫn được đi tiếp**, kèm nhãn. Chỉ chặn khi
nó **thua mua-giữ ở cùng rủi ro** — đó mới là câu hỏi tiền.

**(b) QUẢN LÍ LỆNH quan trọng hơn ENTRY.** Chủ dự án viết:

> *"việc sử dụng kỹ thuật quản lí lệnh tốt còn hơn việc có 1 entry tốt"*
> *"Riêng mục này cần chú ý vì nó là module quan trọng trong toàn bộ hệ thống"*

Sáng 12/09 tôi chạy placebo trên họ trailing rồi đóng lại là ÂM. Theo (a), đó là
**một nhãn**, không phải bản án. Mở lại hướng này.

**(c) Nền tảng là FX.** Cả phiên 12/09 tôi ở chỉ số Mỹ.

---

## 1. Sơ đồ đúng — BA module

### THE SEEKER

| mục trong sơ đồ | trạng thái |
|---|---|
| A. phễu fetch đa nguồn | **CÓ** `tru/seeker.py` · 73 nguồn BẬT · 10.479 tài liệu |
| trình duyệt riêng + Gmail/social | **CÓ** `nhan/cau_browser.py` · 25 nguồn trình duyệt |
| né chặn bot | **CÓ** (WARP · CDP · mô phỏng người dùng) |
| quét thông minh: soi lại trang 1 rồi đi sâu | **CÓ** con trỏ biên giới · 75 trang / 4 vòng |
| xếp hạng ưu tiên nguồn có file dùng được | **CÓ** `uu_tien` trong bảng `nguon` |
| tự follow kênh / nhóm / cá nhân | **CÓ** telegram · 9 kênh theo dõi |
| tự sinh từ khoá mới | **CÓ** bảng `tu_khoa` |
| tìm kiếm ĐA NGÔN NGỮ | **CÓ** habr_nga · qiita_nhat · velog_han · cnblogs_trung |
| nguồn có LỊCH SỬ GIAO DỊCH | **CÓ** mql5_signals · myfxbook · darwinex · collective2 · zulutrade |
| B. bộ lọc — mq5/c++ dùng luôn | **CÓ** `nhan/doc_ma.py` · 570 mã nguồn trong kho |
| văn bản → cơ chế | **CÓ** `nhan/doc_hieu.py` |
| VIDEO → cơ chế | **CÓ** `nhan/doc_video.py` |
| ẢNH → cơ chế | **CÓ** `nhan/doc_anh.py` · OCR kiểm 12/09, trùng khớp từ 78,8% |
| xếp hàng theo chất lượng đầu vào | **CÓ** `candidate_queue` + `uu_tien` |
| suy ngược từ lịch sử giao dịch | **CÓ** `nhan/tin_hieu_mql5.py` |

**SEEKER đủ 14/14.** Việc còn lại là VẬN HÀNH (4 nguồn thu hoạch = 0), không phải xây.

### THE QUANTLAB

#### Tổng quan tài sản — CHỖ THIẾU THẬT SỰ

`nhan/ho_so_symbol.py` đã đo **159 mã**: hurst · VR(2)/VR(10) · ac1 · nửa đời ·
efficiency ratio · nhãn tính cách · biến động năm · ATR% · biên độ bar · spread ·
**phí qua đêm hai chiều** · độ tin chi phí.

| chủ dự án yêu cầu | trạng thái |
|---|---|
| biên độ · chi phí · phí qua đêm | **CÓ** |
| tính hồi quy / trend | **CÓ** (hurst → `nhan_tinh_cach`) |
| trượt giá | **một phần** — `chi_phi.truot_gia_frac`, chưa vào hồ sơ |
| **tính mùa vụ** (không / có / có thì cụ thể thế nào) | **THIẾU** |
| **tương quan** (âm / dương với mã khác) | **THIẾU** |
| **sóng zigzag**: biên độ đẩy · tần suất đẩy · tần suất hồi · biên độ hồi | **THIẾU** |
| **mốc magnetic** | **THIẾU** |
| **entry-time trong năm** (thời điểm xác suất cao) | **THIẾU** |
| các dạng nến | có template, chưa thành ĐẶC TÍNH tài sản |
| hình học / gann | có `gann_activator`, `gann_sq9` |

→ **Việc xây thật đầu tiên.**

#### Cơ chế QUẢN LÍ — module quan trọng nhất theo sơ đồ

| chủ dự án liệt kê | trạng thái |
|---|---|
| ATR | có (toán hạng) |
| trailing stop | **có, đã đo** — 5/42 hơn cả hai nửa · placebo p 0,596 |
| hedging | có trong DSL lưới |
| **buy/sell stop hai đầu** | **THIẾU** |
| **market + stop hedge đối diện** | **THIẾU** |
| DCA · DCA tính vốn | có (lưới AUDCAD / Bigmouse) |
| đánh nhanh chốt nhanh | có |
| chạy ĐỘC LẬP hoặc ĐẮP lên hệ khác | **CÓ** `_thu_quan_tri.py` |

Kho quản trị: **42 luật đã thử**, 18 trong `quan_tri_vi_the.json`.
Kho cơ chế 1.420 thì **0 cái có trường quản trị** — hai họ vẫn tách rời.

#### Chiến lược

| yêu cầu | trạng thái |
|---|---|
| test thô python → test phần mềm giao dịch | **CÓ** (`chay_tester_kho` + khoá tester) |
| backtest file có sẵn trước | **CÓ** |
| kiểm chỉ báo mũi tên / có entry | **CÓ** |
| dựng file chiến lược từ cơ chế | **CÓ** (bộ dịch DSL → MQL5) |
| truy ngược lịch sử giao dịch | **CÓ** |
| **đa cặp × đa khung × đa quản lí × đa thông số** | **một phần** |
| **kết hợp đa chỉ báo đa hệ thống** | **một phần** (`_ghep_he`) |
| bộ tổng kết: bài học + hướng nên tránh | **CÓ** 238 bài học |
| AI giám sát tư duy | **CÓ** EVO |

#### Nội sinh · Luồng ưu tiên

`nhan/noi_sinh.py` **CÓ**. Luồng ưu tiên khi chủ dự án gửi bài — **THIẾU cửa vào rõ ràng**.

### THE EVO

| mục | trạng thái |
|---|---|
| giám sát hiệu suất từng module | **CÓ** `tru/evolution.py` |
| cắt nghĩa vấn đề + đề xuất | **CÓ** — 82 vấn đề · 39 đề xuất |
| THE FINDER tìm công cụ / skill | **CÓ** `tru/finder.py` — 3 công cụ ≥70 điểm đang chờ |

### Ba nguyên tắc vận hành

| | trạng thái |
|---|---|
| 1. bypass — duyệt sẵn mọi đề xuất | đang theo |
| 2. terminal thúc agent chạy tiếp (THE THORN) | **CÓ** `dieu_khien_xa.py` + `q` |
| 3. chạy SONG SONG các trụ không liên quan | **CÓ** `q` 5 làn · nhưng `dieu_phoi` tắt từ 01/09 |

### Ngoài sơ đồ

`tru/banker.py` (vĩ mô FRED) và `tru/nghi.py` — **không có trong sơ đồ**. Không
xoá, nhưng **không tính là việc phải hoàn thiện**.

---

## 2. Việc còn lại — theo sơ đồ, không theo sổ `van_de`

```
[ ] Q1  ho_so_song.py — sóng zigzag (biên độ/tần suất đẩy·hồi) + mốc magnetic
[ ] Q2  mùa vụ + entry-time trong năm, cho từng mã
[ ] Q3  tương quan liên mã (âm/dương) vào hồ sơ
[ ] Q4  buy/sell stop hai đầu + market kèm stop hedge đối diện
[ ] Q5  hạ MDE/FDR/placebo từ CỔNG CHẶN xuống NHÃN CẢNH BÁO
[ ] Q6  đa cặp × đa khung × đa quản lí × đa thông số — chạy đủ tổ hợp
[ ] Q7  cửa vào LUỒNG ƯU TIÊN khi chủ dự án gửi bài / giả thuyết
[ ] S1  4 nguồn thu hoạch = 0 (semantic · fxblue · etoro · quantconnect)
[ ] E1  quyết `dieu_phoi` bật lại hay để `q` thay hẳn      ← cần chủ dự án
[ ] E2  3 công cụ ngoài ≥70 điểm đang chờ xem              ← cần chủ dự án
```

**Q5 trước Q6**, vì chạy tổ hợp qua một cái cổng đặt sai vai thì lại loại sạch
như phiên 12/09.

**Q1–Q4 là xây thật.** Phần còn lại phần lớn là nối dây và vận hành.

---

## 3. Đo tiến độ

Không đo bằng số phép thử. Đo bằng **số dòng trong sơ đồ đã CÓ**:

```
SEEKER      14/14   đủ
QUANTLAB    17/24   thiếu 7
EVO          3/3    đủ
vận hành     2/3    dieu_phoi tắt
──────────────────────────────
            36/44 = 82%
```

Dán con số này vào mọi báo cáo.
