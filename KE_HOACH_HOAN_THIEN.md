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

**Nút thắt là chặng 4→5: 1.035/1.418 cơ chế chưa bao giờ được chấm cổng**, cộng
**567 ứng viên treo** trong `candidate_queue`.

Đây không phải vấn đề đầu vào. Kho đã dày gấp đôi trong hai ngày (689 → 1.418).
Vấn đề là **hàng vào kho rồi nằm đó**.

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

### H1 — THÔNG CHẶNG 4→5 (đòn bẩy cao nhất)

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

**H1 trước** vì nó là chặng hẹp nhất: kho đã có 1.418 cơ chế mà 73% chưa vào
cổng. Mọi việc làm dày thêm đầu vào (H4) đều **vô nghĩa khi chặng 5 còn tắc** —
đổ thêm nước vào ống đang nghẹt.

**H3 trước H4** vì hiệu chuẩn cổng quyết định 14 PASS hiện có là thật hay lọt.
Chạy thêm hàng qua một cái cổng chưa hiệu chuẩn là nhân bản nghi ngờ.

**H5 chạy song song** — nó chờ bạn, không chặn tôi.

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

## 6. Cách đo tiến độ — một con số duy nhất

Không đo bằng "đã làm bao nhiêu việc". Đo bằng **tỉ lệ lọt của chặng hẹp nhất**:

```
tỉ lệ thông = giả thuyết đã đăng ký / cơ chế trong kho
12/09: 383 / 1.418 = 27,0%
```

Dán con số này vào mọi báo cáo. H1 xong mà nó không nhúc nhích thì H1 sai chỗ.
