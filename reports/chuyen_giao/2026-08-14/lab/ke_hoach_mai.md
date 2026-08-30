# KE HOACH NGAY MAI (11/08)

## 1. TEST MT5 THAT - DAILY ZONE GOLD TP=50 (uu tien so 1)
- EA: dung logic "Daily Zone breakout-return + luoi DCA lot phang + chot khi gia hoi phuc ve avg+TP".
- Neu co san EA phu hop thi dung; neu khong thi viet EA MQL5 moi (bo nao vai 'coder').
- Quet tham so tren MT5 Strategy Tester:
  - Pip pha vung (breakout): 20-80
  - Be rong hoi ve: 0-50 pip
  - Buoc luoi (BUOC_PIP): 50-300
  - TP hoi phuc: 50/100/150/200 (gold da thang o 50)
  - So bac luoi toi da, thoi gian cho toi da (30 ngay)
- Tai san: XAUUSD (gold), XAGUSD, EURUSD, GBPUSD, cac cap JPY...
- So sanh voi moc chuan: EURCAD LuoiDoiXung (PF 1.71, DD 559).
- Neu duoc: cau hinh pipeline --maynha / --vps (tao folder Drive chung lab_chung).

## 2. DAU VAO API - CAPTCHA NUA-TU DONG
- Dung helper dang ky nua-tu dong (tu dien + tu chup key, chi de cau bam CAPTCHA).
- Ap dung cho Twelve Data truoc, roi cac trang CAPTCHA khac.

## 3. QUET BACKTEST CAC CO CHE DANG GIA TRI
- Vung cung cau retest + engulfing (diem 10).
- Ichimoku Chikou-Kijun + DI, EMA pullback + RSI reset, Premium/Discount + CHoCH (diem 9).

## 4. NAP NGUON MOI (gian cach tranh rate-limit)
- Chay --dan gian cach (GitHub rate-limit 10 lan/phut) de daemon sinh them co che.
- Daemon chay 24/7; kiem tra trang thai.

## GHI NHO
- Da co: AlphaVantage key, Binance+Yahoo data, 32 co che, gold Daily Zone TP=50 PF 3.93 (survey).
- Pipeline --maynha chua cau hinh (thieu folder Drive chung + MT5 tester that).
