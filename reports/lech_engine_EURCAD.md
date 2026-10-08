# Lech engine luoi <-> tester / EA (08/10/2026): vi sao "24 gio, hang nghin phep thu" chi ra mot he 13%/nam, DD > 30%

Cau hoi cua chu du an (08/10): *"Chay 24h voi hang nghin phep thu, dao boi khap dien dan ma chi duoc 1 he lai 13% voi DD hon 30%?
Cau thay hieu suat nay chap nhan duoc khong? Cau phai xem van de dang thuc su o dau."*

## Tra loi bang loi thuong (ban cho bao cao)

- **Khong chap nhan duoc.** 13%/nam voi sut giam > 30% la ~0,4 dong lai tren moi dong sut giam - ngang ban mau CLMCA da co (13,45%/nam, sut giam 34,9%), tuc la
  chua vuot duoc thu minh da biet.
- **Mot nguyen nhan co bang chung nam trong MAY MO PHONG cua minh:** no cho cac cach "chot lai nho nhieu lan trong cung mot nen" ra lai
  cao gap 2-3 lan so voi MT5 tester va 15-55% so voi chinh EA tren cung mot duong gia. Bang xep hang dung may mo phong do nen **chon ra
  dung loai cau hinh ao nhat** lam ung vien dau bang; tester xac nhan thi chi con mot phan (hoac am).
- Da sua may mo phong (mac dinh moi `duong_di`, do lech voi EA <= 5% o thu tu duong gia trung voi gia dinh) va CHAN AI nghien cuu dung lai
  cach cu. Phan con lai (thu tu cao/thap trong nen, swap, cau truc tick that) KHONG the biet tu du lieu nen: xep hang xong van phai qua tester.

## 1. Bang chung 1 - 125 o hieu chuan: engine ban 3 (`cuc_tri`) vs MT5 tester model 0

Nguon: ket qua `hieu_chuan_luoi` cua may nha (`viec/xong/*-hc-*`, 125 o: EURCAD / AUDCAD / NZDCAD, M5..H1, cua so ~6 thang
2018-01 .. 2019-09, von 10.000, tham so khac nhau). **Day KHONG phai mau ngau nhien**: la loat hieu chuan co chu dich (ung vien dau bang
+ doi chung bo tia / lot phang...), nen chi doc huong va co lon, khong doc nhu ty le tren moi cau hinh.
`lai` la %/nam quy tu cua so ~6 thang (cung don vi voi bao cao `hieu_chuan_luoi`).

| nhom | so o | engine > tester | trung vi (engine - tester), diem %/nam | trung vi (engine bo swap - tester) | trung vi engine/tester (o tester >= +1%/nam) | so lenh engine/tester | maxDD engine/tester |
|---|---:|---:|---:|---:|---|---:|---:|
| tia lenh (tat ca) | 68 | 50 (74%) | +4.4 | +8.7 | x2,20 (n=32, max x16,1) | 1,10 | 0,83 |
| tia lenh M5 | 11 | 9 (82%) | +3.6 | +4.8 | x1,63 (n=6, max x7,3) | 0,97 | 0,82 |
| tia lenh M15 | 33 | 23 (70%) | +6.7 | +14.2 | x3,23 (n=19, max x16,1) | 1,20 | 0,81 |
| tia lenh M30 | 16 | 12 (75%) | +3.5 | +6.8 | x0,92 (n=5, max x2,3) | 1,01 | 0,90 |
| tia lenh H1 | 8 | 6 (75%) | +5.8 | +7.1 | x0,86 (n=2, max x0,9) | 0,99 | 0,74 |
| khong tia (tat ca) | 57 | 19 (33%) | -2.8 | +0.0 | x0,71 (n=13, max x1,6) | 0,92 | 1,02 |
| khong tia M5 | 8 | 2 (25%) | -2.5 | -0.5 | x0,74 (n=2) | 0,73 | 0,94 |
| khong tia M15 | 26 | 8 (31%) | -3.7 | -0.3 | x0,50 (n=7, max x1,6) | 1,11 | 1,10 |
| khong tia M30 | 8 | 4 (50%) | -3.0 | +1.5 | x0,81 (n=1) | 0,89 | 0,97 |
| khong tia H1 | 15 | 5 (33%) | -2.1 | +0.0 | x0,62 (n=3) | 0,89 | 0,98 |
| tia EURCAD | 25 | 23 (92%) | +22.0 | +31.4 | x3,10 (n=18, max x8,0) | 1,33 | 0,86 |
| tia AUDCAD | 25 | 14 (56%) | +1.7 | +7.4 | x1,44 (n=13, max x16,1) | 0,98 | 0,77 |
| tia NZDCAD | 18 | 13 (72%) | +3.4 | +4.8 | x1,48 (n=1) | 1,01 | 0,87 |
| **tat ca 125** | 125 | 69 (55%) | +1.1 | +3.1 | x1,56 (n=45, max x16,1) | 1,01 | 0,94 |

"engine bo swap" = lai engine tru phan swap engine tu tinh (tester bao swap = 0,00 o CA 125 o; engine trung vi -4,4 %/nam, 121/125 o am,
thap nhat -32). Do nhay cua ty le theo nguong "tester >= x": x=0,5 -> x2,39; 1 -> x2,20; 2 -> x1,83; 3 -> x1,79 (o tia lenh).

Doc:
- **O khong tia: engine dung** (bo swap, chenh trung vi +0,0 diem/nam; 37/57 o lech <= 3 diem). Loi la o tia lenh.
- **O tia lenh: engine cao hon tester o 50/68 o**; nang nhat o EURCAD M15 (23/25 o EURCAD tia cao hon, trung vi +22 diem, x3,1, engine mo
  nhieu hon 33% lenh). AUDCAD tia chi lech nhe (trung vi +1,7 diem) - ket qua tot nhat cua lab (AUDCAD luoi co tia) it bi anh huong hon.
- **15 o xep dau theo engine DEU la o tia lenh** (15/15), engine +40,5 .. +153,6 %/nam, tester -33,0 .. +52,6 (trung vi +22,9; 2 o am),
  engine cao hon tester o 15/15. Thu hang hai ben van tuong quan (Spearman 0,79 tat ca; 0,79 tia; 0,82 khong tia) nhung **top-15 hai ben chi
  trung 8/15** va muc lai bi thoi phong 2-7 lan o dau bang - ung vien nao "trong" 40-150%/nam thi ngoai doi chi con 0-50%.
- Thu hang tot hon muc lai: xep hang bang engine dung de LOC SO BO, KHONG de dua ra con so; moi ung vien phai co so cua tester.

## 2. Bang chung 2 - engine vs CHINH EA tren cung mot duong gia (khong phai tester)

`ea_LuoiDayDu.mq5` chay tren san gia C++ (`nhan/ea_gia_lap.py`) voi tick sinh tu CHINH cac bar M15 (4 chuoi x 1500 nen, bien do nen
trung binh ~7 pip, toi da 25), chuoi tick min `paso` = 1e-6 gia (xem muc 5: o 1e-5 co nhieu luong tu hoa). 4 thu tu duong gia TRONG nen:
`theo_nen` (xanh: thap->cao, do: cao->thap = gia dinh cua `duong_di`), `thap_truoc`, `cao_truoc`, `xen_ke`. So = chenh % cua lai engine so
voi lai EA, cong 4 chuoi (am = engine THAP hon EA).

| cau hinh | EA lai (theo nen) | `cuc_tri`: theo nen / thap truoc / cao truoc / xen ke | `duong_di`: theo nen / thap truoc / cao truoc / xen ke |
|---|---:|---|---|
| mua_phang | +129 | +0.3 / -0.3 / -8.9 / -3.5 | +3.1 / +2.4 / -6.4 / -0.8 |
| ban_cong | +1092 | -0.0 / -14.7 / -0.1 / -14.7 | -0.0 / -14.7 / -0.1 / -14.7 |
| hai_nhan_buoc | +723 | +0.7 / -3.1 / -0.6 / -2.8 | +0.1 / -3.6 / -1.1 / -3.3 |
| tn5 (tia lenh) | +1292 | +15.1 / +15.1 / +14.0 / +15.1 | +0.2 / +0.2 / -0.7 / +0.2 |
| cho_lui | +301 | +26.4 / -13.0 / -7.8 / -10.8 | -3.0 / -33.3 / -29.3 / -31.6 |
| chot_tien | +1942 | +37.2 / +37.2 / +37.2 / +37.2 | -0.1 / -0.1 / -0.1 / -0.1 |
| chot_tien_cho_lui | +820 | +25.5 / +26.7 / +21.6 / +12.3 | -4.5 / -3.6 / -7.4 / -14.5 |
| chot_tien_tia | +1601 | +37.1 / +31.1 / +32.5 / +32.4 | +2.1 / -2.4 / -1.3 / -1.4 |
| chot_tien_tia_cho_lui | +1457 | +54.8 / +20.4 / +33.6 / +39.2 | -2.3 / -24.1 / -15.7 / -12.1 |
| tia_cho_lui | +500 | +26.5 / +0.2 / -11.3 / +5.4 | -3.0 / -23.2 / -32.0 / -19.2 |
| buoc_co | +248 | +3.7 / -10.3 / -10.6 / -8.4 | -3.9 / -16.9 / -17.2 / -15.0 |
| buoc_thu | +155 | +0.3 / +0.3 / +0.3 / +0.3 | +0.3 / +0.3 / +0.3 / +0.3 |

Doc:
- **`cuc_tri` lac quan +15..+55% o moi cau hinh co tia lenh / chot theo tien / cho gia lui o thu tu theo nen**, vi no chot o CUC TRI cua
  nen va luon xu ly bat loi truoc (muc 4). Con `chot_tien` +37% o CA 4 thu tu: day la loi cua mo hinh, khong phu thuoc thu tu trong nen.
- **`duong_di`: <= 4,5% o thu tu theo nen o ca 12 cau hinh** (lon nhat -4,5% chot_tien_cho_lui, -3,9% buoc_co, +3,1% mua_phang).
- **Khi thu tu cao/thap trong nen KHAC gia dinh, `duong_di` BI QUAN**, khong lac quan: lech lon nhat +2,4% (mua_phang), thap nhat -33,3%.
  Nhom cho-gia-lui va buoc gian (cho_lui -29..-33, tia_cho_lui -19..-32, chot_tien_tia_cho_lui -12..-24, buoc_co -15..-17,
  chot_tien_cho_lui -4..-15); chi-ban (ban_cong) -14,7% o 2/4 thu tu; cac cau hinh con lai <= 7%. Nghia la danh gia tren bar M15 la can DUOI cho nhom nay (an toan cho xep hang nhung co the loai nham o thang).
- Nhom nay lech vi **OHLC khong cho biet low hay high den truoc**: khong mo hinh nao tren bar giai duoc; chi M1 hoac tick that.

## 3. Bang chung 3 - du lieu tong hop (random walk, khong chi phi, ky vong that = 0)

`python -m nhan.kiem_do_phan_giai` (16 hat x 2 ngay, 1 tick/giay; lech GHEP DOI so voi chay tung tick, don vi bao gia; k = 60 / 300 / 900
tick ~ M1 / M5 / M15; sai so chuan o ngoac):

| cau hinh | `cuc_tri` k=60 / 300 / 900 | `duong_di` k=60 / 300 / 900 |
|---|---|---|
| khong_tia | +0,0 / +3,5 (1,2) / +17,9 (3,8) | +0,0 / -0,4 (0,3) / -1,8 (1,3) |
| tia | +11,3 (2,5) / +57,7 (6,2) / +183,6 (19,3) | +0,8 (3,0) / +0,8 (3,2) / -6,9 (2,3) |
| cho_lui | +0,6 / +8,5 (4,8) / +21,6 (6,1) | +0,0 / -1,0 (0,5) / -2,8 (1,1) |
| chot_tien | +13,5 (2,1) / +47,1 (3,7) / +111,1 (6,4) | -0,2 (1,6) / -1,0 (1,2) / -7,8 (2,7) |
| tia_cho_lui | +6,8 (2,1) / +32,9 (6,5) / +93,0 (11,5) | +1,1 (1,7) / +1,6 (1,8) / +1,5 (3,3) |
| nhan_lot | +32,3 (19,3) / +406,7 (59,1) / +612,7 (33,6) | -10,5 (19,7) / -14,2 (15,7) / -53,8 (32,2) |

Sai lech cua `cuc_tri` **tang theo cap bar** (tia: 11 -> 58 -> 184) - dung loi "than trong sai huong": nen to hon thi cang nhieu cu nhun
nguoc duoc hap thu roi chot o dinh. Quet tham so nen chay M15 de nhanh la chay o khung mo hinh sai nhat. `duong_di` ~ 0 va khong theo khung.
Ghi chu: `duong_di` o `nhan_lot` k=900 -54 voi SE 32 (1,7 SE): lot nhan co do phan tan lon; khong phai bang chung lech.

## 4. Co che

`cuc_tri` (`luoi._mot_ro`, ban cu): moi nen xu ly theo thu tu CO DINH "them tang theo low -> tia cap o HIGH -> TP so voi high".
  (a) Tia cap duoc chot o CUC TRI cua nen chu khong o gia nguong cua no; toi 999 cap/nen. Spread cua tia bi tru hai lan.
  (b) Thu tu trong nen luon thuan loi: tang hap thu mot cu nhun nguoc roi chot o dinh, nen nao cung vay.
`duong_di` (mac dinh): nen xanh (C >= O, ke ca doji) di O->L->H->C, nen do O->H->L->C (duong ngan nhat qua ca hai cuc tri). Moi doan:
doan NGUOC chieu ro mo tang o moc (hoac gia dau doan neu nhay gia vuot moc); doan THUAN chieu chot tia / TP o GIA NGUONG, nhieu lan lien
tiep trong doan (ro chot xong mo lai ngay o gia chot). Spread MOT lan luc mo lenh; lo treo = lo noi lon nhat tren ca duong; cham dung
moc (<= `EPS_CHAM_PIP` = 1e-6 pip) la khop nhu EA / tester.

## 5. Gioi han - KHONG duoc bao la da hieu chuan

1. **Thu tu cao/thap trong nen** (muc 2): -12..-33% cho nhom cho-gia-lui / buoc gian va -15% cho chi-ban tren M15. Giai phap that: du lieu M1 (hoac tick) cho
   cau hinh nhom nay, va xep hang cuoi cung bang tester.
2. **Swap**: tester bao 0,00 o ca 125 o; engine tinh trung vi -4,4 %/nam. Chua biet tester khong tinh swap hay cach doc bao cao bi sai
   (`nhan/hieu_chuan_luoi.py` dong ~540). Anh huong khong nho: bang muc 1 cho thay "bo swap" doi trung vi +1,1 -> +3,1 diem.
3. Cau truc tick that (`Model 0` cua tester sinh tick tu M1; chat luong lich su ~51%), open bar that (engine suy open = close nen truoc
   kep vao [low, high]), nen gap thuan chieu vao nen do rong 0 hoan chot tia / TP sang nen sau.
4. **Luong tu hoa chuoi tick**: o `paso` = 1e-5 (= 1 point) cung mot cau hinh lech them vai % tuy hat; so lieu EA-vs-engine o day dung 1e-6.
5. 125 o la mau co chu dich, khong ngau nhien (muc 1). Cac con so theo nhom la huong va co lon, chua phai uoc luong ty le.

## 6. Da sua gi (commit a6acc76d va cac commit sau)

- `luoi.py`: `ThamSo.khop_bar` mac dinh `duong_di`, `PHIEN_BAN_ENGINE = 4`, `MO_HINH_BAR_NGHIEN_CUU = ("duong_di",)`.
  `luoi_nhan.c/.py` bam sat ban Python tung bit, tu kiem them bien nhi phan, cham-moc thap phan, hut-dung-sai (12 dot bien deu bi bat).
- `nc_thi_nghiem` / `nc_cong_cu`: duong nghien cuu cua AI (`thu_luoi`, `niem_phong_luoi`, `quet_luoi`) TU CHOI mo hinh bar ngoai `duong_di`;
  mo ta cong cu noi ro gioi han nhom cho-gia-lui. `hieu_chuan_luoi` la noi DUY NHAT chon `cuc_tri` (de do lech).
- `ea_gia_lap.chay()`: don thu muc tam sau moi lan chay (truoc do ro ri 2.482 thu muc ~ 29 GB lam day dia).
- Test: `test_luoi_duong_di.py` (hinh hoc khop lenh, tu nhat tren doan tick, khong lech theo khung), `test_ea_luoi_day_du.py` (engine vs EA
  tren cung duong gia, ca hai mo hinh), `test_luoi_nhan.py`.

## 7. Viec ke tiep (may nha)

1. Chay lai 125 o hieu chuan chi bang engine moi (`hieu_chuan_luoi` voi `chi_engine=true`, cache tester da co): do phan lech con lai
   (swap, thu tu trong nen, open) KHONG can tester. Neu o tia lenh con lech > 20% thi xu ly truoc khi tin bat ky xep hang nao.
2. Xep hang cuoi cung = **tester**: ung vien tu quet bang engine phai co so tester (model 0, cung cua so) truoc khi niem phong; ung vien
   nhom cho-gia-lui kiem them tren M1.
3. Kiem swap tester (vi sao 0,00): doc `swap_mode` cua ma + bao cao tester; neu tester that su khong tinh swap thi xep hang tester khong gom swap.

## 8. Tai lap

```
python -m nhan.kiem_do_phan_giai                              # muc 3 (5 giay)
python test_ea_luoi_day_du.py --bang --paso 1e-6               # muc 2 (can g++ ; ~11 phut cho 12 cau hinh x 2 mo hinh x 4 thu tu x 4 chuoi; them --hat 1 --cau-hinh a,b de chay nhanh)
python -m pytest test_luoi_duong_di.py test_luoi_nhan.py test_ea_luoi_day_du.py -q
```
