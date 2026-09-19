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
