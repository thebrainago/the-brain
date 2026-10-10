# VONG LAP KHEP: tim -> boc -> kiem -> giu -> ap dung (chu du an 10/10/2026)

Chu du an nhac lai (10/10/2026): *"muc tieu cua the brain la VONG LAP lien tuc: tim nguon chien luoc / he thong chat luong => boc tach co che
=> kiem dinh => giu lai va chon loc co che hieu qua => ap dung va bo sung vao cac vong ve sau. Viec ta dang lam chi la nhung module nho."*

Nghia la: dung toi uu tung nhanh (gia lap, bo kiem luat backtest, mot con bot). Phai co MOT vong chay lien tuc, va moi chang cua vong
phai DO duoc. Truoc moi viec tu hoi: viec nay dua chang nao cua vong lai gan hon, hay chi lam dep mot nhanh?
(Khong nham voi `vong_lap.py` doi v1 da hu tri o `nghi_huu/`: day la module moi, o `nhan/vong_lap.py`.)

## 1. Bang diem (lam truoc moi phien)

```
python3 b.py vong-lap --in          # chi xem (alias: b vl --in)
python3 b.py vong-lap               # xem + ghi reports/VONG_LAP.md va reports/vong_lap/*
python3 b.py vong-lap --giao 240    # + ra toi da 240 don kiem ngoai mau / kiem lai engine moi / ap dung vao viec/cho (KHONG push)
python3 -m nhan.vong_lap --json     # day du dang JSON
```

Module khong trang thai: moi con so suy ra tu `viec/xong` + `viec/cho` + `viec/may` (git). Khong LLM, khong du lieu gia, khong ghi `nao.db`.
Nguoi goi `--giao` phai tu `git add viec/cho reports/vong_lap` + commit + push.

| chang | la gi | cong cu `nc cc` / don | de xuat ty le gio may |
|---|---|---|---|
| TIM | nguon chien luoc / he chat luong moi (dien dan, MQL5, link, SEEKER) | `yeu_cau_seeker`, `b dien-dan`, `b link` | 10% |
| BOC | boc co che tu nguon (ho so bot, ho so `.set`, ho so tai san) | `ho_so_bot`, `ho_so_set`, `ho_so_tai_san` | 10% |
| KIEM | kiem dinh: TRONG MAU (kham_pha) roi NGOAI MAU (xac_nhan) | `quet_luoi`, `thu_luoi`, `ea_tho_*` ... | 50% (it nhat 1/3 la ngoai mau) |
| GIU | giu lai + chon loc co che qua kiem o nhieu thi truong | `vl-gh-*`, `ghi_hieu_biet` | 5% |
| AP DUNG | nap nguoc: quet chuyen thi truong / khung lan can, yeu cau SEEKER nguon cung loai | `vl-tf-*`, `vl-sk-*` | 15% |
| HA TANG | hieu chuan, do engine, don dep (khong thuoc vong nhung an gio may) | `hieu_chuan_luoi` ... | 10% |

Ty le de xuat la `DICH` trong `nhan/vong_lap.py` (chu du an sua duoc).

## 2. Do 10/10/2026 (truoc khi co vong): vong KHONG khep

Tren 1.573 viec / 105 gio may cua may nha: 84% gio may la quet trong mau; 16% hieu chuan (HA TANG); TIM 0,2%; BOC ~0; GIU 3 viec vat;
AP DUNG 0; kiem NGOAI MAU = 0 viec. 698 vung lai (cao nguyen, 880 lan khai) chua lan nao duoc kiem ngoai mau. Moi luot quet dung engine
v3 (lac quan 15-55% so voi EA that). Dieu nay dung voi muc tieu cua chu du an: chi chay mot khuc cua vong, khuc de do ra con so dep.

## 3. Cach kiem (chang KIEM -> GIU) va vi sao co nhom doi chung

- Moi vung lai cua mot luot quet -> don `vl-xn-<id>`: `nc cc thu_luoi` tren doan `xac_nhan` (doan MO: khong tinh phep thu, khong tieu FDR).
  KHONG BAO GIO tao don `niem_phong` (niem phong la quyet dinh co chu dich cua cloud, mot lan cho moi khai bao dong bang).
- **Nhom doi chung** (de do xem buoc loc "cao nguyen" co hon boc tham khong - tranh *winner's curse*):
  `doi` = o tot nhat cua luot quet KHONG phai cao nguyen (~12% don); `ngau` = mot o ngau nhien cung luoi voi moi vung lai (cu 4 vung lai 1 o).
  Chon ngau nhien theo hat giong co dinh (cung dau vao -> cung o), nen co the tai lap.
- Ket qua moi don duoc doc tu 25 dong cuoi cua `viec/xong` (`TOM_TAT {json}` la dong cuoi moi; dong cuoi cu van doc duoc, bi cat thi
  danh dau KHONG_DO_DUOC). **KHONG_DO_DUOC khong bao gio tinh la QUA hay RUOT.** QUA = co lai sau phi, khong chay tai khoan,
  >= 10 lenh o tai lot da thu; RUOT = ket luan duoc va khong dat.
- Co che = `che_do|kieu_lot|lui/-`. **Nhan GIU**: qua xac_nhan o >= 3 thi truong VA >= 50% trong >= 5 ket qua ket luan duoc. Day la NHAN,
  khong phai cong chan. `so_voi_nen` = HON_NEN / NGANG_NEN / CHUA_BIET (so voi nhom doi chung). `san_sang_niem_phong` chi bat khi co ket qua
  tu engine >= 4 (engine v3 lac quan).

### Cach doc ket qua: ke hoach DONG BANG truoc khi co ket qua nao (10/10/2026)

Khi 1.022 don kiem ngoai mau tra ve, `nhan/vong_lap.so_sanh_nhom` tra loi HAI cau hoi (nguong la hang `SO_SANH_*`, khong doi sau khi nhin so):

1. **Chon o TOT NHAT trong luoi co hon chon BUA mot o cung luoi khong?** (`cao_vs_ngau`, ghep cap, McNemar chinh xac mot phia.) Neu KHONG hon:
   3.000 o quet khong them gi so voi thu vai o -> dem gio may sang chieu rong (them thi truong, co che), khong quet sau.
2. **Luot quet duoc xep CAO NGUYEN co ben hon luot quet khac khong?** (`cao_vs_doi`, hai nhom doc lap, Fisher chinh xac mot phia, chi so sanh o tot nhat
   cua moi ben.) Neu KHONG: cach xep cao nguyen khong du bao gi, dung dung no lam bo loc duy nhat.

- Ket luan: **HON** = chenh >= 10 diem va p < 0,05 (mot phia); **KEM** = nguoc lai; **CHUA_DU** = it hon 20 cap / 20 phep moi ben; con lai **NGANG** va
  luon di kem **MDE** (chenh nho nhat phep thu thay duoc voi luc 80%): "khong thay" co the chi la "khong du mau de thay" (CLAUDE.md: ket luan am tinh kem MDE).
  Chenh be khong bao gio thanh HON du mau lon. Hai phep thu cung luc, khong hieu chinh: day la NHAN canh bao, khong phai cong chan.
- **Cung mot thuoc do** (`kq_cung_thuoc_do`): moi o lay ket luan cua LAN KIEM DAU (engine thap nhat). Don kiem lai engine moi chi ra cho co che da GIU,
  nen neu dung no de so sanh thi nhom cao bi do bang thuoc kho hon. Nhan GIU van dung ket qua tot nhat.
- KHONG_DO_DUOC (don chet, thieu so lieu) bi bo khoi ca hai phep thu - khong bao gio tinh la RUOT. Ca ty le tuyet doi (khoang tin cay Wilson) lan ty le theo
  DO MANH cua cao nguyen (ba nhom, khi >= 30 ket luan) nam trong `reports/VONG_LAP.md`.
- Dong tom tat bang loi thuong nam trong `tom_tat_cho_chu` (nen ra ca trong dong `VONG:` cua `giam_sat_may_nha`); diem nghen tu dong doi huong gio may khi ket qua la NGANG/KEM.

## 4. Chang AP DUNG (nap nguoc vao vong sau)

Co che duoc GIU -> `ke_hoach_ap_dung`: (a) quet chuyen sang thi truong chua quet / khung ke ben (chi vao o TRONG, co du lieu trong
`so_cai/doan.json`); (b) `ke_hoach_nho_lai`: don `vl-sk-*` nho SEEKER tim nguon cung loai co che va `vl-gh-*` ghi vao so tay nghien cuu.
Don chi sinh khi co co che GIU; idempotent (chay lai khong ra don trung).

## 5. Gioi han hien tai (nho ro)

- May nha dang chay ma cu (`44b3b23d+sua`): chi nhan don khong the `can`. 170 don cu khai `can` (engine4, ma-0810, dien-dan-v2, gia-v2, lenh-v1...) nam im
  cho toi khi may nha nap ma moi. Don `vl-xn-*` khong the, nen chay duoc ngay (moi don vai giay). Khi may nha da nap ma moi, `vl-xn4-*` kiem lai bang engine v4.
- Mot lan nap ma moi cho may nha (chu du an dan vao phien Claude Code o may nha): `b cau lay && b cau thu`, commit phan sua tay o `qwen/cau_git.py`
  roi `git pull --ff-only`, khoi dong lai `b cau chay --lien-tuc --nghi 20`, bao lai bang `b cau noi`.
- Tren Linux (cloud) khong co du lieu gia va khong ra mang: cloud chi lam NHAC TRUONG (bang diem, chon dot, ra don, doc ket qua); cac chang can du lieu
  (TIM, BOC tu ma nguon, KIEM) chay o may nha.

## 6. Van hanh moi gio (phien cloud)

Dieu phoi dinh ky `Giam sat may nha moi gio`: `python3 -m nhan.giam_sat_may_nha` (in 4 dong `VONG:` + `HANH_DONG`) -> lam theo khuyen nghi
(thuong la `python3 -m nhan.vong_lap --giao 240`) -> commit `viec/cho` + `reports/vong_lap` + push. Hang doi chia theo chang, khong don het vao quet.

## 7. Viec ke tiep (dung thu tu)

1. May nha chay het cac don `vl-xn-*` -> doc tong ket: ty le qua cua vung lai so voi nhom doi chung (pheu co hon boc tham khong? muc 3, phan "Cach doc ket qua")
   VA so voi chuoi CHI CO NHIEU (muc 8: ty le qua 'tu nhien' cua chang KIEM la bao nhieu).
2. Co che dau tien qua nhan GIU -> kiem do ben: thu cac o lan can cua nguoi qua (khong chi mot o), roi `vl-xn4-*` (engine v4).
3. Co che GIU -> AP DUNG: HEPHAESTUS rai luoi tham so quanh co che, SEEKER di tim nguon cung loai (TIM co muc tieu).
4. Khi du ket qua: chu du an/cloud quyet NIEM PHONG theo luat (mot lan, doan dong bang). Khong tu dong.

## 8. Doi chung nhieu: do chinh chang KIEM tren chuoi CO DAP AN (ke hoach DONG BANG 10/10/2026)

Chang KIEM an 50% gio may va chua tung duoc do. "Qua ngoai mau" cua 1.022 don sap ve co the cao du KHONG co loi the nao (lenh luoi / martingale:
nhieu lai nho, hiem khi lo lon -> tren ~1,7 nam ngoai mau xac suat "co lai va khong chay tai khoan" tu nhien cao). Ty le qua cua may nha chi co nghia
khi biet **chuoi chi co nhieu** cho ra bao nhieu. `python3 -m nhan.doi_chung_nhieu` (Linux, khong can du lieu ngoai) chay CHINH duong ong that:
`quet_luoi` (9 mau che_do x kieu_lot; da doi chieu khop tung don trong 2.303 don quet 3.000 o cua may nha, 0 lech: test
`test_mau_khop_tung_luot_quet_san_xuat_cua_may_nha`) -> o tot nhat -> `danh_gia_luoi` tren xac_nhan -> o ngau nhien cung luoi -> `so_sanh_nhom`; nhung tren chuoi
TONG_HOP co DAP AN. Ket qua la NHAN canh bao, khong phai cong chan (CLAUDE.md: tieu chi duyet la co lai + maxDD < 80%).

### 8.1 Thiet ke (dong bang truoc khi chay lo lon)
- Chuoi: H1, 54.600 bar (kham_pha 60% / xac_nhan 20% / niem_phong 20%: doan niem_phong KHONG BAO GIO duoc cat o day), bien dong ~9%/nam (GARCH), spread ~15 diem,
  hat 1..N (hat 9001+ chi de do trung thuc, khong vao ket qua). Mac dinh quet 1.000 o/mau; san xuat quet 3.000 o (xem 8.5).
- Moi chuoi chay du 9 mau; MOI chuoi la mot don vi doc lap (9 mau chung mot duong gia nen duoc lay trung binh trong chuoi truoc khi gop).

| kich ban | trong chuoi co gi | engine | so chuoi |
|---|---|---|---|
| NHIEU | khong co loi the nao: thuoc do chinh | 3 (`cuc_tri`: may nha dang chay) | 200 |
| NHIEU | nhu tren | 4 (`duong_di`: ma moi) | 100 |
| DAO_DONG_RAT_YEU / DAO_DONG_YEU / DAO_DONG | co thanh phan HOI QUY that, 3 lieu (nua doi 288/144/48 bar) | 4 | 100 moi |
| NHIEU_THAP / NHIEU_CAO | nhu NHIEU, bien dong x0,65 / x1,35 | 4 | 100 moi |
| BETA / XU_HUONG | troi duong / quan tinh (biet truoc) | 4 | 100 moi |
| NHIEU (san xuat: 3.000 o) | thuoc do chinh, dung cau hinh may nha | 3 | 60 |

- Ba muc DAO_DONG dung de biet phep do co **NHAY** khong (variance ratio o chan 12/48/144/288 bar, do 10/10: .999/.982/.961/.956 ; 1.002/.968/.924/.873 ;
  .956/.822/.636/.533). Neu ty le 'qua' / 'hon mua-giu' khong tang theo lieu loi the thi chang KIEM mu: moi ket luan 'ngang nhieu' tu day vo nghia.
- Khong so engine 3 voi engine 4 (`NHIEU@e3` chi so voi ket qua engine 3 cua may nha, `NHIEU@e4` voi `vl-xn4-*`).
- Lenh (chay noi tiep, moi lenh co the ngat va chay tiep: `--ra` ghi tung chuoi mot dong; `--luong` = so nhan, de 4 tren Linux cloud, ~34 o may nha):
```
python3 -m nhan.doi_chung_nhieu --kich-ban NHIEU --khop-bar cuc_tri --so-chuoi 200
python3 -m nhan.doi_chung_nhieu --kich-ban NHIEU --so-chuoi 100
python3 -m nhan.doi_chung_nhieu --kich-ban DAO_DONG_YEU,DAO_DONG,DAO_DONG_RAT_YEU,XU_HUONG,BETA,NHIEU_THAP,NHIEU_CAO --so-chuoi 100
python3 -m nhan.doi_chung_nhieu --kich-ban NHIEU --khop-bar cuc_tri --so-chuoi 60 --toi-da-o 3000 --ra reports/vong_lap/doi_chung_nhieu_3000
```

### 8.2 Do cai gi
Theo (kich ban, engine, mau), gop THEO CHUOI: ti le luot quet xep CAO_NGUYEN; ti le o tot nhat 'qua' ngoai mau (rieng nhom cao nguyen = nhom vong lap that kiem);
ti le o ngau nhien cung luoi 'qua'; cac ti le do **va hon mua-giu/ban-giu**; ti le **duyet theo tieu chi chu du an** (co lai + maxDD < 80%); calmar cua o tot nhat
(thuoc do 'lien tuc' khong bi bao hoa) ; bang chan doan 3x4 tren 150 o ngau nhien/mau: P(qua ngoai mau | co lai trong mau) - P(qua | khong lai trong mau)
(= 'co lai trong mau' du bao duoc gi khong; tren nhieu ky vong ~0, tren DAO_DONG ky vong > 0).

### 8.3 Quy tac doc ket qua THAT so voi nhieu (R2) - dong bang truoc khi doc ket qua that nao
- **Don vi doc lap la THI TRUONG**, khong phai o hay luot quet: 9 mau cua mot (thi truong, khung) chung MOT duong gia, cac khung cua mot thi truong chung cua so ngoai mau.
  Moi thi truong cho MOT con so trong [0, 1]: (a) ty le qua tren >= 3 ket luan duoc cua no, hoac (b) trung binh PHAN VI calmar cua cac o tot nhat cua no so voi chuoi nhieu cung
  engine va cung mau (phan vi trung diem khi bang nhau; chay tai khoan = 0; kham pha khong do duoc thi bo). Can >= 8 thi truong, neu khong `CHUA_DU`.
- T = trung binh cac con so cua cac thi truong. Phan phoi nhieu cua T = trung binh cua M con so rut co hoan lai tu tap con so THEO CHUOI cua kich ban NHIEU cung engine
  (M = so thi truong that; can >= 30 chuoi nhieu; 20.000 lan rut; hat co dinh).
- Ket luan: `BAO_HOA` (nhieu trung binh >= 90% o thuoc do nhi phan 'qua': khong con phan biet, phai doc cot 'qua VA hon mua-giu' hoac thuoc do calmar); `VUOT_NHIEU`
  (p mot phia <= 0,05 VA T hon trung binh nhieu >= 0,10); `DUOI_NHIEU` (doi xung); con lai `NGANG_NHIEU`, LUON kem MDE =
  (1,645 + 0,84) x do lech chuan(chuoi nhieu) / can(M) (chenh nho nhat thay duoc voi luc 80%). Cac hang so (8 / 3 / 30 / 20.000 / 0,05 / 0,10 / 0,90) la hang so trong code, khong doi sau khi nhin so that.
- Phep `so_sanh_nhom` da dong bang o muc 3 coi moi o la doc lap: truoc khi doc no tren ket qua that, **do kich thuoc that cua no** tren du lieu nhieu (12 'thi truong' = 12 chuoi
  nhieu, lap nhieu lan): neu ty le 'HON' sai > 10% thi chi doc no theo nguong toi han 5% thuc nghiem.
- Gioi han (nhin ro): chuoi gia la AUDCAD-like H1 ~9%/nam; may nha quet M5-H1 tren 12 thi truong that (duoi day, gom bien dong, phi khac). Ket qua cu cua may nha (ma cu) khong in `hon_moc_pct`
  (chi calmar / maxDD / chay). => ket qua doc la NHAN canh bao. Nhieu lay tu chuoi that cua tung thi truong (dao dau / block-bootstrap) can du lieu o may nha: chua lam.

### 8.4 Ket qua doi hanh dong the nao (dong bang truoc khi co ket qua)
- BAO_HOA (nhieu cung 'qua' >= 90%): 'qua' khong phan biet; nhan GIU phai doc theo thuoc do khong bao hoa (hon mua-giu, calmar so voi phan vi nhieu); 1.022 ket qua cua may nha
  chi cho biet ty le chay tai khoan, chua phai bang chung loi the. Chay them: NHIEU voi ngoai mau dai gap doi (109.200 bar, 50 chuoi) de xem cua so dai co phan biet duoc khong.
- Ket qua that NGANG_NHIEU: khong them gio may vao quet sau hoac kiem lai cung luoi; chuyen sang chieu rong (thi truong moi, co che moi, nguon moi).
- VUOT_NHIEU: co che giu lai nhu UNG VIEN; can bang chung doc lap (engine 4, tester, doan niem phong theo luat).
- Ty le 'qua' / chenh 'co lai trong mau' khong tang theo lieu DAO_DONG: chang KIEM khong thay duoc loi the that; doi thiet ke kiem truoc khi tin bat ky 'ngang' nao.

### 8.5 Do trung thuc cua '1.000 o thay cho 3.000 o' (10/10, 12 chuoi NHIEU, hat 9001-9012, engine 4)
- mua_phang: CAO_NGUYEN 12/12 ca hai; o tot nhat 'qua' 12/12 (1.000 o) va 11/11 (3.000 o); o ngau nhien 12/12 ca hai.
- ban_phang: hinh dang 4/5/1/2 (CAO/CAI/KHONG_CO_LAI/HON_HOP) voi 1.000 o, 5/5/1/1 voi 3.000 o; o tot nhat 'qua' 5/11 va 3/11; o ngau nhien 6/11 va 7/11.
  => cung ket luan o be mat; khong du de bat chenh nho. De khong phai tin vao day: lo `NHIEU 3.000 o` (60 chuoi, engine 3) la tham chieu dung cau hinh may nha.
- Da thay ngay tu 12 chuoi: tren chuoi **chi co nhieu**, mua_phang bi xep CAO_NGUYEN 12/12 va o tot nhat 'qua' ngoai mau 12/12 (nhung 'qua VA hon mua-giu' chi 6/12 ~ tung dong xu).
  Nghia la 'qua' gan nhu khong phan biet loi the voi nhieu o it nhat mau nay: ly do cua BAO_HOA o 8.3 va cua nhom doi chung o muc 3.

### 8.6 Da lam duoc (10/10/2026, dong bang lai): cong cu doc + ket qua MOT PHAN
- Cong cu: `nhan/doi_chung_nhieu.py` (69 test, `nhan/test_doi_chung_nhieu.py`; kiem bang ~45 loi co y, con 1 loi song sot: `calmar` cua nhom 'doi' xep theo nhom 'cao', thap uu tien).
  Them so voi 8.3: thuoc do `duyet` (= qua VA |maxDD| < 80, dung tieu chi cua chu du an), canh bao khi mau cua 'nhieu' va mau cua ket qua that khac co cau (`nhieu_cung_co_cau_mau`),
  doc ket qua that theo TUNG engine rieng (`doc_that_theo_engine`), do kich thuoc that cua `so_sanh_nhom` (`kich_thuoc_phep_thu`: rut chuoi khong hoan lai, chay phep that nhieu lan).
- Do kich thuoc (test co dinh): khi cac o cua cung mot thi truong dung chung duong gia, McNemar/Fisher cua muc 3 bao 'HON' hoac 'KEM' khoang 1/3 so lan du khong co hieu ung (danh nghia <= 10%)
  -> `doc_theo_thuc_nghiem = True`: chi doc `so_sanh_nhom` theo nguong thuc nghiem `chenh_p05/p95`, khong theo p ly thuyet. Chua chay do nay tren lo lon.
- Lo hieu chuan lon bi he thong cat (qua gioi han thoi gian nen). CON LAI (khong chay lai tu dong): NHIEU engine 4 (100 chuoi) / NHIEU engine 3 (200 chuoi, dung cau hinh may nha) / NHIEU_THAP / NHIEU_CAO ·
  BETA / XU_HUONG / ba lieu DAO_DONG (30 chuoi moi cai). Chua xong: giai doan 3.000 o. File tho `reports/vong_lap/doi_chung_nhieu.jsonl`, tom tat `.json`; tai tao: `python3 -m nhan.doi_chung_nhieu --tong-ket`.
- Doc so (MO TA, khong phai ket luan): tren chuoi CHI co nhieu o tot nhat 'qua' 86% (engine 4) / 88% (engine 3), o ngau nhien 84% / 85% -> 'qua' khong phan biet o tot nhat voi o ngau nhien (bao hoa).
  'qua VA hon mua-giu': o tot nhat 55-57%, o ngau nhien 52%. Khi them co hoi quy that (ba lieu DAO_DONG; VR(288) 0,96 / 0,86 / 0,54): 'qua VA hon mua-giu' o tot nhat 63% / 71% / 77%, o ngau nhien 63% / 61% / 72%.
  => chi phan biet duoc tu lieu manh, va chenh 'o tot nhat - o ngau nhien' chi vai diem: xep hang trong mau gan nhu khong them thong tin so voi o ngau nhien tren chuoi tong hop nay. Day la lo tham chieu cho nhan GIU, khong phai cong chan.
- Quyet dinh 10/10 sau lan chu du an nhac 'dung lam module nho': dong bang hang muc nay o day; KHONG noi sau vao `vong_lap` (task #27) va KHONG chay them lo hieu chuan lon truoc khi co ket qua chuoi that.
