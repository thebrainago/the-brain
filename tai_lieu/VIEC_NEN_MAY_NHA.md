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

## Danh sach (thu tu = thu tu uu tien)

**N1. Kho bot -> bang co so (tester, Model 1 truoc).** Lap `reports/kho_bot.md` (khong file nhi phan): ten, loai (`.mq5` / `.ex5`),
cac `.set`, nguon, ma + khung tac gia noi (vd vang M15). Moi bot: chay CHINH `.set` cua tac gia tren ma + khung tac gia (Model 1,
`ea_tho_chay` doan kham_pha, MOT `gt_id` cho moi bot; moi `.set` = mot phep thu). Ket qua ghi so tay (`b nc cc ea_tho_chay`).
Xuat bao cao tester `.htm` -> `reports/fixture/tester_<ten>_deals.csv.gz` (+ `_orders_mau.csv`, `.set.txt` neu khong co dong khoa).
`.set` nao DAT (lai sau phi + maxDD < 80%) -> `xac_nhan` DUNG MOT LAN. Khong niem phong.

**N2. Ho so co che tung bot (khong tester).** Voi moi bot co deals trong `reports/fixture/`: chay ho so co che
(`b nc cc ho_so_bot`, khi cong cu do co - xem `nhan/ho_so_bot.py`) -> ghi `reports/ho_so_bot_<ngay>.md` + so tay
(`ghi_hieu_biet`, nhan 'ho so co che'). Doc ket qua tung khoi (co / khong / khong ro / khong do duoc) va ghi **cho nao ho so SAI** so voi
`.set` cua tac gia (bang chung dung nhat de sua bo do).

**N3. Hieu chuan engine <-> tester (no cua moi so lieu luoi).** Bang bien the tren AUDCAD M15, CUNG `ThamSo`: (a) luoi phang,
(b) + he so buoc, (c) + lot cong, (d) + tia lenh. Moi dong: lai %/nam, maxDD, so lenh, BUY/SELL, lenh giu lau nhat; hai cot
(`thu_luoi` engine | `ea_tho_chay` + `ea_LuoiDayDu.mq5` tester). Dong dau tien lech > 10% tuong doi = dong "lech" -> bao cloud sua
engine (`luoi.py`, task #48). Them `do_lech_bar` (`nhan/ea_gia_lap.py`, khong tester) de tach "bar lac quan" khoi "san that".

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
