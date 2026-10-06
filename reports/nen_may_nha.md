# Nen may nha - phien 06/10/2026 toi

## Moc 1 - dung moi truong (xong)
- May thieu thu vien (numpy, pandas, scipy, requests, pyautogui, pyperclip, pillow) -> don chay nen DANG_BAN/loi, `link tham-do` loi, `ea_tu_dong` tai 0 file. Da `pip install -r requirements.txt` + pyautogui/pyperclip.
- Cac don 00a/00b/00c va 6 don link-tham-do chay luc CHUA co thu vien -> ket qua 00a vo nghia (toc do 0.0). Can chay lai 00a luc may ranh.
- `b cau dat-session session_01XDvcQqRLu2itnyVWxmPCWz` xong.

## Moc 2 - lich su lenh MQL5 (xong, 06/10)
Lay bang `lay_export_man_hinh.py` (Chrome Profile 3): 2204755, 2231030, 2222743, 2204998, 2245675 (+ co san 2196457, 2195619). CSV o du_lieu_cao/mql5 (ngoai git).
`b nc cc boc_lich_su` (khung M15, ket qua `reports/boc_<id>_<ma>.json`):

| ho so | ma | ket qua |
|--|--|--|
| 2231030 | XAUUSD | DAT (mo ta) - **luoi DCA MUA mot chieu**, lot 0,01 phang, buoc ~21,7 pip, tran 9-10 tang, 604 ro mua / 128 ban, chi 12/732 ro lo (lo ro lon nhat -41), rong +1606 / 1150 lenh, phi 7% lai gop. Tu 2026-07: buoc 21,8, he so 0,96, tran 9. TP doi giua chung (19,9 -> 9,7 pip) |
| 2204755 | GBPUSD / USDJPY | khong ra luat: GBPUSD khong_ro (rong -108), USDJPY luoi_dca nhung rong -125, ngung giao dich hai ma nay tu 09/2024. Chi vang con lai (196 lenh, rong +2987) khong_ro |
| 2196457 | GOLD# -> XAUUSD | khong_ro_ho_co_che: 102/306 ro lo, cat lo lon (-325); khong phai luoi |
| 2204998 | XAUUSD | khong_ro_ho_co_che: 44,7% ro dong lo, ro lo lon nhat -917 |
| 2222743 | XAUUSD | khong_ro_ho_co_che: 62% ro dong lo, thang chi 43% lenh; ro lo lon nhat -2533 |
| 2245675 | USDJPY | don_lenh (khong luoi): 55% lo, nhung rong +5596 -> xu huong / cat lo, can mo ta rieng |

Ket luan: **chi 2231030 boc duoc luat (DAT)**. 4 ho so con lai = CHUA_DO_DUOC luat (khong phai luoi, he cat lo / hai chieu): engine luoi.py chua mo phong cat lo ro (`dung_lo_tong`).
Luu y: ket qua la GIA THUYET, nguoi thang la mau chon theo ket qua; chua thu tren doan ngoai cua so cua ho.
Chua lam: US30/USTEC/US500/BTC (khong co du lieu gia trong data/).

## Moc 3 - EA that (dang lam)
- `ea_tu_dong --tai 24`: tai duoc 24 .mq5 vao reports/ea/kho.json; buoc bien dich trong script loi (terminal "exness" khong co tren may nay, chi co XM Global MT5). `ea_tho_quet kho:*` dang chay (reports/ea_tho_quet_20261006.json).
- 6 don link-tham-do: tradingview OK, github OK; fxblue / darwinex / forexfactory / reddit LOI_MANG (nha mang chan DNS). Bat WARP van bi `CHO` (lui lai 5-10 phut). Thu lai sau.
