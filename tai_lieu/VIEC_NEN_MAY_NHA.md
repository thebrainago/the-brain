# VIEC NEN CUA MAY NHA - hang doi thuong truc (chu du an 04/10/2026)

Chu du an: *"May nha can chay toi uu va khong nen de trong viec ... can luon chay khong de trong chu khong phai ngoi cho"*.
Luat day du: `CLAUDE.md` muc "MAY NHA CHAY LIEN TUC, TUAN TU, KHONG NGOI CHO". File nay la **viec tu lam khi khong co don
cloud danh so nao dang cho** (thu tu uu tien: don cloud danh so -> viec dang do -> file nay). Cloud co the SUA file nay
(them / bot / doi thu tu) - nho `git pull` truoc khi doc.

## Cach lam (cho phien nha co LLM; bo chay khong-LLM chi lam don danh so)

1. Di tu N1 xuong N6, MOI LAN lam mot "mot lat" (1 viec nho, chay xong trong <= 1-2 gio), ghi 3-8 dong vao `reports/nen_may_nha.md`
   (ngay gio | viec | xong / chua / ket o dau | so chinh | can gi tu cloud / chu du an), roi sang lat ke tiep NGAY.
2. Muc het viec (khong con gi moi lam duoc) -> ghi "het" vao nhat ky, nhay muc ke. Het ca sau muc -> gui cloud MOT thu
   (`--chu-de "het viec nen"`), trong luc cho lam `b nc kiem 30` + `b test` (hoi quy) roi lap lai tu N1. KHONG ngoi cho.
3. Luc tester chay (1 viec tester mot luc): lam viec KHONG dung tester (N2, N5, N6 hoac viet bao cao) - dung ngoi canh tester.
4. Khong bao gio: niem phong, dung tai khoan THAT, dua file `.ex5/.ex4/.dll/.exe` vao git, ghi khoa / mat khau / so dien thoai / so tai khoan
   vao repo, vuot 403 / 429 / captcha (dung o ten mien do), mo nguon moi khi chua co DAT o xac_nhan.

## THU TU TESTER do cloud xep (04/10 toi) - dung truoc danh sach duoi

Tester chi co MOT lan (mot `terminal64.exe`) nen cloud xep thu tu; luc mot viec tester chay thi lam viec KHONG tester (cuoi muc nay), xong viec nao sang viec ke NGAY.
Thu #11 van hieu luc: KHONG niem phong, KHONG tai tick moi (Dukascopy...).

- **T1. CLMCA o MODEL 0** (muc tieu cuoi: tim thu dang ra tien). Lan khao sat truoc chay Model 1 (OHLC 1 phut); luat cua lab: Model 1 noi doi khi TP < 2 lan
  bien do M1 nen duong o Model 1 chua phai duong - Model 1 chi dung de LOAI (am o Model 1 thi chac am). Lam: `ea_tho_chay` doan kham_pha, `model` 0 (sua
  `config/ea_tho.json` hoac tro `EA_THO_CFG` toi ban sao), BO `tick_tu` (Model 0 sinh tick tu M1, khong can tick that, khong duoc cat cua so), cua so kham_pha day du
  nhu lan Model 1, CUNG `gt_id`, `bo_set` NGUYEN VAN cho **D_V1** va **L07S** (ba bo C_* lai be: bo qua). `.set` nao con DAT o Model 0 (lai sau phi + maxDD < 80%) ->
  `xac_nhan` DUNG MOT LAN o Model 0 (cung model + von). Khong con DAT -> `ghi_hieu_biet` "Model 1 lac quan: <so Model 1> -> <so Model 0>" (bang chung quy mo lech).
- **T2. Hieu chuan engine <-> tester** (N3, bac thang): ngay sau T1.
- **T3. N1 con lai** (cac bot khac cua kho): Model 1 chi de LOAI; bot nao duong thi chay lai Model 0 truoc khi goi la "co lai".

**Viec KHONG tester** (lam trong luc tester ban, theo thu tu):
1. Xuat deal cua lan tn5 DA CHAY (AUDCAD M15 kham_pha 2018-01-02..2023-07-02, gt_id 4, 2828 lenh) -> `reports/fixture/tester_tn5_deals.csv.gz` +
   `tester_tn5_orders_mau.csv` (200 dong dau) + `tester_tn5_tham_so.txt`: cloud so voi engine TUNG LENH khong ton them tester (huong sua #48). Bao cao cu da bi ghi de
   thi bo qua - bac 5 cua N3 cho cung bo deal (`reports/hieu_chuan/<van tay>_lenh.csv.gz`, chep sang fixture).
2. `ea_gia_lap.do_lech_bar` tren bar M15 that cua AUDCAD kham_pha voi tham so tn5, ba thu tu duong di trong bar (O-H-L-C, O-L-H-C, xau nhat) ->
   `reports/do_lech_bar_tn5.md` (nho: bar KHONG do duoc buoc luoi nho hon bien do bar).
3. N5 (chi phi that), `reports/kho_bot.md` (khong nhi phan), roi N2 khi cong cu `ho_so_bot` co.

## Danh sach (thu tu = thu tu uu tien)

**N1. Kho bot -> bang co so (tester).** Lap `reports/kho_bot.md` (khong file nhi phan): ten, loai (`.mq5` / `.ex5`), cac `.set`, nguon, ma + khung tac gia noi
(vd vang M15). Moi bot: chay CHINH `.set` cua tac gia tren ma + khung tac gia (`ea_tho_chay` doan kham_pha, MOT `gt_id` cho moi bot; moi `.set` = mot phep thu).
**Model 1 chi de LOAI**; bo nao duong thi chay lai Model 0 (xem T1) truoc khi goi la "co lai". Ket qua ghi so tay (`b nc cc ea_tho_chay`).
Xuat bao cao tester `.htm` -> `reports/fixture/tester_<ten>_deals.csv.gz` (+ `_orders_mau.csv`, `.set.txt` neu khong co dong khoa).
`.set` nao DAT o Model 0 (lai sau phi + maxDD < 80%) -> `xac_nhan` DUNG MOT LAN. Khong niem phong.

**N2. Ho so co che tung bot (khong tester).** CONG CU DA CO (05/10): `b nc cc ho_so_bot`. Voi moi bot co deals trong `reports/fixture/`:
`python b.py nc cc ho_so_bot '{"lenh":"reports/fixture/<deals>.csv.gz","bo_set":"reports/fixture/<bo>.set.txt","ma":"GOLD.i#","ten":"<ten>","them":[{"lenh":"...","bo_set":"...","ten":"..."}]}'`
(`them` = cac cap {lenh, bo_set, ten} nua cua CUNG bot de so sanh cac `.set` voi nhau; chi tep trong thu muc du an). Cong cu ghi MOT dong so tay
(doan 'ho_so', khong an phep thu, cung van tay thi dung dong cu) + bao cao ASCII `reports/ho_so/*.md` (bo chay don mang ve cho cloud).
Moi khoa `.set` ra DUNG MOT ket qua; hai loai dang gia nhat cho ban: **MAU_THUAN** (tac gia khai mot dang, lenh that cho thay dang khac -
KHONG chon ben nao, ghi nguyen van) va **nut an** (co che co trong lenh ma khong tham so nao dieu khien). Doc xong ghi `ghi_hieu_biet`
(nhan 'ho so co che') **cho nao ho so SAI** so voi `.set` cua tac gia (bang chung dung nhat de sua bo do). Bang chung mau: `reports/ho_so_bot_that_20261004.md`.
Khi co them `.set` cua cung bot (CLMCA co 5): dua tat ca vao MOT lan chay (`them`) de `so_sanh_bo_set` thanh thi nghiem tu nhien.

**N3. Hieu chuan engine <-> tester (no cua moi so lieu luoi) - BAC THANG (cloud xep lai 04/10 toi).** Cong cu MOT LENH: chay CHINH `ea_LuoiDayDu.mq5` tren tester +
engine CUNG ThamSo tren CUNG cua so (>= 14 ngay, trong doan kham_pha) roi tra KHOP / LECH + canh bao chan doan (ro ket, ty le SELL, do sau theo thoi gian, he so quy doi
tien bao gia, swap...); khong an phep thu (doan 'hieu_chuan', so_phep_thu 0); nua tester duoc nho theo (tham so + cua so + model + von) nen doi engine khong phai chay lai tester:
`python b.py nc cc hieu_chuan_luoi '{"ma":"AUDCAD","khung":"M15","tu":"2018-01-03","den":"<den>","tham_so":<TS>,"model":0,"von":10000,"han_giay":<giay>}'`
Dau ra dai ~200 dong: **ghi ra tep UTF-8 `reports/hieu_chuan_tay_<bo>_<den>.json` (bash: `> tep`; PowerShell: `| Out-File -Encoding utf8 tep`) va `git add` tep do** - bo chay don
khong-LLM chi mang ve 25 dong cuoi; cloud doc tep qua `git pull`.
Bo tham so (cloud da kiem tren `luoi.ThamSo` + `tham_so_ea_tu_luoi`, deu hop le):
  a `{"buoc":60,"tp":40,"tran_tang":10,"lot":0.01}` luoi phang | b = a + `"he_so_buoc":1.2` | c = b + `"kieu_lot":"cong","he_so_lot":0.25,"lot":0.04`
  d `{"buoc":21,"tp":9,"tran_tang":9,"kieu_lot":"cong","he_so_lot":0.25,"lot":0.04,"he_so_buoc":1.2,"tia_lenh":true,"bien_cap":5}` (= tn5) | e = d + `"chot_tien":3`
Bac thang (cua so bat dau 2018-01-03, ngan -> dai, MOT LENH moi bac):
  1 d ..2018-06-30 (han_giay 1800) | 2 d ..2018-12-31 (3600) | 3 d ..2019-12-31 (3600) | 4 d ..2021-06-30 (7200) | 5 d ..2023-06-30 (7200)
  6 a ..2019-12-31 (3600) | 7 a ..2023-06-30 (7200) | 8 e, c, b o cua so 2022-01-03..2022-06-30 (1800 moi cai).
  Bac nao het `han_giay` (CHUA_DO_DUOC) -> chay lai voi han_giay gap doi, KHONG doi tham so. Chay HET 8 bac, khong dung o bac LECH dau tien: cloud can DUONG CONG lech theo
  do dai cua so (diem lech dau tien chi la mot diem). Sau moi bac ghi 5 dong vao `reports/nen_may_nha.md` (bac | KHOP/LECH | lai/nam tester vs engine | DD | so lenh |
  canh bao dau tien | `ky_lech_dau_tien`). Het 8 bac -> MOT thu `XONG hieu chuan ...` cho cloud (<= 12 dong). Them `do_lech_bar` (`nhan/ea_gia_lap.py`, khong tester) de
  tach "bar lac quan" khoi "san that". `"lam_lai_tester":true` chi de ep chay lai nua tester da nho; ha tang chet (CHUA_DO_DUOC) tu chay lai o lan goi sau.

**N4. Chuyen bot sang tai san / khung khac (khi cong cu `chuyen_bot` co).** Bot tot nhat (hien chi con CCBSN v2.6 + "Can Cu Bo 10K 2.7"
va vai `.set` CLMCA): lay ke hoach do thong minh (`b nc cc chuyen_bot`), chay Model 1 tren cap / khung moi theo thu tu cloud xep
(it phep thu truoc, tang dan), ghi **ty le thu / dung** vao so tay de bo hoc "he so dich" (tai_lieu/CHUYEN_BOT.md khi co).

**N5. Chi phi + du lieu that cua XM.** Do chi phi that moi ma dang dung (spread theo gio, swap, hoa hong) -> `reports/chi_phi_xm_<ngay>.md`;
cap nhat `data/` (parquet) cho cac ma trong N1/N3; kiem nguon tick that (XM chi co tu 2024-01, vang tu 2025-09): ghi do phu tick tung
doan. Hang tuan: `b may` (den XANH/VANG/DO) + kiem slot tester (`config/slot_tester*`).

**N6. Lich su lenh nguoi thang (chi nguon DA MO).** Lam tiep `tai_lieu/NGUON_NGUOI_THANG.md` buoc A -> B (chay nguyen file cua ho,
lich su winners) theo nhip 5,5 giay / lan, dung o 403 / 429; luu moc "da toi trang N". Xong thi chay `b nc cc mo_xe_lenh` tren lich su moi.
Khong mo nguon moi (luat: chua co DAT o xac_nhan).

## Nhat ky tien do (do nha ghi)

`reports/nen_may_nha.md`, moi lat mot khoi 3-8 dong, moi nhat tren cung. Cloud doc bang `git pull` roi mo file nay - khong can thu.
