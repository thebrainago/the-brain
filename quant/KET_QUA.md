# KẾT QUẢ QUÉT BACKTEST — QUANTLAB

> Ngày chạy: 2026-08-12 · Dữ liệu: Yahoo Finance, khung D1, 10 năm (2016-08 → 2026-08)
> Tài sản: S&P 500 (`^GSPC`), Vàng (`GC=F` — futures, **thay cho `XAUUSD=X` đã delisted trên Yahoo**), EUR/USD (`EURUSD=X`).
> Đây là **sàng lọc Python**, chưa qua MT5 tick. Kết quả **KHÔNG phải** lời hứa lợi nhuận.

---

## 1. BẢNG KẾT QUẢ (đã trừ chi phí: spread + swap)

| Cơ chế | Tài sản | Số lệnh | Lãi TT | Lãi Buy&Hold | PF | Sharpe | Calmar | MaxDD |
|---|---|---|---|---|---|---|---|---|
| A CungCầu+Engulfing | SP500 | 58 | +32.8% | +253.8% | 1.33 | 0.54 | 0.24 | -12.2% |
| A CungCầu+Engulfing | Vàng | 68 | +73.5% | +234.5% | 1.67 | 1.04 | 0.85 | -6.7% |
| A CungCầu+Engulfing | EURUSD | 1 | -1.2% | +3.6% | 0.00 | -0.59 | -0.10 | -1.2% |
| B Ichimoku Chikou+DI | SP500 | 122 | -1.3% | +253.8% | 1.02 | 0.06 | -0.00 | -39.7% |
| B Ichimoku Chikou+DI | Vàng | 128 | +82.3% | +234.5% | 1.15 | 0.53 | 0.38 | -16.4% |
| B Ichimoku Chikou+DI | EURUSD | 123 | +27.8% | +3.6% | 1.14 | 0.51 | 0.33 | -7.2% |
| C EMA Pullback+RSI | SP500 | 219 | -28.5% | +253.8% | 0.91 | -0.30 | -0.08 | -40.0% |
| C EMA Pullback+RSI | Vàng | 270 | +12.9% | +234.5% | 1.06 | 0.18 | 0.05 | -26.7% |
| C EMA Pullback+RSI | EURUSD | 291 | -14.7% | +3.6% | 0.91 | -0.33 | -0.08 | -19.1% |
| D Premium/Discount+CHoCH | SP500 | 6 | -16.2% | +253.8% | 0.66 | -0.35 | -0.10 | -17.6% |
| D Premium/Discount+CHoCH | Vàng | 5 | +5.5% | +234.5% | 1.30 | 0.21 | 0.07 | -7.6% |
| D Premium/Discount+CHoCH | EURUSD | 1 | +1.2% | +3.6% | 1.87 | 0.22 | 0.14 | -0.8% |

**Đọc nhanh:** đối chiếu cột "Lãi TT" với "Lãi Buy&Hold" cùng kỳ. Chỉ **B trên EURUSD** là vượt buy&hold về lãi tuyệt đối (27.8% vs 3.6%). Các case còn lại đều thua hoặc ngang mốc buy&hold.

---

## 2. TÁC ĐỘNG CỦA CHI PHÍ (bằng chứng "chi phí là sát thủ")

| Cơ chế | Tài sản | Lãi có CP | Lãi không CP | Phần hao do CP |
|---|---|---|---|---|
| B Ichimoku | Vàng | +82.3% | +111.5% | -29.3 điểm % |
| C EMA | Vàng | +12.9% | +34.7% | -21.7 điểm % |
| B Ichimoku | EURUSD | +27.8% | +36.7% | -8.9 điểm % |
| A CungCầu | Vàng | +73.5% | +84.0% | -10.5 điểm % |

**Kết luận:** spread + swap qua đêm ăn mòn đáng kể, đặc biệt với cơ chế giao dịch nhiều (EMA pullback 270-291 lệnh). Bỏ qua chi phí = báo cáo ảo.

---

## 3. ĐÁNH GIÁ TỪNG CƠ CHẾ

### A. Cung cầu retest + engulfing (ưu tiên nhất, điểm 10)
- **Vàng:** tốt nhất về rủi ro — PF 1.67, Sharpe 1.04, Calmar 0.85, MaxDD chỉ -6.7% (buy&hold -25%). Nhưng lãi tuyệt đối 73.5% < buy&hold 234.5%.
- **SP500:** PF 1.33, Sharpe 0.54 — lãi 32.8%, thua xa buy&hold.
- **EURUSD:** chỉ 1 lệnh trong 10 năm — **không đủ mẫu**, kết quả vô nghĩa.
- Nhận xét: logic "retest + engulfing" có vẻ **bắt sóng tốt hơn khi có biến động mạnh (vàng)**, nhưng mẫu EURUSD quá ít. Cần xác minh MT5 tick trước khi tin PF 1.67.

### B. Ichimoku Chikou-Kijun + DI (điểm 9)
- **EURUSD:** case duy nhất vượt buy&hold rõ (27.8% vs 3.6%, PF 1.14). Đáng xem tiếp.
- **Vàng:** PF 1.15 nhưng lãi 82.3% < 234.5% mốc buy&hold.
- **SP500:** thua buy&hold (PF 1.02, Sharpe 0.06, DD -39.7%).
- ⚠️ **Đã sửa lỗi lookahead bias** trong bản ngày 12/08: bản đầu dùng `shift(-26)` (nhìn dữ liệu tương lai) cho Sharpe 1.37 trên SP500 — **sai, đã bỏ**. Bản đúng dùng `shift(+26)` (chỉ dữ liệu quá khứ). Kết quả thật khiêm tốn hơn nhiều.

### C. EMA pullback + RSI reset (điểm 9)
- Thua buy&hold toàn bộ 3 tài sản. SP500/EURUSD âm lãi. Vàng chỉ +12.9% vs 234.5%.
- Giao dịch nhiều (219-291 lệnh) → chi phí ăn mòn mạnh.
- **Kết luận sơ bộ: loại** khỏi diện ưu tiên, trừ khi có biến thể khác.

### D. Premium/Discount + CHoCH (điểm 9)
- Số lệnh **cực thấp** (1-6 lệnh/10 năm) → kết quả **không có ý nghĩa thống kê**.
- PF trên vàng 1.30, EURUSD 1.87 nhưng chỉ 1-5 lệnh. Không đáng tin.
- Bộ lọc CHoCH quá khắt → cần nới tiêu chí hoặc xuống khung nhỏ hơn để có mẫu đủ lớn.

---

## 4. CAVEAT (đọc kỹ trước khi dùng)

1. **Python sàng lọc sơ, chưa qua MT5 tick.** Dữ liệu D1 của Yahoo không phải tick MT5; không mô phỏng trượt giá theo thời điểm thực, độ khớp lệnh, hay swap chính xác theo ngày triển khai.
2. **Vàng dùng futures `GC=F`**, không phải `XAUUSD` spot (đã delisted trên Yahoo). Nến contang/backwardation của futures có thể lệch nhẹ so với spot — kết quả vàng coi là gần đúng.
3. **Chi phí là ước lượng** (spread trung bình + swap/đêm, xem `metrics.py` → `CHI_PHI`), chưa phải bảng giá thật của một sàn cụ thể. Kết quả có thể đổi theo broker.
4. **Một pass in-sample, chưa walk-forward / placebo.** Các tham số là mặc định hợp lý, **KHÔNG tinh chỉnh** để đẹp (chống overfit). Kết quả đẹp có thể là may mắn.
5. **Case ít lệnh (1-6 lệnh) là vô nghĩa thống kê** — chỉ coi là gợi ý, không phải phát hiện.
6. Nghi ngờ PF survey cao (như "Vàng PF 3.93") không tái hiện ở đây: **không cơ chế nào đạt PF > 1.7 trên mẫu đủ lớn** và **không cơ chế nào vượt buy&hold trên SP500**. Điều này đúng với cảnh báo "đừng tin survey".

---

## 5. KHUYẾN NGHỊ BƯỚC TIẾP

- Đưa **B_Chikou_DI trên EURUSD** (case duy nhất vượt buy&hold) lên MT5 tick để xác minh.
- **A_CungCầu+Engulfing trên Vàng** đáng xem (PF 1.67, DD thấp) nhưng cần mẫu nhiều hơn (nới tần suất tín hiệu) trước khi tin.
- **C và D tạm hoãn**: C thua rõ, D thiếu mẫu.
- Trước khi theo đuổi bất kỳ cơ chế nào: chạy walk-forward + placebo trên `^GSPC` rồi mới lên MT5.

---

## 6. FILE ĐÃ TẠO (trong `lab/quant/`)

| File | Vai trò |
|---|---|
| `du_lieu.py` | Tải/cache dữ liệu Yahoo D1 (^GSPC, GC=F, EURUSD=X) |
| `metrics.py` | Đo lường Sharpe/PF/Calmar/MaxDD + mô hình chi phí spread/swap + buy&hold |
| `tin_hieu.py` | Hàm chỉ báo kỹ thuật (pivot, engulfing, EMA, RSI, ADX/DI, Ichimoku) |
| `co_che_A_cung_cau_engulfing.py` | Cơ chế A: cung cầu retest + engulfing |
| `co_che_B_ichimoku_chikou_di.py` | Cơ chế B: Ichimoku Chikou-Kijun + DI |
| `co_che_C_ema_rsi.py` | Cơ chế C: EMA pullback + RSI reset |
| `co_che_D_premium_choch.py` | Cơ chế D: Premium/Discount + CHoCH |
| `chay_tat_ca.py` | Chạy 4 cơ chế × 3 tài sản, ghi JSON |
| `ket_qua_all.json` | Kết quả thô đầy đủ (dữ liệu nguồn của bảng trên) |
| `KET_QUA.md` | File này |
| `data/*.csv` | Dữ liệu Yahoo đã cache |
