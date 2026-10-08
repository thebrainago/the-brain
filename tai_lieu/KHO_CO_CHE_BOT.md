# KHO KHOI CO CHE CUA CAC CON BOT

**Tep nay SINH TU MA (`python -m nhan.khoi_co_che --viet`), KHONG sua tay** - sua `nhan/khoi_co_che.py` roi sinh lai.
Test `test_khoi_co_che.py` so sanh tep nay voi ban sinh ra, nen no khong bao gio cu.

Chu du an 04/10/2026: *"moi bot se co chien luoc va cach quan tri cung nhu tinh dac sac khac nhau. Muc tieu cua the brain la boc tach duoc co che / chien luoc hoac yeu to dac sac cua cac con bot de thu ap dung cheo hoac ket hop them vao cac he thong va ea sau nay."*

## 1. Y TUONG MOT DONG

Mot con bot = **to hop cac KHOI co che** (vao lenh, them lenh, lot, thoat, bao ve, bo loc). Khoi dung chung giua nhieu bot la khoi 'chuan'; khoi chi mot hai bot dung la **yeu to dac sac**. Muon ap dung cheo: lay khoi cua bot A, cai vao he luoi cua ta (hoac bot B), do lai bang `b nc cc ...`. Bot la HOP DEN (.ex4/.ex5, khong co ma nguon) nen khoi chi co hai nguon: (1) loi tac gia / bo `.set` = **kien thuc truoc so lieu** (tep nay), (2) lich su lenh cua tester = **bang chung** (`nhan/ho_so_bot.py`, doi chieu: xac nhan / bac bo / khoi moi).

- 55 khoi, 17 bot (12 bot co mo ta khoi + he cua ta; 5 bot chua co nguon mo ta).
- Dong chay: tester -> `lenh_tester.vi_the_tu_tep` -> `ho_so_bot` -> doi chieu voi bang nay -> them khoi con thieu vao engine -> nhan ban bot -> so lenh voi hop den.
- Muc bang chung: N = ma nguon cua ta (he luoi.py); K = ten/gia tri tham so trong bo .set cua tac gia; T = thong bao cua chu bot (nhom Telegram); V = loi tac gia / nguoi trinh bay trong video (phu de tu dong, co the nhan sai); G = ta suy ra, chua ai noi (can lich su lenh moi chot). (D = lich su lenh tester: `ho_so_bot` ghi, khong nam trong bang tinh.)
- Trang thai engine: **co** = co (engine mo phong duoc, da co test); **mot_phan** = mot phan (gan dung, chua dung y het); **chua** = chua (can them vao luoi.py + nhan C + EA); **ngoai** = ngoai (can nguoi / chi bao ngoai - khong mo phong tu lich su).

## 2. BOT: AI LA AI, DAC SAC O DAU

### ccbsn - CCBSN (Can Cu Bu Sieng Nang) v2.6 / v3.0.5
- San: MT5; tep: .ex5 + 10 bo .set; nguon thong tin: 224 tham so trong 10 bo .set; khong co video (hoi dap o nhom Telegram).
- Ket qua tester that: tester (Model 1, GOLD.i# M15, kham_pha 2018-01-01..2021-10-11; thu nha 60fa, 6487): kham_pha lai: v3.0.5 Vamge10K +8623 DD 23,8% PF 2,45, v2.6 CanCuBo10K27 +6482 DD 23%; cac bo .set khac (min3000, CC304, onlybuy, H1_50usd, M15_10K_5KUT) am / chay het tai khoan. XAC NHAN 2021-10-13..2024-04-07 (moi bo mot lan): CHI v2.6 + 'Can Cu Bo 10K 2.7 DD 3K.set' song: +4923, DD 25% (~2,6k USD, lot co dinh), PF 1,89, 1467 lenh; von 5k DD 45,9%, 20k DD 13,1%. Vamge / Vange2 / 500_2 truot. Model 4: 0% tick that (XM thieu) -> chua du dieu kien niem phong; v2.6 Model 4 kham_pha +5939 (equity DD 42,6%). **[SONG SOT xac nhan]**
- Dac sac: DCA nang 5 tang: he so lot doi theo bac (moc 10/20/30/40/50 lenh), buoc 4 nac, lenh doi ung sau 5-12 lenh, doi TP khi lo, tia (Sniper) + All Sniper, loc DCA. Bo .set theo von (10K, 500, 50, 3000, US Tech, only-buy). Ten file 'DD 3K' = tuyen bo cua nguoi dung, khong phai bang chung. Tham so chua xep khoi: InpDCAMODE (0/1/5, chua biet nghia - co the la kieu DCA), InpMagicID.
- Khoi: `vao_ngay_lap_tuc`[G]; `hai_chieu_doc_lap`[K]; `mot_chieu`[K]; `luoi_gian_cach_deu`[K]; `luoi_buoc_gian_dan`[K]; `luoi_buoc_theo_bac`[K]; `lenh_doi_ung_sau_n_lenh`[K]; `lot_cong`[K]; `lot_nhan`[K]; `lot_nhan_theo_bac`[K]; `tran_lot_tong`[K]; `tran_so_lenh`[K]; `tp_chuoi_tu_gia_tb`[K]; `tp_tung_lenh`[K]; `doi_tp_khi_lo`[K]; `tia_n_lenh_khi_chuoi_dai`[K]; `all_sniper`[K]; `loc_spread`[K]; `loc_gio_giao_dich`[K]; `loc_ngay_thu_lich`[K]; `loc_tin_tuc`[T]; `loc_adx_atr`[T]; `loc_dca_tu_lenh_n`[K]
- Khoi it bot dung (yeu to dac sac): `luoi_buoc_theo_bac`, `lenh_doi_ung_sau_n_lenh`, `lot_cong`, `lot_nhan_theo_bac`, `doi_tp_khi_lo`, `all_sniper`, `loc_spread`, `loc_ngay_thu_lich`, `loc_tin_tuc`, `loc_adx_atr`, `loc_dca_tu_lenh_n`

### bigmouse - Bigmouse Hedging (T91 hedging v2.2)
- San: MT5; tep: .ex5; nguon thong tin: video Bigmouse -CO8sCuE31c.
- Ket qua tester that: tester: 0 lenh (khong vao duoc - can lenh dau tay hoac che do auto)
- Dac sac: Hedging bang lenh STOP doi ung voi tong lot x2 (4 lenh dau) roi x1,6; thoat theo tong tien, cat am, va KICH HOAT HOA VON sau N lenh (bo TP duong, chi dat SL o hoa von).
- Khoi: `vao_ngay_lap_tuc`[V]; `vao_tay_roi_dca`[V]; `lenh_doi_ung_stop`[V]; `lot_tong_gap_doi`[V]; `lot_fibo`[V]; `tran_lot_tong`[V]; `tran_so_lenh`[V]; `tp_chuoi_tien`[V]; `sl_cung`[V]; `cat_lo_theo_tien`[V]; `thoat_hoa_von_khi_chuoi_dai`[V]; `keo_sl_hoa_von_khi_co_lai`[V]; `loc_gio_giao_dich`[V]
- Khoi it bot dung (yeu to dac sac): `lenh_doi_ung_stop`, `lot_tong_gap_doi`, `lot_fibo`, `cat_lo_theo_tien`, `thoat_hoa_von_khi_chuoi_dai`

### black_dragon - EA Black Dragon MT5 V13 (vang)
- San: MT5; tep: .ex5 + .set vang 20k; nguon thong tin: video Black Dragon IhdzG_Za3jg.
- Ket qua tester that: tester (Model 1, GOLD.i# M15, kham_pha 2018-01-01..2021-10-11): am hoac chay het tai khoan trong doan kham_pha (thu nha 60fa)
- Dac sac: DCA hai chieu khong chi bao, buoc gian x1,2 (400 point), lot nhan, TP 'treo len', toi da 99 lenh moi chieu; che do manual (magic 0) va auto.
- Khoi: `vao_ngay_lap_tuc`[V]; `vao_tay_roi_dca`[V]; `hai_chieu_doc_lap`[V]; `luoi_buoc_gian_dan`[V]; `lot_nhan`[V]; `lot_tu_dong_theo_von`[V]; `tran_so_lenh`[V]; `tp_treo_len`[V]; `loc_gio_giao_dich`[V]; `loc_tin_tuc`[V]
- Khoi it bot dung (yeu to dac sac): `lot_tu_dong_theo_von`, `tp_treo_len`, `loc_tin_tuc`

### bnk - BNK.HBot
- San: MT4; tep: .ex4; nguon thong tin: video BNK m-ECCVUrfh4.
- Dac sac: DCA co 'GONG DUONG DOI UNG': khong chot lenh dang lai, giu no de can bang cac lenh am, chot ca chuoi roi mo chuoi moi.
- Khoi: `luoi_gian_cach_deu`[G]; `gong_duong_doi_ung`[V]; `lot_nhan`[V]; `tran_so_lenh`[V]
- Khoi it bot dung (yeu to dac sac): `gong_duong_doi_ung`

### copy_lot - EXP-COPYLOT (Copy1 / Copy2)
- San: MT4+MT5; tep: .ex4 / .ex5 master + client; nguon thong tin: 2 video Copylot PKqS6XO1QTE + XA4Cm3E-oNE.
- Dac sac: KHONG phai bot giao dich: sao chep lenh tu tai khoan Master sang Client (ty le lot 1:1). Khong co khoi co che nao.

### gold_hunter - T91 Gold Hunter
- San: MT5; tep: .ex5 + 2 .set; nguon thong tin: video Gold Hunter bnEMqsmJ5AI.
- Ket qua tester that: 2 bo .set: tester (Model 1, GOLD.i# M15, kham_pha 2018-01-01..2021-10-11): am hoac chay het tai khoan trong doan kham_pha (thu nha 60fa)
- Dac sac: Chi BUY vang khi RSI(4) M5 < 15, nhoi hang tram lenh moi lan co tin hieu; thoat KHONG theo pip / USD ma khi gia trung binh duong va RSI > 50.
- Khoi: `vao_rsi_qua_ban`[V]; `vao_theo_ma`[V]; `mot_chieu`[V]; `them_lenh_theo_tin_hieu`[V]; `lot_phang`[V]; `thoat_rsi_va_tb_duong`[V]
- Khoi it bot dung (yeu to dac sac): `vao_rsi_qua_ban`, `vao_theo_ma`, `them_lenh_theo_tin_hieu`, `lot_phang`, `thoat_rsi_va_tb_duong`

### hand_dca - HandDCA.HBot (kem chi bao SSL)
- San: MT4; tep: .ex4; nguon thong tin: video HandDCA zDxRwEiGvwE.
- Dac sac: 'Danh tay + DCA tu dong': nguoi vao lenh dau bang SSL ba khung (M15 xanh da dong + M5 xanh + M1 doi mau), bot tu DCA nguoc lai va chinh TP de co lai duong nho.
- Khoi: `vao_tay_roi_dca`[V]; `vao_chi_bao_ngoai`[V]; `tp_chuoi_tu_gia_tb`[V]
- Khoi it bot dung (yeu to dac sac): `vao_chi_bao_ngoai`

### hand_atmx - HandATMX.HBot (cap nhat trailing oneway)
- San: MT4; tep: .ex4; nguon thong tin: video HandDCA QN5DUZC9wBM.
- Dac sac: DCA nhoi theo lenh tay + 'Trailing Oneway': khi chuoi mot chieu > N lenh va tong lai > X USD thi keo SL ve hoa von cong delta; che do hai chieu rieng khi tong Buy+Sell > 10.
- Khoi: `vao_tay_roi_dca`[V]; `tp_chuoi_tien`[V]; `keo_sl_hoa_von_khi_co_lai`[V]

### kawkaw46 - KawKawKaw46 V2 (EMA46 XAU M1)
- San: MT4; tep: .ex4 + .set XAU M1; nguon thong tin: video KawKaw w66ELN7cDPg.
- Dac sac: DCA mot chieu tren vang: luoi TU GIAN khi gia di nguoc, khi gia hoi thi nhoi them lenh lam luoi day va keo TP lai gan; lot cong deu.
- Khoi: `vao_theo_ma`[V]; `mot_chieu`[V]; `luoi_buoc_gian_dan`[V]; `luoi_day_khi_gia_hoi`[V]; `lot_cong`[V]; `tp_chuoi_tien`[V]
- Khoi it bot dung (yeu to dac sac): `vao_theo_ma`, `luoi_day_khi_gia_hoi`, `lot_cong`

### newyear - NewYear.HBot (v1 va v2.1)
- San: MT5; tep: .ex5; nguon thong tin: 2 video NewYear uFomm1PqlFY + fbhWUKamAkg.
- Ket qua tester that: NewYear2.1 (Model 1, GOLD.i# M15, kham_pha 2018-01-01..2021-10-11): kham_pha +9666 DD 64%, TRUOT xac nhan 2021-10..2024-04 (tai khoan chay het von); lan chay dau treo / log spam (thu nha 60fa).
- Dac sac: Theo xu huong + MARTINGALE SAU SL (lot x2: 0,01 -> 0,32); v2.1 co TP / SL co dinh, keo SL ve hoa von khi lot 0,08 va lai 2 gia, chia lot, ba khung gio.
- Khoi: `vao_theo_xu_huong`[V]; `nhoi_theo_loi`[V]; `lot_nhan_sau_sl`[V]; `tp_tung_lenh`[V]; `sl_cung`[V]; `keo_sl_hoa_von_khi_co_lai`[V]; `loc_gio_giao_dich`[V]; `loc_sideway_nen`[V]
- Khoi it bot dung (yeu to dac sac): `vao_theo_xu_huong`, `nhoi_theo_loi`, `lot_nhan_sau_sl`, `loc_sideway_nen`

### nuti - NuTi.HBot 1.3 (MT4 va MT5)
- San: MT4+MT5; tep: .ex4; nguon thong tin: 2 video NuTi S43_cKlP9y0 (MT5) + bYH9WFJ5rIg (MT4).
- Dac sac: 'TAM GIA' = gia mo cua ngay: tren Sell, duoi Buy (danh nguoc); ba 'QUANG' theo so lenh (lenh 1-9 TP don 2 gia, tu lenh 10 TP chuoi hoa von + 0,5 gia voi lot lon); DCA theo nen; tia lenh.
- Khoi: `vao_tam_gia_ngay`[V]; `hai_chieu_doc_lap`[V]; `mot_chieu`[V]; `luoi_buoc_theo_bac`[V]; `luoi_theo_nen_moi`[V]; `lot_nhan`[V]; `lot_nhan_theo_bac`[V]; `tran_lot_tong`[V]; `tran_so_lenh`[V]; `tp_chuoi_tu_gia_tb`[V]; `tp_tung_lenh`[V]; `tia_n_lenh_khi_chuoi_dai`[V]; `cat_lo_theo_tien`[V]; `loc_ngay_thu_lich`[V]; `loc_bao_bien_dong`[V]
- Khoi it bot dung (yeu to dac sac): `vao_tam_gia_ngay`, `luoi_buoc_theo_bac`, `luoi_theo_nen_moi`, `lot_nhan_theo_bac`, `cat_lo_theo_tien`, `loc_ngay_thu_lich`, `loc_bao_bien_dong`

### semi_hft - SEMI HFT EA V3.3
- San: MT5; tep: .ex5; nguon thong tin: video SEMI HFT aEVSlzjyhWs.
- Ket qua tester that: tester: treo / het gio (khong co ket qua)
- Dac sac: DCA hai chieu lot nhan 1,08, thoat bang trailing (khong TP chuoi); phia Buy TACH NHOM va chot lenh thap nhat truoc, phia Sell gong ca chuoi; khi Sell ket thi giu Buy duong lam dem.
- Khoi: `hai_chieu_doc_lap`[V]; `luoi_gian_cach_deu`[V]; `gong_duong_doi_ung`[V]; `lot_nhan`[V]; `tia_n_lenh_khi_chuoi_dai`[V]; `trailing_stop_chuoi`[V]; `loc_gio_giao_dich`[V]
- Khoi it bot dung (yeu to dac sac): `gong_duong_doi_ung`, `trailing_stop_chuoi`

### signalx - SignalX.HBot (+ Atomic Analyst)
- San: MT4; tep: .ex4; nguon thong tin: video SignalX YvfSeiSLqAM.
- Dac sac: Lenh don theo tin hieu CHI BAO NGOAI (doc buffer), MARTINGALE x2 sau moi SL (0,01 -> 0,64); khong luoi.
- Khoi: `vao_chi_bao_ngoai`[V]; `lot_nhan_sau_sl`[V]; `tp_tung_lenh`[V]; `sl_cung`[V]
- Khoi it bot dung (yeu to dac sac): `vao_chi_bao_ngoai`, `lot_nhan_sau_sl`

### black_wolf - Black Wolf
- San: MT5; tep: .ex5 + .set; nguon thong tin: chua co video / huong dan.
- Ket qua tester that: tester: treo / spam log (da chan log > 300 MB)
- Dac sac: Chua biet co che: chua co nguon mo ta.

### goldminer - GoldMiner MT5
- San: MT5; tep: .ex5; nguon thong tin: chua co video / huong dan.
- Ket qua tester that: tester: treo / het gio
- Dac sac: Chua biet co che: chua co nguon mo ta.

### trailing_hbot - Trailing.HBot (2 ban)
- San: MT4; tep: .ex4; nguon thong tin: chua co video / huong dan.
- Dac sac: Chua biet co che (ten goi y trailing).

### unforgiven - UNFORGIVEN
- San: MT4; tep: .ex4; nguon thong tin: chua co video / huong dan.
- Dac sac: Chua biet co che: chua co nguon mo ta.

### luoi_cua_ta - He luoi cua ta (luoi.py + nhan C + ea_LuoiDayDu.mq5)
- San: MT5; tep: ma nguon; nguon thong tin: ma nguon cua ta.
- Ket qua tester that: AUDCAD luoi co tia, holdout +13,26%/nam (mo phong, engine co the lac quan ~15% o tia lenh)
- Dac sac: Luoi hai chieu / mot chieu, buoc gian dan, lot phang / cong / nhan, tia cap dau-cuoi, chot theo tien, cho gia lui truoc khi vao lai.
- Khoi: `vao_ngay_lap_tuc`[N]; `vao_lai_sau_cho_lui`[N]; `hai_chieu_doc_lap`[N]; `mot_chieu`[N]; `luoi_gian_cach_deu`[N]; `luoi_buoc_gian_dan`[N]; `lot_phang`[N]; `lot_cong`[N]; `lot_nhan`[N]; `tran_so_lenh`[N]; `tp_chuoi_tu_gia_tb`[N]; `tp_chuoi_tien`[N]; `tia_cap_sau_dau`[N]; `cat_lo_chuoi_theo_pip`[N]; `thoat_theo_thoi_gian`[N]; `nghi_sau_cat_lo`[N]

## 3. MA TRAN BOT x KHOI

Ky hieu: N = ma nguon cua ta (he luoi.py), K = ten/gia tri tham so trong bo .set cua tac gia, T = thong bao cua chu bot (nhom Telegram), V = loi tac gia / nguoi trinh bay trong video (phu de tu dong, co the nhan sai), G = ta suy ra, chua ai noi (can lich su lenh moi chot); `.` = khong co. Cot dau: so bot ngoai dung.

**VAO LENH DAU - khi nao mo chuoi**

| khoi | so bot | ccbsn | bigmouse | black_dragon | bnk | gold_hunter | hand_dca | hand_atmx | kawkaw46 | newyear | nuti | semi_hft | signalx | luoi_cua_ta |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vao_ngay_lap_tuc | 3 | G | V | V | . | . | . | . | . | . | . | . | . | N |
| vao_tay_roi_dca | 4 | . | V | V | . | . | V | V | . | . | . | . | . | . |
| vao_rsi_qua_ban | 1 | . | . | . | . | V | . | . | . | . | . | . | . | . |
| vao_tam_gia_ngay | 1 | . | . | . | . | . | . | . | . | . | V | . | . | . |
| vao_chi_bao_ngoai | 2 | . | . | . | . | . | V | . | . | . | . | . | V | . |
| vao_theo_ma | 2 | . | . | . | . | V | . | . | V | . | . | . | . | . |
| vao_theo_xu_huong | 1 | . | . | . | . | . | . | . | . | V | . | . | . | . |
| vao_lai_sau_cho_lui | 0 | . | . | . | . | . | . | . | . | . | . | . | . | N |

**TANG VI THE / LUOI - them lenh the nao**

| khoi | so bot | ccbsn | bigmouse | black_dragon | bnk | gold_hunter | hand_dca | hand_atmx | kawkaw46 | newyear | nuti | semi_hft | signalx | luoi_cua_ta |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hai_chieu_doc_lap | 4 | K | . | V | . | . | . | . | . | . | V | V | . | N |
| mot_chieu | 4 | K | . | . | . | V | . | . | V | . | V | . | . | N |
| luoi_gian_cach_deu | 3 | K | . | . | G | . | . | . | . | . | . | V | . | N |
| luoi_buoc_gian_dan | 3 | K | . | V | . | . | . | . | V | . | . | . | . | N |
| luoi_buoc_theo_bac | 2 | K | . | . | . | . | . | . | . | . | V | . | . | . |
| luoi_theo_nen_moi | 1 | . | . | . | . | . | . | . | . | . | V | . | . | . |
| luoi_day_khi_gia_hoi | 1 | . | . | . | . | . | . | . | V | . | . | . | . | . |
| them_lenh_theo_tin_hieu | 1 | . | . | . | . | V | . | . | . | . | . | . | . | . |
| nhoi_theo_loi | 1 | . | . | . | . | . | . | . | . | V | . | . | . | . |
| lenh_doi_ung_stop | 1 | . | V | . | . | . | . | . | . | . | . | . | . | . |
| lenh_doi_ung_sau_n_lenh | 1 | K | . | . | . | . | . | . | . | . | . | . | . | . |
| gong_duong_doi_ung | 2 | . | . | . | V | . | . | . | . | . | . | V | . | . |

**LOT - lot moi lenh va tran**

| khoi | so bot | ccbsn | bigmouse | black_dragon | bnk | gold_hunter | hand_dca | hand_atmx | kawkaw46 | newyear | nuti | semi_hft | signalx | luoi_cua_ta |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lot_phang | 1 | . | . | . | . | V | . | . | . | . | . | . | . | N |
| lot_cong | 2 | K | . | . | . | . | . | . | V | . | . | . | . | N |
| lot_nhan | 5 | K | . | V | V | . | . | . | . | . | V | V | . | N |
| lot_nhan_theo_bac | 2 | K | . | . | . | . | . | . | . | . | V | . | . | . |
| lot_tong_gap_doi | 1 | . | V | . | . | . | . | . | . | . | . | . | . | . |
| lot_fibo | 1 | . | V | . | . | . | . | . | . | . | . | . | . | . |
| lot_nhan_sau_sl | 2 | . | . | . | . | . | . | . | . | V | . | . | V | . |
| lot_tu_dong_theo_von | 1 | . | . | V | . | . | . | . | . | . | . | . | . | . |
| tran_lot_tong | 3 | K | V | . | . | . | . | . | . | . | V | . | . | . |
| tran_so_lenh | 5 | K | V | V | V | . | . | . | . | . | V | . | . | N |

**THOAT / CHOT - dong chuoi bang cach nao**

| khoi | so bot | ccbsn | bigmouse | black_dragon | bnk | gold_hunter | hand_dca | hand_atmx | kawkaw46 | newyear | nuti | semi_hft | signalx | luoi_cua_ta |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tp_chuoi_tu_gia_tb | 3 | K | . | . | . | . | V | . | . | . | V | . | . | N |
| tp_chuoi_tien | 3 | . | V | . | . | . | . | V | V | . | . | . | . | N |
| tp_tung_lenh | 4 | K | . | . | . | . | . | . | . | V | V | . | V | . |
| tp_treo_len | 1 | . | . | V | . | . | . | . | . | . | . | . | . | . |
| thoat_rsi_va_tb_duong | 1 | . | . | . | . | V | . | . | . | . | . | . | . | . |
| doi_tp_khi_lo | 1 | K | . | . | . | . | . | . | . | . | . | . | . | . |
| tia_cap_sau_dau | 0 | . | . | . | . | . | . | . | . | . | . | . | . | N |
| tia_n_lenh_khi_chuoi_dai | 3 | K | . | . | . | . | . | . | . | . | V | V | . | . |
| all_sniper | 1 | K | . | . | . | . | . | . | . | . | . | . | . | . |
| thoat_theo_thoi_gian | 0 | . | . | . | . | . | . | . | . | . | . | . | . | N |

**BAO VE / CAT LO / HOA VON**

| khoi | so bot | ccbsn | bigmouse | black_dragon | bnk | gold_hunter | hand_dca | hand_atmx | kawkaw46 | newyear | nuti | semi_hft | signalx | luoi_cua_ta |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sl_cung | 3 | . | V | . | . | . | . | . | . | V | . | . | V | . |
| cat_lo_theo_tien | 2 | . | V | . | . | . | . | . | . | . | V | . | . | . |
| cat_lo_chuoi_theo_pip | 0 | . | . | . | . | . | . | . | . | . | . | . | . | N |
| nghi_sau_cat_lo | 0 | . | . | . | . | . | . | . | . | . | . | . | . | N |
| thoat_hoa_von_khi_chuoi_dai | 1 | . | V | . | . | . | . | . | . | . | . | . | . | . |
| keo_sl_hoa_von_khi_co_lai | 3 | . | V | . | . | . | . | V | . | V | . | . | . | . |
| trailing_stop_chuoi | 1 | . | . | . | . | . | . | . | . | . | . | V | . | . |

**BO LOC / LICH - luc nao khong choi**

| khoi | so bot | ccbsn | bigmouse | black_dragon | bnk | gold_hunter | hand_dca | hand_atmx | kawkaw46 | newyear | nuti | semi_hft | signalx | luoi_cua_ta |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| loc_spread | 1 | K | . | . | . | . | . | . | . | . | . | . | . | . |
| loc_gio_giao_dich | 5 | K | V | V | . | . | . | . | . | V | . | V | . | . |
| loc_ngay_thu_lich | 2 | K | . | . | . | . | . | . | . | . | V | . | . | . |
| loc_tin_tuc | 2 | T | . | V | . | . | . | . | . | . | . | . | . | . |
| loc_adx_atr | 1 | T | . | . | . | . | . | . | . | . | . | . | . | . |
| loc_sideway_nen | 1 | . | . | . | . | . | . | . | . | V | . | . | . | . |
| loc_bao_bien_dong | 1 | . | . | . | . | . | . | . | . | . | V | . | . | . |
| loc_dca_tu_lenh_n | 1 | K | . | . | . | . | . | . | . | . | . | . | . | . |

## 4. TUNG KHOI

### VAO LENH DAU - khi nao mo chuoi

**`vao_ngay_lap_tuc`** - Vao ngay, khong cho tin hieu (engine: co; 3 bot ngoai dung: ccbsn, bigmouse, black_dragon)
- Mo ta: Mo lenh dau ngay khi bat bot hoac ngay sau khi chuoi truoc dong (Buy, Sell hoac ca hai); khong dung chi bao.
- Tham so: chieu: mua | ban | hai chieu, tre sau khi chuoi truoc dong
- Dau van tay trong lich su lenh: Chuoi moi bat dau cung phut / cung bar voi luc chuoi cu dong; gio vao khong theo mot chi bao nao. (phep do `vao_lai`)
- Engine: luoi.chay mo tang 1 o dau bar khi khong co ro dang song (cho_lui = 0). [truong luoi.ThamSo: cho_lui]
- Ap cheo: Khoi nen: moi he luoi cua ta dung no. Thay no bang diem vao co dieu kien (RSI, tam gia ngay...) de xem loc diem vao co them ky vong khong.
- Rui ro: Vao ngay luc thi truong dang chay manh mot chieu = chuoi sau ngay tu dau.

**`vao_tay_roi_dca`** - Nguoi vao lenh dau, bot lo phan sau (engine: ngoai; 4 bot ngoai dung: bigmouse, black_dragon, hand_dca, hand_atmx)
- Mo ta: Lenh dau do nguoi dat (hoac che do manual / magic 0); bot chi lo them lenh, TP, trailing.
- Tham so: magic 0 = tay
- Dau van tay trong lich su lenh: Khong quan sat duoc tu lich su lenh: lenh dau khong theo quy luat nao; chi thay phan bot lam (luoi, TP). (khong do duoc tu lenh)
- Engine: Can mot nguoi hoac mot luat vao; thay bang khoi VAO co dieu kien de mo phong.
- Ap cheo: Thay 'nguoi' bang mot luat vao do duoc (vd 3 khung SSL cua HandDCA, hoac luat tim bang tim_quy_luat) roi thu phan quan ly cua bot nay.
- Rui ro: Bot khong co phan vao: ket qua phu thuoc hoan toan nguoi dung, khong the tu chay.

**`vao_rsi_qua_ban`** - Vao khi RSI ngan han qua ban (engine: chua; 1 bot ngoai dung: gold_hunter)
- Mo ta: Mua khi RSI chu ky ngan (vd 4) tren khung nho (M5) xuong duoi nguong (vd 15); moi lan co tin hieu la them mot lenh.
- Tham so: rsi_chu_ky, khung, nguong_vao
- Dau van tay trong lich su lenh: Lenh mo o bar ngay sau khi RSI cat nguong; nhieu lenh cung chieu mo lien tiep khi RSI van thap; khoang cach gia giua cac lenh khong deu. (phep do `dieu_kien_vao`)
- Engine: luoi.py khong co tin hieu vao; DSL ngu_phap co rsi nhung chi cho lenh don, khong cho chuoi nhoi.
- Ap cheo: Thu lam cua vao cho he luoi cua ta: thay 'vao ngay' bang 'vao khi RSI(4) < 15' tren AUDCAD M15 va so voi vao ngay.
- Rui ro: Chi mua + nhoi: xu huong giam dai = ket ca chuoi, khong co SL (theo video).

**`vao_tam_gia_ngay`** - Vao theo 'tam gia' = gia mo cua ngay (engine: chua; 1 bot ngoai dung: nuti)
- Mo ta: Lay gia mo cua ngay lam moc; Sell khi gia len qua tam X, Buy khi gia xuong duoi tam X (danh nguoc xu huong); triet ly 'choi SAU bao': doi gia lech 30-40 gia roi moi tha.
- Tham so: khoang lech vao (3-30 gia), buy_on / sell_on
- Dau van tay trong lich su lenh: Lenh dau cua ngay cach gia mo cua ngay mot khoang gan co dinh; Sell nam tren moc, Buy nam duoi moc. (phep do `dieu_kien_vao`)
- Engine: Can gia mo cua ngay: luoi.py chua co dac trung nay.
- Ap cheo: Khoang cach toi gia mo cua ngay la mot dac trung moi cho tim_quy_luat; thu lam dieu kien vao cua he luoi.
- Rui ro: Ngay co 'bao' (vang di 40-60 gia trong 5-10 phut khong hoi): chuoi ket.

**`vao_chi_bao_ngoai`** - Doc tin hieu tu chi bao ben ngoai (engine: ngoai; 2 bot ngoai dung: hand_dca, signalx)
- Mo ta: Bot doc buffer cua mot chi bao (so buffer cho Buy, so buffer cho Sell) hoac nguoi nhin chi bao roi vao tay (SSL ba khung cua HandDCA).
- Tham so: ten chi bao, buffer buy, buffer sell
- Dau van tay trong lich su lenh: Khong thay chi bao tu lich su lenh; chi thay lenh vao thua thot khong theo nhip luoi. (khong do duoc tu lenh)
- Engine: Chi bao cu the khong co san.
- Ap cheo: Ma 'SSL ba khung dong cung mau' co the viet thanh dac trung de thu bang tim_quy_luat.
- Rui ro: Chi bao ve lai (repaint): vao theo nen chua dong la sai (loi nguoi trinh bay).

**`vao_theo_ma`** - Vao theo duong trung binh (MA / EMA) (engine: chua; 2 bot ngoai dung: gold_hunter, kawkaw46)
- Mo ta: Chon huong vao lenh theo vi tri gia so voi MA (vd EMA 46) hoac che do 'theo entry' / 'theo MA'.
- Tham so: chu_ky_ma, khung
- Dau van tay trong lich su lenh: Chieu lenh dau khop dau cua (gia - MA) tai bar vao. (phep do `dieu_kien_vao`)
- Engine: luoi.py khong co tin hieu vao.
- Ap cheo: Dac trung (gia - MA) / ATR co the dung lam bo loc chieu cho che do mot_chieu.
- Rui ro: MA tre: vao muon khi thi truong dao chieu nhanh.

**`vao_theo_xu_huong`** - Danh theo xu huong (trend-following) (engine: chua; 1 bot ngoai dung: newyear)
- Mo ta: Vao cung chieu voi xu huong (khung H1 tro len), nhoi them khi xu huong tiep tuc; tac gia canh bao sideway la ke thu.
- Tham so: khung, luat xu huong (khong noi)
- Dau van tay trong lich su lenh: Cac lenh cung chieu mo khi gia di CUNG chieu loi (Buy: lenh sau mo o gia cao hon), nguoc voi luoi gian cach. (phep do `them_khi_hoi`)
- Engine: luoi.py chi co luoi nguoc xu huong.
- Ap cheo: Khoi doi nghich voi luoi: 'luoi khi sideway, theo trend khi co trend' can bo loc che do (loc_adx_atr / loc_sideway_nen).
- Rui ro: Sideway: bi cuon lenh lien tiep.

**`vao_lai_sau_cho_lui`** - Cho gia lui roi moi vao lai (khoi CUA TA) (engine: co; 0 bot ngoai dung)
- Mo ta: Sau khi mot ro chot TP khong mo lai ngay ma cho gia lui them N pip nguoc chieu roi moi vao.
- Tham so: cho_lui (pip)
- Dau van tay trong lich su lenh: Khoang cach thoi gian va gia giua chuoi vua dong va chuoi moi lon hon 0 va gan co dinh. (phep do `vao_lai`)
- Engine: luoi.ThamSo.cho_lui. [truong luoi.ThamSo: cho_lui]
- Ap cheo: Da do tren EURCAD (+7,9% -> +12,1%/nam, tester that). Thu tren moi ma khi ghep voi khoi cua bot khac.
- Rui ro: Bo lo nhip hoi nhanh sau chot neu cho_lui qua lon.

### TANG VI THE / LUOI - them lenh the nao

**`hai_chieu_doc_lap`** - Hai chuoi Buy va Sell chay doc lap (engine: co; 4 bot ngoai dung: ccbsn, black_dragon, nuti, semi_hft)
- Mo ta: Chuoi Buy va chuoi Sell cung song, moi chuoi co luoi va TP rieng; lenh Sell khong cat lo lenh Buy.
- Tham so: kieu: hai chieu
- Dau van tay trong lich su lenh: Co luc nam ca Buy lan Sell cung mo (tai khoan hedging); nhieu luc chi mot chieu. (phep do `huong`)
- Engine: luoi.ThamSo.che_do = hai_chieu. [truong luoi.ThamSo: che_do]
- Ap cheo: Phan lon bot luoi chay hai chieu; so voi mot_chieu tren cung ma.
- Rui ro: Trend manh: chuoi nguoc trend am sau, chuoi thuan trend chot lai nho, am rong tang theo thoi gian.

**`mot_chieu`** - Chi mot chieu (chi Buy hoac chi Sell) (engine: co; 4 bot ngoai dung: ccbsn, gold_hunter, kawkaw46, nuti)
- Mo ta: Chi danh mot chieu (thuong chi Buy vang theo y 'vang dai han tang'); xu ly xong chuoi roi moi sang chuoi khac.
- Tham so: chieu: mua | ban
- Dau van tay trong lich su lenh: Tu 95% lenh tro len cung mot chieu. (phep do `huong`)
- Engine: luoi.ThamSo.che_do = mua | ban. [truong luoi.ThamSo: che_do]
- Ap cheo: Chi nen thu tren tai san co xu huong dai han ro (vang, chi so); don bay thap hon vi khong co chuoi doi khang.
- Rui ro: Xu huong nguoc dai = ket ca chuoi (khong co ve phia doi dien).

**`luoi_gian_cach_deu`** - Luoi gian cach deu (engine: co; 3 bot ngoai dung: ccbsn, bnk, semi_hft)
- Mo ta: Moi lenh them cach lenh truoc dung mot buoc co dinh (pip hoac gia).
- Tham so: buoc, tran so lenh
- Dau van tay trong lich su lenh: Khoang cach gia giua cac lenh lien tiep gan nhu hang so (CV nho). (phep do `buoc_theo_bac`)
- Engine: luoi.ThamSo.buoc. [truong luoi.ThamSo: buoc]
- Ap cheo: Khoi nen; so sanh voi buoc gian dan va buoc theo bac tren cung ma.
- Rui ro: Buoc nho + lot tang = lenh day, am sau rat nhanh.

**`luoi_buoc_gian_dan`** - Buoc gian dan theo he so (engine: co; 3 bot ngoai dung: ccbsn, black_dragon, kawkaw46)
- Mo ta: Buoc thu k = buoc * he_so^(k-1) co tran; he_so > 1 = song lau hon khi xu huong, < 1 = day dan.
- Tham so: buoc, he_so_buoc, buoc_tran
- Dau van tay trong lich su lenh: Khoang cach lien tiep tang theo ti le co dinh (1,05-1,2) cho den khi chay vao tran. (phep do `buoc_theo_bac`)
- Engine: luoi.ThamSo.he_so_buoc, buoc_tran. [truong luoi.ThamSo: he_so_buoc, buoc_tran]
- Ap cheo: Black Dragon (x1,2) va CCBSN (InpDistanceMulti) deu dung: thu cung gia tri tren AUDCAD.
- Rui ro: Gian qua nhanh: luoi that thua nhieu khi gia hoi khong du xa de chot.

**`luoi_buoc_theo_bac`** - Buoc theo bac (doi buoc o moc so lenh) (engine: chua; 2 bot ngoai dung: ccbsn, nuti)
- Mo ta: Buoc doi theo so lenh: bac 1 cho lenh 2-9, bac 2 tu lenh 10, bac 3 ... (CCBSN Distance1-4, NuTi 'quang').
- Tham so: so_lenh_moc_k, buoc_bac_k
- Dau van tay trong lich su lenh: Khoang cach gia giua cac lenh doi gia tri o nhung chi so lenh co dinh (vd lenh 10, 20, 30). (phep do `buoc_theo_bac`)
- Engine: luoi.py chi co mot buoc + he so; chua co bang buoc theo tang.
- Ap cheo: Khoi DE THU DAU: CCBSN la bot song sot duy nhat va dung 4 nac buoc; them vao luoi.py (+C +EA) la viec ro rang.
- Rui ro: Nhieu tham so = de khop nhieu: phai quet cao nguyen, khong cai gai.

**`luoi_theo_nen_moi`** - Chi them lenh khi mo nen moi (engine: chua; 1 bot ngoai dung: nuti)
- Mo ta: Mot nen chi duoc them toi da mot lenh (tranh don lenh khi gia chay nhanh trong mot nen); NuTi DCA theo nen.
- Tham so: khung nen
- Dau van tay trong lich su lenh: Thoi gian mo cac lenh them trung dau nen; khong co hai lenh them cung mot bar. (phep do `nhip_them_lenh`)
- Engine: Engine them lenh theo gia trong bar; chua co rang 'toi da 1 lenh / bar'.
- Ap cheo: De do: them tham so 'moi bar toi da 1 lenh'; xem co cat duoc DD luc tin manh khong.
- Rui ro: Them cham luc gia da di xa: gia trung binh kem hon.

**`luoi_day_khi_gia_hoi`** - Gia hoi thi nhoi them lenh, keo TP lai gan (engine: chua; 1 bot ngoai dung: kawkaw46)
- Mo ta: Khi gia di nguoc roi hoi lai, bot van them lenh (luoi day them) va keo TP ve gan: ket thuc chuoi som hon (KawKaw).
- Tham so: buoc them khi hoi, khoang TP keo lai
- Dau van tay trong lich su lenh: Co lenh them mo o gia TOT hon lenh them truoc (gia da hoi); TP chuoi gan gia trung binh. (phep do `them_khi_hoi`)
- Engine: luoi.py chi them lenh khi gia di nguoc them.
- Ap cheo: Giam thoi gian chuoi nhung tang lot trung binh; thu tren chuoi sau.
- Rui ro: Them lenh o gia hoi ma gia quay dau = lot nang them o gia xau.

**`them_lenh_theo_tin_hieu`** - Moi lan co tin hieu la them mot lenh (engine: chua; 1 bot ngoai dung: gold_hunter)
- Mo ta: Khong co khoang cach co dinh: moi tin hieu vao (vd RSI < 15 tren M5) them mot lenh cung chieu, ke ca dang am (GoldHunter: hang tram lenh).
- Tham so: tin hieu, tran lenh (khong noi)
- Dau van tay trong lich su lenh: Khoang cach gia giua lenh them khong deu, co the dao chieu (them o gia tot hon hoac xau hon). (phep do `them_khi_hoi`)
- Engine: luoi.py them theo buoc gia, khong theo tin hieu.
- Ap cheo: Neu tin hieu tot hon luoi co dinh thi lenh them nen nam o 'day nhip' chu khong o moi buoc; so tung thang.
- Rui ro: Tin hieu bam day nhieu lan: don lot o gia xau.

**`nhoi_theo_loi`** - Nhoi them khi dang lai (pyramiding) (engine: chua; 1 bot ngoai dung: newyear)
- Mo ta: Them lenh khi vi the dang lai de an xu huong (NewYear: 'nhoi theo trend', phu de mo ho).
- Dau van tay trong lich su lenh: Lenh them mo o gia THEO huong loi (Buy: gia cao hon lenh truoc). (phep do `them_khi_hoi`)
- Engine: luoi.py khong co nhoi thuan xu huong.
- Ap cheo: Doi nghich cua luoi: chi hop khi xu huong chay xa.
- Rui ro: Dao chieu luc da nhoi nhieu: mat het lai cua chuoi.

**`lenh_doi_ung_stop`** - Lenh stop doi ung (hedging bang lenh cho) (engine: chua; 1 bot ngoai dung: bigmouse)
- Mo ta: Sau lenh dau, dat lenh STOP nguoc chieu cach gia mot khoang (350-360 point); khi stop khop thi dat tiep stop nguoc lai: tao thang bac hedging (Bigmouse).
- Tham so: khoang_cach_buy_sell, he_so_lot_tong
- Dau van tay trong lich su lenh: Lenh mo bang BUY STOP / SELL STOP (cot Type trong bang Orders); chieu luan phien; khoang cach gia hang so. (phep do `doi_ung`)
- Engine: luoi.py chi mo lenh thi truong.
- Ap cheo: Chi dang thu neu do that cho thay lai; ghep voi lot_tong_gap_doi moi co nghia.
- Rui ro: 36 lenh la 'tai khoan khong con' (loi tac gia trong video).

**`lenh_doi_ung_sau_n_lenh`** - Mo lenh doi ung sau N lenh (hedge khi sau) (engine: chua; 1 bot ngoai dung: ccbsn)
- Mo ta: Khi mot chuoi co N lenh (CCBSN: 5-12), mo them lenh NGUOC chieu voi lot nho co dinh (0,01-0,05) de giam toc do am.
- Tham so: InpOrders2OpenOpp, InpLotsOpp, InpPerLotsOpp
- Dau van tay trong lich su lenh: Co lenh nguoc chieu xuat hien dung khi so lenh cua chuoi doi dien dat so co dinh; lot nho va khong tang. (phep do `doi_ung`)
- Engine: luoi.py hai chuoi chay roi nhau, khong co lenh doi ung trong cung chuoi.
- Ap cheo: Khoi nen thu SOM vi CCBSN song sot dung no; do bang quet_luoi sau khi them.
- Rui ro: Hedge khong dong: neu khong co luat dong, hai chieu cung ket.

**`gong_duong_doi_ung`** - Gong lenh dang lai de can lenh am (engine: chua; 2 bot ngoai dung: bnk, semi_hft)
- Mo ta: Khong chot lenh dang lai: giu no de bu cho cac lenh am (BNK), den khi chot ca chuoi; SemiHFT giu Buy khi Sell ket.
- Dau van tay trong lich su lenh: Co lenh dang lai bi giu rat lau (lau hon trung vi nhieu lan), chi dong cung luc voi ca chuoi. (phep do `gong_duong`)
- Engine: luoi.py chot theo ca chuoi, khong giu lenh duong rieng.
- Ap cheo: Giam DD hien thi, khong giam rui ro that neu khong co luat dong; do bang 'lenh nao bi giu bao lau'.
- Rui ro: Lenh duong bi giu roi dao chieu: mat het lai da co.

### LOT - lot moi lenh va tran

**`lot_phang`** - Lot phang (engine: co; 1 bot ngoai dung: gold_hunter)
- Mo ta: Moi lenh trong chuoi cung lot.
- Tham so: lot
- Dau van tay trong lich su lenh: Lot lenh k = lot lenh 1 voi moi k. (phep do `lot_theo_bac`)
- Engine: luoi.ThamSo.kieu_lot = phang. [truong luoi.ThamSo: kieu_lot, lot]
- Ap cheo: Khoi an toan nhat; moc so sanh cho moi khoi lot khac.
- Rui ro: Phang khong cuu duoc chuoi dai (nhung DD tang cham).

**`lot_cong`** - Lot tang cong (engine: co; 2 bot ngoai dung: ccbsn, kawkaw46)
- Mo ta: Lot lenh k = lot0 + (k-1) * buoc_lot (CCBSN InpPlus 0,01; KawKaw 'lot step add').
- Tham so: InpPlus, lot step add
- Dau van tay trong lich su lenh: Lot tang deu cung mot luong moi lenh. (phep do `lot_theo_bac`)
- Engine: luoi.ThamSo.kieu_lot = cong. [truong luoi.ThamSo: kieu_lot, he_so_lot]
- Ap cheo: Hien hon nhan: so tren cung ma.
- Rui ro: Chuoi rat dai van phinh lot (tuyen tinh).

**`lot_nhan`** - Lot nhan theo he so (engine: co; 5 bot ngoai dung: ccbsn, black_dragon, bnk, nuti, semi_hft)
- Mo ta: Lot lenh k = lot0 * he_so^(k-1), he_so thuong 1,05-1,3 (BlackDragon, BNK 1,2, SemiHFT 1,08, NuTi 1,1, CCBSN 1,18-1,3).
- Tham so: InpMultiplier, xlot
- Dau van tay trong lich su lenh: Ti le lot lien tiep gan hang so > 1. (phep do `lot_theo_bac`)
- Engine: luoi.ThamSo.kieu_lot = nhan, he_so_lot. [truong luoi.ThamSo: kieu_lot, he_so_lot]
- Ap cheo: Khoi trung tam cua DCA; do 'do sau toi da song duoc' theo he so.
- Rui ro: Luy thua: DD phinh o cuoi chuoi.

**`lot_nhan_theo_bac`** - He so lot doi theo bac (engine: chua; 2 bot ngoai dung: ccbsn, nuti)
- Mo ta: He so nhan lot thay doi o cac moc so lenh (CCBSN: lenh 10/20/30/40/50 -> he so moi 1,2/1,1/1,05/1,06/1,03; NuTi quang 2 lot lon tu lenh 10).
- Tham so: InpOrders2NewMultiplier1-5, InpNewMultiplier1-5
- Dau van tay trong lich su lenh: Ti le lot lien tiep r_k = lot_k / lot_(k-1) doi gia tri o chi so lenh co dinh. (phep do `lot_theo_bac`)
- Engine: luoi.py chi co mot he so; chua co bang moc -> he so.
- Ap cheo: Khoi song sot: them vao luoi.py (kieu_lot = bac, bang moc -> he so) roi quet.
- Rui ro: Lot cuoi chuoi lon: DD phinh o day.

**`lot_tong_gap_doi`** - Tong lot mot chieu gap doi chieu kia (engine: chua; 1 bot ngoai dung: bigmouse)
- Mo ta: Tong lot chieu dang thua luon x2 tong lot chieu doi dien trong 4 lenh dau, tu lenh 5 con x1,6 (Bigmouse).
- Tham so: he_so_4_dau, he_so_tu_lenh_5
- Dau van tay trong lich su lenh: Tai moi thoi diem tong lot Buy / tong lot Sell xap xi 2,0 roi 1,6. (phep do `lot_theo_bac`)
- Engine: luoi.py khong co hai chieu noi voi nhau.
- Ap cheo: Chi co nghia khi di cung lenh_doi_ung_stop.
- Rui ro: Tong lot tang rat nhanh (max lot 15 theo tac gia).

**`lot_fibo`** - Lot theo day Fibonacci (engine: chua; 1 bot ngoai dung: bigmouse)
- Mo ta: Lot lenh k theo day Fibonacci (1,1,2,3,5,8...) thay cho nhan (Bigmouse, tac gia chua test).
- Dau van tay trong lich su lenh: Ti le lot lien tiep gan 1,618 sau vai lenh dau. (phep do `lot_theo_bac`)
- Engine: luoi.py khong co.
- Ap cheo: Toc do tang nam giua nhan 1,3 va nhan doi: so voi nhan 1,6.
- Rui ro: Tang nhanh o dau chuoi.

**`lot_nhan_sau_sl`** - Nhan lot sau moi lan cat lo (martingale lenh don) (engine: chua; 2 bot ngoai dung: newyear, signalx)
- Mo ta: Sau moi lenh cat lo, lenh ke tiep nhan doi lot (0,01 -> 0,02 -> 0,04 -> ... 0,32 / 0,64); thang thi ve lot dau (NewYear, SignalX).
- Tham so: he so lot nhan 2, lot toi da
- Dau van tay trong lich su lenh: Lot lenh moi = 2 x lot lenh vua cat lo; ve lot dau sau lenh thang. (phep do `lot_theo_bac`)
- Engine: luoi.py la chuoi luoi, khong co lenh don nhan sau SL.
- Ap cheo: Chu du an chap nhan martingale (tieu chi: co lai sau phi + maxDD < 80%); thu tren he co tin hieu ro.
- Rui ro: Chuoi thua 7 lenh = lot x64: chay tai khoan; win rate thap la tu sat.

**`lot_tu_dong_theo_von`** - Lot tu dong theo von (engine: chua; 1 bot ngoai dung: black_dragon)
- Mo ta: Lot lenh dau = so du / n (vd 0,01 cho moi 1000 von).
- Tham so: auto lot
- Dau van tay trong lich su lenh: Lot dau cua chuoi tang dan theo so du tai luc vao. (phep do `lot_theo_von`)
- Engine: luoi.ThamSo.lot la hang so; lot chot ngoai engine (niem_phong_luoi).
- Ap cheo: Ket hop voi tran_lot_tong thanh 'lai kep co kiem soat'.
- Rui ro: Lai kep cung la thua kep sau chuoi xau.

**`tran_lot_tong`** - Tran lot (engine: chua; 3 bot ngoai dung: ccbsn, bigmouse, nuti)
- Mo ta: Gioi han tong lot hoac lot lon nhat cua chuoi (Bigmouse 15, NuTi MT5 3, CCBSN InpMaxLots 0,02-2,3).
- Tham so: InpMaxLots, max lot
- Dau van tay trong lich su lenh: Lot lon nhat cua cac chuoi dung o mot gia tri (cao nguyen) du chuoi sau. (phep do `rui_ro`)
- Engine: luoi.py khong co tran lot.
- Ap cheo: Tran lot la cach chan chay tai khoan: thu tran thap + tran so lenh.
- Rui ro: Cham tran ma gia van di nguoc: ket o lot lon.

**`tran_so_lenh`** - Tran so lenh cua chuoi (engine: co; 5 bot ngoai dung: ccbsn, bigmouse, black_dragon, bnk, nuti)
- Mo ta: Ngung them lenh khi chuoi dat N lenh (Bigmouse 36, BlackDragon 99, NuTi 9 / 60 / 100, CCBSN InpMax*Orders 5-1000).
- Tham so: InpMaxBuyOrders, InpMaxSellOrders, max order
- Dau van tay trong lich su lenh: Do sau chuoi bi cat o mot gia tri co dinh (nhieu chuoi dung o N). (phep do `chuoi_sau`)
- Engine: luoi.ThamSo.tran_tang. [truong luoi.ThamSo: tran_tang]
- Ap cheo: Khoi nen; quet tran_tang voi cac khoi lot.
- Rui ro: Cham tran ma gia van di nguoc: ket o lot lon.

### THOAT / CHOT - dong chuoi bang cach nao

**`tp_chuoi_tu_gia_tb`** - TP ca chuoi tu gia trung binh (engine: co; 3 bot ngoai dung: ccbsn, hand_dca, nuti)
- Mo ta: Dong ca chuoi khi gia cach gia trung binh X pip (CCBSN InpTPDCA; NuTi quang 2 'hoa von + 0,5 gia'; HandATMX 1 gia).
- Tham so: InpTPDCA, tp pip
- Dau van tay trong lich su lenh: Gia dong cach gia trung binh cua chuoi mot khoang hang so (pip); cac lenh cua chuoi dong CUNG LUC. (phep do `thoat`)
- Engine: luoi.ThamSo.tp. [truong luoi.ThamSo: tp]
- Ap cheo: Khoi nen cua luoi; thay bang chot theo tien / theo RSI de so.
- Rui ro: TP nho: chot thieu khi xu huong that.

**`tp_chuoi_tien`** - TP ca chuoi theo tien (engine: co; 3 bot ngoai dung: bigmouse, hand_atmx, kawkaw46)
- Mo ta: Dong ca chuoi khi tong lai (da tru phi) dat X USD, bat ke gia (Bigmouse 5 USD, HandATMX 10 USD, KawKaw, CCBSN).
- Tham so: tp usd, chot_tien
- Dau van tay trong lich su lenh: Tien thu cua chuoi luc dong gan hang so trong khi khoang cach gia thay doi. (phep do `thoat`)
- Engine: luoi.ThamSo.chot_tien (don vi: tien tren 0,01 lot). [truong luoi.ThamSo: chot_tien]
- Ap cheo: Chuoi dai thi X USD = it pip: thu theo tien vs theo pip.
- Rui ro: Chuoi dai chot som: bo phan lai lon cua xu huong.

**`tp_tung_lenh`** - TP rieng tung lenh (engine: mot_phan; 4 bot ngoai dung: ccbsn, newyear, nuti, signalx)
- Mo ta: Moi lenh co TP rieng (CCBSN InpTP, NuTi quang 1 TP don 2 gia, SignalX TP 2 gia); lenh dong rieng khi gia cham.
- Tham so: InpTP, tp don
- Dau van tay trong lich su lenh: Cot T/P trong bang Orders khac 0; lenh dong boi [tp] tai dung gia TP; khong dong cung luc ca chuoi. (phep do `sl_tp_tung_lenh`)
- Engine: luoi.py chot ca chuoi; chi co tia_cap (dau + cuoi) gan giong. [truong luoi.ThamSo: tia_lenh, bien_cap]
- Ap cheo: TP tung lenh + khong SL = luoi 'ban dai' kieu NuTi quang 1; thu voi 60-100 lenh.
- Rui ro: Lenh sau cung ket lai het: khong co co che gom.

**`tp_treo_len`** - TP treo len (TP dich dan) (engine: chua; 1 bot ngoai dung: black_dragon)
- Mo ta: Khi them lenh, TP cua chuoi duoc dich theo (BlackDragon 'TP trailing treo len').
- Dau van tay trong lich su lenh: Cot T/P cua cac lenh trong chuoi doi gia tri moi khi them lenh (can bang Orders co lenh sua). (khong do duoc tu lenh)
- Engine: luoi.py dat TP tu gia trung binh moi lan.
- Ap cheo: Thuc chat giong tp_chuoi_tu_gia_tb khi TP tinh tu gia tb: co the da nam trong khoi nen.
- Rui ro: Kho tach khoi tp_chuoi_tu_gia_tb neu khong co bang lenh sua.

**`thoat_rsi_va_tb_duong`** - Thoat khi trung binh duong va RSI vuot nguong (engine: chua; 1 bot ngoai dung: gold_hunter)
- Mo ta: Dong ca chuoi khi gia trung binh cua chuoi dang lai va RSI(4) M5 > 50 (GoldHunter), khong dat TP pip / USD.
- Tham so: nguong thoat rsi
- Dau van tay trong lich su lenh: Tien thu khi dong khong co cum co dinh; lenh dong luc gia da qua gia trung binh. (phep do `thoat`)
- Engine: luoi.py khong co chi bao.
- Ap cheo: Thay TP co dinh bang 'thoat khi hoi nhe + RSI het qua ban': thu tren luoi AUDCAD, do chuoi ngan lai bao nhieu.
- Rui ro: Chi bao ve lai tre: thoat muon, nha lai.

**`doi_tp_khi_lo`** - Doi TP khi chuoi dang lo (engine: chua; 1 bot ngoai dung: ccbsn)
- Mo ta: Khi lo cua chuoi vuot X% (CCBSN -5 .. -20%), bot ha muc TP xuong (chap nhan chot it hon de thoat som).
- Tham so: InpUseChangeTPDCA, InpPerLoss2ChangeTP
- Dau van tay trong lich su lenh: Chuoi sau thoat voi lai nho hon chuoi nong cung loai; TP giam theo do sau cua chuoi. (phep do `doi_tp`)
- Engine: luoi.py TP khong doi theo lo.
- Ap cheo: Ke thua cho_lui va tia_cap: kieu 'thoat som khi sau'; thu bang quet_luoi.
- Rui ro: Chot it o dung luc co the hoi manh.

**`tia_cap_sau_dau`** - Tia cap: ghep lenh sau nhat voi lenh dau (khoi CUA TA) (engine: co; 0 bot ngoai dung)
- Mo ta: Ghep lenh sau nhat voi lenh dau tien, dong ca cap khi tong lai cua cap >= bien_cap pip (cat ngan thang bac ma khong cho ca chuoi ve).
- Tham so: bien_cap, cap_moi_bar
- Dau van tay trong lich su lenh: Hai lenh (dau va cuoi) dong cung luc truoc phan con lai cua chuoi. (phep do `thoat_tung_phan`)
- Engine: luoi.ThamSo.tia_lenh, bien_cap, cap_moi_bar (tu LuoiDoiXung.mq5). [truong luoi.ThamSo: tia_lenh, bien_cap, cap_moi_bar]
- Ap cheo: Khoi cua ta; so voi tia_n_lenh_khi_chuoi_dai cua CCBSN / NuTi.
- Rui ro: Engine lac quan ~15% o tia lenh (viec #48): so tren tester that.

**`tia_n_lenh_khi_chuoi_dai`** - Tia N lenh khi chuoi dai (engine: mot_phan; 3 bot ngoai dung: ccbsn, nuti, semi_hft)
- Mo ta: Khi chuoi co >= N lenh, chot rieng M lenh (nang am hoac thap nhat) den khi lai sau tia >= X USD, phan con lai van chay (CCBSN Sniper, NuTi 'tia lenh' N=10 M=2 2,5 USD, SemiHFT Buy chot lenh thap nhat truoc).
- Tham so: InpUseSniper, InpTPSniper, InpMoneySniperFull, InpFirstOrdersSniper, InpLastOrdersSniper
- Dau van tay trong lich su lenh: Co dot dong CHI MOT PHAN chuoi (so lenh dong cung luc < so lenh dang mo), lap lai nhieu lan trong cung chuoi. (phep do `thoat_tung_phan`)
- Engine: tia_cap_sau_dau ghep 1 cap dau-cuoi; chua co tia M lenh theo N. [truong luoi.ThamSo: tia_lenh, bien_cap, cap_moi_bar]
- Ap cheo: Khoi nen thu SOM: CCBSN song sot dung no; mo rong tia_cap thanh tia M lenh khi chuoi >= N.
- Rui ro: Tia lenh tot, giu lenh xau: gia trung binh tien ve phia xau.

**`all_sniper`** - All Sniper: dong tat ca khi lai X USD sau N lenh (engine: chua; 1 bot ngoai dung: ccbsn)
- Mo ta: Sau khi chuoi co N lenh (1-55), neu tong lai >= X USD (1-10) thi dong TAT CA: luat thoat an toan cho chuoi dai (CCBSN).
- Tham so: All Sniper: so lenh, All Sniper: USD
- Dau van tay trong lich su lenh: Chuoi dai (>= N lenh) dong cung luc voi tong tien nho co dinh (1-10 USD). (phep do `thoat`)
- Engine: luoi.py chot_tien khong doi theo so lenh.
- Ap cheo: Mot chot_tien bac thang theo do sau chuoi: thu bang quet_luoi.
- Rui ro: Chot non voi tien nho: mat truong lai khi chuoi dai hoi manh.

**`thoat_theo_thoi_gian`** - Thoat theo thoi gian giu chuoi (khoi CUA TA) (engine: co; 0 bot ngoai dung)
- Mo ta: Dong het chuoi khi no da song >= N gio ke tu luc mo lenh dau, du lai hay lo (time stop).
- Tham so: thoat_gio
- Dau van tay trong lich su lenh: Thoi gian giu chuoi dam o mot gia tri (dong dung N gio sau luc mo) thay vi rai theo luc gia ve. (khong do duoc tu lenh)
- Engine: luoi.ThamSo.thoat_gio (08/10/2026, kieu duong_di): dong o GIA MO cua bar dau tien du N gio; nhan C; EA InpExitHours. [truong luoi.ThamSo: thoat_gio]
- Ap cheo: Quet thoat_gio cung cat_lo_pip: chuoi chua hoi sau N gio co hay hoi nua khong (do duoi cua chuoi lo).
- Rui ro: Dong luc dang lo: lo noi thanh lo that.

### BAO VE / CAT LO / HOA VON

**`sl_cung`** - SL co dinh tung lenh (engine: chua; 3 bot ngoai dung: bigmouse, newyear, signalx)
- Mo ta: Moi lenh co cat lo co dinh (NewYear 2.1 SL ~7 gia, SignalX, Bigmouse SL theo RR 1,3).
- Tham so: sl pip
- Dau van tay trong lich su lenh: Cot S/L khac 0; nhieu lenh dong boi [sl] o khoang cach co dinh. (phep do `sl_tp_tung_lenh`)
- Engine: luoi.py khong co SL tung lenh.
- Ap cheo: Cong cu cho he lenh don (martingale); khong hop voi luoi khong SL.
- Rui ro: Cat lo lien tiep: lot nhan len roi cham SL.

**`cat_lo_theo_tien`** - Cat lo theo tien (chuoi / tai khoan) (engine: mot_phan; 2 bot ngoai dung: bigmouse, nuti)
- Mo ta: Dong het khi am X USD (Bigmouse 'cat am', NuTi 'shot tai khoan' -300 USD, de tat): bien 'khong cat lo' thanh 'cat lo co tran'.
- Tham so: cat am USD, shot tai khoan
- Dau van tay trong lich su lenh: Cum chuoi dong boi [ea] / stopout voi lo gan co dinh -X; hoac tai khoan ve 0. (phep do `thoat`)
- Engine: CAT CA CHUOI theo tien: luoi.ThamSo.cat_lo_tien (08/10/2026, kieu duong_di; nhan C; EA InpCutMoney). Cat theo TAI KHOAN (dung_lo_tong) van KHONG cai dat (luoi.chay tu choi != 0). [truong luoi.ThamSo: cat_lo_tien]
- Ap cheo: Dat tran DD tu truoc (vd 50%) la cach giu maxDD < 80% theo cong cua chu du an.
- Rui ro: Cat dung luc day: mat co hoi hoi phuc.

**`cat_lo_chuoi_theo_pip`** - Cat lo ca chuoi theo khoang cach pip (khoi CUA TA) (engine: co; 0 bot ngoai dung)
- Mo ta: Dong het chuoi khi gia di nguoc >= X pip so voi gia trung binh THEO LOT cua chuoi (tinh lai sau moi tang): cat lo co tran thay vi cho hoi.
- Tham so: cat_lo_pip
- Dau van tay trong lich su lenh: Chuoi lo dong o khoang cach gia gan hang so tu gia trung binh (khong phai o mot so tien co dinh); ban boc vang 08/10 cho thay 36-62% chuoi dong LO. (khong do duoc tu lenh)
- Engine: luoi.ThamSo.cat_lo_pip (08/10/2026, kieu duong_di): khop o dung moc cat (gia nhay qua moc thi o gia nhay); nhan C; EA InpCutPips (khop tung tick voi engine, test_ea_luoi_day_du). [truong luoi.ThamSo: cat_lo_pip]
- Ap cheo: Quet cat_lo_pip tren luoi AUDCAD / vang: tran lo co dinh doi lai ty le thang giam bao nhieu, so voi cat theo tien.
- Rui ro: Cat dung day: chuoi hoi sau do khong con; gia nhay (gap) thi lo that lon hon moc.

**`nghi_sau_cat_lo`** - Nghi sau khi cat lo / thoat gio (khoi CUA TA) (engine: co; 0 bot ngoai dung)
- Mo ta: Sau khi cat lo hoac thoat theo gio, KHONG mo chuoi moi trong M gio (chot loi khong nghi): tranh vao lai ngay luc thi truong dang chay nguoc.
- Tham so: nghi_gio
- Dau van tay trong lich su lenh: Sau chuoi dong LO, khoang trong den chuoi ke tiep dai hon sau chuoi dong LAI. (khong do duoc tu lenh)
- Engine: luoi.ThamSo.nghi_gio (08/10/2026, kieu duong_di); nhan C; EA InpRestHours. [truong luoi.ThamSo: nghi_gio]
- Ap cheo: Chi co nghia khi da bat cat lo hoac thoat gio: thu nghi_gio = 0 / 1 / 4 / 12.
- Rui ro: Nghi qua dai bo lo luc hoi.

**`thoat_hoa_von_khi_chuoi_dai`** - Chap nhan hoa von khi chuoi dai (engine: chua; 1 bot ngoai dung: bigmouse)
- Mo ta: Khi chuoi co N lenh (Bigmouse: 3), bo TP duong va chi dat SL o hoa von: chuoi thoat o 0 thay vi cho lai.
- Tham so: so lenh kich hoat, kich hoat hoa von
- Dau van tay trong lich su lenh: Chuoi dai dong boi [sl] voi tien thu ~ 0 (am nho = phi), khong phai TP duong. (phep do `hoa_von`)
- Engine: luoi.py chi thoat o TP duong.
- Ap cheo: Luat 'cat DD': thu bien N nho / lon tren luoi - doi lai het lai cua chuoi dai.
- Rui ro: Cat het co hoi cua chinh chuoi nguy hiem nhat.

**`keo_sl_hoa_von_khi_co_lai`** - Keo SL ve hoa von khi da co lai (engine: chua; 3 bot ngoai dung: bigmouse, hand_atmx, newyear)
- Mo ta: Khi chuoi co >= N lenh va tong lai > X (USD / gia), keo SL ve hoa von cong them delta (HandATMX 3 lenh / 5 USD / 1 gia; NewYear 2.1 lot 0,08 va lai 2 gia; SemiHFT, Bigmouse 2 gia).
- Tham so: so lenh toi thieu, nguong lai, delta
- Dau van tay trong lich su lenh: Chuoi dong boi [sl] voi tien thu duong NHO (xap xi delta) thay vi TP; xuat hien sau chuoi dai. (phep do `hoa_von`)
- Engine: luoi.py khong co SL.
- Ap cheo: Khoi lap lai o 5 bot: xay mot lan, thu cho moi he luoi.
- Rui ro: Quet sat ngay sau khi dat, mat lai tiem nang (tac gia noi).

**`trailing_stop_chuoi`** - Trailing stop ca chuoi (engine: chua; 1 bot ngoai dung: semi_hft)
- Mo ta: Thoat bang trailing stop tu hoa von (SemiHFT: khong co TP chuoi; lai 2 gia tu hoa von thi dich trailing).
- Tham so: trailing start, trailing step
- Dau van tay trong lich su lenh: Tien thu khi dong bien thien rong (khong cum), dong boi [sl] o gia cao hon gia trung binh. (phep do `hoa_von`)
- Engine: luoi.py khong co.
- Ap cheo: Thay TP co dinh bang trailing: thu tren nhung chuoi hoi manh.
- Rui ro: Cat qua som neu trailing sat.

### BO LOC / LICH - luc nao khong choi

**`loc_spread`** - Loc spread (engine: chua; 1 bot ngoai dung: ccbsn)
- Mo ta: Khong vao / khong them lenh khi spread vuot X point (CCBSN InpMaxSpread 3-500).
- Tham so: InpMaxSpread
- Dau van tay trong lich su lenh: Khong thay duoc tu deal (bao cao khong co spread); gian tiep: khong co lenh vao o gio spread rong (qua dem). (khong do duoc tu lenh)
- Engine: luoi.py dung chi phi spread theo mo hinh, khong loc.
- Ap cheo: Chi phi that cua he luoi (spread rong luc roll-over) la bo loc nhay: thu cho luoi AUDCAD.
- Rui ro: Loc qua chat: bo qua nhip vao tot.

**`loc_gio_giao_dich`** - Loc gio giao dich (engine: mot_phan; 5 bot ngoai dung: ccbsn, bigmouse, black_dragon, newyear, semi_hft)
- Mo ta: Chi cho mo lenh trong cac khung gio (BlackDragon, Bigmouse 'gio mo cua', NewYear 2.1 time trade 1-3, SemiHFT theo ngay, CCBSN lich ngay / gio).
- Tham so: gio bat dau, gio ket thuc, time trade 1-3 (NewYear 2.1)
- Dau van tay trong lich su lenh: Phan bo gio vao lenh dau khong deu: co gio khong bao gio co lenh. (phep do `gio_ngay`)
- Engine: luoi.ThamSo.gio_vao_tu / gio_vao_den (08/10/2026, kieu duong_di): MOT cua so gio (qua nua dem duoc) chi chan MO CHUOI MOI; chua co nhieu cua so (time trade 1-3), loc ngay trong tuan, hay chan them tang. [truong luoi.ThamSo: gio_vao_tu, gio_vao_den]
- Ap cheo: Thu loai gio xau (qua dem / tin) cho luoi: dac trung gio da co trong DSL, do bang quet_luoi sau khi them.
- Rui ro: Quet gio la cach de cai gai: can kiem tren doan xac nhan.

**`loc_ngay_thu_lich`** - Loc ngay / thu / lich (engine: chua; 2 bot ngoai dung: ccbsn, nuti)
- Mo ta: Tranh sang thu Hai, toi thu Sau, dau - cuoi thang, cuoi quy, nua cuoi thang 12, ngay le My (loi khuyen tac gia NuTi); CCBSN co lich.
- Tham so: lich ngay tranh, bat / tat loc lich
- Dau van tay trong lich su lenh: Khoang lang (nhieu ngay khong co lenh vao) lap lai theo lich. (phep do `gio_ngay`)
- Engine: luoi.py khong loc ngay.
- Ap cheo: Gia thuyet kiem duoc bang so lieu dai: cac ngay 'tranh' co that su lam luoi lo? (xem LOI_KHUYEN_VAN_HANH).
- Rui ro: Mau nho theo ngay: de cai gai.

**`loc_tin_tuc`** - Loc tin tuc (engine: chua; 2 bot ngoai dung: ccbsn, black_dragon)
- Mo ta: Tat khi co tin manh (BlackDragon co nhung chua cau hinh; CCBSN v3.0.6 theo thong bao).
- Tham so: news filter
- Dau van tay trong lich su lenh: Khong thay duoc tu deal; gian tiep: lenh vao thua quanh gio tin. (khong do duoc tu lenh)
- Engine: luoi.py khong co lich tin.
- Ap cheo: Can lich tin that (nguon ngoai): chua co trong kho.
- Rui ro: Phu thuoc nguon lich.

**`loc_adx_atr`** - Loc ADX / ATR (do manh xu huong, do bien dong) (engine: chua; 1 bot ngoai dung: ccbsn)
- Mo ta: Dung ADX hoac ATR de khong vao / khong them lenh khi xu huong qua manh hoac bien dong qua lon (CCBSN v3.0.6 theo thong bao).
- Tham so: ADX, ATR
- Dau van tay trong lich su lenh: Chi thay duoc khi co bar gia: lenh vao thua thot khi ADX cao. (khong do duoc tu lenh)
- Engine: luoi.py khong co bo loc.
- Ap cheo: Bo loc che do chinh cho luoi: ADX cao = khong luoi. Thu bang quet_luoi neu kho dac trung co adx.
- Rui ro: Loc qua chat bo lo moi luoi sau nhip manh (chinh la luc lai lon).

**`loc_sideway_nen`** - Loc sideway bang nen (engine: chua; 1 bot ngoai dung: newyear)
- Mo ta: Nhan ra sideway khi 3-4 nen khong thoat duoc vung cua nhau thi tat bot (NewYear, van hanh tay).
- Dau van tay trong lich su lenh: Chi thay duoc khi co bar gia. (khong do duoc tu lenh)
- Engine: luoi.py khong co.
- Ap cheo: Dung cho he theo xu huong (sideway la ke thu); voi luoi thi nguoc lai.
- Rui ro: Do bang mat: kho viet thanh luat.

**`loc_bao_bien_dong`** - Loc bao bien dong (engine: chua; 1 bot ngoai dung: nuti)
- Mo ta: Bao = di 40-60 gia trong 5-10 phut khong hoi (NuTi): chi tha bot SAU bao (gia da di 30-40 gia).
- Tham so: ngay thau, khoang lech
- Dau van tay trong lich su lenh: Chi thay duoc khi co bar gia M1-M5. (khong do duoc tu lenh)
- Engine: luoi.py khong co.
- Ap cheo: Dac trung bien dong ngan (range 5-10 phut / ATR) lam bo loc vao / them lenh; xem DD co giam khong.
- Rui ro: Dinh nghia 'bao' theo cam tinh.

**`loc_dca_tu_lenh_n`** - Loc DCA tu lenh thu N (engine: chua; 1 bot ngoai dung: ccbsn)
- Mo ta: Tu lenh thu N tro di (1-25) moi them lenh neu bo loc (khong ro bo loc nao) cho phep (CCBSN InpUseFilterDCA).
- Tham so: InpUseFilterDCA
- Dau van tay trong lich su lenh: Sau lenh N, nhip them lenh kem deu hoac dai hon cac lenh dau. (phep do `nhip_them_lenh`)
- Engine: luoi.py khong co.
- Ap cheo: Chua biet bo loc la gi: dau van tay tren lich su lenh se goi y.
- Rui ro: Chua ro.

## 5. KHOANG TRONG ENGINE - XAY GI TRUOC

Khoi chua (hoac moi mot phan) co trong `luoi.py`. Thu tu = **o bot song sot truoc**, roi so bot dung. Bot song sot hien nay: ccbsn (tester that, xem muc 2); thu tu nay la GOI Y XAY, khong phai du bao khoi nao ra tien.

| # | khoi | engine | so bot | bot song sot | thieu gi |
|---|---|---|---|---|---|
| 1 | loc_gio_giao_dich | mot_phan | 5 | ccbsn | luoi.ThamSo.gio_vao_tu / gio_vao_den (08/10/2026, kieu duong_di): MOT cua so gio (qua nua dem duoc) chi chan MO CHUOI MOI; chua co nhieu cua so (time trade 1-3), loc ngay trong tuan, hay chan them tang. |
| 2 | tp_tung_lenh | mot_phan | 4 | ccbsn | luoi.py chot ca chuoi; chi co tia_cap (dau + cuoi) gan giong. |
| 3 | tia_n_lenh_khi_chuoi_dai | mot_phan | 3 | ccbsn | tia_cap_sau_dau ghep 1 cap dau-cuoi; chua co tia M lenh theo N. |
| 4 | tran_lot_tong | chua | 3 | ccbsn | luoi.py khong co tran lot. |
| 5 | loc_ngay_thu_lich | chua | 2 | ccbsn | luoi.py khong loc ngay. |
| 6 | loc_tin_tuc | chua | 2 | ccbsn | luoi.py khong co lich tin. |
| 7 | lot_nhan_theo_bac | chua | 2 | ccbsn | luoi.py chi co mot he so; chua co bang moc -> he so. |
| 8 | luoi_buoc_theo_bac | chua | 2 | ccbsn | luoi.py chi co mot buoc + he so; chua co bang buoc theo tang. |
| 9 | all_sniper | chua | 1 | ccbsn | luoi.py chot_tien khong doi theo so lenh. |
| 10 | doi_tp_khi_lo | chua | 1 | ccbsn | luoi.py TP khong doi theo lo. |
| 11 | lenh_doi_ung_sau_n_lenh | chua | 1 | ccbsn | luoi.py hai chuoi chay roi nhau, khong co lenh doi ung trong cung chuoi. |
| 12 | loc_adx_atr | chua | 1 | ccbsn | luoi.py khong co bo loc. |
| 13 | loc_dca_tu_lenh_n | chua | 1 | ccbsn | luoi.py khong co. |
| 14 | loc_spread | chua | 1 | ccbsn | luoi.py dung chi phi spread theo mo hinh, khong loc. |
| 15 | keo_sl_hoa_von_khi_co_lai | chua | 3 | - | luoi.py khong co SL. |
| 16 | sl_cung | chua | 3 | - | luoi.py khong co SL tung lenh. |
| 17 | cat_lo_theo_tien | mot_phan | 2 | - | CAT CA CHUOI theo tien: luoi.ThamSo.cat_lo_tien (08/10/2026, kieu duong_di; nhan C; EA InpCutMoney). Cat theo TAI KHOAN (dung_lo_tong) van KHONG cai dat (luoi.chay tu choi != 0). |
| 18 | gong_duong_doi_ung | chua | 2 | - | luoi.py chot theo ca chuoi, khong giu lenh duong rieng. |
| 19 | lot_nhan_sau_sl | chua | 2 | - | luoi.py la chuoi luoi, khong co lenh don nhan sau SL. |
| 20 | vao_theo_ma | chua | 2 | - | luoi.py khong co tin hieu vao. |
| 21 | lenh_doi_ung_stop | chua | 1 | - | luoi.py chi mo lenh thi truong. |
| 22 | loc_bao_bien_dong | chua | 1 | - | luoi.py khong co. |
| 23 | loc_sideway_nen | chua | 1 | - | luoi.py khong co. |
| 24 | lot_fibo | chua | 1 | - | luoi.py khong co. |
| 25 | lot_tong_gap_doi | chua | 1 | - | luoi.py khong co hai chieu noi voi nhau. |
| 26 | lot_tu_dong_theo_von | chua | 1 | - | luoi.ThamSo.lot la hang so; lot chot ngoai engine (niem_phong_luoi). |
| 27 | luoi_day_khi_gia_hoi | chua | 1 | - | luoi.py chi them lenh khi gia di nguoc them. |
| 28 | luoi_theo_nen_moi | chua | 1 | - | Engine them lenh theo gia trong bar; chua co rang 'toi da 1 lenh / bar'. |
| 29 | nhoi_theo_loi | chua | 1 | - | luoi.py khong co nhoi thuan xu huong. |
| 30 | them_lenh_theo_tin_hieu | chua | 1 | - | luoi.py them theo buoc gia, khong theo tin hieu. |
| 31 | thoat_hoa_von_khi_chuoi_dai | chua | 1 | - | luoi.py chi thoat o TP duong. |
| 32 | thoat_rsi_va_tb_duong | chua | 1 | - | luoi.py khong co chi bao. |
| 33 | tp_treo_len | chua | 1 | - | luoi.py dat TP tu gia trung binh moi lan. |
| 34 | trailing_stop_chuoi | chua | 1 | - | luoi.py khong co. |
| 35 | vao_rsi_qua_ban | chua | 1 | - | luoi.py khong co tin hieu vao; DSL ngu_phap co rsi nhung chi cho lenh don, khong cho chuoi nhoi. |
| 36 | vao_tam_gia_ngay | chua | 1 | - | Can gia mo cua ngay: luoi.py chua co dac trung nay. |
| 37 | vao_theo_xu_huong | chua | 1 | - | luoi.py chi co luoi nguoc xu huong. |

## 6. DE XUAT AP CHEO VAO HE LUOI CUA TA

Menu thi nghiem (khong phai ket luan): khoi nao nen ghep vao he luoi cua ta truoc. `them` = khong dung hang voi khoi dang co; `thay X` = cung loai tru nhau (chon mot).

| # | khoi | kieu | so bot | engine | ly do |
|---|---|---|---|---|---|
| 1 | loc_gio_giao_dich | them | 5 | mot_phan | 5 bot dung (ccbsn, bigmouse, black_dragon, newyear, semi_hft); co o bot SONG SOT (ccbsn); engine: mot phan |
| 2 | tp_tung_lenh | thay tp_chuoi_tu_gia_tb/tp_chuoi_tien | 4 | mot_phan | 4 bot dung (ccbsn, newyear, nuti, signalx); co o bot SONG SOT (ccbsn); engine: mot phan |
| 3 | tia_n_lenh_khi_chuoi_dai | them | 3 | mot_phan | 3 bot dung (ccbsn, nuti, semi_hft); co o bot SONG SOT (ccbsn); engine: mot phan |
| 4 | tran_lot_tong | them | 3 | chua | 3 bot dung (ccbsn, bigmouse, nuti); co o bot SONG SOT (ccbsn); engine: chua |
| 5 | loc_ngay_thu_lich | them | 2 | chua | 2 bot dung (ccbsn, nuti); co o bot SONG SOT (ccbsn); engine: chua |
| 6 | loc_tin_tuc | them | 2 | chua | 2 bot dung (ccbsn, black_dragon); co o bot SONG SOT (ccbsn); engine: chua |
| 7 | lot_nhan_theo_bac | thay lot_phang/lot_cong/lot_nhan | 2 | chua | 2 bot dung (ccbsn, nuti); co o bot SONG SOT (ccbsn); engine: chua |
| 8 | luoi_buoc_theo_bac | thay luoi_gian_cach_deu/luoi_buoc_gian_dan | 2 | chua | 2 bot dung (ccbsn, nuti); co o bot SONG SOT (ccbsn); engine: chua |
| 9 | all_sniper | them | 1 | chua | 1 bot dung (ccbsn); co o bot SONG SOT (ccbsn); engine: chua |
| 10 | doi_tp_khi_lo | them | 1 | chua | 1 bot dung (ccbsn); co o bot SONG SOT (ccbsn); engine: chua |
| 11 | lenh_doi_ung_sau_n_lenh | them | 1 | chua | 1 bot dung (ccbsn); co o bot SONG SOT (ccbsn); engine: chua |
| 12 | loc_adx_atr | them | 1 | chua | 1 bot dung (ccbsn); co o bot SONG SOT (ccbsn); engine: chua |
| 13 | loc_dca_tu_lenh_n | them | 1 | chua | 1 bot dung (ccbsn); co o bot SONG SOT (ccbsn); engine: chua |
| 14 | loc_spread | them | 1 | chua | 1 bot dung (ccbsn); co o bot SONG SOT (ccbsn); engine: chua |
| 15 | keo_sl_hoa_von_khi_co_lai | them | 3 | chua | 3 bot dung (bigmouse, hand_atmx, newyear); engine: chua |
| 16 | sl_cung | them | 3 | chua | 3 bot dung (bigmouse, newyear, signalx); engine: chua |
| 17 | cat_lo_theo_tien | them | 2 | mot_phan | 2 bot dung (bigmouse, nuti); engine: mot phan |
| 18 | gong_duong_doi_ung | them | 2 | chua | 2 bot dung (bnk, semi_hft); engine: chua |
| 19 | lot_nhan_sau_sl | thay lot_phang/lot_cong/lot_nhan | 2 | chua | 2 bot dung (newyear, signalx); engine: chua |
| 20 | vao_theo_ma | thay vao_ngay_lap_tuc | 2 | chua | 2 bot dung (gold_hunter, kawkaw46); engine: chua |

## 7. LOI KHUYEN VAN HANH -> GIA THUYET DO DUOC

Nguoi trinh bay lap lai: bot phai 'lai' (chon ngay tha, tat khi sideway / tin manh / dau cuoi thang). Day la LOI KE, chua phai su that; nhung nhieu y kiem duoc bang so lieu dai cua ta (chia ket qua luoi theo gio / thu / ngay trong thang).

| # | loi khuyen | bot noi | khoi loc | cach kiem |
|---|---|---|---|---|
| 1 | Tranh sang thu Hai va toi thu Sau | nuti | loc_ngay_thu_lich | Chia ket qua luoi theo (thu, gio vao chuoi): nhom 'thu Hai gio dau' / 'thu Sau gio cuoi' co ky vong am hon khong? |
| 2 | Tranh dau - cuoi thang, cuoi quy (30/6, 30/9, 31/12) va nua cuoi thang 12 | nuti | loc_ngay_thu_lich | Chia theo ngay trong thang / quy; so chuoi mo trong cac ngay 'tranh' voi cac ngay con lai tren doan kham_pha, kiem lai tren xac_nhan. |
| 3 | Tranh ngay le My | nuti | loc_ngay_thu_lich | Dung lich ngay le My (du lieu ngoai); so ket qua chuoi mo trong tuan le voi tuan thuong. |
| 4 | Tat khi co 'bao': di 40-60 gia trong 5-10 phut khong hoi | nuti | loc_bao_bien_dong | Dac trung bien dong ngan (range 5-10 phut chia ATR) lam bo loc vao / them lenh; xem DD luoi co giam khi bo cac bar bao. |
| 5 | Sideway: 3-4 nen khong thoat vung cua nhau thi tat bot (voi he theo xu huong) | newyear | loc_sideway_nen | Chi hop he theo xu huong; voi luoi thi dao nguoc: luoi tot hon khi sideway - do ca hai. |
| 6 | Khong tha phien khuya (23h - 2h gio VN) va luc co tin manh | newyear | loc_gio_giao_dich | Voi luoi AUDCAD: gio vao nao co ky vong am? (loc_gio_giao_dich; do tren kham_pha, kiem tren xac_nhan). |
| 7 | Choi phien A / Au, tranh phien My cho DCA vang (BlackDragon) - nhung phien My hop scalp (HandDCA) | black_dragon | loc_gio_giao_dich | Hai loi nguoc nhau: do ket qua luoi theo phien de xem phien nao hop he nao. |
| 8 | 18h - 21h gio VN hay di ngang / dao chieu nen de dinh chuoi DCA dai | hand_dca | loc_gio_giao_dich | Do do dai chuoi theo gio vao chuoi. |

## 8. PHAN LOAI THAM SO .SET THEO TEN

`loai_tu_ten_tham_so(ten)` doan khoi tu TEN tham so (CCBSN `Inp*` va ten pho bien). Chi la goi y de doc bo `.set`; tham so khong xep duoc duoc ghi 'chua xep' de AI doc tay.

## 9. KHONG PHAI GI

- Khong phai danh gia bot: dat / am van do bang `cham_diem` va so tay `nc.db`.
- Khong phai ban sao bot: nhan ban bot = viec #53 (can lich su lenh that + bo `.set` that).
- Bot cu / bot crack co the co ma doc (BAT_DAU_O_NHA.md): chi chay tren tester hoac demo, tat DLL, **khong dua file bot vao git**.

