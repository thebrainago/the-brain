# Khao sat Drive "Tong Hop File Bot - Trade An Lac" (04/10/2026)

Chu du an dua link (thu muc Google Drive cong khai). Chu du an noi cac bot (ke ca ban crack) la bot ho gop tien mua hoac da bi crack ban ra thi truong -> tai de nghien cuu (04/10). Tep tho CHI o `du_lieu_cao/drive_trade_an_lac/` (gitignore, KHONG vao git). Chi chay tren tester / tai khoan DEMO, tat DLL, khong bao gio tai khoan that.

## Noi dung (191 tep)
- 128 indicator `0.Indicator\*.ex5` (nguon "ForexCracked.com"): CHUA tai (khong phai bot; hoi chu du an neu can).
- Bot (da tai, 54 muc, 15 MB, khong loi): CCBSN (v2.6, v3.0.5 .ex5 + 10 .set), Bigmouse Hedging T91 v2.2 (.ex5), Black Dragon MT5 V13 (.ex5 + .set vang 20k), Black Wolf (.ex5 + .set), BNK.HBot (.ex4), Gold Hunter T91 (.ex5 + 2 .set), GoldMiner MT5 (.ex5), HandDCA + HandATMX (.ex4), KawKawKaw46 V2 (.ex4 + .set XAU M1), NewYear.HBot 2.1 (.ex5), NuTi.HBot 1.3 (.ex4), SEMI HFT V3.3 (.ex5), SignalX.HBot + Atomic Analyst (.ex4), Trailing.HBot (.ex4, 2 ban), UNFORGIVEN (.ex4), EXP-COPYLOT master/client MT4+MT5 (copy trade, .ex4/.ex5 + PDF manual).
- 3 bang tinh (.xlsx): tinh rui ro DCA theo he so lot (xlot 1,1-2,0; vang, tien, cap JPY: gia, buoc pip, tong lot, am cao theo lenh) + vi du tinh DD that (vang, lot gap doi 0,01 -> 1,28, 8 lenh).
- Bo qua: MT4setup/MT5setup, MT4 Clean (terminal.exe, metaeditor.exe), PDF hoa hong san Exness (khong lien quan).
- TAT CA la tep BIEN DICH (.ex4/.ex5): khong co ma nguon. Khong doc duoc logic tu tep; logic lay tu video HD + bo .set.

## "Cach dung" = video YouTube (moi thu muc co "Link HD.docx" chi toi video)
15 video, deu co phu de tu dong tieng Viet (da tai: `du_lieu_cao/drive_trade_an_lac/_video_phu_de/*.txt`). Tom tat tung bot: `reports/drive_bot_cach_dung.md` (agent doc 15 phu de; phu de co loi nhan dang giong noi).
Video: Bigmouse -CO8sCuE31c, Black Dragon IhdzG_Za3jg, BNK m-ECCVUrfh4, Copylot PKqS6XO1QTE + XA4Cm3E-oNE, Gold Hunter bnEMqsmJ5AI, HandDCA zDxRwEiGvwE + QN5DUZC9wBM, KawKaw w66ELN7cDPg, NewYear uFomm1PqlFY + fbhWUKamAkg, NuTi S43_cKlP9y0 + bYH9WFJ5rIg, SEMI HFT aEVSlzjyhWs, SignalX YvfSeiSLqAM. CCBSN khong co video trong thu muc nay (hoi dap o nhom Telegram VU TRU EA).

## CCBSN ("Can Cu Bu Sieng Nang", ban chu du an goi "csr") - doc tu 10 bo .set (224 tham so, 40 giong nhau o moi bo)
Day la bot DCA/luoi nang, KHONG phai bot SL cung. Cac khoi tham so:
- Vao lenh dau: `InpTypeBuySell` (0 hai chieu, 2 only-buy), loc spread `InpMaxSpread` 3-500 (don vi diem), `InpMaxBuyOrders/SellOrders` 5-1000, `InpMaxLots` 0,02-2,3.
- DCA: `InpDCAMODE` 0/1/5, he so lot `InpMultiplier` 1,0-1,5 (mac dinh 1,18-1,3), thang he so theo so lenh (`InpOrders2NewMultiplier1-5`/`InpNewMultiplier1-5` ~ 10/20/30/40/50 lenh -> 1,2/1,1/1,05/1,06/1,03), cong lot `InpPlus` 0,01; khoang cach `InpDistance0` 9,8-200, buoc theo tang `InpDistance1-4` (15-150) va he so gian `InpDistanceMulti` 1,0-1,2.
- Thoat: `InpTP` 3-500, `InpTPDCA` 3-1200 (TP cua ca nhom), doi TP khi lo (`InpUseChangeTPDCA`, `InpPerLoss2ChangeTP` -5..-20%).
- Lenh doi ung/hedge: `InpOrders2OpenOpp` 5-12, `InpLotsOpp` 0,01-0,05, `InpPerLotsOpp` 0-15.
- "Sniper": chot tung phan/loc lenh (`InpUseSniper`, `InpTPSniper` 5-30, `InpMoneySniperFull` 1-10 USD, `InpFirst/LastOrdersSniper`, `Sniper Partial` khi lo -5..-30%) va "All Sniper" (dong tat ca khi lai 1-10 USD sau 1-55 lenh).
- Bo loc: DCA filter (`InpUseFilterDCA`, mo sau 1-25 lenh), tin tuc/ADX/ATR (theo thong bao v3.0.6 o nhom), lich ngay/gio, `InpMagicID`.
- Bo set theo von: 10K (DD tac gia ~3K), 500 USD (`CCBSN_500_2`), 50 USD (H1), 3000 (XAU M15), US Tech 3-point, only-buy. Ten file ghi "10K ... DD 3K" = TUYEN BO cua nguoi dung, khong phai bang chung.

Nhan xet cho day chuyen: CCBSN dung chat "luoi/DCA hai chieu + chot tung phan (tia lenh)" ma engine `nhan/luoi.py` da co (che_do hai_chieu, lot cong/nhan, tia_lenh, tran_tang). Khoang trong (chua co trong engine): he so lot theo bac (10/20/30/40/50 lenh), buoc gian theo tang 4 muc, lenh doi ung khi hang chuc lenh, doi TP theo lo, "All Sniper". Muon mo phong CCBSN cho dung phai them cac khoi nay, hoac chay thang `.ex5` tren MT5 tester (LAN EA THO) voi tung bo `.set`: ung vien so 1 cua duong chay thang (co san 10 bo .set cua tac gia, vang M15 / H1 / US Tech).

## Viec tiep (cloud quyet)
1. Chay `CCBSN v3.0.5.ex5` + 10 bo .set tren MT5 tester (XAUUSD M15, doan kham_pha 2018-2023, phi XM that), doc DD that / so lenh toi da / lot toi da. Don bay chap nhan duoc; cong chan = lai sau phi + maxDD < 80%.
2. Cac bot HBot/T91/Black Dragon/Gold Hunter: doc `drive_bot_cach_dung.md` lay luat, roi chon bot nao chay tester truoc.
3. Neu can indicator ForexCracked: bao chu du an (128 tep, chua tai).
