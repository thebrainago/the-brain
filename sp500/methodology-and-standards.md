# Methodology & standards

## Chuẩn PASS chiến lược
- Sau ~3 tháng nghiên cứu SP500: **MT5 là trọng tài live; Python chỉ là sàng lọc sơ bộ.**
- Mọi backtest Python phải gồm chi phí thực ngay từ đầu: spread Exness thực (US500M ~5–8 pt), slippage, swap qua đêm.
- Loại ngay: tần suất < 2 lệnh/tuần; lợi nhuận TB < 5 pt/lệnh sau chi phí; R:R kém / TP quá ngắn so với SL.
- Chỉ chiến lược qua Python (placebo/robustness + full cost) mới code thành EA MT5.
- Chỉ tính PASS khi EA sống sót MT5 single-run live.
- **Cấm vĩnh viễn tối ưu hóa trên MT5** (curve-fitting).

## Thống kê (3 mức)
- CHẶT: Bonferroni. VỪA: FDR-BH 10%. Dưới VỪA: chưa đủ bằng chứng.
- Mọi chiến lược cần Bonferroni/FDR + walk-forward 3 pha theo thời gian trước khi forward-test MT5.
- Chỉ Bonferroni là quá chặt cho dữ liệu thị trường: Bonferroni nhóm theo tần suất tín hiệu + tầng giữa FDR-BH là cách đã kiểm chứng.

## Pipeline 3 tầng bắt buộc (sau audit 2026-07-14)
1. STATISTICS: Bonferroni + walk-forward 3 pha.
2. ECONOMICS: rr ≥ 0.2, n ≥ 50/pha, edge ≥ 3× spread.
3. PLACEBO (`placebo_test.py`): giữ E/tp/sl/max_hold, thay entry bằng entry NGẪU NHIÊN, so với 200 mô phỏng; phải thắng random.
Bổ sung: era-check trên khung dài (M30 8.5 năm, M15 4.2 năm). SP500 đi từ 2,090 → 9 → 5 survivor qua các tầng.

## Nguyên tắc rút ra
- MT5 single-run là trọng tài cuối: spread/slippage/swap live thường giết edge trông ổn trên Python.
- Chi phí giết edge intraday trên CFD retail: spread 2 pt đã xóa edge thô +1.62 pt.
- Placebo là thiết yếu: momentum/drift LONG-only có thể "có edge" chỉ nhờ drift thị trường (placebo 68–92%); cần test hai chiều để xác nhận alpha thật.
- Sai số thang giá tuyệt đối làm hỏng phân tích 15 năm: ngưỡng cố định theo điểm (vd ZZ 40 pt) khác hẳn về % theo chế độ giá; luôn chuẩn hóa theo ATR hoặc %.
- Xung đột cơ chế: DCA (mean-reversion) ghép vào setup momentum/breakout là thảm họa (-17,000 pt).
- Sửa bug TRƯỚC khi chạy qua đêm; kiểm tra logic trên dữ liệu ngắn/tổng hợp trước.
- trend_spearman KHÔNG phải bằng chứng edge: xu hướng đẹp có thể là TRIỆU CHỨNG của bug martingale.

## Bug code đã bắt và sửa
- Look-ahead entry: phải dùng Open[i+1], không dùng Close[i].
- TP/SL tie-break trên cùng một bar.
- `worst_adverse` chỉ tính lúc close thay vì running minimum suốt thời gian giữ.
- Lỗi thang giá tuyệt đối: ngưỡng cố định không hợp lệ qua 15 năm → dùng ATR.
- Checkpoint propagation: `--force-rerun` âm thầm dùng lại kết quả cũ.
- Trùng entry trong `intraday_tpsl`.
- Regime strategy dùng Close-to-Close thay vì Open-to-Open.
- Bộ lọc chu kỳ bầu cử Mỹ áp nhầm cho tài sản ngoài Mỹ.
- `--mt5-adhoc` hardcode `yahoo=None`, chặn data dài hạn cho UK/DE/CA.
- (2026-07-14) Timeout bias; test thống kê sai (binomtest → t-test avg_R); thiếu sàn reward:risk (martingale ngụy trang) — chi tiết trong research-log.

## Cách làm việc
- Nghiên cứu chạy đêm trên workstation; báo cáo xuất ra được review trong chat.
- Ưu tiên kiến trúc một file hợp nhất thay vì nhiều script rời; multiprocessing, parquet, checkpoint/resume là chuẩn.
- Phân tích từng tài sản riêng sau khi kết quả gộp gây hiểu nhầm.
- Ý tưởng được test thực nghiệm và bị loại nếu dữ liệu bác bỏ; ưu tiên trung thực hơn kết quả đẹp.
- Viết tài liệu bàn giao (BAN_GIAO.md) cuối các phiên dài.
