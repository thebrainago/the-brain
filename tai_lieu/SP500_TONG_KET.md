# SP500 — TONG KET TOAN BO NGHIEN CUU (ban chuan de mo tai san khac)

> Chu du an dua vao he ngay 18/09/2026. Day la BAN DO quy trinh, khong phai
> bao cao. Khi sang tai san moi: chay lai danh muc muc 3, theo quy trinh muc 2,
> tranh bug muc 5, calibrate theo muc 7.
>
> **Trang thai SP500: COMPLETE** (chot 14/07/2026, bo sung ZZ-V 15/07).
> ~2,3 trieu gia thuyet da quet. **Song sot sau du 4 tang: 2.**

## LUAT GOC

Python chi la SANG LOC SO BO. **MT5 single-run la trong tai cuoi.**
MT5 optimization bi **cam vinh vien** (curve-fitting).

## QUY TRINH 4 TANG (2.090 -> 9 -> 5 -> 2)

**Tang 0 — loai som:** tan suat < 2 lenh/tuan · loi < 5 diem/lenh sau chi phi ·
R:R xau. Chi phi that phai nhet TU DAU (spread, slippage, swap moi dem giu).

**Tang 1 — THONG KE:** Bonferroni theo NHOM tan suat (khong toan cuc) ·
CHAT = Bonferroni, VUA = FDR-BH 10% · walk-forward 3 phase ·
one-sample t-test tren avg_R, **KHONG binomtest winrate**.

**Tang 2 — KINH TE:** `MIN_RR=0.2` · `MIN_N_PHASE=50` (DCA: 100) ·
`MIN_EDGE_MULT=3x spread` · `MAX_LOT_DCA=3.0`.
Sinh ra de giet **martingale tra hinh**: tp=0.1xATR / sl=4.0xATR -> rr=0.025,
winrate 100% tren 15-20 lenh. Bonferroni KHONG bat duoc (breakeven winrate cua
rr=0.025 la 97,6%, nen 100% vuot qua ngon lanh). Dung toan hoc, vo gia tri kinh te.

**Tang 3 — PLACEBO (bat buoc):** giu nguyen E/tp/sl/max_hold, thay entry bang
entry NGAU NHIEN, so voi 200 mo phong. Doc theo DO ON DINH: 100% deu tren moi
muc TP = that; 83/91/98/96 nhay quanh nguong = nhieu.
Vi sao bat buoc: `Pivot_H1_S1/support` qua Bonferroni ca 3 phase, n=2.731,
avg_R=+0,0685 — nhin nhu edge that. Nhung entry random duoc +0,0584. Khong test
thong ke nao bat duoc; **chi placebo bat duoc**.

**Tang 4 — ERA-CHECK:** can khung dai (M30 8,5 nam / M15 4,2 nam; M5 17 thang =
mot regime duy nhat, vo nghia). Phai song qua **crash** (COVID) va **bear le the**
(2022) — hai co che khac nhau. Suy giam theo thap ky = co che da chet (Daily_IBS).

## 15 NGUYEN TAC DA KIEM CHUNG

1. MT5 single-run la trong tai cuoi. Python can nhung khong du.
2. Chi phi giet intraday tren CFD ban le — rang buoc CAU TRUC, khong phai thieu ky nang.
3. Placebo bat buoc: LONG-only tren tai san co drift co the "co edge" hoan toan nho drift.
4. Doc placebo theo DO ON DINH, khong theo con so don le.
5. **WR cao + PF cao = dau hieu BUG**, khong phai dau hieu gioi. WR 94-98% gan nhu
   luon la timeout bias hoac martingale.
6. **`trend_spearman` dep KHONG phai bang chung edge** — no la TRIEU CHUNG cua bug:
   E lon hon -> entry hiem hon -> de dat WR 100% gia -> trend cang dep.
7. Cau truc lanh manh ma stats tra ve 0 la ket qua DUNG (0/320 multi-indicator).
8. Xung khac co che: dung ghep mean-reversion (DCA) len setup momentum/breakout
   (da do: **-17.000 pts**).
9. Chuan hoa moi nguong theo ATR/% — khong bao gio dung diem co dinh tren chuoi dai.
10. Edge nam o CHO XAC NHAN, khong o BAT DAO ROI: `breakout_up` song, `support` chet.
11. Era-check can khung dai.
12. Crash khong mot chieu: phan biet V-crash va bear le the, chung can bo loc khac nhau.
13. Cat lo luon thang "gong cho ve".
14. Moi tai san phan tich RIENG. Gop lo tung cho ket qua sai lech.
15. Tan suat thap = rui ro overfit. 2 lenh/nam thi WR 100% tren 11 lenh chang noi len gi.

## 12 BUG DA LAM SAI LECH KET QUA THAT

| # | Bug | Cach bat |
|---|---|---|
| 1 | **TIMEOUT BIAS** | Lenh khong cham TP/SL bi LOAI khoi mau -> 44,7% lenh bi vut, WR phong len ~97%. Fix: timeout dong theo gia thi truong, R = actual_pnl/sl |
| 2 | Sai test thong ke | Sau khi fix (1), `binomtest(winrate)` vo hieu. Chuyen sang t-test tren avg_R |
| 3 | Khong co san R:R | Sinh 2.081 martingale tra hinh |
| 4 | Look-ahead entry | Phai dung `Open[i+1]`, KHONG `Close[i]` |
| 5 | TP/SL cung nen | Phai co quy tac tie-break |
| 6 | `worst_adverse` do tai close | Phai do running-minimum suot thoi gian giu |
| 7 | Sai thang gia tuyet doi | Nguong co dinh (ZZ 40pt) la % rat khac nhau qua 15 nam |
| 8 | Checkpoint propagation | `--force-rerun` am tham tai su dung ket qua cu |
| 9 | Entry trung lap | Trong `intraday_tpsl` |
| 10 | Regime dung Close-to-Close | Phai Open-to-Open |
| 11 | Bo loc chu ky bau cu My ap cho tai san phi My | |
| 12 | `--mt5-adhoc` hardcode `yahoo=None` | Chan du lieu dai han |

## TAI SAN NAO HOP GI (do duoc, khong doan)

Chay ĐAU TIEN cho moi tai san moi: Hurst · OU fit · drift dai han · bat doi xung
up/down leg · retrace median · crash history · bien do song theo percentile.

- **SP500**: Hurst 0,51-0,53 (gan random walk), OU **FAIL**, drift +6,34%/nam
  -> long-bias, KHONG co mean-reversion cau truc -> grid doi xung khong co co so.
- **AUDCAD**: mean-reversion THAT (hai dong commodity).
- **UK100**: drift gan 0 -> la **bai test vang** de phan biet tin hieu that voi drift.

## SONG SOT TREN SP500 — DUNG 2 THU

1. `Pivot_H1_S1 / breakout_up / E=+0.3 / SL=4.0xATR / TP 1.0-1.4xATR` — qua du 4 tang,
   placebo 100% tren ca 5 muc TP, era-check 9/9. Edge that ~+0,048-0,053R
   (mot NUA avg_R la drift).
2. **Seasonality 56 nam** — 15 CHAT + 11 VUA. Dung lam BIAS huong, khong phai entry.

Bo sung: **ZZ-V** (2-8 lenh/nam) — nhung LONG-only KHONG thang entry ngau nhien
(placebo 68-92%): "+7.171pt" cua LONG la thu hoach drift. Tin hieu ZigZag chi co
gia tri that khi giao dich CA HAI CHIEU (placebo 100%).

## CON NO (SP500)

1. Chuan hoa nguong ZigZag theo ATR (uu tien #1)
2. Chay ZZ-V qua pipeline chinh thuc 4 tang
3. Chay ZZ-V tren UK100 — bai test drift quyet dinh
4. Danh gia Setup C (D1 Continuation) tren MT5
5. Thu hep Multi-Indicator ve rieng ho Donchian roi test lai FDR
6. Hoan thien `orderflow_backtest.py` khi co Rithmic
7. Re-run Magnetic Tier S (412 combo) qua du 4 tang
