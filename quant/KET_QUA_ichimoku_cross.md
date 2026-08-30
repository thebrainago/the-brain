# KẾT QUẢ — GIẢ THUYẾT ICHIMOKU CROSS (QUANTLAB)

> Ngày chạy: 2026-08-12 · Dữ liệu Yahoo D1, 10 năm (2016-08 → 2026-08)
> Giả thuyết của người dùng: *"2 đường Ichimoku (Tenkan × Kijun) cắt nhau → vào lệnh ngay lập tức. Xem giữ lệnh bao lâu (số nến) hay bao nhiêu điểm (TP) là tốt nhất."*
> Script: `quant/tim_ichimoku_cross.py` · Kết quả JSON: `quant/ket_qua_ichimoku_cross.json`
> Đây là **sàng lọc Python cấp 1**, chưa qua MT5 tick. Khung intraday (phút/giờ) phải test bằng MT5 Strategy Tester.

---

## 1. CÁCH TEST
- Cơ chế: **Tenkan (9) cắt Kijun (26)** — golden cross → LONG, death cross → SHORT, vào lệnh ở **giá close của nến xác nhận** (không lookahead).
- 2 chế độ thoát lệnh:
  - **Hold**: giữ cố định N nến (1, 2, 3, 5, 8, 13, 21).
  - **TP**: thoát khi chạm mục tiêu `TP = k × ATR(14)` (k = 0.5, 1, 1.5, 2, 3), không có stop (để cô lập tác động của TP).
- Đã trừ **chi phí thật** (spread + swap, theo `quant/metrics.py`) và so sánh trực tiếp với **buy&hold cùng kỳ**.
- 3 tài sản: S&P500 (`^GSPC`), Vàng (`GC=F`), EUR/USD (`EURUSD=X`). Tổng 36 tổ hợp.

## 2. KẾT QUẢ CHÍNH (đã trừ chi phí)

| Xếp | Tài sản | Chế độ | Tham số | Số lệnh | Lãi TT | Lãi Buy&Hold | Sharpe | PF | MaxDD |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **EURUSD** | Hold | **3 nến** | 80 | **+21.9%** | +3.6% | 0.95 | 1.71 | n/a |
| 2 | EURUSD | Hold | 21 nến | 65 | +18.4% | +3.6% | 0.42 | 1.13 | n/a |
| 3 | EURUSD | Hold | 2 nến | 82 | +13.5% | +3.6% | 0.73 | 1.64 | n/a |
| 4 | EURUSD | Hold | 8 nến | 74 | +11.3% | +3.6% | 0.37 | 1.15 | n/a |
| 5 | EURUSD | Hold | 5 nến | 76 | +10.9% | +3.6% | 0.41 | 1.20 | n/a |
| 6 | EURUSD | Hold | 1 nến | 85 | +10.4% | +3.6% | 0.79 | 2.11 | n/a |

**Nhận định:**
- **Chỉ EURUSD có edge thật** so với buy&hold (lãi TT > BH ở mọi hold 1–21). Điểm ngọt nhất = **hold 3 nến D1** (21.9% vs 3.6%, Sharpe 0.95, PF 1.71).
- **Cơ chế thoát theo thời gian (hold) thắng cơ chế thoát theo TP (mục tiêu điểm)** trên EURUSD: mọi TP đều thua hoặc ~0 (TP 0.5 → −15.9%). → Với chiến lược cross này, **giữ lệnh theo thời gian tốt hơn chốt theo điểm**.
- Trên S&P500 và Vàng, cross **không có edge**: dù lãi dương (Vàng hold2 +48%, SP500 hold21 +78%) nhưng **thấp hơn hẳn buy&hold** (+234% / +254%) — vì 2 tài sản này có trend mạnh 1 chiều, đánh lật lắt làm mất trend. → **Không đề xuất** cho SP500/Vàng.

## 3. KẾT LUẬN & BƯỚC TIẾP
1. **Đề xuất đưa lên MT5**: Ichimoku Tenkan×Kijun cross, **EURUSD, giữ 3 nến D1** (≈3 ngày), không TP cố định. Vai CODER viết EA bằng `iIchimoku` (Tenkan/Kijun) + `iATR`.
2. **Bước sau (MT5 Strategy Tester, dữ liệu tick):**
   - Quét **khung intraday** (H1, H4, M15) — câu hỏi "khung nào phản ứng tốt nhất" của người dùng chỉ trả lời chính xác được ở đây.
   - Thử giữ lệnh theo **số phút/giờ** và theo **điểm (points)** với spread thật từng cặp.
   - Thêm **stop loss** (hiện chưa có) rồi đo lại MaxDD + Calmar.
3. **Lưu ý quy tắc**: không tinh chỉnh tham số trên cùng bộ dữ liệu đã tìm ra (tránh overfit); chạy walk-forward / out-of-sample trước khi tin.

---
*Xem thêm: `quant/KET_QUA.md` (4 cơ chế trước đó) — cơ chế B Ichimoku Chikou+DI trên EURUSD cũng vượt buy&hold (27.8%), củng cố hướng "Ichimoku + EURUSD".*
