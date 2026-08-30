# BANKER — KẾ HOẠCH TỰ HỌC (CFA + KINH TẾ MÁC-LÊNIN)

> Cập nhật: 2026-08-12 · Mục tiêu: nâng năng lực phân tích vĩ mô của vai Banker theo yêu cầu người dùng (tự học CFA Lv1-3 + kinh tế chính trị Mác-Lênin), rồi áp dụng vào chuỗi Thế giới → Việt Nam → Hải Phòng.

## 1. LỘ TRÌNH CFA (Chartered Financial Analyst)
Nguồn: tài liệu CFA do người dùng cung cấp + tóm tắt chuẩn CFA Institute. Mỗi cấp gồm 3 giai đoạn: **đọc → hiểu khái niệm → vận dụng vào dữ liệu thật (FRED/VIX/COT)**.

### Cấp I (nền tảng) — ưu tiên ngay
- **Đạo đức nghề nghiệp (Ethics)** — chuẩn mực/ứng xử.
- **Kinh tế** (Economics): cung-cầu, chu kỳ kinh tế, chính sách tiền tệ/tài khóa, tỷ giá hối đoái, lạm phát — **đây là phần dùng nhiều nhất cho Banker**.
- **Phân tích tài chính doanh nghiệp** + **Thống kê** (xác suất, hồi quy, phân phối).
- **Thị trường vốn, chứng khoán, tài sản cố định, phái sinh, quản lý danh mục**.
- **Liên hệ thực tế**: mỗi chương xong → đối chiếu 1 seri FRED (DGS10, DFF, DTWEXBGS, VIXCLS) để "thấy" khái niệm trong số liệu.

### Cấp II (phân tích định lượng + tài sản)
- **Quản lý danh mục nâng cao**, **mô hình định giá tài sản** (CAPM, APT, factor), **phân tích thu nhập cố định & phái sinh** (DV01, duration, option Greeks).
- **Phân tích tài chính chi tiết** (3 báo cáo tài chính, evaluation).
- **Vận dụng**: dùng factor model để nhận diện regime risk_on/risk_off (đã có trong `phan_tich_che_do`), đọc COT/định giá.

### Cấp III (quản lý danh mục & tạo lập tài sản)
- **Quản lý danh mục tổ chức**, **GIPS**, **phân bổ tài sản cá nhân**, xây dựng IPS.
- **Vận dụng**: đề xuất phân bổ tài sản theo regime (risk_on → cổ phiếu/commodity; risk_off → trái phiếu/USD).

## 2. KINH TẾ CHÍNH TRỊ MÁC-LÊNIN
Giáo trình gồm: **kinh tế chính trị Mác-Lênin** (hàng hóa - giá trị, quy luật giá trị, tư bản & giá trị thặng dư, tích lũy tư bản, khủng hoảng), **học thuyết kinh tế của V.I. Lênin** (chủ nghĩa tư bản độc quyền, đế quốc chủ nghĩa).
- **Vì sao hữu ích cho Banker**: khung phân tích **chu kỳ khủng hoảng** (quá tích lũy, nợ, bong bóng tài sản) — giúp nhận diện đỉnh/đáy vĩ mô dài hạn, bổ sung cho khung CFA (định lượng, ngắn hạn hơn).
- **Chuỗi áp dụng**: hiểu cấu trúc sản xuất & dòng chảy tư bản → giải thích vì sao VN/hải Phòng hưởng lợi từ dịch chuyển chuỗi cung ứng (FDI) → đối chiếu vĩ mô VN.

## 3. CHUỖI PHÂN TÍCH CỦA BANKER
1. **Thế giới** (FRED: DGS10, DFF, DTWEXBGS, VIXCLS + COT S&P) → nền tảng risk on/off.
2. **Việt Nam** (FRED: DEXVNUS tỷ giá VND/USD — đã thêm vào `banker.py`; bổ sung sau: GDP, CPI, FDI, lãi suất SBV) → định hướng đồng nội tệ, tăng trưởng.
3. **Hải Phòng** (cảng biển, FDI khu công nghiệp, bất động sản công nghiệp) → động lực khu vực người dùng sống; nguồn: báo cáo vùng/kinh tế địa phương.

## 4. TRẠNG THÁI HIỆN TẠI
- [x] FRED + COT thế giới đã chạy (`reports/banker_brief.md`).
- [x] Thêm seri VN (DEXVNUS) vào `banker.py` — **đang bị chặn mạng khi fetch FRED DEXVNUS** (code sẵn, chạy lại khi mạng thông).
- [ ] Lấy bộ dữ liệu GDP/CPI/FDI VN + lãi suất SBV (bước sau).
- [ ] Dựng module đọc báo cáo kinh tế Hải Phòng.
---
*Xem thêm: `reports/BANKER_vn_macro.md` (phân tích Thế giới → VN → Hải Phòng), `reports/banker_brief.md` (brief vĩ mô chạy thật).*
