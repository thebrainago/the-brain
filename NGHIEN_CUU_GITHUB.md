# NGHIEN_CUU_GITHUB.md - De xuat nang cap tu du an open-source (2026-08-10)

> Ket qua khao sat repo GitHub/mang. Xep theo LỢI ÍCH / CONG SUC. Moi muc ghi
> vi tri "gan vao khau nao" cua pipeline (KHUNG.md) de ap dung.

## A. XUYEN SUOT - Bo may test (uu tien nhat)
1. **Headless MT5 Strategy Tester** (github topic `strategy-tester`)
   - Chuc nang: compile MQL5, chay backtest tu shell, parse report, batch da symbol/TF.
   - Gan vao: thay cho vong `_chay_test` cham (mo MT5 GUI) -> chay batch nhanh tren VPS.
   - Gia tri: CAO. Bo cong: thap-trung (da co mt5_worker.py, chi them batch+cil).
2. **VectorBT**
   - Vectorized backtest siêu nhanh -> quet hang tram nghin cau hinh trong Python.
   - Gan vao: tang "Python sweep rong" (mo_phong_v2 hien pure-Python cham).
   - Gia tri: CAO. Bo cong: trung (phai viet lai bo mo phong theo vectorized).
3. **Backtrader** (event-driven, 15k sao) + **GenTrader** (GA tren Backtrader)
   - Khop tham so bang genetic, walk-forward, monte carlo.
   - Gan vao: OPTIMIZER + loc tu dong (sweep -> GA -> walk-forward).
   - Gia tri: CAO. Bo cong: trung.

## B. WALK-FORWARD / DANH GIA BEN (chong overfit)
4. **TonyMa1/walk-forward-backtester**: WFO san co trong Python.
5. **Kiploks Trading Robustness Engine**: deterministic backtest + WFA + robustness test.
6. **PyGAD** (GA) + **GeneTrader** (imsatoshi): GA toi uu tham so + chon cap.
   - Gan vao: loc_tu_dong (khung da co) -> the them monte carlo + WFA.
   - Gia tri: TRUNG-CAO. Bo cong: thap neu dung thu vien co san.

## C. NGUON Y TUONG / STRATEGY MINING (bo sung vao NGUON.md)
7. **awesome-quant** (wilsonfreitas) + **awesome-systematic-trading** (wangzhe3224):
   bach khoa toan thu vien + chien luoc -> cap nhat SOURCE LOOP lien tuc.
8. **Machine Learning for Trading** (stefan-jansen): code factor/ML research -> nhom factor.
9. **QuantConnect LEAN**: bo may backtest da tai san -> multi-asset (us500, vang, futures).
10. **Freqtrade**: hyperopt (GA) + backtesting/crypto -> bo sung da cap de mo rong.
11. **NumPy/pandas-based factor libs** (Alphalens, QuantStats): do yield factor + thong ke.

## D. DE XUAT TICH HOP VAO THE BRAIN (thu tu khuyen nghi)
1. [T1] Nang `_chay_test` thanh **batch headless MT5** (da symbol/TF, parse report) -> VPS.
2. [T2] Nang OPTIMIZER dung **GA + walk-forward** (Buoc 4-6) -> thay cho quet tuần tu.
3. [T3] The **monte carlo + robustness** vao loc_tu_dong -> giam edge gia.
4. [T4] Tich hop **VectorBT** lam "Python sweep rong" cho logic thuần OHLC.
5. [T5] SOURCE LOOP cap nhat tu **awesome-quant/systematic-trading**.

## E. GHI CHU
- Khong copy code ngay; dung lam THAM KHAO + ap dung ky thuat (WFA, GA, batch).
- Uu tien tich hop the tưng phần, giu cau truc 8-vai + bang cong viec hien tai.