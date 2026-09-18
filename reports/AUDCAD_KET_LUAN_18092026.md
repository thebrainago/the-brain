# AUDCAD H4 — TUONG TAN SUAT/SHARPE (do 18/09/2026)

Tester THAT tren `AUDCADmicro`, 668 co che ho RSI/hoi quy, lot 5.0, von 10.000 USD,
**2013.01.01 -> 2026.09.01 (13,66 nam)**.

## Du lieu co that 13,66 nam — da xac minh

Broker nay tung bi bat cat lich su tu 2022-08 ([[exness-lich-su-cat-2022-08]]),
va tester KHONG bao loi khi thieu du lieu. Phep thu: chay lai cung co che voi
cua so 6,67 nam -> **71 lenh** so voi **141 lenh** o 13,66 nam. Ti le 50,4% so
voi do dai 48,8% -> so lenh ti le dung voi cua so, tuc du lieu co that ca ky.

## KET QUA CHINH: hai dieu kien LOAI TRU NHAU

| Nhom | So co che | Sharpe |
|---|---:|---|
| Du tan suat Tang 0 (>= 2 lenh/tuan) | 147/668 | **0 co che nao Sharpe > 0** |
| Sharpe >= 1,0 | 5 | tan suat **0,03-0,24 lenh/tuan** (thap hon nguong 8-65 lan) |

**Giao cua hai dieu kien: RONG.**

5 co che manh nhat, va tan suat cua chung:

| Co che | Lenh | /tuan | Sharpe | DD% |
|---|---:|---:|---:|---:|
| nguoi_tra_tien_vi_chien_luoc_nay_ket_hop | 22 | 0,03 | 2,19 | 1,37 |
| reversion_zscore_extreme_filter | 40 | 0,06 | 1,31 | 1,27 |
| rsi_sell_overbought_cross | 168 | 0,24 | 1,21 | 1,54 |
| rsi_xuong_nguong_cao | 164 | 0,23 | 1,13 | 1,78 |
| dashboard_mean_reversion_signal | 167 | 0,24 | 1,11 | 2,78 |

Nguoc lai, 5 co che NHIEU LENH nhat deu am nang:
`rsi_buy` 9.870 lenh (13,9/tuan) Sharpe **-1,15** · `mua_rsi14_tren_30_rsi14_duoi_70`
9.368 lenh Sharpe **-2,96** · `pine_cm_rsi_2_strat` 8.843 lenh Sharpe **-3,94**.

## Y NGHIA

Day dung la **nguyen tac 2** cua tong ket SP500 hien ra tren FX H4: *"chi phi
giet intraday — rang buoc CAU TRUC, khong phai thieu ky nang"*. Tang tan suat
tren AUDCAD la tang so lan tra spread, va edge hoi quy khong du day de bu.

**Ket luan: khong the tim duoc he AUDCAD ra tien bang ENTRY don thuan.** Da quet
668 co che, tuong dung o do. Huong con lai la **QUAN TRI VI THE** — dung mot entry
tam thuong nhung xu li lenh tot, dung nhu chu du an noi 05/09: *"voi FX quan li vi
the tot thi entry sai van co loi"*. Xem [[quan-tri-vi-the-lon-hon-entry]] va
[[luoi-audcad-do-day-du]].

## Ung vien cu `AUDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55`

PASS cong Python tu 31/08 (Sharpe 1,156). Tester that: **Sharpe 0,68**, 141 lenh,
PF 1,61, DD 3,46%, +2,76%/nam o cung rui ro (moc mua-giu +0,03%/nam).
Tester cat gan mot nua Sharpe — dung luat "Python chi la sang loc so bo".
No cung chi xep hang ~13, khong phai co che tot nhat.
