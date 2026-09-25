# GOI VIEC: TIEU CHI TIEN CUA CHU DU AN — "chi can co lai va maxdd duoi 80%" (25/09/2026)

Phien cloud [DOC], nhanh `claude/autonomous-trading-system-rzzt7h`. Khong MT5 tester, khong ghi
`nao.db` that, khong sua `config/*.json`. Phien [GHI] review roi gop.

Nguyen van chu du an: *"Dung 1 chut, toi khong quan tam martigel hay dca hay la phuong lhaps gi.
Toi trade don bay toi chap nhan rui ro, chi can co lai va maxdd duoi 80% la ok"*.

## 1. Da lam gi

**Mot nguon cho tran sut giam**: `nhan/cham_diem.TRAN_SUT_GIAM = 80.0` (truoc 60). Moi cong doc
tu day - doi mot cho la ca he doi theo.

| cong | truoc | sau |
|---|---|---|
| `cong.py` (the he cong 5 -> **6**) | CHAN: thang mua-giu (1, 2, 3) · phi do duoc (7) · du lenh (8) · khe dao ngay (11) · tang 2 (12, 13 - tu commit 6d032d1 sang nay) | CHAN: **co lai sau phi (14)** · **maxDD < 80% (15)** · 7 · 8 · 11. NHAN: 1-3, 12-13 (van tinh, van ghi; `verdict_chan` giu cach doc chat nhat) |
| `cong_ra_tien.py` | CAGR >= 20% · DD <= 70% · hon mua-giu cung DD | CAGR > 0 · DD < 80% · hon mua-giu -> `nhan` |
| `bang_he._cong_tien` | "KHONG hon mua-giu" lam truot | -> `nhan`; xep hang VAN day he thua mua-giu xuong duoi |
| `cham_diem` | tran sut giam 60% | 80% |
| nha nghien cuu `nc_thi_nghiem` | DAT = hon moc o DD 20% + tang 2 | DAT = **co lai sau moi phi**; `tien` = CAGR tot nhat voi maxDD < 80%; niem phong: maxDD < 80% o **don bay chot truoc** |

**Phep do tien moi** (`nc_thi_nghiem.tien_duoi_tran`): tang truong G(L) = sum log(1 + L*x) LOM theo
don bay L, nen "co lai o mot muc don bay nao do" <=> tong loi suat rong tung bar > 0, va muc ra tien
tot nhat = min(Kelly, don bay cham DD 80%, 10). Khong bao gio bao CAGR o don bay qua Kelly (o do giam
don bay vua it rui ro hon vua nhieu tien hon). Truong `gioi_han_don_bay` noi cai gi chan.

**Niem phong chot don bay TRUOC khi mo**: don bay = muc tot nhat tren kham pha + xac nhan lien mach
(doan noi bo `truoc_niem_phong`), roi doan niem phong chay o CHINH don bay do. DAT = co lai VA maxDD <
80% o don bay do. Chon don bay tren chinh doan niem phong la nhin truoc - con so luc do luon dep va
khong ai trade duoc no.

**Xuat MQL5 mang don bay da chot**: `xuat_mq5` ghi `don_bay_cam_ket` (don bay, DD, CAGR o doan niem
phong) cua tung co che vao `reports/nc_hang_doi_tester.jsonl` - tester chay dung muc do, va DAT that =
co lai va maxDD < 80% trong tester.

**Luoi / martingale / DCA** (`danh_gia_luoi`): he so lot cham tran 80% tinh CHINH XAC bang chia doi
tren duong equity (von + k*(equity - von), lai lo tuyen tinh theo lot) thay cho nhan tuyen tinh
20/|DD|. DAT = co lai, khong chay tai khoan o lot dang thu.

**Nhan moi (khong chan)**, trong `nhan_canh_bao` cua moi ket qua:
- `beta`: tach lai gop = BETA (phoi nhiem TB x troi tai san) + CANH THOI DIEM. >= 50% la beta -> nhan.
- `duoi_lo`: he lai nho nhieu lan / lo lon it lan chi lo gia that khi gap du lenh thua. Hoa von khi ti
  le thua q* = rr/(1+rr); can >= 3/q* lenh moi thay duoi (rr 0,025 -> 123 lenh). Thieu -> ghi so can.
- `KHONG hon moc` (mua-giu/ban-giu co don bay cung tran DD), tang 2 kinh te (kieu martingale, edge mong).

**Hien chuong AI** (`nc_tac_tu.HIEN_CHUONG`): tieu chi moi nguyen van; MOI phuong phap hop le; cong
khong loc beta nen AI phai loc khi chon huong; do duoi lo cua he martingale TRUOC khi niem phong.

**Hieu chuan** (`b nc kiem 30`): them kich ban tong hop **BETA** (khong edge, troi +6%/nam nhu chi so)
va phep do **cong ba doan** (`nc_tu_lai.do_cong_ba_doan`): y tuong NGAU NHIEN tren NHIEU va BETA, gia
thuyet co chu dich tren HOI_QUY va HOI_QUY_YEU, tren H4 va D1 (D1 = truong hop xau nhat: phi nho so
voi nhieu). Bo dem tach CHUA_DO_DUOC rieng - lan chay thu dau tien bat duoc chinh loi cua no (ho
`kiem_cong` khong hop le -> moi y tuong CHUA_DO_DUOC, bi dem nham thanh "truot").

**Sua kem - 9 test cong do tu 18/09**: `test_phoi_nhiem_holdout` (6) va `test_cong_do_phan_giai` (3)
dung fixture "di het cong" voi loi = 0 -> rr thuc te 0 -> truot tang 2. Truoc 25/09 chung chet vi
KeyError, sau commit 6d032d1 chet vi FAIL. Nay tang 2 la nhan va fixture dung loi duong nho (giong
`test_cong_fdr_v2`) -> qua (can `nao.db` co bang - xem muc 4).

## 2. Bang chung

- **Test** (cloud, Python 3.11): `test_tieu_chi_chu_du_an.py` MOI 14 test - hieu chuan hai chieu cua
  chinh tieu chi (phai QUA: co lai ma thua mua-giu, kieu martingale co lai, DD 79,9%; phai TRUOT: lo,
  DD 80%), mot nguon tran DD, Kelly/tran, he so lot luoi chinh xac, tach beta, duoi lo, kich ban BETA.
  Bo test nha nghien cuu + cong tien + cong: `test_nc_*` + `test_tieu_chi_chu_du_an` + `test_cong_ra_tien`
  + `test_bang_he_g1` + `test_cham_tien` + `test_khop_rui_ro` + `test_cong_fdr_v2` + `test_cong_tang2`:
  **110 qua**. `test_cong_do_phan_giai` + `test_phoi_nhiem_holdout` voi `nao.db` tam da khoi tao: **21/21
  qua** (truoc thay doi: 9 do).
- **Hieu chuan day chuyen** (`b nc kiem 30`, tieu chi moi): 6 dung · 1 chua ket luan (LOC, it lenh o
  xac nhan) · **0 sai · 0 bao dong gia**; hoc tu lenh 4/4; bao dong gia `tim_quy_luat` 6,7% / 13,3%;
  cong suat do tim rong 3/8 vs co chu dich 8/8 - GIONG HET truoc khi doi cong (bo tim quy luat co null
  rieng, chan nhieu truoc khi cong kip thay).
- **Cong ba doan qua DUONG CONG CU THAT** (so tay, van tay, niem phong mot lan; `b nc kiem 30` muc 5,
  `reports/NC_HIEU_CHUAN.md`): edge that **40/40 DAT**; y tuong ngau nhien tren NHIEU 1/200 (H4) + 3/200
  (D1), ca 4 mang nhan; tren BETA 10/200 (H4) + 35/200 (D1), nhan BETA-hoac-moc bat 5 + 22. Nhan ban
  NHAM tren edge that: BETA 0/40, KHONG hon moc 1/40. So D1 khop KHIT phep so doc lap o muc 3 (3/200 va
  35/200) - hai duong do khac nhau ra cung mot so.

## 3. So truoc / sau - CUNG y tuong, CUNG du lieu

Chay moi y tuong qua ca hai cong (cu: hon moc o DD 20% + tang 2; moi: co lai + maxDD < 80% o don bay
chot truoc). 200 y tuong NGAU NHIEN tren moi chuoi khong edge (10 hat x 20), 10 gia thuyet co chu dich
tren moi chuoi co edge. So la so DAT niem phong (giao thuc AI: chi di tiep cai DAT o doan truoc).

| khung | chuoi | cong CU | cong MOI |
|---|---|---:|---:|
| H4 | NHIEU (khong edge) | 0/200 | 1/200 (0,5%) |
| H4 | BETA (khong edge, troi nhu chi so) | 0/200 | 10/200 (5%) |
| H4 | HOI_QUY (edge that, manh) | 7/10 | **10/10** |
| H4 | HOI_QUY_YEU (edge that, yeu - van co lai sau phi) | **0/10** | **10/10** |
| D1 | NHIEU | 0/200 | 3/200 (1,5%) |
| D1 | BETA | 0/200 | 35/200 (17,5%) |
| D1 | HOI_QUY | 10/10 | 10/10 |
| D1 | HOI_QUY_YEU | 8/10 | 10/10 |

Doc:
- **Cong cu giet 15/40 edge THAT**, ca 10/10 edge yeu tren H4 - he co lai sau phi van bi loai vi tang 2
  doi lai rong >= 3x phi spread. Day dung la dieu chu du an phan nan: cong cu loai he ra tien.
- **Cong moi bat 40/40 edge that**, doi lai: 1% y tuong ngau nhien tren nhieu lot toi DAT (may man),
  va tren chuoi troi nhu chi so 5-17,5% y tuong nghieng mua lot (co lai THAT, nhung la beta). Hai loai
  do la viec cua NHAN, khong phai cua cong - xem muc 4.

## 4. Rui ro con lai

1. **Cong moi khong loc may man va khong loc beta** - dung tieu chi chu du an, va so o muc 3 la cai
   gia. Nhan BETA + KHONG hon moc bat 27/45 (H4 5/10, D1 22/35) cai lot tren chuoi BETA; phan con lai la canh thoi
   diem MAY MAN tren doan niem phong (t ~ 2,3) - chi so phep thu cua dong gia thuyet va Sharpe giam
   phat canh duoc. AI thu N y tuong thi ky vong ~N x 1% DAT gia tren tai san khong troi.
2. **DD lich su khong phai DD tuong lai.** Don bay cham tran 80% trong mau nghia la mot doan xau hon
   se vuot 80%. Niem phong do dung dieu nay o don bay chot truoc; khi trade that nen chay duoi muc do.
3. **Tran don bay 10** (quy uoc `vao_lenh.quy_ve_dd`): he phoi nhiem thap cham tran 10 ma DD con xa
   80% (nhan "cham tran don bay"). Nang tran thi tien to hon tren giay nhung rui ro khe gia (bar data
   khong thay trong nen) tang theo.
4. **`config/nguong.json` `_ghi_chu_che_do_cong`** van mo ta chan cung cu ("thang moc, phi do duoc, du
   lenh, khe dao ngay") - phien [DOC] khong duoc sua config; phien [GHI] sua mot dong ghi chu.
5. **Phieu `to_hop`** (pheu to hop cu cua QUANTLAB) van loc "song sot" theo hon moc o DD 20% tren train
   va hold (`to_hop.py` dong ~581). Do la bo loc TIM KIEM, khong phai cong duyet - chua doi.
6. Test can du lieu that / `nao.db` co bang (`test_chuoi_dai_hai_chang`, `test_gop_lop`, va 9 test cong
   o muc 1 khi chay bang `nao.db` rong) do tren cloud truoc va sau thay doi nhu nhau - xem muc 2.

## 5. Viec chua lam

1. [GHI] `b test` tren may chu du an (co `nao.db` + du lieu that); sua ghi chu `config/nguong.json`.
2. [GHI] `b he` / `bang_he` tren kho that: dem bao nhieu he NAY qua cong tien ma truoc bi loai vi thua
   mua-giu - va doc nhan BETA cua chung truoc khi goi la he.
3. `b nc tu-lai AUDCAD H4` / `EURGBP H4` / `XAUUSDM H4` voi du lieu + chi phi THAT (cap cheo FX gan nhu
   khong troi -> it bay beta nhat, dung cho de bat dau).
4. Neu chu du an muon pheu `to_hop` cung theo tieu chi moi: doi dieu kien song sot sang "co lai train VA
   hold" (giu `hon_moc` lam cot nhan).
