# Overview — SP500 / CFD index quant research

## Mục tiêu & phạm vi
- Xây framework nghiên cứu định lượng chặt chẽ cho CFD chỉ số: tìm và kiểm chứng live các edge cơ học, không phải hệ discretionary.
- Trọng tâm: SP500/US500M qua MT5/Exness; mở rộng dự kiến UK100, DE40, CA60.
- Giao dịch LONG-only trên chỉ số, discretionary có hệ thống hỗ trợ (không phải EA thuần cơ học).
- Nghiên cứu chạy qua đêm trên workstation (32GB RAM, 20 threads).
- GEX / dữ liệu option chỉ là bộ lọc xác nhận lớp trên chiến lược có sẵn, không trade option độc lập.

## Hạ tầng (tại thời điểm ghi chú)
- Claude Code (Windows, bypass permissions), thư mục làm việc "Research SP500", file CLAUDE.md chứa toàn bộ luật dự án.
- Quy trình: Claude Code chạy đêm → xuất báo cáo → gửi sang chat để review chiến lược và lên kế hoạch tiếp.
- MT5 không tự mở khi chạy Python: phải mở thủ công và thấy "Connected" trước khi lấy data.

## Framework Python
- `data_pipeline.py` — lấy Yahoo/Stooq/MT5 vào parquet, VIX từ mirror CBOE GitHub, `copy_rates_range()` theo chunk cho full history.
- `time_stats.py` — 7 task: cycles, seasonality, time_level_matrix, intraday_raw, intraday_tpsl, era_check, report (.docx).
- `magnetic_backtest.py` + `pipeline.py` — 88+ magnetic level, lưới E/TP/SL, mean-reversion và breakout/continuation, Bonferroni nhóm theo tần suất tín hiệu, era stability, walk-forward.
- Khác: `multi_indicator_pipeline.py` (~1,700+ dòng, 6 stage A–F), `zz_toolkit.py`, `rithmic_tickstore_backfill.py`.
- 6 file master prompt (01–06): ZigZag, magnetic levels, time edge, indicator combos, intermarket correlations.

## EA MQL5
- Setup A — Pivot Breakout H1 (magic 500001): FAIL MT5 live. Edge thô ~+1.62 pt/trade, spread Exness thực ~6 pt → lỗ cấu trúc ~-4.38 pt/trade (vấn đề chi phí, không phải bug).
- Setup B — Pullback-in-uptrend H4, Ichimoku Tenkan>Kijun + RSI<40 (magic 500002): mẫu MT5 quá ít (20 lệnh); edge mỏng (~+0.177R sau chi phí).
- Setup C — D1 Continuation (magic 500003): chưa đánh giá trên MT5.

## Phát hiện đã xác nhận (trạng thái lúc ghi)
- Drift dài hạn SP500: +6.34%/năm CAGR; 16 lần crash ≥15% đều hồi phục (số liệu khác nhau theo kỳ dữ liệu; xem research-log cho 56 năm: 12 crash, +8.10%/năm).
- Chỉ D1 và H4 có edge thật; M1–H1 âm/gần 0 sau spread.
- EMA_ATRfilt(50×200) có Sharpe OOS walk-forward cao nhất (0.960); EMA(10,26) là 0.904.
- Edge lịch (CHẶT/Bonferroni): tháng 12, Turn-of-Month, Pre-holiday, Santa Claus Rally, NFP, Pre-election year. September Effect ở mức VỪA (FDR).
- Magnetic Tier S (bản cũ, CÓ THỂ SAI do timeout bias — xem audit 2026-07-14): Pivot/Fib H1 false-breakout reversal, 412 combo, WR 84–87%.
- ZZ-V: LONG-only là drift-harvesting (placebo 68–92%). Config tối ưu mom=10, mom_thresh=1%, zz=40, gap=80, ml=3, tp=80, sl=300. Ngưỡng ZZ cố định theo điểm không hợp lệ qua 15 năm — cần chuẩn hóa ATR.
- ONL DCA: 457 basket 2019–2025, 88.8% đóng ở L1; ca xấu nhất (COVID/tariff) ~-1,251 pt mỗi layer × 3 layer.

## Việc sắp tới
1. Sửa ngưỡng ZigZag chuẩn hóa ATR (ưu tiên #1).
2. Mở rộng UK100, DE40, CA60 từng tài sản một (không chạy batch); dùng chế độ ATR-only cho lưới magnetic ở tài sản ngoài SP500.
3. Rithmic cho order flow (CVD, Footprint, Volume Profile, Big Trades); Tier 2 (GEX, options walls) chỉ forward-log vì không backtest được lịch sử.
4. Hoàn thiện `orderflow_backtest.py` khi có tài khoản Rithmic.

## Công cụ & nguồn dữ liệu
- Broker/execution: MT5 qua Exness (US500M, tài khoản cent); XM cũng được nhắc.
- Data: MT5 (2019–nay), Yahoo/Shiller (98+ năm daily), CBOE GitHub mirror (VIX), Stooq; Rithmic (dự kiến).
- Dev: Python, MQL5, Pine Script v3, Claude Code. Output: parquet, .docx, .mq5, .md.
