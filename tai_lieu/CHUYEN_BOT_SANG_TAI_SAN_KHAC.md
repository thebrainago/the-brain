# CHUYEN BOT SANG TAI SAN / KHUNG / THAM SO KHAC (thiet ke, 04/10/2026)

**Trang thai: THIET KE.** Lop dich, kho the phuong phap, bo hoc va bo kiem chung **chua co ma chay** (muc 2 noi ro cai gi da co, cai gi chua). Thu tu lam o muc 13.
Tai lieu nay la cau tra loi cho thong diep (B) cua chu du an 04/10/2026 - phan chu du an goi la *"phan quan trong nhat va quyet dinh rang ta co dang 'hoc' duoc gi hay khong"*.

## 0. TOM TAT CHO CHU DU AN (doc 1 phut)

1. **Cau hoi:** bot chuyen cho vang, muon thu sang cap tien / khung khac / input khac thi lam sao - do het hay do thong minh?
2. **Tra loi: DO THONG MINH, khong do het va khong chep nguyen so.** Do het thi so to hop qua lon va moi o do la mot lan "bat may rui" (hang tram o -> co o tot chi vi may). Chep nguyen so thi sai vi vang va cap tien khac bien do, khac phi, khac don vi.
3. **Cach lam:** doi moi tham so ve don vi khong phu thuoc tai san (vi du: buoc luoi bang bao nhieu lan bien do mot nen; chot loi bang bao nhieu lan chi phi; lot = neu luoi di het do sau thi mat bao nhieu % von). Roi dich sang thi truong moi theo vai cach (giu ti le bien do / giu ti le chi phi / giu "tinh cach" cua bot). Dung engine re do mot luoi NHO quanh cac du doan, cuoi cung chi ~12 ung vien moi chay MT5 tester that.
4. **"Tinh cach" cua bot** do duoc tu lich su lenh: so lenh moi nam, chuoi dai bao nhieu lenh, giu lenh bao lau, bao nhieu % chot lai, luoi vao sau bao nhieu lan bien do... Chuyen sang tai san moi phai GIU tinh cach, khong giu con so.
5. **Moi co che** (hedge, doi TP khi lo, tia, loc gio, diem vao...) tach thanh mot **THE PHUONG PHAP**: mo ta + cac o tham so co kieu + dieu kien dung + bang chung. Dinh nghia nam trong git, bang chung nam trong so tay nghien cuu. Lan sau chi thay so vao the, khong boc lai tu dau.
6. **Biet co "hoc" duoc khong:** do bang BO KIEM CHUNG tren the gioi nhan tao co dap an biet truoc (8 cap, L0-L7). Neu he thong khong tim lai duoc dap an dat san thi no chua hoc gi. Nguong dat duoc ghi TRUOC khi chay.
7. **Trung thuc ve hien trang:** da co 52 khoi co che duoc phan loai, mot phan cac phep do tinh cach, engine quet luoi nhanh, cong cu hieu chuan engine - tester. **Chua co:** lop dich, kho the, bo hoc, bo kiem chung. Cau tra loi "du thong minh chua" hien la **CHUA**, va tai lieu nay noi do dien se do bang cai gi.
8. **Lam tiep:** muc 13 (S0..S5), bat dau bang he don gian (luoi tron) nhieu lan nhu chu du an goi y, tang toc sau. Can may nha: chay tester cho ~12 ung vien moi cap (bot, tai san). Chu du an can quyet: nguon tick (khuyen: KHONG tai Dukascopy), cau hinh moi truong cloud (muc 16).

## 1. CAU HOI CUA CHU DU AN VA TRA LOI NGAN

Nguyen van thong diep (B), bo dau:

> "Hom nay co ca 1 kho bot rat lon cho ban backtest du cac setup va thong so. Nhung cau hoi la vi du cac bot nay chuyen cho gold toi muon chay thu sang cap tien timeframe va input khac thi lam sao? Ta se do het cac thong so hay co cach nao do thong minh dua tren dac diem bot de uoc luong cach danh phu hop khong? Co che boc tach da lam toi dau roi du thong minh chua ? Vi du cac co che hedge co che thoat lenh hoac diem vao lenh cua 1 Ea tot ta de tach ra thanh co che rieng va sau bo sung vao cac phep thu duoc khong ? Phan nay se la phan quan trong nhat va quyet dinh rang ta co dang 'hoc' duoc gi hay khong nen hay lam ki, co the thu tren cac he thong va tai san don gian nhieu lan roi moi tang toc cung duoc. Khi do cang test duoc nhieu ta cang hoc duoc nhieu va cang day dan kinh nghiem hon. Phan nao nay can co co che boc tach va luu tru ra thanh cac phuong phap, sau nay de tai su dung thi se su dung lai va thay so vao. Nhu the ta se hoc duoc tu chien luoc giao dich da co loi nhuan + phuong phap va ki thuat cua EA + cac tai lieu phuong phap cong khai + chi bao duoc ket hop vao nhau."

| # | Cau hoi | Tra loi ngan | Muc |
|---|---|---|---|
| Q1 | Do het thong so hay do thong minh? | Thong minh: doi ve don vi khong thu nguyen, dich theo cac "bat bien" co ten, quet luoi RUT GON tren engine, tester chi cho top-k. Khong bao gio quet khong gian tham so tho. | 8, 9 |
| Q2 | Co che boc tach da toi dau, du thong minh chua? | Chua. Co kho 52 khoi + phep do mot phan + cong cu hieu chuan. Thieu lop dich, kho the, bo hoc. Do thong minh bang bo kiem chung L0-L7, khong bang cam tinh. | 2, 11 |
| Q3 | Tach hedge / thoat / vao thanh co che rieng roi bo sung vao phep thu duoc khong? | Duoc: mot co che = mot THE (git) + mot khoi engine tat mac dinh + hai loai phep do (cat khoi ngay trong bot bang .set; them khoi vao he khac theo cap A/B). | 7, 12 |
| Q4 | Luu thanh phuong phap de sau thay so vao? | The phuong phap co O THAM SO co kieu va lop dich; "thay so" = dien o bang gia tri da dich cho thi truong dich. | 7, 8 |
| Q5 | Hoc tu: chien luoc co loi nhuan + ky thuat EA + tai lieu cong khai + chi bao ket hop? | Bon nguon vao CUNG mot kho the; to hop = ghep the vao nhau qua rang buoc `can` / `xung_dot`, moi to hop la mot phep thu dem du. Chi bao di qua HEPHAESTUS (rai luoi tham so). | 12 |
| Q6 | Thu tren he don gian nhieu lan roi moi tang toc? | Dung: S2 chay luoi tron (engine da khop tester o luoi tron) tren nhieu cap / khung truoc khi dung bot phuc tap. | 13 |

## 2. DA CO GI, CON THIEU GI (doi chieu voi ma that, 04/10/2026)

| Thanh phan | Tep | Lam duoc | Con thieu |
|---|---|---|---|
| Kho khoi co che | `nhan/khoi_co_che.py` + `tai_lieu/KHO_CO_CHE_BOT.md` (sinh tu ma) | 52 khoi (VAO 8, TANG 12, LOT 10, THOAT 9, BAO_VE 5, LOC 8); trang thai engine: co 13, mot_phan 2, chua 35, ngoai 2; `khoang_trong_engine()` xep 37 khoang trong; `de_xuat_ap_cheo()`; `loai_tu_ten_tham_so()` | O THAM SO co kieu / don vi / lop dich; bang chung dang trong nc.db |
| Ho so bot | `nhan/ho_so_bot.py` (WIP, chua qua test day du) | Mot phan phep do tren lich su lenh (buoc, tien trinh lot, phu moi tang...) | Cac phep do con lai (chuoi sau, thoat, doi TP, tran lot tong, hoa von, nhip them lenh, gio trong ngay); registry `PHEP_DO`; bao cao bang loi thuong |
| Ho so tai san | `nhan/ho_so_symbol.py` | Tinh cach thi truong (hurst, vr2, vr10, ac1, er), bien dong (atr_pct_bar, bien_do_bar_pct, bar_moi_nam), phi (spread_bps, phi qua dem, vong quay toi da) | Khoang cach nguon - dich; do sau thi truong E(H,q) (muc 6.4) |
| Chuyen he sang khung khac | `nhan/ngoai_sinh.chuyen` | Giu TY LE KICH HOAT cua nguong chi bao (phan vi), khong giu con so | Chi cho he DSL (chi bao); khong biet khoang cach luoi / lot / thoi gian |
| Quet luoi tren engine | `nhan/nc_thi_nghiem.quet_luoi` | Toi da 6 truc, <= 1000 o, chi doan kham_pha, ~11,6 ms mot o (nhan C, 190k nen M15) so voi 578 ms Python; nhan hinh dang CAO_NGUYEN / CAI_GAI / HON_HOP / KHONG_CO_LAI | Truc phai la danh sach gia tri DON, doc lap: **khong dien duoc truc ghep** (dich dong thoi buoc va tp). Can ham anh em nhan DANH SACH O cu the (muc 15) |
| Hieu chuan engine - tester | `nhan/hieu_chuan_luoi.py` (da test) | Mot lan goi = nua tester (co nho) + nua engine + hang so sanh KHOP / LECH; thuoc do tin cay cua buoc sang loc | Ket qua THAT tu may nha (bac thang 8 bac dang cho tester) |
| Engine luoi | `nhan/luoi.py` (`ThamSo` 17 truong) | Luoi tron khop tester (B1: tester +0,26%/nam, engine +0,24%/nam) | Lech xa o tn5 (tia + cong lot + he so buoc): tester -3,24%/nam, engine +33,8%/nam (viec #48); 35 khoi chua cai |
| The gioi nhan tao co dap an | `nhan/nc_du_lieu.tong_hop` (`TONG_HOP_<KICH_BAN>_<HAT>`: NHIEU, HOI_QUY, HOI_QUY_YEU, LOC, XU_HUONG, BETA) | Co dap an cho **tin hieu vao** | Khong co the gioi cho luoi / chi phi / khung / hedge (muc 11) |
| Hephaestus | `nhan/hephaestus.py` | De co che: rai luoi tham so, ghep nut | Chua noi voi kho the |

**Ket luan:** vat lieu tho da du de lam S0-S2 ma khong dung them nguon / engine moi. Cai THIEU la phan "nao" - dich, the, hoc, kiem chung - dung la cai chu du an noi.

## 3. NGUYEN TAC

1. **Giu TINH CACH, khong giu SO.** Con so o vang vo nghia o AUDCAD; hanh vi (chuoi dai bao nhieu, giu bao lau, sau bao nhieu lan bien do) moi la cai can giu.
2. **Moi cach dich la mot GIA THUYET co ten** (bat bien I1..I6). Dich co the sai; do duoc, so sanh duoc, ghi vao so tay.
3. **Do re truoc, do that sau.** Engine chi dung de LOAI va XEP HANG, KHONG de tuyen bo DAT. Do tin cay cua engine = bang hieu chuan; engine chua cai co che nao thi co che do KHONG duoc xep hang bang engine.
4. **So phep thu la TIEN.** Moi o luoi tieu mot phep thu cua dong gia thuyet; luoi rut gon, khai bao truoc (co `plan_hash`), diem = cao nguyen (trung vi vung lan can) chu khong phai o tot nhat.
5. **Hoc chi tu doan kham_pha.** `xac_nhan` va `niem_phong` khong bao gio vao bo hoc (neu vao thi doan xac_nhan het doc lap).
6. **Am tinh phai kem MDE; "khong do duoc" khac "am".** Dich xuong duoi nguong phan giai cua bar (buoc / bien do nen < 2,0) thi engine tra CHUA_DO_DUOC, khong tra AM.
7. **Kiem chung bang the gioi dap an biet truoc truoc khi tin ket qua that.** Qua bo kiem chung la dieu KIEN CAN, khong phai du.
8. **Khong ep.** The khong du dieu kien dung thi bao CHUA_DO_DUOC kem ly do (`KHONG_AP_DUOC: ...`), khong chay tuy tien.

Ba trang thai ket qua giu nguyen nhu luat chung (DAT / AM / CHUA_DO_DUOC); `KHONG_AP_DUOC` chi la LY DO cua CHUA_DO_DUOC, khong phai trang thai thu tu.

## 4. DUONG ONG

```
 bot: file EA (.ex5 / .mq5) + cac bo .set + lich su lenh + loi tac gia
   |
   v  1 BOC        do tren lich su lenh (ho_so_bot) + doc .set (ea_tho.doc_set) + kho khoi (khoi_co_che)
   v  2 CHUAN HOA  moi tham so -> LOP + don vi ; lich su -> VAN TAY tinh cach ; tai san -> vector thi truong
   v  3 THE        moi co che -> the phuong phap (git) ; bang chung (nc.db)
   v  4 DICH       the + thi truong dich -> tham so dich, theo vai bat bien I1..I6 (+ so w)
   v  5 DO         luoi rut gon tren engine -> top-k -> tester Model 0 (kham_pha) -> xac_nhan (MOT lan)
   v  6 HOC        hang (bot, nguon, dich, cach dich, ket qua) -> luat -> bang "lop tham so x khoang cach -> cach dich tot"
   ^_______________________________________________________________________________| (lan sau bat dau tu du doan da hoc)
```

**Vi du minh hoa (SO GIA DINH de de hieu, KHONG phai so do):** bot vang co buoc luoi 400 diem, vang di mot nen M15 tam 160 diem. Buoc = 2,5 lan bien do mot nen. Tren cap tien mot nen chi di 14 diem, buoc 400 diem la vo nghia (thanh "mot lan nam gia 28 nen"). Chep ti le: 2,5 x 14 = 35 diem. Nhung phi cap tien la 25 diem: buoc 35 diem bi phi an gan het. Phai co **san chi phi** va phai biet **chuoi lenh co vuot noi do sau ma thi truong nay thuong ra** khong. Do la ly do can nhieu bat bien (bien do, chi phi, do sau) chu khong chi mot cong thuc.

## 5. BUOC 1 - BOC

### 5.1 Ba nguon va thang bang chung (cao -> thap)
1. **DO** tren lich su lenh that (`lenh_tester.vi_the_tu_tep` -> `ho_so_bot`): chieu dai chuoi, buoc thuc te, he so lot thuc te.
2. **.set** (ten + gia tri tac gia dat; `ea_tho.doc_set`): muc `K` trong kho khoi.
3. **Ma nguon cua ta** (`N`), thong bao nhom (`T`), video (`V`), gia dinh (`G`).

DO thang .set thang loi tac gia. Mau thuan thanh muc rieng: *"tac gia noi X, lenh that cho thay Y"* - bao chu du an bang loi thuong, khong tu chon ben nao.

### 5.2 Doc cheo cac bo .set cua CUNG mot bot
CCBSN co 10 bo .set (theo von 10K, 500, 50...), CLMCA co 5 bo. Cac bo nay la **thi nghiem tu nhien ve cach chinh tac gia tu thu nho / phong to bot**: tham so nao doi theo von, doi theo ti le nao, tham so nao giu nguyen. Day chinh la mot vi du cua bat bien I4 trong tay tac gia - du lieu mien phi, co san, khong can chay tester. `ho_so_bot` phai co phep do `so_sanh_bo_set` (lop tham so + ti le doi giua cac bo).

### 5.3 Dau ra cua BOC
Mot `ho_so_bot` (JSON) gom: danh sach khoi phat hien (co the nhieu, moi khoi co muc bang chung), tham so do duoc, **van tay tinh cach** (muc 6.3), va muc mau thuan. Dang bao cao bang loi thuong 3-8 dong cho chu du an (`viet_bao_cao`).

### 5.4 Thuc te con thieu
`ho_so_bot.py` moi co mot phan phep do. Bot nhi phan (.ex5) khong doc duoc ma: chi co .set + lich su lenh; "nhan ban" la suy doan, khong phai chep. Viec #50 / #52 trong danh sach.

## 6. BUOC 2 - CHUAN HOA

### 6.1 Lop tham so (mot tham so thuoc DUNG mot lop)

| Lop | Vi du | Don vi chuan | Dich mac dinh |
|---|---|---|---|
| KC_BUOC | `buoc`, `buoc_tran`, `cho_lui` (la khoang cach pip, khong phai thoi gian) | A (bien do mot nen) | I1 / I2 pha tron (so w) |
| KC_TP | `tp`, tp sau N lenh | A va C | I2 nghieng, san >= 3 C |
| KC_SL | cat lo, hoa von, trailing | A | I1 |
| TAM | tran_tang x buoc (co he so buoc) | E(H,q) do sau thi truong | I6 (giu bien do an toan) |
| SO_DEM | `tran_tang`, `bien_cap`, `cap_moi_bar`, tia sau N lenh | khong thu nguyen | giu so; TAM duoc kiem lai |
| HE_SO | `he_so_lot`, `he_so_buoc` | khong thu nguyen | giu nguyen |
| LOT | `lot`, lot cong | % von mat khi luoi di den do sau E(H,q) | I4 (ngan sach rui ro) |
| TIEN | `chot_tien`, "All Sniper X USD", nguong hoa von | % von | theo (lot x khoang cach x gia tri diem) |
| THOI_GIAN | gio phien, so nen cua chi bao, tre tinh bang phut | gio dong ho hoac so nen | I5 (hai ung vien) |
| NGUONG_CHI_BAO | RSI < 30, ADX > 25 | phan vi (ti le kich hoat) | `ngoai_sinh.chuyen` (giu ti le kich hoat) |
| PHI | tran spread cho phep vao lenh (`InpMaxSpread`) | C (chi phi mot vong) | I2 (nhan ti le chi phi, doi sang point cua ma dich) |
| CONG_TAC | `che_do`, `kieu_lot`, `tia_lenh`, `muc_stopout`, `don_bay` (thuoc tai khoan) | - | giu nguyen |

Co **12 lop** (them PHI so voi ban thiet ke dau: tran spread khong thuoc loai khoang cach nao khac). Khoa `.set` khong phan loai duoc bang ten / gia tri duoc de o `CHUA_PHAN_LOP` (khong tu doan: vi du `InpPlus` - cong lot hay cong buoc? - o ca hai bo CCBSN).

**Luat mot-lop:** MOI truong cua `luoi.ThamSo` va moi o tham so cua mot the phai co mot lop; test se dung neu them truong moi ma khong phan lop (chong "quen" am tham). Truong `ThamSo` da khai bao nhung engine khong doc (`luoi.CHUA_CAI_DAT`) khong duoc dua vao truc quet - quy tac nay `quet_luoi` da co.

### 6.2 Ba dai luong thi truong dung chung (don vi: gia)
```
A      = trung vi (high - low) cua nen            (ho_so_symbol: bien_do_bar)
C      = chi phi mot vong (spread + hoa hong + truot, do that, khong khai)    (config/chi_phi_do.json)
E(H,q) = phan vi q cua do lech lon nhat trong H nen lien tiep (do sau thi truong)
pv     = gia tri mot don vi gia cua mot lot, quy ra tien tai khoan             (luoi_quy_cach / MT5)
```
`E(H,q)` la dai luong MOI, tinh **chi tu gia** (khong can chien luoc) tren doan kham_pha cua (ma, khung): "trong thoi gian ma bot thuong giu mot chuoi, thi truong nay thuong day gia di xa bao nhieu". Day la cai quyet dinh song / chet cua luoi / DCA / martingale.

### 6.3 Van tay tinh cach (do tren lich su lenh, don vi khong thu nguyen)
Ten du kien (khop voi phep do `ho_so_bot`):
- `nhip`: so chuoi moi 100 nen va moi nam; `huong`: ti le BUY.
- `buoc_A`, `tp_A`: buoc / chot loi chia A.
- `chuoi_sau`: trung vi, p90, max so lenh trong mot chuoi.
- `do_sau_A`: do lech xau nhat cua chuoi chia A; `do_sau_E`: chia E(H,q).
- `giu_gio`: trung vi, p90 thoi gian giu chuoi (gio dong ho va so nen).
- `ti_le_tp`: ti le chuoi dong bang TP so voi bi cat / hoa von.
- `lai_lo_A`: lai trung binh / lo trung binh, tinh theo A.
- `tien_trinh_lot`: lot lenh thu n chia lot lenh dau; lot lon nhat.
- `rui_ro_von`: tien se mat o do sau p90 / von.

Khoang cach van tay: tong |log(ti so)| co trong so cho cac dai luong duong, |hieu| cho cac ti le; trong so dong bang trong `config/chuyen_nguong.json`. "Giu tinh cach" = khoang cach <= nguong ghi truoc.

### 6.4 Vector thi truong va khoang cach
Tu `ho_so_symbol` + `E`: `log A_pct`, `C / A` (phan phi trong mot nen), hurst, vr2, vr10, ac1, er, duoi (kurtosis), carry (swap / A), do sau lich su (so nam). **Khoang cach g = dich - nguon** tung thanh phan. g nho -> du doan tu tin; g lon (nhat la khac ve hoi quy o dung chan troi cua bot) -> bao `CANH_BAO_KHOANG_CACH`, ta uu tien it o hon va tester nhieu hon (muc 9).

### 6.5 Dieu kien dung (kiem TRUOC moi phep dich)
- Du lieu sau du (>= N nam) va du lenh (>= 20 lenh moi o) tren doan kham_pha.
- Chi phi do duoc (`cp.do_tin` khong phai `KHAI`).
- **Phan giai:** buoc dich / A_dich >= 2,0 (`NGUONG_PHAN_GIAI`); duoi nguong chi tester do duoc, engine tren bar tra CHUA_DO_DUOC.
- Lot dich >= lot toi thieu va khong vuot ky luat stop-out / don bay cua tai khoan.
- Lop quy cach biet (`luoi.lop_quy_cach` khong phai `khong_ho_tro`); **tai san co dong tien yet gia khac dong tai khoan** (vi du AUDCAD yet bang CAD) phai co phep quy doi dung (ban chat cua nghi van #48: lech don vi).
- Swap: chuoi giu rat lau (tn5 giu den ~3,8 nam!) ma carry cua phia chu dao am manh thi gan co `CANH_BAO_CARRY`.

## 7. BUOC 3 - THE PHUONG PHAP

### 7.1 Kho
- **Dinh nghia** nam trong git: `kho_phuong_phap/<ma>.json`, gieo ban dau tu 52 khoi cua `khoi_co_che`.
- **Bang chung** nam trong `nc.db` (bang `the_bang_chung`), xuat ra git bang `b nc xuat` -> `so_cai/nc/`. Phan "bang chung tom tat" trong the **sinh tu bang chung**, khong sua tay.

### 7.2 Dang the
```
{
 "ma": "lenh_doi_ung_sau_n_lenh",
 "loai": "TANG",                    # VAO | TANG | LOT | THOAT | BAO_VE | LOC | CHI_BAO | QUAN_LI
 "ten": "Mo lenh doi ung sau N lenh (hedge khi sau)",
 "mo_ta": "mot cau mot dong, ngon ngu thuong",
 "tham_so": [                       # cac O de "thay so vao"
   {"ten": "n_kich_hoat", "lop": "SO_DEM", "don_vi": "lenh", "mien": [3, 12, 1], "ten_trong_set": "<ten tac gia>", "ten_trong_engine": null},
   {"ten": "ti_le_lot_doi", "lop": "HE_SO", "mien": [0.5, 2.0, 0.25]},
   {"ten": "tp_doi", "lop": "KC_TP", "don_vi": "A", "mien": [0.5, 4.0, 0.5]}
 ],
 "can": ["co_chuoi_lenh_cung_chieu"],           # dieu kien tien quyet (khoi / tinh chat)
 "xung_dot": [],                                # khoi khong di cung
 "tuong_tac_biet": [],                          # tuong tac da do duoc (nhat the, khong mo ta chung chung)
 "vet": ["chuoi_sau", "huong"],                 # phep do trong ho_so_bot lo ra khoi nay
 "engine": {"trang_thai": "chua", "co": ["<truong ThamSo tat mac dinh>"], "nhan_c": false, "ea_mq5": false},
 "nguon": [{"bot": "ccbsn", "muc": "K", "tham_chieu": "..."}],
 "dieu_kien_dung": ["phan_giai", "lot_toi_thieu"]
}
```
Gia tri trong vi du chi de lam ro CAU TRUC; gia tri that doc tu `.set` bang `ea_tho.doc_set` luc BOC, khong dien tay.

### 7.3 Bon loai nguon, mot kho
1. **Khoi cua bot co loi nhuan** (muc 5) - the `khoi`.
2. **Ky thuat EA** (cach quan li lenh cua bot) - the `QUAN_LI`.
3. **Tai lieu phuong phap cong khai** - qua SEEKER -> `ngu_phap` (kien thuc moi chi vao qua ngu phap, khong `exec` ma LLM sinh) -> the voi o tham so.
4. **Chi bao** - qua HEPHAESTUS (rai luoi tham so); thanh the `CHI_BAO`, nguong thuoc lop NGUONG_CHI_BAO.

### 7.4 "Thay so vao"
`dich(the, nguon_ctx, dich_ctx, ...)` tra ve gia tri cho TUNG O cua the o don vi cua thi truong dich (muc 8). Cung the sinh truc cho luoi rut gon (moi o co `mien` va lop). Lan sau gap bot moi dung khoi cu thi KHONG boc lai: chi thay so.

## 8. BUOC 4 - DICH

### 8.1 Cac bat bien (moi cai la mot cach dich, co ten)

| Ten | Giu nguyen cai gi | Cong thuc (khoang cach d, don vi gia) |
|---|---|---|
| I1 ty le bien do | d / A | `d_dich = d_nguon * A_dich / A_nguon` |
| I2 ty le chi phi | d / C | `d_dich = d_nguon * C_dich / C_nguon` |
| pha tron | giua I1 va I2 | `d_dich = d_nguon * (A_dich/A_nguon)^(1-w) * (C_dich/C_nguon)^w`, w trong [0,1] |
| I3 van tay | tinh cach (muc 6.3) | tim nhan chung s cho cac khoang cach sao cho khoang cach van tay dich - nguon nho nhat (tim 9 diem nua-quang-tam tren engine) |
| I4 ngan sach rui ro | % von mat o do sau | `lot_dich = lot_nguon * (L_nguon / von_nguon) / (L_dich / von_dich)`, L = thua lo (tien) cua CA chuoi o do sau E(H,q) |
| I5 dong ho / so nen | thoi gian that hoac so nen | `n_dich = n_nguon * T_nguon / T_dich` (giu gio dong ho) hoac `n_dich = n_nguon` (giu so nen); lay CA HAI lam ung vien |
| I6 bien do an toan | tam / E(H,q) | `tam_dich = tam_nguon * E_dich(H_dich,q) / E_nguon(H_nguon,q)`; so tang tinh lai tu buoc dich va he so buoc |
| TIEN | tien / (lot x d x pv) | `m_dich = m_nguon * (lot_dich*d_dich*pv_dich) / (lot_nguon*d_nguon*pv_nguon)` |

Quy tac chung: **chan duoi** `d >= 3 C_dich` (khong nho hon ba lan chi phi mot vong); chan phan giai `d >= 2 A_dich` (neu thap hon thi chi tester do duoc). Mac dinh co so (se bi bo hoc ghi de, muc 10): buoc `w = 0`, chot loi `w = 0,5`, tam theo I6, lot theo I4.

### 8.2 Thu tu dich mot bot luoi / DCA
1. Tinh `A, C, E, pv` cua dich (chi tu doan kham_pha).
2. Dich khoang cach (buoc, tp, sl) -> theo 8.1 + chan.
3. Dich TAM theo I6 -> suy ra so tang `tran_tang` tu buoc moi va `he_so_buoc`.
4. Dich lot theo I4, kiem lot toi thieu + ky luat stop-out.
5. Dich TIEN (chot tien, hoa von) theo (lot x d x pv).
6. Dich THOI_GIAN: sinh hai ung vien (giu gio / giu so nen).
7. Gom thanh danh sach <= 9 **cach dich co so** (tich cua cac lua chon con nghi ngo), moi cach dich kem nhan "vi sao" bang loi thuong.

### 8.3 Van tay lam NHAN, khong dung loi nhuan (y tuong cot)
Moi cap (bot, tai san dich) cho ra mot nhan **khong can loi nhuan**: nhan chung `s_I3` ma van tay khop nhat tren engine. Co `s_I3` thi so voi `s_I1`, `s_I2`, ... ta biet bat bien nao du doan dung cho lop tham so nao. Nhan nay **re, nhieu mau, khong dinh da phep thu loi nhuan**; con loi nhuan (it mau, dat tien) la trong tai cuoi cung. Han che trung thuc: khop tinh cach khong bao dam co lai (lai den tu tinh cach NHAN thi truong); chi khop duoc tren phan engine mo phong duoc (35 khoi chua cai -> khop mot tap con), nen **bat buoc doi chieu tren top-k bang tester**.

## 9. BUOC 5 - DO THONG MINH

### 9.1 Cac tang
| Tang | Lam gi | Ngan sach | Tai nguyen |
|---|---|---|---|
| 0 Dieu kien | muc 6.5; khong dat thi dung, ghi ly do | 0 | khong |
| 1 Du doan | <= 9 cach dich co so (muc 8.2) | 0 | khong |
| 2 Luoi rut gon | 4 truc khong thu nguyen quanh du doan: nhan khoang cach s (5 gia tri, nua-quang-tam), pha tron w (0 / 0,5 / 1), tam (x0,7 / x1 / x1,4), lot theo ngan sach rui ro (x0,5 / x1 / x2) = 5x3x3x3 = 135 o moi du doan | ~400 o toi da | engine (nhan C) ~5 giay |
| 3 Thu hep | giu 25% o tot nhat **theo diem cao nguyen**, thu hep luoi (khoang cach / 2), lap <= 2 vong | ~40 o | engine |
| 4 Tester top-k | <= 12 ung vien khac NHAU (cac cao nguyen khac nhau, khong phai 12 o ke nhau), Model 0, chi doan kham_pha | <= 12 lan tester | tester (mot cai duy nhat) |
| 5 Xac nhan | moi o song sot qua tester: `xac_nhan` DUNG MOT LAN theo dong gia thuyet | 1 | theo luat chung |

Tester chay theo **thu hep dan**: truoc het cho ca k tren khoang ngan (~12 thang cua kham_pha), chi top 4 moi chay het doan - tiet kiem gio tester (thoi gian chay tester ~tuyen tinh theo do dai doan, xem bac thang hieu chuan).

### 9.2 Diem cao nguyen (chong "o may man")
Diem cua mot o = **trung vi vung lan can 3x3** (hai truc quan trong nhat) cua `lai_pct_nam` voi dieu kien maxDD < 80% va >= 20 lenh. Chon cao nguyen, khong chon dinh nhon (CAI_GAI = gai: bo). Day la cach giam thien lech "tot nhat trong N o".

### 9.3 Luat dem phep thu
- Mot dong gia thuyet = `chuyen:<bot>:<tai san dich>`; moi khung them vao CUNG dong (thu 3 khung = nhan do da phep).
- Moi o luoi / moi lan tester la mot phep thu; luoi, quy tac thu hep, ngan sach khai bao truoc (co `plan_hash`) khi mo dong gia thuyet.
- Luoi rut gon <= ~500 o moi (bot x dich x khung): neu du doan da hoc tot thi luoi **hep hon, it o hon** (xem duong cong hoc, muc 10.4).

### 9.4 Do tin cay cua engine trong tang 2-3
Engine duoc tin **theo lop o** chi khi `hieu_chuan_luoi` cho KHOP o lop do. Luoi tron: khop (B1). Tia / cong lot / he so buoc (tn5): lech xa. Vi vay ket qua engine cua o co co che da lech duoc danh dau `engine_chua_tin`, tang 3 khong duoc dung no de loai, va ngan sach tester tang len. Do **tuong quan hang** (Spearman) engine - tester tren top-k duoc ghi vao bao cao: thap -> khong tin xep hang engine cho lop nay (viec #48).

## 10. BUOC 6 - HOC

### 10.1 Hang du lieu
Moi lan chuyen xong ghi mot hang `chuyen_hang` (nc.db, xuat `so_cai/nc/chuyen_hang.jsonl`): bot (the), nguon, dich, khung, cach dich da dung (bat bien + w cho tung lop), `s_I1`, `s_I2`, `s_I3`, `s_chon`, khoang cach van tay, ket qua engine, ket qua tester, tuong quan hang, nhan (DAT / AM / CHUA_DO_DUOC kem ly do), vector khoang cach g. **Chi hang kham_pha duoc dua vao bo hoc.**

### 10.2 Cai gi duoc hoc
1. **Bang "lop tham so x khoang cach -> cach dich tot"** (nho: ~12 lop x vai dac trung g): hoi quy ben (Theil-Sen / Huber) co co ve (ridge) ve phia mac dinh (b=1, c=0 tuc la I1 thuan) - voi it mau, **co ve ve cai prior tot hon la thoi phong**.
2. **Luat ve nhan `s_I3`**: `log s_I3 ~ a + b log(A_dich/A_nguon) + c log(C_dich/C_nguon) + d * (khoang cach hoi quy) + ...`
3. **Gia tri bien cua khoi** (muc 12.1): khoi nao dang tien trong bot nao.

### 10.3 Kiem dinh (chong tu lua)
- Roi-mot-tai-san-ra (leave-one-asset-out): luat chi duoc tin neu **sai so du doan tren tai san bi giu lai < baseline I1 thuan** it nhat bien do ghi truoc.
- Hang < 30: bang van la **prior**, khong goi la "da hoc"; bao cao ghi so hang va khoang tin cay.
- Luat phai tai tao duoc dap an cai san o the gioi L1-L3 (muc 11) truoc khi duoc dung tren du lieu that.

### 10.4 Duong cong hoc (thuoc do cuoi cung)
Xep cac lan chuyen theo thoi gian. Neu he thong thuc su hoc thi **so o can den cao nguyen** va **so lan tester den ket qua tot** phai GIAM dan khi co them hang, o cung muc hoi tiec (regret) vs dap an. Bo kiem chung do duong cong nay tren chuoi chuyen nhan tao; neu duong cong phang thi "hoc" chua co that.

## 11. BO KIEM CHUNG (the gioi nhan tao co dap an biet truoc)

### 11.1 The gioi
`nhan/thu_chuyen.sinh_the_gioi(loai, hat, so_nam, khung)`: gia cong tinh tren M1 (chuoi tong hop gia tri GARCH + duong di con 8 buoc nhu `nc_du_lieu.tong_hop` de high/low la cuc tri that), roi gop thanh khung can; gom phi, swap, hop dong. **Dap an tinh duoc**: gia cong tinh (cong) de moi khoang cach gia nhan dung k lan; hoac **oracle** = quet day tren duong gia rat dai (100 nam) cua the gioi do mot lan, khong co da phep thu vi do la dap an chu khong phai phat hien.

### 11.2 Cac cap

| Cap | The gioi | Dap an cai san | Kiem cai gi |
|---|---|---|---|
| L0 | nguon = dich | dich == nguon, khoang cach van tay 0, engine bang nhau tung bit | ong dan (khong can hoc) |
| L1 | tang bien do nhan k (0,5 / 2 / 4), phi nhan k | moi khoang cach nhan k; lot nhan 1/k; ket qua tien KHONG DOI | dung bat bien I1, phep don vi, engine bat bien theo ti le |
| L2 | cung bien do, phi nhan m (2 / 4) | san chi phi cat vao buoc/tp; oracle cho toi uu moi | dung I2, chan duoi |
| L3 | M1 -> M15 / H1; the gioi dinh nghia theo GIO DONG HO (OU nua doi gio) va the gioi dinh nghia theo SO NEN (AR moi nen) | the gioi dong ho -> giu gio; the gioi so nen -> giu so nen | I5: chon dung bat bien theo loai the gioi |
| L4 | hoi quy YEU hon o dich (nua doi dai hon tam luoi) | oracle: lai nho hoac am; he phai tra "khong co lai" / giam tam | I6 + khong ep (khong DAT gia) |
| L5 | xu huong / drift (luoi phai thua) | AM | ti le DAT gia |
| L6 | the gioi co dung mot khoi B (vd doi TP khi lo hoac hedge) co hieu ung biet truoc | bot = luoi tron + B | BOC tim dung B tu LENH (khong tu tham so); ap cheo B len bot khac tai hien huong va do lon hieu ung |
| L7 | hai khoi co tuong tac biet truoc (hedge + doi TP) | tuong tac khac 0 | phat hien tuong tac; khong bao tuong tac gia khi cong tinh |

### 11.3 Doi chung (baseline) va chi so
- **B0** chep nguyen so; **B1** chi I1; **B2** quet ngau nhien cung so o engine (ngan sach ngang nhau).
- **M1** hoi tiec tuong doi so voi oracle (trung vi tren 30 hat); **M2** ti le DAT gia tren the gioi khong co lai (L5, NHIEU); **M3** so lan tester dung (<= 12); **M4** tuong quan hang engine - dap an tren the gioi (o co oracle); **M5** duong cong hoc (muc 10.4).
- "Thong minh hon quet het" chi duoc noi neu **thong minh thang B2 o ngan sach ngang** voi khoang tin cay bootstrap cua hieu nam duoi 0, tren L1-L5 gop.

### 11.4 Nguong DE XUAT (dong bang truoc khi chay lan dau, o S1)
Dat trong `config/chuyen_nguong.json` co `version` + `sha256`; lan chay dau ghi hash vao so tay; doi nguong sau do = **version moi**, bao cao ghi ca hai (khong doi nguong de qua).
- L0: bang nhau tuyet doi.
- L1: |log(s_tim / k)| <= 0,12; ket qua tien khop trong 3%.
- L2-L4: hoi tiec trung vi <= 0,15; thong minh <= 0,8 x hoi tiec B2.
- L5 / NHIEU: ti le DAT gia sau xac_nhan <= 0,05; o tang ung vien (truoc xac_nhan) <= 0,25.
- L6: BOC dung khoi voi precision >= 0,8 va recall >= 0,8; huong hieu ung dung >= 90% hat, do lon sai <= 30%.
- L7: phat hien tuong tac (> 2 sai so chuan) >= 80% hat co tuong tac; tuong tac gia <= 10% hat khong co.
Day la **de xuat**, chu du an / phien nghien cuu duyet truoc khi dong bang. Dung nguong lam cong chan tuyet doi (luat 25/09: nhan canh bao khong phai cong chan); chung la de **biet co hoc duoc khong**.

### 11.5 Chi phi
Mot hat the gioi: ~400 o engine ~5 giay (nhan C) + 1 phep danh gia hold-out. Oracle: mot lan moi loai the gioi, vai tram o tren duong rat dai, vai phut. Tat ca chay duoc tren cloud (khong can MT5, khong can tester).

## 12. AP DUNG CHEO, TAI LIEU CONG KHAI, CHI BAO

### 12.1 Do gia tri khoi NGAY TRONG con bot (cat khoi bang .set) - viec re nhat, gia tri cao nhat
Cac bot nhu CCBSN co cong tac bat / tat trong .set (lenh doi ung sau N lenh, tia, doi TP khi lo, loc DCA...). Chay **cung bot, cung doan, chi tat MOT khoi** tren tester (Model 0) cho ra **gia tri bien that cua khoi trong chinh bot** (khong can viet ma). Moi khoi <= 2 lan chay (bat va tat), ghi vao bang chung cua the. Day tra loi thang cau "yeu to dac sac cua bot nam o dau", va khong phu thuoc do tin cay cua engine.

### 12.2 Them khoi vao he khac (A/B ghep cap)
He nen B vs B + khoi X, **cung nen, cung phi, cung doan**, do hieu so (lai, maxDD) - tren engine khi engine da co khoi X, tren tester neu khong. Khoi chua co trong engine phai duoc **cai truoc**: ky luat nhu moi khoi moi - truong `ThamSo` TAT MAC DINH, nhan C, tham so trong EA luoi day du, mot bac hieu chuan. Thu tu cai dat theo `khoang_trong_engine()` voi uu tien cho khoi cua **bot song sot** (hien chi CCBSN) roi den khoi nhieu bot dung. Hien: loc gio giao dich (5 bot), TP rieng tung lenh (4, mot phan), tia N lenh khi chuoi dai (3, mot phan), tran lot tong (3), loc ngay / thu / lich (2), loc tin tuc (2), he so lot doi theo bac (2), buoc theo bac (2), All Sniper, doi TP khi lo, lenh doi ung sau N lenh... (mot bot). Day mo rong `luoi.py` (tat mac dinh) chu khong phai engine moi.

### 12.3 Tai lieu phuong phap cong khai
SEEKER tim -> `ngu_phap` (khong `exec` ma LLM sinh) -> the voi o tham so (lop duoc gan theo bang ten -> lop; ten la thi gan `CHUA_PHAN_LOP` de nguoi / LLM xem xet, khong tu doan).

### 12.4 Chi bao
HEPHAESTUS rai luoi tham so; moi chi bao la mot the `CHI_BAO` (loai VAO); nguong dich bang `ngoai_sinh` (giu ti le kich hoat); the do chi chay tren bo kiem chung va tren (ma, khung) nho truoc.

### 12.5 To hop
Ghep the nay vao the kia qua `can` / `xung_dot`; chi thu to hop do `de_xuat_ap_cheo` goi y hoac do bo kiem chung da xac nhan co hieu ung; moi to hop la mot phep thu tinh du vao dong gia thuyet.

## 13. LO TRINH

| Buoc | Lam gi | Xong khi | Ai chay | Phu thuoc |
|---|---|---|---|---|
| **S0** | `nhan/dich_tham_so.py` (dai so don vi, 12 lop, bat bien I1-I6, chan, E(H,q)); luat mot-lop; `quet_o` | test don vi: dong nhat, quy luat ti le, chan; moi truong ThamSo co lop | cloud (co test) | can duoc chay test |
|  | **TRANG THAI 05/10/2026:** phan DICH xong (`dich_tham_so.py`, 840 dong), kiem bang script tam 36 phep + 13 phep thu dot bien (xem muc 13.1); **chua** co `test_dich_tham_so.py` chay bang pytest (che do quyen), **chua** co `quet_o` | | | |
| **S1** | the gioi L0-L3 + bo kiem chung + doi chung B0-B2 + dong bang nguong; chay chi engine | L0 bang nhau; L1 tim lai k; bang so sanh thong minh vs B0-B2 | cloud | S0 |
| **S2** | **he don gian that, NHIEU lan:** luoi tron (B1) tren AUDCAD -> NZDCAD, USDCHF, AUDNZD, EURGBP... o M15 va H1; engine rut gon + tester top-4; ghi hang | >= 30 hang; tuong quan hang engine - tester; thong minh vs I1 thuan tren DU LIEU THAT | cloud + may nha (tester) | S1; bac thang hieu chuan #56 |
| **S3** | `ho_so_bot` xong; van tay that cua CCBSN / CLMCA; nhan `s_I3` vang -> FX; **cat khoi bang .set** (12.1); bang hoc v0 | van tay co that; gia tri bien cua cac khoi cua CCBSN; bang v0 voi ghi so hang | cloud + may nha | #50, #52 |
| **S4** | cai khoi vao engine theo thu tu uu tien (12.2) + do A/B + bac hieu chuan cho moi khoi | moi khoi: khop tester o lop do hoac ghi ro lech | cloud + may nha | #48 |
| **S5** | to hop + tai lieu cong khai + chi bao qua HEPHAESTUS; bao cao "hoc duoc gi" theo lop tham so | bang hoc khoi dau co khoang tin cay; bao cao 3-8 dong cho chu du an | cloud + may nha | S3, S4 |

### 13.1 S0 da kiem nhu the nao (05/10/2026, khong dung pytest)

Mot script tam (`tai_lieu/ban_va_chua_test/kiem_dich_tham_so.txt`, chay: `python3 kiem_dich_tham_so.py` tu thu muc goc sau khi doi duoi) cho:
- 36 phep kiem, deu dat. Co 4 phep neo vao ENGINE THAT chu khong chi vao cong thuc cua chinh module: (a) lo treo dinh cua `luoi.chay_mang` tai tang n khop `hinh_rui_ro` voi 5 kieu luoi (lot phang / nhan / cong, buoc co gian, tran buoc) x mua / ban x n = 3, 7, 12; (b) vang -> AUDCAD: sau khi dich theo I4, lo treo dinh tinh theo % von cua engine hai ben bang nhau trong 2% (con "giu lot" thi lech > 50%); (c) E(H,q) khop vong lap ngay tho; (d) I6: cung mot duong gia, M15 -> H1, giu gio dong ho ra he so tam ~1 con giu so nen ra ~2 (dung luat can bac hai).
- 13 phep thu dot bien (sua co y mot dong trong ban sao cua module) - ca 13 deu bi bat: bo san 3C, doi dau I4, dao mu pha tron, ha nguong phan giai, lech cua so E, sai mu buoc / lot, dao ti le I6, hong gop trung, nham huong TIEN, bo lot toi thieu, thieu mot lop, dich so nen mac dinh. (Ban dau 1/13 lot luoi: nguong phan giai - da them diem kiem nam giua hai phia 2,0.)
- Han che da biet: engine tren bar chi tin cay khi moi khoang cach >= 2 lan bien do nen; duoi nguong `engine_do_duoc = False` (chi tester do duoc). `dung_lo_tong` dat != 0 cung gan co do vi `luoi.py` chua cai dat. Gia tri diem `pv` va von phai cung dong tien; voi tep `.set` dung dong tien tai khoan.

**Duong gang:** hieu chuan engine (#56) nam tren duong gang cua S2 - chua biet engine dang tin duoc o dau thi sang loc bang engine la mu. Vi vay thu tu tester cua may nha da xep ngay sau CLMCA (xem `VIEC_NEN_MAY_NHA.md`).

## 14. GIOI HAN TRUNG THUC

- **Khop tinh cach khong dam bao co lai.** Loi nhuan cua bot co the den tu vi cau truc vang (phi, swap, nhip), khong chuyen duoc. Ket qua "khong co lai o tai san dich" la ket qua HOP LE, khong phai that bai cua he thong.
- **Engine tren bar lac quan o tia / chot_tien** (~15% theo #48; tn5 lech xa) - moi quyet dinh ve co che do do phai qua tester. Chi luoi tron (B1) hien duoc tin.
- **It mau.** 17 bot, trong do chi vai bot co lich su lenh that; hang hoc se it. Moi luat phai vuot kiem dinh roi-mot-tai-san-ra; duoi 30 hang chi la prior.
- **Bot nhi phan (.ex5) la hop den.** Chi doc duoc .set va lich su lenh; ban nhan ban cua ta co the khac o chi tiet ma khong biet.
- **Mot tester duy nhat** quyet dinh toc do: <= 12 lan / cap (bot, tai san). Thu hep dan de tiet kiem gio.
- **Da phep thu.** Moi o la mot phep thu; luoi rut gon + cao nguyen + khai bao truoc + `xac_nhan` mot lan la ba tang chong; khong xoa duoc hoan toan.
- **Tick that chi tu ~2024-01 (FX) / ~2025-09 (vang)**; bot nhay vi cau truc (tia, hoa von) chi kiem tra duoc bang Model 4 tren doan gan day.
- **The gioi nhan tao chi thu duoc cai ta nghi ra.** Qua L0-L7 la dieu kien can, khong phai du.

## 15. MODULE VA CONG CU DU KIEN (`dich_tham_so.py` da co ma 05/10; con lai chua)

| Tep | Vai tro |
|---|---|
| `nhan/the_phuong_phap.py` | dang the, doc / ghi kho, gieo tu `khoi_co_che`, bang chung tom tat sinh tu nc.db |
| `nhan/dich_tham_so.py` | **DA CO** - lop tham so, dai so don vi, bat bien I1-I6, chan, E(H,q), dich + bao cao "vi sao" |
| `nhan/do_thong_minh.py` | xay luoi rut gon, thu hep dan, chon top-k khac nhau, ke hoach tester (khong tu chay tester), dem phep thu + `plan_hash` |
| `nhan/thu_chuyen.py` | the gioi L0-L7, doi chung B0-B2, chi so M1-M5, kiem hash nguong |
| `nhan/nc_thi_nghiem.quet_o` | ham anh em cua `quet_luoi` nhan DANH SACH O cu the (truc ghep); `quet_luoi` goi lai no - **hoi quy giu nguyen** |
| nc cong cu | `chuyen_bot` (dich + ke hoach), `ke_hoach_do` (luoi rut gon + ngan sach, khong chay), `luu_the` (ghi the / bang chung), `thu_chuyen` (chay bo kiem chung) |
| du lieu | `kho_phuong_phap/*.json`, `config/chuyen_nguong.json` |
| test | `test_dich_tham_so.py`, `test_do_thong_minh.py`, `test_thu_chuyen.py`, `test_the_phuong_phap.py` (dap an cai san, doi chung am, dot bien ban: sua co y phai bi bat) |

Dang ky vao `nhan/kien_truc.py` o lop "NHA NGHIEN CUU - AI nam quyen". Khong mo them nguon / engine moi: lop dich dung `quet_luoi`, `hieu_chuan_luoi`, `ho_so_symbol`, `ngoai_sinh`, `khoi_co_che` co san; mo rong `luoi.py` tat mac dinh (12.2) la **mo rong, khong phai engine moi**.

## 16. CAN AI LAM GI

**Chu du an (khong gap rut, khong chan S0-S2):**
1. Nguon tick: khuyen **khong** tai Dukascopy; sang loc bang Model 0, kiem lai nhom song sot bang tick XM that tren doan gan day.
2. Moi truong cloud: Network access -> Custom them `api.ai-box.vn` va bien moi truong `AIBOX_API_KEY` (khoa chi nam trong cai dat moi truong, khong bao gio dan vao chat hay repo); chi phien MOI moi nhan. Chua bat buoc cho S0-S2 (khoi kiem chung la ma, khong can LLM).
3. De cloud chay duoc test cho S0 tro di: doi che do quyen khoi che do tu dong hoac mo phien moi.

**May nha** (khi co hang doi): tester cho S2 (top-k), ho so that cua CCBSN / CLMCA (S3), thong so symbol that (hop dong, gia tri diem, swap) cho cac cap se thu - hien `luoi_quy_cach.json` chi co XAUUSD va USDJPY (+ AUDCAD dac biet, lop `fx_chuan` theo cong thuc cho cap khac).

**Cloud** (khong can ai): S0, S1, viet the, viet nguong de xuat, bao cao.

*Lich su: 04/10/2026 ban thiet ke dau tien (thong diep B cua chu du an). Cap nhat khi xong tung buoc S0-S5.*
