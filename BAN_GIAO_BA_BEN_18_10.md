# Bàn giao ba bên: chủ dự án · Claude · Grok (tối 18/10/2026)

**Đọc theo thứ tự:** `CHI_THI_CHU_DU_AN.md` → `BO_TIEU_CHI_MOI.md` → file này → `reports/RA_SOAT_MODULE_18_10.md` → `tai_lieu/SEEKER_KHO_VAN_HANH.md`.

## 1. Mục tiêu không đổi

- **Chỉ có ba yếu tố cốt lõi:** lãi sau phí và các mức giãn; sụt giảm ≤ 80 %; lãi ≥ 10 %/năm. Lot co giãn được, nên câu hỏi thật là: **lãi/năm chia sụt giảm ≥ 10/80**. Mọi thứ khác (p-value, FDR, placebo, MDE, thắng mua-giữ, "hai nửa", số lệnh) chỉ là **nhãn**, không dùng để bỏ hệ.
- **Phong cách của chủ dự án:** không SL, TP nhỏ, DCA, giữ lệnh, gỡ lệnh, hedge, ghép hệ. Tài khoản Exness cent và XM micro.
- **Việc bây giờ là GOM:** cơ chế, tư duy, tín hiệu và nhất là **xử lí lệnh** từ các kho EA, chỉ báo và chiến lược vận hành được. EA cuối cùng là đích đến sau, chưa làm bây giờ.

## 2. Hôm nay đã làm (cả brain2 và the-brain)

1. **Seeker săn KHO** (`python tru/seeker.py san-kho | tai-kho | kiem-ke`): đọc ký hiệu mã trong cả file, lấy kho về `data/cau_kho/`, kiểm kê EA / chiến lược / chỉ báo / kĩ thuật xử lí lệnh. Đã đọc EA31337 (`reports/SEEKER_EA31337.md`).
2. **Rà soát chủ động bốn mảng** (cổng, gom nguồn, chi phí và mô phỏng, MT5). Kết quả từng lỗi ở `reports/RA_SOAT_MODULE_18_10.md`. Đã sửa nhóm lỗi nguy hiểm nhất:
   - **Kết quả đẹp hơn thật:** tài khoản cháy báo thắng; lệnh bán được cộng lãi ảo khoảng phương sai mỗi bar (≈ 3 %/năm trên chỉ số); SL bị gap khớp ở giá SL; spread giờ rollover không bao giờ bị tính; phí qua đêm tính cả lệnh trong ngày; bài stress "phí x2" không làm gì.
   - **Loại nhầm hệ có lãi:** sàng thô quantlab còn đòi thắng mua-giữ; hệ đảo chiều mua/bán bị coi là "mua-giữ trá hình"; trần kích hoạt 0,60 loại hệ xu hướng; spec chỉ có lưới/DCA bị bỏ; hệ đạt cốt lõi bị kẹt ở `UNG_VIEN`.
   - **MT5:** đòn bẩy bị tester bỏ qua (`Leverage=30` → 1:100); lần chạy hỏng bị đánh dấu "đã thử" vĩnh viễn; đọc báo cáo cũ và `.ex5` cũ như kết quả mới; log agent trỏ thư mục dữ liệu cũ.

**Hệ quả với số cũ:** mọi kết quả mô phỏng Python trước 18/10 có **lệnh bán**, **khớp lúc rollover** hoặc **giữ lệnh trong ngày** đều lệch. Số của lệnh bán bị thổi phồng; số khớp lúc rollover rẻ hơn thật. Danh sách `DANH_SACH_HE_DAT.md` lấy từ **sổ MT5** nên không dính lỗi mô phỏng Python. Sổ đó vẫn có hai hạn chế: tài khoản `#` của XM tắt swap, và pha IS không có tick thật (mục D4 trong báo cáo rà soát).

## 3. Chia việc

| Ai | Việc |
|---|---|
| **Máy nhà (MT5, dữ liệu thật)** | (a) `git pull` cả hai repo. (b) Đo lại spread theo giờ, có cả giờ 23 và 0, để làm mới `config/chi_phi_do.json` (`chi_phi.do_spread_tu_bar_mt5`). (c) Chạy lại các hệ trong `DANH_SACH_HE_DAT.md` trên sàn của anh: `python mt5tools/chay_lai_tren_san.py` (nay đặt đòn bẩy đúng). (d) `python tru/seeker.py san-kho --tai 5` với `GITHUB_TOKEN` trong biến môi trường. (e) Cài **Browser MCP** cho agent đọc trang sau Cloudflare: `may_nha\CAI_BROWSER_MCP.cmd` (`tai_lieu/BROWSER_MCP.md`). (f) Hàng chờ cũ: `tai_lieu/HANG_CHO_MAY_NHA.md` #37–#43, S14–S15 |
| **Grok** | (a) Đọc kho đã tải: passivbot (gỡ lệnh kẹt "auto unstuck"), hummingbot (DCA/grid executor), freqtrade-strategies và NostalgiaForInfinity (DCA bằng `adjust_trade_position`). Ghi tóm tắt kiểu `reports/SEEKER_EA31337.md`: luật vào, luật thoát, cách DCA / hedge / gỡ, tham số mặc định, lỗi. (b) Seeker quét nguồn tồn đọng: 271 repo GitHub và 69 kênh Telegram chưa đọc (C10) |
| **Claude** | Các lỗi CHỜ còn lại trong báo cáo rà soát, theo thứ tự: ATR nhìn trước (A8), `mo_phong_v2` gắn cứng EURCAD (A9), bảng symbol chung (A10, A11), `quan_tri.boc_kho` (C6), đọc GitHub bỏ chỉ báo (C7), mã hoá (C8), `ma_nguon` (C9), `noi_sinh` hai chiều (B9), `chon_ung_vien` (B8), khoá tester (D7) |
| **Cần chủ dự án quyết** | (1) **Pháp lý:** mã EA của người khác đang trong git công khai (báo cáo rà soát mục E). (2) **Thiết kế khối "quản trị" trong DSL** để thông tin xử lí lệnh vào được kho cơ chế (C5). (3) **Mô phỏng theo kiểu của anh trong `to_hop`:** không SL, DCA, giữ lệnh (B7). Hai việc (2) và (3) nên bàn cả ba bên tối nay |

## 4. Luật làm chung (giữ nguyên)

- Không đưa khoá, token, mật khẩu vào git (chỉ dùng biến môi trường). Không khôi phục các file đăng nhập Chrome đã gỡ.
- Mã của người khác chỉ để trong `data/` (git bỏ qua); repo giữ tóm tắt và URL. Không chạy mã tải về khi chưa đọc.
- Mọi thay đổi vào **cả hai repo** (brain2 và the-brain).
- Phân biệt `CHUA_DO_DUOC` với kết quả âm. Lần chạy hỏng không phải "đã thử, không lãi".
- MT5 tester là thẩm phán cuối. Chỉ một phiên được dùng tester tại một thời điểm.
