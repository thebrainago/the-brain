# Nguồn: EA31337 (robot MT4/MT5 mã nguồn mở), đọc ngày 17/10/2026

- **Nguồn:** https://github.com/EA31337/EA31337 (GPL-3.0). Bản đọc: commit 9b9bd38 (20/09/2024), kèm `EA31337-strategies` 3da76f4, `EA31337-strategies-meta` 3ddd3ea và `EA31337-classes` 35a2814.
- **Đọc gì:** toàn bộ 69 chiến lược vào lệnh, 42 meta-strategy và lớp điều khiển (chế độ, task, bộ lọc, stop, lot). Chỉ đọc, không chạy.
- **Chi tiết từng cái:** `reports/SEEKER_EA31337.json`, gồm luật mua/bán, stop, tham số mặc định và lỗi tìm thấy. Repo **không chứa** mã của EA31337, chỉ có tóm tắt và URL.

**Một câu:** EA31337 mạnh ở **ghép và chuyển chiến lược theo hoàn cảnh** (phiên, thứ, spread, biến động, trạng thái vốn, xu hướng D1) và ở **quản lí theo vốn cả tài khoản**. Phần **xử lí lệnh yếu**: DCA lot đều không trần, trailing thực tế không chạy, không có gỡ lệnh, không có chốt cả rổ. Repo không công bố kết quả backtest; tham số mặc định được tối ưu cho EURUSD. Code có nhiều lỗi (ghi trong JSON).

## 1. Đáng gom về kho: cái kho mình CHƯA có hoặc rất ít

| Mảng | Cơ chế | Kho mình có |
|---|---|---|
| **Ghép/chuyển chiến lược** | Chọn chiến lược theo **spread** (<1 / 1–2 / 2–4 / ≥4 pip) | không |
| | Chọn theo **biến động** (ATR H8 tăng thì Awesome, giảm thì Bands; RSI của tick volume) | không |
| | Chọn theo **trạng thái vốn** (lãi thả nổi ±5 / ±10 %; quá ±10 % thì ngừng vào mới) | không |
| | Chọn theo **margin còn trống** (80 / 50 / 20 %; dưới 20 % thì không vào) | không |
| | Chọn theo **lãi đã chốt trong ngày** (dưới hoặc trên 1 %) | không |
| | **Một chiến lược mỗi thứ trong tuần** · **một chiến lược mỗi phiên** (London / NY / Sydney / Tokyo) · giờ chẵn/lẻ | rất ít (`ngay_trong_tuan` 22) |
| | **Vị trí so với D1**: trong/ngoài Bollinger D1 (24, 1,0) · vùng Camarilla S1–R1 / S2–R2 / S3–R3 · SAR D1 vừa đảo 1/2/3 nến · nến D1 và W1 cùng hay khác màu | Camarilla 2 · SAR 2 |
| | **Double** (hai chiến lược cùng đồng ý) · **Trio** (một chiến lược để vào, một để thoát, một để đặt SL/TP) · **Mirror** (bất kì chiến lược nào báo) | không |
| | **Đảo tín hiệu** (Reversal) | có (`__dao`) |
| **Lọc vào lệnh** | Cùng xu hướng D1 (RSI16 D1 ≥ 50 hai nến) · giá vượt pivot nến trước · phá đỉnh/đáy nến trước · không có lệnh tốt giá hơn đang mở · vốn ≥ 99 % số dư | lọc D1 rất ít (2) |
| **Vào lệnh** | Dải **TMA** (TMA_True, TMA_CG) · **SVE Bollinger** · TMAT_SVEBB (SVE dưới dải dưới và râu chạm TMA) | không |
| | Retracement (Ichimoku sát hỗ trợ sau nến D1 tăng) · ZigZag phá swing · Pinbar + RSI/CCI | ít |
| **Xử lí lệnh** | **Hedge theo cân bằng lot**: chỉ cho mở lệnh nào làm cân lại tổng lot mua/bán | không |
| | **Thang lệnh chờ hai phía** (Formation): limit cách 5 % và 10 % biên độ 2 ngày, dời theo giá mỗi phút | lưới có, kiểu này không |
| | **Kèm lệnh limit tốt giá hơn 50 point** mỗi khi vào lệnh thị trường (Order_Limit) | không |
| | **Nhồi một lần** sau khi cả một nến chạy ngược (Enhance) | không |
| | DCA lưới 20 pip, lot đều, không trần (Martingale / Oscillator_Martingale) | có |
| **Quản lí tài khoản** | Task: **vốn lãi ≥ +5 % thì đóng hết** · **lỗ ≤ −5 % thì đóng lệnh lỗ nhất** · **lỗ ≤ −2 % thì đóng lệnh LÃI nhất** · đóng các lệnh đang lãi · đóng phía thua / phía thắng | không |
| | Mỗi khung (M15…H12) chạy một chiến lược riêng trên cùng tài khoản | ý tưởng ghép có, chưa thành cơ chế |
| | Một **chiến lược stop chung** cho mọi lệnh (Envelopes H8) | không |

## 2. Không đáng gom (hoặc chỉ làm mốc)

- 40-ish chiến lược một chỉ báo (AC, AD, MFI, RSI, WPR, Stochastic, DeMarker…): kho đã có hàng nghìn biến thể cùng loại.
- Trailing và hoà vốn: code có, nhưng điều kiện khoá làm nó **không bao giờ chạy**.
- Lot tự động khoảng 0,01 lot / 10.000 USD; không quản lí rủi ro theo %.

## 3. Cách dùng cho The Brain

1. Nhóm **ghép/chuyển chiến lược** và **task theo vốn** là thứ mới nhất. Chúng là "não điều phối" giữa các mảnh mình đã có (MRZ, RSI, IBS, song mốc…). Đây đúng là phần ghép hệ anh muốn.
2. Nhóm **xử lí lệnh** chỉ thêm được 4 ý nhỏ (hedge cân lot, thang limit hai phía, kèm limit tốt giá, nhồi một lần). Phần DCA/gỡ/rổ vẫn phải gom từ nguồn khác: EA lưới và DCA trên MQL5, tài khoản tín hiệu DCA sống lâu.
3. Bước tiếp theo khi anh muốn: chuyển các mục ở bảng 1 thành khai báo trong kho (`config/co_che_dsl.json` cho vào lệnh/lọc, `config/quan_tri_dsl.json` cho xử lí lệnh), giữ URL nguồn.
