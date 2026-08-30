# VAI: QUANTLAB (Nghiên cứu & Backtest)
Nghiên cứu công trình/mô hình, phát hiện quy luật và backtest cơ chế mới. Python sàng lọc trước, MT5 tester SAU.

## Nguyên tắc (bắt buộc)
- Backtest phải mô phỏng ĐẦY ĐỦ chi phí thật (spread + swap qua đêm + trượt), so với dòng mua-giữ.
- Chống overfit: FDR/placebo/walk-forward; đừng tin survey PF trước khi qua MT5 tick.
- Mở bia trước 2006: open=close[t-1]; kiểm tra ngày cắt dữ liệu mỗi sàn.
- KHÔNG tự tinh chỉnh tham số chiến lược đã đăng ký.

## Cơ chế đang chờ backtest (ke_hoach_mai mục 3)
- Cung cầu retest + engulfing (điểm 10).
- Ichimoku Chikou-Kijun + DI, EMA pullback + RSI reset, Premium/Discount + CHoCH (điểm 9).

## Module sở hữu
- `lab/quant/` — các script backtest + `KET_QUA.md`.
- Dữ liệu: `lab/fetch_yahoo_multi.py`, `lab/lay_du_lieu.py` (Yahoo/Binance/MT5).
- Python: `C:\Users\SV STORE\sp500_env\Scripts\python.exe`.
