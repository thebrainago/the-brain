# BAO CAO PHIEN CLOUD — 19/09/2026

Lam theo `PROMPT_CLOUD.md` (nut that bo doc ma) va `VIEC_MAI_19092026.md` muc 1
(san EA co tia lenh -> rut loi quan tri lenh). Khong cham vao cai gi can
`nao.db`, MT5 tester hay du lieu gia — dung theo rang buoc cua repo.

## SO DO DUOC, TRUOC VA SAU

Hai bai do, ca hai chay duoc tren cloud, khong can gi ngoai repo:

```
python mau_thu/do_moc.py            # ho 1 - tin hieu VAO
python mau_thu/do_moc_quan_tri.py   # ho 2 - QUAN TRI LENH   (bai MOI)
```

| bai do | truoc | sau |
|---|---:|---:|
| co che tu 22 diem vao lenh (`do_moc`) | **0** | **2** |
| file ra >= 2 nut quan tri (`do_moc_quan_tri`) | **0** | **5** |
| nut quan tri boc duoc | 10 | 29 |

Cot thu hai la cot dang de y hon: `quan_tri.loc` gat moi co che duoi 2 nut chay
duoc, nen truoc phien nay **ca bo mau ra khong co che quan tri nao dung duoc**.

## 1. BO DOC MA: 0 -> 2  (`nhan/doc_ma.py`)

Chan doan cu trong `PROMPT_CLOUD.md` ("ngu phap chi dien dat duoc bieu thuc truc
tiep tren gia/chi bao") chi dung mot nua. `_no_dieu_kien` DA co san duong truy
nguoc bien trung gian tu truoc. Van de la **bang ky hieu rong tu dau**: bo doc
khong nhin thay mot bien nao cua file `.mq5` ca.

Bon lop loi chong len nhau, tat ca deu do MQL5 viet kieu C con `doc_ma` viet
cho Pine:

1. **Khai bao co KIEU.** `bool up = ...` / `double ma = ...` / `input int n = 14;`
   — ca `_GAN_BOOL`, `_GAN_CB` lan `_GAN` cua `thu_hoi_thanh_phan` deu doi ten
   bien o DAU dong. Gap MQL5 la truot sach.
2. **Dau `;` cuoi dong.** `_no_dieu_kien` doi phep so sanh `fullmatch` ca ve;
   con mot dau `;` thi `a > b;` khong bao gio khop. Trieu chung nhin tu ngoai
   la mot bieu thuc hop le nam trong `chua_dien_dat_duoc` — rat de doc nham
   thanh "ngu phap con thieu toan hang".
3. **Toan tu kieu C.** `&&` phai ngang hang `and`; `||` phai bi tu choi nhu
   `or`; `!x` phai DAO phep so sanh chu khong duoc bo dau `!` roi doc tiep.
4. **Mang MQL5.** `CopyBuffer(MaHandle,...,MaValues)` lam `MaValues` thanh chinh
   chi bao cua handle; `CopyRates(...,current)` lam `current[k].close` thanh gia.
   Day la cach MQL5 doc chi bao — khong dich duoc thi mot EA MQL5 dien hinh
   khong ra duoc gi.

Them: doc duoc Donchian kieu MQL5 (`highs[ArrayMaximum(highs)]`), dang pha vo
pho bien nhat cua kho EA.

### Cho de sai nhat, va cach da chan

**CHIEU CUA CHI SO.** Mac dinh mang MQL5 KHONG phai chuoi thoi gian: `mang[0]`
la bar CU NHAT cua doan vua chep, khong phai bar hien tai. Chi
`ArraySetAsSeries(mang,true)` moi lam `[0]` thanh bar moi nhat. Doc nham chieu
la doi han do tre — cung ho voi bay `Open[i+1]` — va no **im lang**: bang so van
ra, chi la ra cua mot co che khac.

Nen: khong biet chieu VA khong biet so bar thi `_tu_mang` **tu choi** thay vi
doan. Cung luat cho Donchian: dang `CopyHigh(sym,tf,t_dau,t_cuoi,mang)` khong
suy ra duoc so bar (do dai phu thuoc khung chay) nen tu choi han. Ca hai dang
deu co test rieng khoa lai.

## 2. HO CO CHE THU HAI: 0 -> 5  (`nhan/quan_tri_than.py`, MOI)

Dung viec chu du an giao toi 18/09: *"cach tia lenh can tinh vi hon — can tim
cac EA co kha nang tia lenh de rut loi phan quan ly lenh"*.

`quan_tri.boc_mot` doc **ten cac `input`**, nen no chi thay phan tac gia da cho
nguoi dung chinh. Do tren 10 file mau: moi file ra **dung MOT** nut — ma `loc`
doi toi thieu hai. Trong khi do `EA Snippets_Breakout_Breakout2.mq5` co han mot
bo chot lenh hoan chinh, viet thang trong ma:

```
if(peakwin>=45 && profits<(peakwin*0.9))   CloseAll();   // rot dinh lai
if(profits<=-120)                          CloseAll();   // dung lo ca ro
```

Ca ba con so 45 · 0,9 · 120 **khong co `input` nao mo ta**, nen bo boc theo ten
input mu hoan toan. Va do chinh la ho co che da bien AUDCAD tu +0,66%/nam thanh
+13,26%/nam — **ho dang trong lai la ho ra tien nhat da do duoc**.

Module moi doc CHINH MA CHAY: tim ham tinh lai ca ro (cong don
`POSITION_PROFIT`) va ham dong ca ro (lap tren `PositionsTotal`), roi doc nguong
o cac `if` dan toi dong ro. Boc duoc: chot theo **rot dinh lai** · dung lo /
chot lai ca ro · khoang cach hedge trong than ham · tia mot phan vi the.

Da noi vao `quan_tri.boc_mot`, tuc vao buoc 1 cua `day_chuyen_quantlab` — mot
trong bon cua vao that. Input thang khi ca hai cung noi ve mot nut; than ham chi
dien cho trong. `input_goc` ghi `"than_ham"` de sau con truy nguon tung con so.

### Ba cho de nhan bua, deu co test chan

- **Dong da chu thich** la ban tac gia DA BO. Ban goc de day bon dong
  `//if(postotal==N&&peakwin>=...)`; dem chung la doc ra mot EA chua tung chay.
- **Nguong khong phai hang so thi khong doan.** `Breakout5-2-2` la ca nay that:
  nguong vu trang la `takeprofitamountperstartvolume*GetStartVolume()`, tuc no
  **co gian theo lot**, nen mot hang so o day se la con so sai.
- **So sanh khong dan toi dong ro** (`if(profits>=200) Print(...)`) khong tinh.

Va khi doc duoc CO CHE ma khong doc duoc SO thi bao ra o truong `thieu`, khong
im lang — im lang lam ban quet doc y het "EA nay khong co co che gi", tuc lan
`CHUA_DO_DUOC` voi `AM`.

## 3. CAI THU MA KHONG AN

- **Donchian khong nang duoc moc `do_moc`.** Da viet xong duong doc
  `highs[ArrayMaximum(highs)]`, nhung ca 10 file mau deu dung dang **theo THOI
  GIAN** (`CopyHigh(sym,tf,starttime,endtime,highs)`) o duong vao lenh — do dai
  cua so tinh bang bar khong suy ra duoc. Duong nay an cho dang theo so bar, da
  co test khoa lai, nhung tren bo mau nay no dung im. Khong tinh la thanh cong.
- **`_Point*margin` van chua dich duoc.** `upbreakout = current[0].high -
  (_Point*margin) > highrange` — `_Point` phu thuoc symbol (3/5 chu so), nen mot
  con so o day khong co nghia neu chua biet ma. De nguyen o
  `chua_dien_dat_duoc`, khong bia.
- **`Tradesinfo.initup` / `.hedgeprice` / `.zonesequence` van bi tu choi**, va
  dung ra la nen tu choi: do la **trang thai may** cua EA (zone recovery dang o
  chan nao), khong phai mot bieu thuc tren gia. Muon dich lop nay thi phai co
  ngu phap cho MAY TRANG THAI, khong phai them toan hang. Day la 10/22 diem vao
  lenh cua bo mau — tuc tran cua `do_moc` khong phai 22.

## 4. CON LAI, VUONG O DAU

- **`nhan/luoi.py` va `mo_phong_v2.py` deu dang MO COI** (BAN_DO.md). `luoi.py`
  la module da cho ket qua +13,26%/nam ngay 18/09, con `mo_phong_v2` la dich
  chay cua ca ho quan tri. Ca ho khong co duong chay nao goi toi. Noi chung lai
  can du lieu gia nen khong lam duoc o cloud — nhung day la lo hong CAU TRUC,
  khong phai viec ton.
- **`mo_phong_v2` chua co nut cho "rot dinh lai ca ro"** (`_chot_lui_tu` /
  `_chot_lui_ty`) va cho **tia mot phan vi the** (`_tia_*`). Bo boc da lay duoc
  chung tu EA that; cho trong bay gio nam o bo MO PHONG, khong con o bo boc.
  Day la viec tiep theo ro rang nhat, va no cung ho voi `tia_lenh` — thu da
  chung minh gia tri bang so tren AUDCAD.
- **Con so 2/22 va 5/10 la do tren 10 file.** Muon biet no co that su nang pheu
  12.078 tai lieu khong thi phai chay lai tren may co `nao.db`:
  `quan_tri.boc_kho()` va duong `doc_ma` cua `bien_dich_ung_vien`.

## TEST — DA DOI CHIEU, KHONG HONG GI

Them 41 ham test: 14 cho `doc_ma` kieu MQL5 · 4 Donchian · 23 cho
`quan_tri_than` (ke ca test buoc noi vao `quan_tri.boc_mot` va test qua duoc
`quan_tri.loc`).

Doi chieu 30 file test lien quan toi bon module da sua, chay **cung mot thu
muc** (worktree rieng cho ket qua khac — vai test doc duong dan that):

| | so test do |
|---|---:|
| ma MOI (HEAD) | **1** |
| ma CU (`nhan/` tua ve bb51292) | 14 |

Mot ca do o HEAD la `test_ngu_phap_toan_hang::test_van_con_phan_biet_duoc_hai_
loai_thieu` — **no do o ca hai ben**, nguyen nhan la thieu bang `thanh_phan`
cua `nao.db`. Muoi ba ca con lai cua ban cu chinh la cac test moi viet phien
nay, do dung nhu mong doi khi chay voi ma cu.

Nen: **khong co test nao dang xanh bi hong**. Cac test do khac cua bo test lab
tren cloud deu la do thieu `nao.db` / `data/` — dung nhu README bao truoc.

---

# PHAN 2 — MAY DE CO CHE (chu du an duyet, cung ngay)

Chu du an: *"he dang kha thu dong... no dang chi may mo nhung thu san co"*, va
*"neu co he thong ra tien thi cha ai up len"*.

## DIEM THAT: nua chu dong cua he CHUA TUNG DUOC VIET

`nhan/hephaestus.py` - module DE CO CHE, so do khai tu 13/09 kem loi goi
`b hepha` - khong ton tai. Bon luong sinh dang co deu bat nguon tu CAI DA CO:
`to_hop` ghep co che da co · `noi_sinh` doc lich su mot ma · `ngoai_sinh`
chuyen he da pass sang ma khac · `suy_nguoc` doc dau chan nguoi khac. Khong ai
sinh ra co che MOI. Nen he chi con nua thu dong.

## DA XAY

| | |
|---|---:|
| kho hien co | 4.049 co che, dung 34/45 toan hang |
| `duc()` de ra | **620 co che, ca 620 la cai kho CHUA CO** (0 trung) |
| dung toi | **40/45** toan hang (kho dung 34) |
| `bien_the()` tu 400 co che kho | 1.069 ban, 1.038 cai kho chua co |
| chay that tren du lieu | 620/620 khong nem loi · 526 trong dai kich hoat 0,2-98% |

18 khuon, moi khuon la mot LUAN DIEM ve ai tra tien va mang theo cau `co_che`
cua no. Khuon lon nhat la `ghep_qua_ho` (252/620): dat kich hoat cua ho nay
trong bo loc cua ho khac - thu khong tai lieu nao viet san vi no khong thuoc
truong phai nao.

    b hepha do · duc · bien-the · ghep · nap · tu-vung

`nap` CHAY KHO o mac dinh. Ly do cu the: hom nay, de xem thu no chay khong,
toi goi `them_co_che` mot lan - no ghi THAT vao `config/co_che_dsl.json` ngay
lap tuc, khong hoi lai. Kho da tung tut 2.975 -> 21 co che trong mot buoi sang
vi nhung chuyen nho hon the.

## HAI NUT QUAN TRI CON THIEU — DA LAP

`mo_phong_v2` nhan them `chot_lui_tu`/`chot_lui_ty` (nha lai mot phan DINH LAI
ca ro) va `tia_tu`/`tia_ty` (dong mot phan vi the). Ca hai boc ra tu EA that
bang `quan_tri_than`, truoc day mang tien to `_` vi khong co cho chay.

`chot_lui` khac `trailing_tu` DA CO o cho quan trong: trailing do bang PIP tu
dinh GIA, cai nay do bang TY LE cua dinh LAI. Ro 8 tang co lot gap 8 lan ro 1
tang nen cung mot so pip la mot so tien khac han - trailing 10 pip that chat
voi ro nho va long leo voi ro lon, dung nguoc cai ta muon.

## BON LOI TU BAT DUOC KHI CHAY THAT (cong cu phap cho qua sach ca bon)

- `gia < bien_TREN` deo lot mot lenh BAN - gia nam duoi bien tren Bollinger o
  gan nhu moi bar, tuc dieu kien LUON DUNG.
- `cao_nhat` nhan nguon qua `cua`, khong qua `cot` -> sau spec nem KeyError.
- `phan_vi(5) < 0,05` KHONG BAO GIO dung: thu hang trong cua so 5 bar chi nhan
  5 gia tri roi rac nen nho nhat la 0,20. Sau co che an sau suat FDR de doi
  lay mot cau tra loi da biet truoc.
- Toi gop DON VI voi DAO QUANH KHONG lam mot "thang do", va cai sai do loai im
  lang chinh hai khuon vua viet (`khoi_luong > tb(khoi_luong)` va
  `tuyet_doi(than_nen) > 0,6 x bien_do` - ca hai dung dan).

## PHAT HIEN KEM THEO

**TIA VA CAT_HOA TRANH VIEC CUA NHAU.** Voi `cat_hoa_tu=2` (mac dinh), `tia`
kich hoat **0 lan** tren 60.000 bar - cat hoa dong cac cap truoc khi lai ca ro
kip cham nguong. Tat cat hoa di thi cung cau hinh do tia 9-22 lan/nam.

Nghia la mot bang so co `tia_nam = 0` doc nhu "tia vo dung" trong khi that ra
no CHUA BAO GIO DUOC CHAY. Da ghi vao docstring va co test khoa.

**BAY TOAN HANG LOT SO.** `CHI_BAO_CO` chinh la `_DIEN_DAT_DUOC` cua bo boc.
Bo dieu phoi tinh duoc 52 toan hang, so khai 47. Bay cai lot: donchian ·
ichimoku · vwap · keltner · supertrend · heiken · mau_nen. Tuc moi tai lieu noi
ve chung deu bi cham "khong dien dat duoc" roi bo. Da them test khoa CHIEU
NGUOC (doc ten tu chinh ma nguon bo dieu phoi).

## CHUA LAM DUOC

- **Chua co ket luan nao ve chuyen chung ra tien.** 620 co che moi qua cong CU
  PHAP va chay duoc; `nap` tren cloud bao dung `CHUA_DO_DUOC` vi khong co
  `data/`. Phep do ty le kich hoat - va sau do la tester - phai chay tren may.
- 5 toan hang con chua co khuon: do_lech · doi · gann_sq9 · phuong_sai ·
  trang_thai_lat.
- So do tren random walk chi tra loi "co chay khong". Ky vong duoi random walk
  bang **-chi phi**, nen khong duoc doc chung nhu dau hieu co edge.
