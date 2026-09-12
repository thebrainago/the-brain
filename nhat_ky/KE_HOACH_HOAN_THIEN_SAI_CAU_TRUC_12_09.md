# KẾ HOẠCH HOÀN THIỆN HỆ THỐNG

> Chốt 12/09/2026. Thay `KE_HOACH_XAY.md` làm tài liệu điều hướng chính.
> `KE_HOACH_XAY.md` là kế hoạch **xây năng lực** (6 khối, đã xong 5, khối 1 đóng
> có điều kiện). Tài liệu này là kế hoạch **hoàn thiện dây chuyền** — khác nhau
> ở chỗ: khối thì xong là xong, còn dây chuyền thì phải **thông từ đầu đến cuối**.

---

## 1. Hệ thống là một dây chuyền 8 chặng

Đo 12/09/2026. Con số là trạng thái thật trong `nao.db`, không phải mục tiêu.

```
 CHẶNG                          HIỆN CÓ      LỌT QUA      GHI CHÚ
 ─────────────────────────────────────────────────────────────────────────
 1  NGUỒN                       73 BẬT          —        4 nguồn thu hoạch = 0
 2  TÀI LIỆU                    10.479          —
 3  NỘI DUNG (đã đọc)            7.154        68%        3.325 chưa đọc
 4  CƠ CHẾ (đã bóc)              1.418        20%        570 là mã nguồn
 5  GIẢ THUYẾT (đã đăng ký)        383        27%        ◄── NÚT THẮT
 6  KẾT QUẢ (đã chấm cổng)       1.280          —        FDR 1.807, bác 406
 7  PASS                            14        3,7%
 8  CHẠM TIỀN                        1          —        1 hệ chạy, 1 hạn mức
```

### ĐÍNH CHÍNH 12/09 — chặng 4→5 KHÔNG nghẽn

Bản đầu của tài liệu này gọi chặng 4→5 là nút thắt, với hai chứng cứ, và **cả
hai đều sai**:

1. *"567 ứng viên treo trong `candidate_queue`"* — SAI. Con trỏ tiêu thụ
   (`reports/quantlab_candidate_cursor.json`) đang ở **id 637**, mà id lớn nhất
   trong bảng cũng là **637**. Đã rút hết. Bảng đó là **nhật ký chỉ-ghi-thêm**
   (trigger chặn UPDATE/DELETE) nên hàng vẫn nằm đó vĩnh viễn — đó là dấu vết
   kiểm toán, không phải tồn đọng.

2. *"1.035 cơ chế chưa bao giờ được chấm"* — ĐÚNG SỐ, SAI CÁCH ĐỌC. Chạy cả
   1.132 cơ chế "lành lặn" trên `XM_US500CASH` D1 (4.054 bar, MDE 1,097):

   ```
   Sharpe tốt nhất 0,877 · phân vị 95% 0,486 · TRUNG VỊ 0,001
   >>> vượt MDE: 0 / 1.132  =  0,0%
   ```

   **Không một cái nào.** Chúng không bị kẹt — chúng bị **cổng MDE loại đúng
   như thiết kế**, vì không cái nào đủ tín hiệu để phân biệt với nhiễu.

**Hệ quả cho kế hoạch:** H1 (thông chặng 4→5) **bị huỷ**. Đẩy tỉ lệ 27% lên cao
hơn nghĩa là đăng ký những giả thuyết không thể phát hiện được, đốt ngân sách
FDR mà không đổi kết cục. Và "tỉ lệ thông" ở mục 6 là **thước đo sai** — sửa ở
mục 6.

Dây chuyền **đang thông**. Cái thiếu không phải đường ống mà là **tín hiệu đủ lớn
để đo được** — cùng bức tường `MDE ≈ 2,98/√năm` đã đo sáng nay.

---

## 2. Sáu trụ — trạng thái và phần còn thiếu

| trụ | nhịp tim | mã chết | phần chưa hoàn thiện |
|---|---|---:|---|
| SEEKER | nghi 04/09 | 1 | 4 nguồn BẬT mà thu hoạch = 0; 17 PDF ảnh chưa OCR |
| QUANTLAB | nghi 04/09 | 0 | **không chấm được 16 EA đặt lệnh thật** (thiếu template) |
| NGHI | nghi 01/09 | 0 | — |
| BANKER | nghi 11/09 | 0 | 3/4 phần chưa làm (giáo trình, nhận định, mục VN) |
| EVO | nghi 01/09 | 0 | — |
| FINDER | song 04/09 | 0 | 3 công cụ ngoài ≥70 điểm chờ người xem |
| **DIEU_PHOI** | **dung 01/09** | — | **control plane TẮT 11 ngày** |

Sản lượng vẫn lành (10.479 tài liệu · 238 bài học · 41.524 chỉ số vận hành), tức
các trụ **chạy được**, chỉ là **không ai gọi chúng**.

---

## 3. Việc còn lại, xếp theo ĐÒN BẨY chứ không theo thứ tự phát hiện

Ước lượng là **giờ máy + lượt Claude**, không phải giờ người.

### ~~H1 — THÔNG CHẶNG 4→5~~ — **ĐÃ HUỶ, xem đính chính mục 1**

**H1a ĐÃ ĐO XONG 12/09** (`_truy_chang_4_5.py`). 1.389 cơ chế chưa thành giả thuyết:

```
1.132  (81,5%)  LÀNH LẶN — qua kiểm khai báo, sinh tín hiệu, kích hoạt 1,7-42,8%
  166  (12,0%)  trượt kiểm khai báo — hầu hết chỉ THIẾU TRƯỜNG `co_che`
   43  ( 3,1%)  KhungThieuGio — cơ chế theo PHIÊN chạy trên khung không có giờ
   40  ( 2,9%)  không kích hoạt lần nào
    8  ( 0,6%)  kích hoạt 100% = mua-giữ đổi tên
```

**Kết luận: H1 là việc CHẠY, không phải việc VIẾT.** Bốn phần năm kho chỉ thiếu
người đưa vào cổng.

- **H1b** Chạy 1.132 cơ chế lành lặn qua cổng. **NHƯNG KHÔNG ĐƯỢC ĐỔ THẲNG**:
  đăng ký 1.132 giả thuyết sẽ đốt sạch ngân sách FDR tích luỹ. Phải theo đúng
  phễu đã có — **chặn bằng MDE trước, chỉ đăng ký cái đủ lực** (đo 24/08: lọc
  MDE cho 3 đăng ký thay vì 99). *Claude dựng phễu 1 lượt · qwen chạy mẻ*
- **H1c** 166 cơ chế thiếu trường `co_che`: đây là lỗ của khâu BÓC, không phải
  của cơ chế. Sửa bộ bóc để không sinh khai báo thiếu trường bắt buộc, rồi điền
  bù cho 166 cái cũ. *Claude · 1–2 lượt*
- **H1d** 43 cái `KhungThieuGio`: chạy trên khung CÓ GIỜ (H1/H4) hoặc bar phiên
  (`du_lieu.nap_phien`), không phải D1. *Claude · 1 lượt*
- **H1e** `can_mau_moi_tu_ma_nguon`: 16 file .mq5 **đặt lệnh thật** mà `mau.py`
  chưa có template. *Claude · 2–3 lượt*
- **H1f** 567 ứng viên treo trong `candidate_queue` — chạy sau khi phễu H1b xong.
  *qwen*

### H2 — BẬT LẠI CONTROL PLANE hoặc CHÍNH THỨC BỎ
Hiện `q` (qwen) đang là người lái thật; `dieu_phoi` tắt 11 ngày. **Hai hệ điều
phối cùng tồn tại là nợ kỹ thuật**, không phải dự phòng.
- **H2a** Quyết: giữ `dieu_phoi` hay để `q` thay hẳn. *Cần chủ dự án*
- **H2b** Nếu giữ: bật lại + kiểm hai bên không giành tester (khoá đã kín 12/09).
  Nếu bỏ: gỡ `dieu_phoi` khỏi tài liệu, chuyển 6 trụ thành làn của `q`.
  *Claude · 2 lượt*

### H3 — HIỆU CHUẨN CỔNG PASS (NẶNG, đang mở)
`hieu_chuan_v6`: cổng chưa từng được hiệu chuẩn bằng **V6 thật** (thiếu lớp
bias>0, danh mục 3 chỉ số, bar D1 theo phiên). Một cổng chưa hiệu chuẩn thì 14
PASS kia **không biết là thật hay lọt**. *Claude · 3–4 lượt*

### H4 — MỞ LỚP NGUỒN ĐANG VÔ HÌNH
- **H4a** `ocr_anh_chan_nguon`: 425 trang × 14,2s EasyOCR ≈ **100 phút máy**,
  chạy nền một lần. *qwen · máy 100 phút*
- **H4b** Sửa 4 nguồn thu hoạch = 0 (semantic, fxblue, etoro, quantconnect) và
  1 nguồn chết (rss_reddit_quant). *qwen · 1–2 lượt*

### H5 — BA CON SỐ **CHỈ CHỦ DỰ ÁN TRẢ LỜI ĐƯỢC**
Mọi ngưỡng của hệ đang dùng mặc định học thuật 0,05 — là **mặc định, không phải
chân lý**. Cần khai vào `lab/config/nguong.json`:
1. một chiến lược thật sự tốt, sau chi phí, đáng bao nhiêu **một năm**?
2. một chiến lược vô dụng lọt qua gây thiệt hại bao nhiêu **một năm** (gồm VPS,
   spread, thời gian)?
3. xác suất tiên nghiệm: trong 100 ý tưởng đưa vào, bạn nghĩ bao nhiêu cái thật?

**Không ai làm thay được**, và nó chỉnh lại toàn bộ cổng phía sau.

### H6 — DỌN NỢ NHỎ
`ngu_phap_thieu_toan_hang` · `cong_cu_dang_xem` (3 công cụ ngoài) ·
`cho_kiem_tick_mt5` · `nguon_can_trinh_duyet` · 1 mã chết.
*qwen phần lớn · Claude 1 lượt*

---

## 4. Vì sao thứ tự này

**H1 đã huỷ** sau khi đo: chặng đó không nghẽn.

**H3 lên đầu.** Hiệu chuẩn cổng là việc còn lại có giá trị cao nhất: 14 PASS hiện
có **chưa biết là thật hay lọt**, vì cổng chưa từng được hiệu chuẩn bằng V6 thật.
Một hệ đã hoàn thiện mà cổng chưa hiệu chuẩn thì mọi con số nó in ra đều treo.

**H4 sau H3** — mở thêm lớp nguồn chỉ đáng làm khi cổng đã đáng tin.

**H5 chạy song song** — nó chờ bạn, không chặn tôi.

**H2 cần bạn quyết** — hai hệ điều phối cùng tồn tại là nợ, không phải dự phòng.

---

## 5. Ranh giới Claude / qwen / chủ dự án

Giữ nguyên ranh giới đã đo 11/09 (LLM điền `co_che` cho 48 khai báo, thẩm định
bác 41, ròng cứu 3 — 6% không dùng được cho một cổng nhưng rất tốt cho khối
lượng đọc):

| việc | Claude | qwen | chủ dự án |
|---|:--:|:--:|:--:|
| `nhan/ngu_phap.py`, `nhan/mau.py`, schema, cổng | ✓ | ✗ | |
| hiệu chuẩn cổng, thiết kế tầng chạm tiền | ✓ | ✗ | |
| đọc/bóc/OCR khối lượng, chạy mẻ | ✗ | ✓ | |
| chấm đạt/âm | ✗ | ✗ | `qwen/cong.py` chấm bằng mã |
| ba con số ở H5 | ✗ | ✗ | ✓ |
| giữ hay bỏ `dieu_phoi` | ✗ | ✗ | ✓ |

---

## 6. Cách đo tiến độ

**Thước đầu tiên tôi đề xuất là SAI** và ghi lại đây để không ai dùng lại:

> ~~tỉ lệ thông = giả thuyết / cơ chế trong kho = 27,0%~~

Đẩy tỉ số này lên chỉ có nghĩa là đăng ký thêm giả thuyết **không thể phát hiện
được** — 0/1.132 cơ chế chưa đăng ký vượt nổi MDE. Một thước đo mà cách duy nhất
để cải thiện là làm điều sai thì là một thước đo hỏng.

**Thước đúng cho việc HOÀN THIỆN HỆ:** đếm phần còn thiếu, và nó hữu hạn —

```
 [ ] cổng PASS hiệu chuẩn bằng V6 thật            (H3, NẶNG)
 [ ] 17 PDF ảnh đã OCR                            (H4a, ~100 phút máy)
 [ ] 166 cơ chế thiếu trường `co_che` đã điền     (lỗ khâu BÓC)
 [ ] 43 cơ chế theo PHIÊN chạy đúng khung có giờ
 [ ] 16 EA đặt lệnh thật có template trong mau.py
 [ ] 4 nguồn thu hoạch = 0 đã sửa
 [ ] BANKER 3/4 phần còn lại
 [ ] quyết giữ hay bỏ `dieu_phoi`                 (chủ dự án)
 [ ] ba con số ở H5 đã khai                       (chủ dự án)
```

Chín ô. Hệ hoàn thiện khi cả chín tick. **Không ô nào trong đó là "tìm thêm
edge"** — đó là việc khác, và nó bị chặn bởi MDE chứ không bởi độ hoàn thiện
của hệ.
