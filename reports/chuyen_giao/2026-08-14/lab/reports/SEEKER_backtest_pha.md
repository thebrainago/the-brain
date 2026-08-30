# SEEKER — Quyết định nền tảng BACKTEST (Đợt 1)

> Vai: SEEKER · Cập nhật: 2026-08-12
> Câu hỏi: "Đánh giá nhanh VÀ đảm bảo nhất nên dùng gì — MT5 Strategy Tester, TradingView, hay nền tảng khác (VectorBT/Backtrader/custom)?"
> Nguyên tắc dự án (THE_BRAIN): **Python sàng lọc nhanh TRƯỚC → MT5 tick CUỐI.** Không tin backtest Python trước khi qua MT5 tick.

---

## Kết luận ngắn
- **Đánh giá nhanh (scan nhiều cặp/khung):** Python (`VectorBT` nếu có sẵn, nếu không thì `Backtrader` hoặc `custom` pandas/vòng lặp). Chạy trên OHLCV, timeout ngắn, sàng hàng trăm → vài ý tưởng.
- **Đảm bảo CUỐI (chuẩn "truth"):** **MT5 Strategy Tester chế độ tick.** Nơi duy nhất trong 3 lựa chọn mô phỏng spread thật + fill thật + slippage + commission như tài khoản thật.
- **TradingView:** chỉ dùng để **prototype/đọc ý tưởng nhanh** (Pine Script) hoặc xác nhận trực quan. KHÔNG dùng làm trọng tài cuối (không tick thật, không kiểm soát fill/slippage, hộp cát đóng, khó scan tự động hàng loạt).
- **Pipeline 3 lớp:** `Python scan` → `MT5 tick` → (tùy chọn) `forward demo thật`. Mỗi lớp có ngưỡng riêng.

## Bảng so sánh

| Tiêu chí | MT5 Strategy Tester | TradingView | Python VectorBT | Backtrader | Custom (pandas) |
|---|---|---|---|---|---|
| **Tốc độ** | Trung bình–nhanh (tick chậm hơn bar, nhưng tối ưu MQL5) | Nhanh cho 1 ý tưởng, chậm khi tự động hoá nhiều | **Rất nhanh** (vectorized, khối lớn) | Trung bình (event-driven) | Nhanh nếu viết vectorized |
| **Độ chính xác tick** | **Cao nhất** (real tick / every tick / spread + fill + slippage) | Trung bình (dữ liệu bar, không tick thật, fill thô) | Thấp–trung bình (dựa OHLCV, giả định fill giá đóng) | Thấp–trung bình (cùng giả định bar) | Thấp–trung bình (bạn kiểm soát mức mô phỏng) |
| **Chi phí** | MT4/MT5 miễn phí (cần terminal + broker demo) | Bản free giới hạn; trả phí cho dữ liệu/tính năng | Miễn phí (thư viện) + chi phí dữ liệu | Miễn phí + chi phí dữ liệu | Miễn phí + chi phí dữ liệu |
| **Phù hợp scan nhiều cặp/khung** | Trung bình (chạy serial từng symbol; có optimizer) | Kém (thủ công/1 chart, khó batch) | **Rất tốt** (loop symbol×khung, song song) | Tốt (loop + song song) | Tốt (tự viết loop) |
| **Vai trò khuyến nghị** | **Xác minh CUỐI (truth)** | Prototype/ý tưởng nhanh | **Sàng lọc nhanh lớp 1** | Sàng lọc lớp 1 (thay thế VectorBT nếu chưa có) | Sàng lọc lớp 1 (kiểm soát tham số tối đa) |

## Khuyến nghị cụ thể cho dự án
1. **Lớp 1 — Sàng lọc nhanh (Python):**
   - Dùng **VectorBT** nếu đã có trong `sp500_env` (nhanh nhất cho scan nhiều cặp/khung). Nếu chưa có, dùng **Backtrader** hoặc **custom pandas** — vẫn đạt mục tiêu "sàng nhanh".
   - Chạy timeout ngắn, tái sử dụng nguồn thô (OHLCV), output: danh sách ý tưởng kèm PF/sharpe/drawdown.
   - **KHÔNG tin con số này làm kết luận — chỉ dùng để loại bớt.**
2. **Lớp 2 — Xác minh CUỐI (MT5 Strategy Tester):**
   - Export cơ chế + tham số đã sàng → **EA MQL5** (vai CODER) → chạy **chế độ "Every tick based on real ticks"**.
   - Chọn symbol + khung + spread thật, bật commission/slippage hợp lý.
   - Ngưỡng chốt: PF, drawdown, số lệnh, walk-forward / placebo / out-of-sample theo chuẩn chống overfit của dự án.
3. **Lớp 3 (tùy chọn):** demo forward vài tuần trước khi đưa live.
4. **TradingView:** dùng lúc brainstorming ý tưởng (Pine Script nhanh, xác nhận bằng mắt) — không phải trọng tài cuối.

## Tại sao KHÔNG chọn TradingView làm trọng tài cuối
- Không có dữ liệu tick thật; fill/slippage mô phỏng thô → kết quả dễ lạc quan (overfit kiểu "trong quá khứ").
- Hộp cát đóng, khó tự động hoá/batch scan nhiều cặp ở quy mô lớn.
- Thích hợp prototype nhanh hơn là bằng chứng xác minh cuối.

## Lý do MT5 là "ĐẢM BẢO nhất"
- Mô phỏng **spread thật + fill thật + slippage + commission** sát tài khoản thật.
- Chế độ **every tick** phát hiện "biên" (slippage, khoảng cách order) mà Python/bar không thấy.
- Đúng nguyên tắc dự án: "kết luận cuối luôn qua MT5 tester (Python chỉ sàng lọc sơ)".

## Ghi chú triển khai (đề xuất, chưa làm — ngoài phạm vi đợt này)
- Kiểm tra VectorBT có sẵn trong `sp500_env`; nếu chưa, dùng Backtrader/custom.
- Sớm xác minh cơ chế vàng "Daily Zone Gold TP=50" qua MT5 tick (theo `CAI_THIEN_BRAIN.md`) bằng EA phù hợp.
