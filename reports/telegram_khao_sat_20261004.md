# Khao sat 4 link Telegram chu du an duyet (04/10/2026)

| link | ket qua | ghi chu |
|---|---|---|
| @vutruea (VU TRU EAFOREX) | DA THEO DOI (Join Group); 8.555 thanh vien | nhom dien dan; nhieu bot EA - day la nguon chinh |
| @incatorsNT8bookmap (Software & Indicator) | DA THEO DOI; ~1.010 thanh vien | nghieng indicator/phan mem (ATAS, Bookmap, Sierra, NT8), nhieu ban crack -> khong tai; co chu de "EA MT4, MT5" it file |
| @bobvolmanchannel (Nhat Hoai Trader Channel) | DA THEO DOI (Subscribe); 11.300 nguoi | kenh khoa hoc Bob Volman + quang cao; khong co bot EA |
| t.me/c/2120351422/237 | CHUA VAO DUOC | nhom/kenh rieng, chua la thanh vien: can LINK MOI (t.me/+...) tu chu du an |

## VU TRU EAFOREX - chu de (thay duoc)
HUONG DAN CAI DAT - KHO INDICATOR - KHO CODE MQ4 - KHO COPYTRADE (co dang ID + mat khau investor cua nguoi khac: KHONG dung) - Y TUONG CLAUDE - BUON CHUYEN - HOI DAP BOT CCBSN (co bot tra loi) - KHO BOT.

## Bot thay trong KHO BOT (moi lan chi doc ~3 man hinh gan nhat, CHUA het lich su)
| ten | loai | ghi chu |
|---|---|---|
| CLMCA (CLMCA.zip, 126 KB) | .mq5 (75 KB, MIT) + .ex5 + 5 .set + SHA256SUMS | XAUUSD M15, 5 chien luoc (Sonic R/EMA Dragon, loc xu huong), SL cung moi lenh, khong TP/martingale/grid, risk co dinh (D_V1: $50/lenh), doi SL theo moc R + trailing. Tac gia tu bao backtest 2018-08/2026 da tru phi PF 1,24-1,36; D_V1 +$17.100, DD $7.600, chuoi thua 52 lenh. TUYEN BO tu bao, tac gia noi chua du can cu chay tien that. Quet ma: khong DLL/WebRequest/Socket; FileOpen chi log/state. Nguon goc: github.com/pandaluvly/clmca-ea |
| Scalp_m5_break_fix.ex5 (67 KB) | bien dich | scalp M5 break; khong co ma nguon; chi chay tester demo |
| VuTru_Fibo_BB_Pullback.ex5 (73 KB) + M2_FIBO.set | bien dich + set | chay M2; lot 0,05 mac dinh |
| CCBSN v3.0.6 (.ex5 ~740 KB) | bien dich | bo loc tin/ADX/ATR, DCA theo ATR, trailing theo tien, chong don lenh, gioi han slippage, lich theo ngay; co bot hoi dap |
| support trade v4.ex5 (nhom Software & Indicator, chu de EA MT4/MT5) | bien dich | |
Tep tai ve: du_lieu_cao/telegram/vutruea/ (gitignore): CLMCA.zip (+ thu muc giai nen), Scalp_m5_break_fix.ex5.

## Viec tiep (cloud quyet, xem `tai_lieu/QUY_TRINH_NHOM_TELEGRAM.md` muc F)
1. CLMCA: dua `CLMCA.mq5` + 5 .set vao `ea_tho_*` (MT5 tester, XAUUSD M15, doan kham_pha) - ung vien thu nhat, co ma nguon va giay phep mo.
2. Quet het lich su KHO BOT / KHO CODE MQ4 bang Export/Telethon (khong chup man hinh).
3. Chu du an: link moi cho t.me/c/2120351422/237.
