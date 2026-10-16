# Hệ thống liên quan

## ONL DCA v2.0 (SP500, Jun 2026)
- L1 vào ở ONL (mặc định 40 cent lot); L2 DCA ở Pivot S1 chỉ khi S1 < ONL − 10pt; trailing stop +15pt, trail 8pt; ~94.9% win rate (backtest 2020–2026) — LƯU Ý: nhóm kết quả ONL/magnetic trước audit 2026-07-14 không đáng tin (xem research-log).
- Lot thích ứng: 20 cent (cảnh báo), 40 cent (bình thường), 60 cent (hậu crash).
- Quản lý crash dựa vào bơm vốn ngoài, không thiết kế khoảng cách DCA để chịu crash thảm họa; đã phân tích lot phẳng vs lot bậc thang.
- Mục tiêu ~$47/tháng trên tài khoản nền $300 (đã bị bảng sinh tồn cho là quá mỏng).

## Project Bien Do (SP500 + UK100)
- Pipeline nghiên cứu đa symbol: codebase Python 19+ file, output Parquet: biên độ sóng, mùa vụ, magnetic levels, đặc tính thị trường.
- Thách thức: tối ưu RAM/multiprocessing. Đã sửa: khoảng trống dữ liệu, nghẽn threading, OOM do nối Parquet lớn, lỗi ticker Yahoo.
- Edge đã ghi: bộ lọc mùa vụ (Halloween, Q4, Turn-of-Month, Santa), magnetic H1 Pivot/Fib (trước audit), DCA swing H4 lot phẳng (sau audit: RÚT LẠI).
- Hurst SP500 ~0.51–0.53 → gần random walk, không mean reversion, nhưng drift long-only mạnh.

## UK100 (FTSE 100) pipeline (Jun–Jul 2026)
- Dựng framework backtest UK100 theo mô hình SP500: ZigZag/biên độ, session/timing, DCA (ONL→PDL, WR 96.4%, PF 6.48), sizing cho tài khoản cent. ONL BUY là setup mạnh nhất (PF 2.29, WR 68.3%); VWAP bị loại (volume thật = 0 trên CFD); 2 layer vs 3 layer chưa chốt.
- Stress test: GFC 2008 (-47.8%), COVID (-35.8%).
- Mùa vụ/crash: UK100 hồi phục chậm hơn SP500; Halloween/Sell-in-May có cơ sở học thuật mạnh nhất cho UK; khủng hoảng GBP không gây crash cổ phiếu do ~75% doanh thu FTSE 100 ở nước ngoài.
- Phân tích UK100_Magnetic_v1.xlsx với lọc PF > 1.1, N ≥ 50, WR > 50% + walk-forward.
- **QUAN TRỌNG:** mọi kết quả UK100 trước 2026-07-14 KHÔNG ĐÁNG TIN (cùng mẫu martingale/timeout đã tạo 2,081 survivor SP500 giả; "WR 96.4% PF 6.48" chính là dấu hiệu đó). Bốn bản sửa nằm trong code dùng chung (`pipeline.py`, `magnetic_backtest.py`, `time_stats.py`, `stage2_toiuu.py`; cái cuối vá bằng `apply_patch_dca_martingale.py`: MIN_RR_DCA=0.2, MIN_N_DCA=100, MAX_LOT_DCA=3.0). Chạy lại UK100 phải qua đủ 3 tầng + `era_check_longtf.py` (M30/M15).
- UK100 là tài sản gần không drift: placebo càng quan trọng — edge mua thật không được giải thích bằng drift; nếu chỉ ngang random entry thì loại.
- Trước khi chạy: đặt `SPREAD_ATR_EST` trong `pipeline.py` và `--spread` trong `time_stats` theo spread thật của UK100 (ATR ~70pt, spread ~2pt → ~0.03), không dùng spread SP500.
- Gộp hàng trăm file parquet rời thành hai file consolidated.

## GEX scanner & macro dashboard (Jun 2026)
- `gex_scanner_v2.py`: VIX term structure, PCR từ chuỗi option SPX, điểm tín hiệu tổng hợp (0–100), dashboard checklist ONL BUY.
- Backtest bộ lọc GEX/flow làm overlay cho ONL (dùng VIX làm proxy GEX).
- Đã đánh giá nền tảng GEX của Việt Nam (app.turtletrading.vn/gex): lo ngại mẫu nhỏ và độ trễ.
- Dashboard dòng tiền ETF vĩ mô để xác nhận tín hiệu SP500 live.

## DongDongTV Session Trading V3 (EA bên thứ ba)
- Tự động hóa tối ưu MT5 Strategy Tester cho EA DCA/Martingale này; công cụ phân tích tham số hướng sinh tồn, lọc cứng theo drawdown thay vì tối đa hóa lợi nhuận.

## Sierra Chart + Rithmic (Jul 2026)
- Đánh giá Sierra Chart (Package 11) + Rithmic làm đường nâng cấp; quy trình thực tế: xuất data SC ra CSV rồi chạy backtest Python độc lập.
- Đã xét các phương án phơi nhiễm SP500 dài hạn có đòn bẩy (phí tài trợ CFD, rủi ro margin call futures, phân rã ETF đòn bẩy): kết luận không có giải pháp sạch cho đòn bẩy cao/không SL/giữ dài hạn.
