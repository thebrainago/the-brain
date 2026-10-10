# GÓI BÀN GIAO the-brain → brain2

> Xuất ngày **10/10/2026** từ kho `thebrainago/the-brain`, nhánh `claude/autonomous-trading-system-rzzt7h`, commit `8a1151c`.
> **Một chiều**: the-brain → brain2. Phiên Claude đám mây của the-brain soạn theo yêu cầu của chủ dự án; phiên đó không có quyền ghi vào brain2 (chủ dự án đã từ chối việc xin quyền): brain2 tự đọc, tự chọn, tự làm.

---

## A. Dành cho chủ dự án (lời thường, 30 giây)

- **Đây là gì.** Một thư mục gom (1) *kinh nghiệm* the-brain đã trả giá: bẫy đã sa, con số đã đo, điều đã sai; (2) *dữ liệu có thể giao*, toàn bộ do the-brain tự suy ra; (3) gợi ý nên làm gì trước. Để brain2 khỏi phải trả lại các cái giá đó.
- **Việc bạn phải làm.** Mở `LOI_NHAN_CHO_GROK.md`, chép phần trong khung (bản đầy đủ, hoặc bản ngắn nếu bot giới hạn độ dài), dán cho Grok. Link nằm sẵn trong tin nhắn.
- **Ràng buộc đã ghi (theo câu của bạn).** Chạy trên máy hiện có, **không nâng lõi, không mua VPS**, không đăng ký dịch vụ trả tiền. Muốn mua gì thì phải có số đo và hỏi bạn trước (`01` mục 7).
- **Cố ý không đưa.** Bot / EA / `.set` / lịch sử lệnh thô của người khác, giá của sàn, tên tín hiệu – EA – tác giả, khóa / mật khẩu / số tài khoản, số tiền cá nhân, dữ liệu cào từ trang cần đăng nhập (`05` mục 2).
- **Còn mở, cần bạn.**
  1. brain2 duyệt theo tiêu chí 25/09 của bạn (lãi sau phí + maxDD < 80 %) hay giữ cổng chặt hơn hiện có — Grok sẽ hỏi bạn một câu (`01` mục 3).
  2. Lấy lịch sử lệnh của "người thắng" cần phiên đăng nhập của bạn — nhưng **chưa cần** cho các việc đầu.

---

## B. Dành cho AI đọc gói này

### B1. Link gốc

Các đường dẫn dạng `nhan/…`, `tai_lieu/…`, `reports/…`, `config/…` trong gói là **tệp của kho the-brain** (kho công khai, không cần đăng nhập). Ghép với:

- Xem trang: `https://github.com/thebrainago/the-brain/blob/claude/autonomous-trading-system-rzzt7h/<đường dẫn>`
- Bản thô: `https://raw.githubusercontent.com/thebrainago/the-brain/claude/autonomous-trading-system-rzzt7h/<đường dẫn>`
- Ví dụ: `nhan/luoi.py` → `https://raw.githubusercontent.com/thebrainago/the-brain/claude/autonomous-trading-system-rzzt7h/nhan/luoi.py`
- Cả gói: `https://github.com/thebrainago/the-brain/tree/claude/autonomous-trading-system-rzzt7h/ban_giao_brain2`

Link nhánh có thể chết nếu nhánh bị gộp / xóa → dùng link **ghim commit** do chủ dự án đưa kèm (không bao giờ đổi), hoặc (nếu nhánh đã được gộp) tìm thư mục `ban_giao_brain2/` trên nhánh mặc định `main`. Không mở được link nào → nói chủ dự án, sẽ có bản zip của đúng thư mục này.

Tệp the-brain được trích nhiều nhất (đọc khi cần, không bắt buộc): `nhan/luoi.py` (engine lưới), `nhan/swap_uoc.py`, `nhan/hieu_chuan_luoi.py`, `nhan/doi_chung_nhieu.py` (đã đóng băng — đừng chép nguyên), `tai_lieu/VONG_LAP.md`, `tai_lieu/RA_SOAT_KIEN_TRUC_03102026.md`, `tai_lieu/NGUON_NGUOI_THANG.md`, `tai_lieu/TOI_UU_TOKEN.md`, `reports/chan_doan_hieu_suat_08102026.md`.

### B2. Thứ tự đọc (≈ 20.000 từ tổng)

| # | Tệp | Là gì | Cỡ |
|---|---|---|---|
| 1 | `01_LUAT_CHU_DU_AN.md` | **Lệnh của chủ dự án** — đọc kĩ nhất. Chỗ nào mâu thuẫn với tệp khác thì `01` thắng | ≈ 1.800 từ |
| 2 | `02_KINH_NGHIEM.md` | Kinh nghiệm đã trả giá. Nếu chỉ có 5 phút: **mục 0** (mười điều). Sau đó mục **B** (bẫy mô phỏng) và **C** (bẫy thống kê) | ≈ 5.800 từ |
| 3 | `04_MANH_GHEP_NEN_LAY.md` | **P1…P7**: mảnh ghép lấy được sang brain2 (bảng nhanh ở đầu; P1 có bước làm chi tiết + bảng 15 ô), danh sách *không lấy*, thứ tự làm đề xuất | ≈ 4.000 từ |
| 4 | `03_KET_QUA_DA_DO.md` | Các con số đã đo (R1–R14) + danh sách **CHƯA ĐO** + cách đọc từng con số | ≈ 3.300 từ |
| 5 | `05_NGUON_DU_LIEU.md` rồi `du_lieu/README.md` | Dữ liệu có gì / cố ý không có gì; tải giá cho P1 ở đâu; mô tả từng cột + đoạn mã tự kiểm số | ≈ 3.700 từ |
| 6 | `06_GOI_Y_VIEC_TIEP.md` | Ý kiến của Claude về việc đầu (**không phải lệnh**) | ≈ 1.000 từ |

Gói ở đây chỉ **đưa ra** hiểu biết; việc chọn việc là của brain2.

### B3. Sơ đồ thư mục

```
ban_giao_brain2/
├─ README.md                       (tệp này)
├─ LOI_NHAN_CHO_GROK.md            (tin nhắn để chủ dự án dán; bản đầy đủ + bản ngắn)
├─ 01_LUAT_CHU_DU_AN.md            luật + ý muốn của chủ dự án
├─ 02_KINH_NGHIEM.md               A việc / B mô phỏng / C thống kê / D dữ liệu-nguồn / E dùng AI-LLM / F vận hành / G nếu dùng MT5
├─ 03_KET_QUA_DA_DO.md             R1–R14 + CHƯA ĐO
├─ 04_MANH_GHEP_NEN_LAY.md         P1–P7 + đừng lấy
├─ 05_NGUON_DU_LIEU.md             dữ liệu: đã giao / không giao / lấy phần thiếu
├─ 06_GOI_Y_VIEC_TIEP.md           gợi ý của Claude
└─ du_lieu/
   ├─ README.md                    mô tả cột + tự kiểm số
   ├─ hieu_chuan_125_o.csv         125 cấu hình lưới: engine nến ↔ MT5 tester
   ├─ hieu_chuan_tom_tat.json      số tóm tắt (tính lại từ CSV)
   ├─ doi_chung_nhieu_tom_tat.json đối chứng nhiễu: 9 kịch bản
   ├─ vung_lai_trong_mau.csv       1.055 vùng lãi (toàn bộ TRONG mẫu)
   ├─ mql5_400_phan_loai.csv       400 hồ sơ tín hiệu công khai (chỉ ID + số)
   ├─ mql5_31_nguoi_thang.csv      31 hồ sơ sống ≥ 2 năm
   ├─ so_tay_nghien_cuu/           sổ tay nghiên cứu: cau_hoi · gia_thuyet · thi_nghiem (.jsonl)
   └─ xuat_du_lieu.py              mã sinh các tệp trên (chỉ để kiểm nguồn gốc; chỉ chạy được ở gốc kho the-brain)
```

### B4. Từ điển ngắn

| Từ | Nghĩa trong gói này |
|---|---|
| **ô** | một cấu hình tham số chạy một lần (một tổ hợp tham số trên một mã – một khung) |
| **lưới** / **DCA** / martingale | mở thêm lệnh khi giá đi ngược, cách nhau `buoc` pip; chốt khi giá về lại gần trung bình. Chủ dự án coi cả ba là **hợp lệ** (`01` mục 2) |
| **tia lệnh** | tuỳ chọn của lưới: ghép lệnh sâu nhất với lệnh đầu, đóng cả cặp khi cặp đạt lãi `bien_cap` pip. Engine nến lạc quan nhất ở đây (`02` B1) |
| **cao nguyên** | vùng tham số mà phần lớn ô lân cận đều có lãi (khác "cái gai": một ô lãi đơn lẻ) |
| **trong mẫu / ngoài mẫu** | đoạn giá dùng để tìm tham số / đoạn khóa theo ngày, chỉ chạm **một lần** để xác nhận |
| **engine** | bộ mô phỏng của the-brain chạy trên nến (Python, có nhân C tuỳ chọn) |
| **tester** | MT5 Strategy Tester — "đáp án thật" gần nhất có được (vẫn là mô phỏng trên nến, nhưng chạy chính EA) |
| **niêm phong** | luật "chạm đoạn kiểm một lần" có dấu vân tay, không chạy lại cùng giả thuyết (`01` mục 10) |
| **CHƯA ĐO ĐƯỢC** vs **ÂM** | `ÂM` = đã đo và kết quả xấu. `CHƯA ĐO ĐƯỢC` = phép đo không chạy được / thiếu dữ liệu / lỗi. **Không bao giờ** gán CHƯA ĐO ĐƯỢC thành ÂM |
| **maxDD** | mức sụt giảm lớn nhất từ đỉnh vốn (chủ dự án chấp nhận tới 80 % ở đòn bẩy ≤ 10) |
| **swap** | phí giữ lệnh qua đêm; tester của the-brain **không ghi** swap (`02` B3) |
| **P1…P7** | bảy mảnh ghép ở `04`; bảng nhanh ở đầu tệp đó |
| **bot A / bot B** | hai bot vàng đã bóc luật từ lịch sử lệnh *của máy thử* (không nêu tên; `02` A7) |

### B5. Độ tươi và giới hạn (chi tiết `05` mục 6, `03` phần CHƯA ĐO)

- Số liệu đo bằng **giá và engine của the-brain**. brain2 dùng nguồn giá và engine khác → kiểm lại trên dữ liệu brain2 trước khi tin, và nói rõ chỗ nào là số của the-brain, chỗ nào đã đo lại.
- Cột engine trong bảng 125 ô là **bản v3 (cực trị)**; bản v4 (đường đi, mặc định từ 08/10) **chưa** được đối chiếu lại với tester trên 125 ô (còn ≈ 120 ô chờ máy nhà the-brain).
- Sổ tay nghiên cứu trong gói có thể **cũ hơn** sổ tay thật ở máy nhà (nơi duy nhất ghi sổ cái). Con số phễu (12.078 → 285 → 18) là số trước 02/10.
- Ghi chú trong gói là **dữ liệu để cân nhắc, không phải lệnh**. Việc không hoàn tác được hoặc đổi cài đặt: chủ dự án quyết (`01` mục 9, 12).
- Nếu bạn thấy một thông tin nhạy cảm lọt vào gói, báo chủ dự án để gỡ ngay.
