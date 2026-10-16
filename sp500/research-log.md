# Research log — kết quả chi tiết SP500

## Khung backtest (May–Jun 2026)
- Framework module hóa: `magnetic_common.py`, `magnetic_tier1/2/3.py`, `Portfolio_Optimizer.py`; 400,000+ tổ hợp tham số, mean reversion (S1/S2) và breakout (S4/S6), M15 2019–2026 (34,857 bar); 18 worker trên máy 19 nhân; output gộp một workbook mỗi lần.
- Kiến trúc nền: hệ xoay quanh các mức giá chính (ONH/ONL, PDH/PDL, PWH/PWL, PMH/PML, Pivot S1–S3/R1–R3, Fibonacci, VWAP), kiểm bằng walk-forward + Bonferroni.
- Triết lý BUY-only trên chỉ số ("scalp trong ngày, kẹt thì giữ") dựa trên niềm tin uptrend dài hạn. Dùng thuật ngữ ICT/SMC (magnetic levels, liquidity sweeps, FVG, displacement) song song với định lượng thuần.
- Tài khoản cent (1 lot = $0.01/pt), bơm vốn thay cho hard SL khi crash.
- Spec US500Cash (Exness/XM): min volume 0.1 (không phải 0.01), step 0.1, contract size 1, tick 0.01, tick value 0.01 USD → lot 0.1 ≈ 10 cent/pt; swap buy qua đêm -1.17/ngày.
- Timing/session (May 2026): `mt5_candle_statistics.py` v2/v3/v4 — momentum theo từng phút (1,440 slot); cụm bullish mạnh nhất 16:28–16:51 UTC (đầu phiên Mỹ); phiên London (08–13h UTC) bearish nhất quán; heatmap theo giờ Việt Nam (UTC+7).
- ORB (May 2026): Setup 1 (momentum) thua cấu trúc vì MAE vượt SL trước khi mean-revert; Setup 2 (Judas swing/fade) tốt nhất ở E=15–20pt, TP=15pt; viết lại `orbsl_v2.py` với SL neo theo entry; combo mạnh E=45–50, TP=ORB, SL=10–18pt.
- ZigZag amplitude & forex DCA (May 2026): mở rộng `rangev6.py`; biến thể AUDCAD/AUDNZD; lưới DCA ATR-động AUDCAD (H4 khoảng cách median ~133 pip, TP ~67 pip); AUDCAD hợp mean reversion, EURAUD thì không.

## Tính cách SP500 (consolidated parquet, Jul 2026)
- Hurst 0.51–0.53 (gần random walk), OU fit THẤT BẠI (không mean-reversion), drift +12–16%/năm với 100% cửa sổ dương, down-move sắc hơn up-move → thiên hướng long-only có cơ sở thống kê thật; lưới đối xứng/short thì không.
- Biên độ sóng: H4 leg k=1.5 median ~49pt, p70 ~76pt, p90 ~137pt; retrace H4 median ~120–133% leg → cơ sở cho DCA spacing (~p60–70 = 60–76pt) và TP (~median 37–49pt).
- Leg ZigZag (265,343 legs): up-leg lớn và dài hơn down-leg ở H4/H1 (H4: up 39.0pt/16h vs down 35.6pt/12h); retrace median 96–99% leg trước → không nên add-to-losers vô hạn. H4 thực dụng: DCA ~55–60pt, TP ~39pt (1.2×ATR), một đợt đẩy ~2 ngày giao dịch.
- Bảng crash lịch sử (12 sự kiện): tệ nhất -56% (2008), -49% (2000), -34% COVID 2020 trong 35 ngày, -25% 2022, -18.9% 2025 — là bài test sinh tồn thật cho mọi DCA/grid.
- Chu kỳ 56.5 năm daily: 12 crash ≥ -15% (đều hồi phục), tệ nhất -56.8% (đỉnh 2007-10), hồi phục dài nhất 2,114 ngày (~5.8 năm), drift +8.10%/năm; crash -15% xảy ra khoảng 4.7 năm một lần.

## AUDIT 2026-07-14 — 3 bug, mỗi bug đổi số
**Kết quả cũ SAI (giữ làm lịch sử, không dùng):** xếp hạng "464 magnetic survivor wr_test 91–98%" là do TIMEOUT BIAS.
1. TIMEOUT BIAS (`magnetic_backtest.py`, `pipeline.py`, `time_stats.py`): lệnh không chạm TP/SL trong max_hold bị LOẠI khỏi mẫu (`trade_count += resolved`). 44.7% lệnh bị bỏ → winrate phồng ~97%. Sửa: timeout đóng ở giá thị trường, R = actual_pnl/sl. Patch `apply_patch_timeout.py` (5/5 test).
2. TEST THỐNG KÊ SAI: binomtest(winrate vs breakeven) giả định Bernoulli (+tp/-sl); sau fix 1 giả định vỡ. Chuyển sang one-sample t-test avg_R > 0 (giống `stage2_toiuu.py`).
3. KHÔNG CÓ SÀN REWARD:RISK (`pipeline.py`): sau fix 1 ra 2,090 survivor nhưng 2,081 là MARTINGALE NGỤY TRANG (tp=0.1×ATR, sl=4.0×ATR → rr=0.025, WR 100% trên 15–20 lệnh). Bonferroni không bắt được (breakeven WR 97.6%). Patch `apply_patch_martingale.py`: MIN_RR=0.2, MIN_N_PHASE=50, MIN_EDGE_MULT=3× spread.
- PLACEBO thành tầng 3 bắt buộc (`placebo_test.py`). Ví dụ thật: Pivot_H1_S1/support qua Bonferroni cả 3 pha, n=2,731, avg_R=+0.0685 — nhưng entry NGẪU NHIÊN được +0.0584 (percentile 83–92%): chỉ cưỡi drift. Không test thống kê nào bắt được, chỉ placebo.
- Pipeline 3 tầng: SP500 2,090 → 9 → 5.

## KẾT QUẢ CUỐI SP500 (2026-07-14, ~2.3M giả thuyết)
**(1) Edge sống sót:** Pivot_H1_S1 / breakout_up / E=+0.3 / SL=4.0×ATR / TP 1.0–1.4×ATR (5 combo).
- n_test 233–235, winrate 81.5–86%, placebo percentile 100.0% ở cả 5 mức TP (nhất quán hoàn hảo = dấu hiệu hiệu ứng thật).
- avgR +0.094 đến +0.113, ~50% là drift (random entry +0.046–0.060) → edge THẬT ≈ +0.048–0.053R ≈ 8–10 pt/lệnh ròng sau spread 1.5pt.
- Era-check M30 (8.5 năm) + M15 (4.2 năm): 9/9 ổn định, xu hướng dương (+0.012 đến +0.017), sống sót COVID 2020 và bear 2022. Kỳ vọng ~+0.10R/lệnh trên M5 ≈ 18–19 pt ròng.
- Cơ chế: E=+0.3 nghĩa là CHỜ giá phá LÊN trên S1 rồi mới mua (xác nhận momentum), KHÔNG mua dip tại mức.
- BỊ LOẠI: toàn bộ phía `support` (E=0.0, buy-on-touch): placebo 83.5/91.5/98.0/96.5 = nhiễu. Mua mức đang rơi không có edge; chờ bounce thì có.
**(2) Mùa vụ 56 năm daily:** 15 CHẶT + 11 VỪA (Q4, TurnOfMonth, Nov–Apr, Santa, DOW_Tue, DOW_Wed, WeekOfMonth_1). Dùng làm BIAS hướng, không phải entry độc lập.

**BỊ LOẠI sau audit:** Multi-Indicator (320 combo, 0 qua FDR; cấu trúc TP/SL lành mạnh rr 0.67–2.0 → chứng tỏ khi cấu trúc đúng thì thống kê chặt trả về 0 chính xác); DCA/stage2 (6 "survivor" là martingale + tăng lot: tp=20.43/sl=150 → rr=0.14, WR 96%, max_lot 11.5, basket tệ nhất -1,610pt; `stage2_toiuu.py` khi đó chưa có MIN_RR); intraday_tpsl (0 ứng viên, M5 chỉ 17 tháng → n=67 < 100); Daily_IBS (chết từ thập niên 2020); Asia_open (martingale, rr 0.025–0.083, n=22); ONL-DCA (rỗng).
- Daily_IBS chết: avg_R +0.44 (1980s), +0.83 (1990s), +1.02 (2000s), +0.40 (2010s), rồi -0.58 (2020s, p=0.999). IBS ăn qua GAP qua đêm của thị trường cash; CFD 24/5 giết cơ chế đó.
- Bài học: trend_spearman KHÔNG phải bằng chứng edge. Asia_open/resistance có rho 0.75–0.88 ổn định 3 pha nhưng là martingale thuần. E lớn → vào lệnh hiếm → dễ ra WR 100% giả → trend đẹp là TRIỆU CHỨNG của bug.
- Era-check cần khung DÀI: M5 tối đa 100k bar = 17 tháng → chia 4 "era" thành 4 mảnh cùng một chế độ. Pivot_H1 KHÔNG chạy trên H1 (1 bar/period → mọi entry bị từ chối). Dùng M30 hoặc M15 (`era_check_longtf.py`).

## ZigZag V-Reversion (2026-07-15) — edge thứ hai, tần suất thấp
- Logic: sau một leg ZigZag ≥ thresh điểm trên H1 (phát hiện real-time, không look-ahead) VÀ thị trường đang chạy nhanh (|momentum 20 bar| ≥ 3%), vào NGƯỢC chiều (mean-reversion), DCA mỗi gap điểm, tối đa 3 layer, hard SL 300pt.
- Bộ lọc momentum là chìa khóa: mom≥0% +36pt/basket; ≥3% +52pt WR97%; ≥5% +76pt WR100% (đơn điệu = thật). Placebo 99–100%. Walk-forward 3/3 dương sau khi thêm lọc momentum.
- Điểm yếu đã giải: không lọc momentum thì thua ở bear gặm nhấm chậm (Bear 2022: -235pt) nhưng thắng ở V-crash nhanh (COVID 2020: +1026pt). Lọc momentum đổi Bear2022 từ -235 sang +235. Lọc MA200 tệ hơn (cắt mất edge).
- Phát hiện: (a) LONG bắt đáy >> SHORT bán đỉnh (+45 vs +13 chưa lọc, nhờ drift); (b) "gồng chờ về" là cách thoát TỆ NHẤT (+22pt, tệ nhất -670pt) — cắt SL luôn thắng; (c) DCA khoảng cách tăng dần (1.5×/layer) nhỉnh hơn khoảng cách đều.
- Cảnh báo overfit: cấu hình tốt nhất (thresh90/gap150) chỉ 34 basket/15 năm (~2/năm), mỗi pha walk-forward 11–12 lệnh, WR100% trên 11 lệnh không có ý nghĩa. Tin cấu hình tần suất cao hơn: thresh60/gap60/mom≥3% = 77 basket, +30pt, WR97%, tệ nhất -314pt. Đây là bổ sung tần suất thấp (2–8 lệnh/năm), không phải chiến lược chính; cơ chế ngược với Pivot breakout nên có đa dạng hóa thật.
- Grid đầy đủ (`zz_grid_search.py`, 161,280 combo, Bonferroni + walk-forward 3/3) rồi `zz_variants.py`: tối ưu thật là mom_thresh=1.0% (không phải 2–3%), zz=40 (không phải 60), TP=80 (không phải 45) → lợi nhuận tổng ~2.2×. Cấu hình chọn: mom_period=10, mom_thresh=1.0%, zz=40, gap=80, ml=3, tp=80, sl=300.
- SỰ THẬT từ placebo: LONG-ONLY KHÔNG thắng random entry (placebo 68–92%). "+55pt/lệnh, +7171pt tổng" của LONG là DRIFT-HARVESTING: random BUY + DCA + TP rộng cũng có lãi vì SP500 trôi lên. Tín hiệu ZigZag chỉ thêm giá trị thật khi giao dịch CẢ HAI hướng (placebo 100%) vì random SHORT lỗ.
- Xếp hạng biến thể (tối đa 3 layer): (1) "tia lệnh" (scale-out, mỗi layer TP riêng) hai chiều: placebo 100%, +36.4pt, tệ nhất -968pt; (2) pool (đóng cả basket ở TP trung bình) hai chiều: placebo 98%, +35pt. BỊ LOẠI: DCA tăng lot (tệ nhất -2342pt, gấp đôi rủi ro, TB giảm còn +22pt); trailing stop (placebo 83%, chỉ +12pt). Rủi ro thật tính theo lot: -968 đến -1022pt.
- Era-check LONG 4 giai đoạn: +46/+71/+48/+66pt, xu hướng +3.7/giai đoạn. Crash: COVID +828pt (WR88%), Bear2022 +120pt (WR80%, yếu), 2025 +404pt (WR83%). Giả thuyết "SHORT là tín hiệu ngừng mua" BỊ BÁC (LONG mở ngay sau SHORT còn tốt hơn: +73 vs +53pt).
- Test quan trọng nhất kế tiếp: chạy trên UK100 (drift gần 0). Nếu ZZ-V vẫn lãi thì tín hiệu ZigZag thật; nếu sụp thì edge LONG chỉ là drift SP500. Scripts: `zz_strategy_research.py`, `zz_grid_search.py`, `zz_final_validate.py`, `zz_variants.py`.

## Mùa vụ & chu kỳ tổng thống
- Chu kỳ tổng thống (56 năm, tự tính): Pre-election +16.87% (WR 85.7%, p<0.001, mạnh nhất), Post-election +11.34% (p=0.03), Election +8.71% (p=0.07), Midterm +1.34% (p=0.77, yếu nhất). 2026 là năm Midterm; 2027 là Pre-election.
- Mùa vụ chi tiết: Q4 +4.11% CHẶT (quý mạnh nhất), Q3 +0.34% yếu nhất; tháng mạnh Nov +1.74%/Dec/Jan/Apr (VỪA), Sep -0.78% (tháng âm duy nhất); DOW Tue+Wed mạnh nhất (VỪA), thứ Hai phẳng; hiệu ứng lịch CHẶT: Santa +0.166%/ngày, Pre-holiday +0.133%, TurnOfMonth +0.075%, WeekOfMonth_1 +0.062%, Nov–Apr +0.053%.
- "GOLDEN WINDOW": mùa vụ quyết định KHI NÀO (Tue/Wed + Week1 hoặc TurnOfMonth + Nov–Jan hoặc Apr + gần Santa/holiday), Pivot_H1_S1 breakout quyết định ENTRY (giá phá trên S1+0.3ATR), ZigZag quyết định TP (~median H4 = 39pt/1.2ATR, ~2 ngày). Vùng đỏ: Sep/Q3/thứ Hai/midterm 2026. Đã xuất 4 docx: SP500_BaoCao_TongKet, _MuaVu, _BoSung, _TongHop.

## Multi-Indicator (xem lại 2026-07-14)
- Không phải rác (khác Magnetic/DCA martingale): cấu trúc lành mạnh (rr 0.67–2.0) nhưng không combo nào qua FDR (tốt nhất p_BH_adj=0.18). Mọi top combo là biến thể Donchian_breakout[20] trên H4 + bộ lọc xu hướng. Tốt nhất: EMA_cross[9,21]+Donchian[20] Sharpe 0.985, CAGR +9.1%, MaxDD -14%, WR 60%, n=320. Hướng tiếp: thu hẹp về họ Donchian để giảm số test.

## Vốn & sinh tồn
- Edge magnetic mạnh nhất có MAE tới 500pt = -17% tài khoản 300 USD cho MỘT lệnh ở lot 0.1 → 300 USD quá mỏng.
- Bảng sinh tồn (`us500_bang_sinh_ton.xlsx`: Gia_dinh / 3_kich_ban / Crash_lich_su; giá SP500 ~7579; spacing 65pt, TP 45pt, 5 layer, equity stop 15%): KB1 300$/lot0.1 chỉ chịu 5.1% giảm + MAE ăn 18% tài khoản trong một lệnh = chết ở nhịp chỉnh thường; KB2 1200$/lot0.1 chịu ~23% (qua 2022), MAE 4.6% = mức tối thiểu dùng được; KB3 300$/lot0.01 (cần us500m) chịu 59% qua COVID, MAE 1.8% nhưng lợi nhuận cũng /10. Kết luận: nạp ~1200$ giữ lot 0.1, HOẶC giữ 300$ chuyển us500m lot 0.01; 300$+lot0.1 bị toán học loại.
- Thiết kế bot đã thống nhất: thiên LONG, mùa vụ quyết định KHI NÀO vào, DCA swing H4 lot phẳng lo CÁCH quản lý, bắt buộc hard equity stop trên equity thả nổi; ONL entry tạm gác (chưa có bằng chứng). us500m mới có OHLC thô (9,226 dòng), chưa có bảng phân tích.
- Walk-forward từng xác định 16 setup Tier A/B, thu về 3 setup xác nhận thật (khung cũ: ONL S2 BUY WR 94.9% ratio 368; ONH S2 SELL ratio 230 — CẦN KIỂM LẠI sau audit 2026-07-14).
