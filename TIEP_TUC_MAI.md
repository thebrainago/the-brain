# TIEP TUC MAI — chot 15/09/2026 (phien chieu)

Bao cao day du: `lab/BAO_CAO_2026_09_15.md` (PHAN 2 o cuoi file).

Phien nay bat dau tu muc 2 cua "Viec tiep" phien truoc (*chay lai 56 co che
`than_nen`*). Viec do mat 20 giay va ra ket qua AM. Ba thu tim duoc tren duong
di thi dang hon nhieu, va ca ba cung mot hinh dang:
**cong CO ton tai nhung khong nam tren duong chay**.

## TRANG THAI

    kho co che        3.260  (3.233 + 27 ban chuan hoa `k x ATR`)
    ra duoc tester    2.991 / 3.217   (dau phien: 2.654 / 3.216)
    khong dich duoc     226           (dau phien: 563)
    bo test           ~1.050 xanh
    git               xem `b lich 3`

## VIEC TIEP, THEO THU TU

**1. `mau_nen` — 135 co che, mon lon nhat con lai.**
Bo dich chua noi duoc `mau_nen`, va no chi la boolean tu OHLC vai bar nen dich
duoc. Sau no la `supertrend` 40 va `heiken` 40 (ca hai deu DE QUY - can can
than hon, khong phai mot bieu thuc thuan).

    python -c "import sys;sys.path.insert(0,'.');from nhan import ngu_phap as NP,dich_mq5 as D;k=[c for c in NP.doc_kho() if not NP.kiem_khai_bao(c)];D.sinh_ea(k,'X',khung='H4');import collections;print(collections.Counter(str(c['_khong_dich'])[:50] for c in k if c.get('_khong_dich')).most_common(8))"

**2. HAI HE AUDCAD DA QUA TESTER (13/09) VAN CHUA RA DEMO.**
Day la viec cu nhat dang ton. Duong con thieu la **MT5 -> demo -> tien that**,
khong phai them mot huong nghien cuu nua. Xem `b uu-tien lan`.

**3. Gan `b thang-gia` vao CUA VAO KHO.**
Hien no chi quet kho da co. Co che moi van lot vao duoc voi mot hang so don vi
gia, vi cua vao kho do ty le kich hoat roi lay cai dat duoc tren MOT chuoi.
`ngu_phap._them_co_che_trong_khoa` nay da giu `_ty_le_theo_chuoi` — con thieu
mot dong doc no.

**4. `BI_DANH` ánh xạ `XAUUSD -> GOLD` NAY SAI.**
Tai khoan `XMGlobal-MT5 10` khong co `GOLD`, chi co `GOLDmicro`. Thu muc lich
su ten `GOLD` van nam trong `bases/` nen khong ai thay. Moi luot bench quan tri
tren vang truoc day se ra 0 lenh. Kiem: `b ten-ma XAUUSD GOLD`.

## CONG CU MOI

    b ten-ma [MA]        ma co tren may chu dang dang nhap khong + ten gan dung
    b ten-ma --lam-moi   doc 1.630 ma THAT tu terminal vao config/ma_may_chu.json
    b thang-gia          quet ca kho: loi khai nao dinh NGUONG DON VI GIA
    python _chuan_hoa_thang_gia.py --xem | --ghi    hang so don vi gia -> k x ATR

## BAY MOI, PHAI NHO

1. **"0 lenh" co BA nguyen nhan, khong phai hai.** Hong moi truong · loi dich ·
   **va LOI KHAI**. Cai thu ba moi tim ra 15/09: `than_nen > 0.5` so mot dai
   luong DON VI GIA voi hang so tran, nen chet sach tren FX va song tren
   vang/chi so. Ca ban Python lan ban MQL5 deu "dung".

2. **Bang dau hieu phai khop voi cai may THAT SU in ra.** `DAU_HIEU_HONG` co
   `unknown symbol` suot nhieu ngay trong khi MT5 in `not exist`. Truoc khi tin
   mot bo do, lay ba thu chac chan CO ra thu.

3. **Chan doan doc log phai gioi han theo LUOT CHAY, khong theo gio.**
   `chan_doan_log` cu nhin lui mot tieng, nen mot luot chay DUNG ten ma da bi
   quy toi bang dong log `symbol AUDCAD not exist` cua luot TRUOC. Mot bo chan
   doan tra ve nguyen nhan CU con nguy hiem hon khong chan doan gi.

4. **Do phu cua bo dich la mot con so phai canh.** `test_dich_chi_bao_moi.py`
   co chan neo o 88%. Mot lan "don dep" lam no tut se khong bao loi gi - chi lam
   bang ket qua tester ngan di.

5. **Quy ket cho THANG GIA thi moi thu khac phai giu nguyen.** Ban do dau tien
   tron khung (H4/D1) va bat oan ngay. Sau nay do bat cu chieu nao cung vay.

---

# BO SUNG cuoi phien 15/09 — sau khi chu du an giao them viec

## DA XONG

1. **Duong ra tien** (`nhan/chay_that.py`, `b demo`). Chan lai o mot cho
   CAN NGUOI: **tai khoan XM dang dang nhap la TIEN THAT, so du 0,00** - can
   mot tai khoan DEMO. Da chay het duong o che do dien tap.
2. **Nut that toc do**: `sua_bar_hong` ton 8,12s moi lan `nap()` tren chuoi
   SACH, chay SAU cache. Da them cong do vector hoa: **25-40 lan nhanh hon,
   ket qua giong het tren 7 ma**. `test_ngoai_sinh` treo >30 phut -> 195 giay.
3. **Seeker da ngon ngu**: bang `tu_khoa` that 241 tu **100% ASCII**; ban doc
   **92,9% tieng Anh**. Da nap 166 cum x 15 thu tieng -> **391 tu, 103 phi-ASCII**.
   Dang ky **6 dien dan quoc gia** da do la vao duoc (mql5 Nga, traderviet,
   thaiforexschool, note_fx, fx-on, smart-lab).
4. **`b tai-san <MA>`** - noi `nhan/ho_so_tai_san.py` (816 dong, MO COI) vao
   cua vao. Them tach song theo chieu + `b dem-nen`.

## CON LAI, THEO THU TU CHU DU AN DUA

1. **Khau boc tach** (thuc quan noi hai module lon nhat) - CHUA danh gia.
   Ba module MO COI nam dung o day: `nhan/doc_pdf.py`, `nhan/doc_anh.py`
   (ca hai co OCR), va `nhan/tu_dang_nhap.py`.
2. **He dao nguoc tu lich su trade** (passview -> tu dang nhap -> truy nguoc
   -> chien luoc) - CHUA co. `nhan/tu_dang_nhap.py` la manh dau tien.
3. **Thuat toan cham diem tinh chat -> co che quan li, ghi vao tung cap.**
   `nhan/tinh_cach_chieu.py` la ban nhap (MO COI, nay da co test). Con thieu:
   tuong quan -> chien luoc cap (EURUSD vs GBPUSD), mua vu -> lich vao lenh.
4. **Quan li lenh khong phu thuoc entry** - dang do, xem `b pmg`.
5. **Noi sinh tren AUDCAD** - cap tiem nang nhat ma chua dao sau.
6. **EVO chua tich hop skill/cong cu ngoai** - `b san` co san, chua chay.

## SO PHAI NHO

    ho so song chi co cho 27/158 ma (131 ma du lieu goc la NGAY)
    bo dich MQL5 phu 2.991/3.217 (con 226: mau_nen 135, supertrend 40, heiken 40)
    dem nen KHONG du bao duoc gi (r<=0,195 tren 134 ma) - chi de MO TA

## KHAU BOC TACH — do xong cuoi phien 15/09

    12.006 tai lieu -> 7.994 co toan van (66,6%) -> 5.869 du dai -> 2.442 da boc
    bo dich MQL5 phu 2.991/3.217 (93%, dau phien 82,5%)

**SUAT THAT THEO NGUON** (tai lieu vao -> co che ra) - con so quyet dinh:

    mql5_code          1.166 ->  776   66,6/100
    tradingview_pine     696 ->  147   21,1/100
    youtube              109 ->   21   19,3/100
    github             3.309 ->  205    6,2/100
    HOC THUAT          3.767 ->    0   **0,00/100**   <- 31% ca kho

Da sua hai cho lam nghen:
  - bo do luat MU voi tieng Nga/Nhat/Trung/Han/Thai -> ton kho boc 16 -> 165
  - `_diem_nang_suat` xep hang nguon theo NGHICH DAO so tai lieu (phep noi khop
    4/387 dong) -> nay dem tu kho co che, 772/3.241 noi duoc

**VIEC TIEP CUA KHAU NAY:**
1. 4.114 tai lieu chua co toan van, nhung **80% la sieu du lieu hoc thuat**
   (suat 0). Chi nen lay toan van cho ~660 cai con lai (mql5_code 192,
   stackexchange 161, github 110, fxblue 103, etoro 100, tradingview 93).
2. `nhan/doc_pdf.py` + `nhan/doc_anh.py` van MO COI - ca hai co OCR.
3. Ha uu tien thu thap cua nhom hoc thuat; ngan sach do dang bi chiem boi nguon
   suat 0.

---

# PHIEN "LAM TIEP" — 15/09 toi

## BO DICH MQL5 PHU 100% KHO

    dau phien 15/09   2.654 / 3.216   (82,5%)
    bay gio           3.237 / 3.237   (100%)

Da them: tuyen_tinh · adx · cci · donchian · keltner · stochastic · dong_luong ·
macd · bon toan tu GOP · mau_nen (10 mau) · bollinger · heiken · supertrend ·
va BI DANH (`stoch`, `bb_upper`, `bb_lower` - bo dich nay goi thang
`ngu_phap._doi_bi_danh`).

**`supertrend` la XAP XI** (trang thai la cai chot, khong suy giam) - da ghi ro
trong ma, cua so khoi dong 500 bar. `heiken` thi CHINH XAC (0,5^60).

## HAI PHAT HIEN HE THONG

1. **19% kho la BAN TRUNG HANH VI.** 616/3.236 co che sinh ra chuoi tin hieu Y
   HET mot co che khac tren AUDCAD H4. `loc_co_che._van_tay_hanh_vi` co tu
   truoc va chay dung, nhung `chay_tester_kho` doc thang kho nen chua bao gio
   goi no. Nay da noi vao (`_gop_trung_hanh_vi`).
   Vi du chac chan: `bua == 2*rau_duoi - 1` va `sao_bang == 2*rau_tren - 1`
   (lech 1,1e-16, Spearman 1,000000) - bon ten mau chi la HAI mau.

2. **Seeker doc nguoc chieu nang suat.** `_diem_nang_suat` co tu so noi
   `t.url = g.nguon` ma cot do chua `'kham_pha'` -> khop 4/387 dong -> tu so
   luon 0 -> ham thanh `1/(n+2)` = xep hang theo NGHICH DAO so tai lieu.
   Va prior 0,5 lam nguon TOT NHAT (mql5_code 0,459) vinh vien thua nguon CHUA
   AI THU. Nay prior = suat that do duoc (0,3044).
   Hang doi doc: **60/60 `semantic` -> 60/60 `mql5_code`**.

## VIEC TIEP

1. **Quet toan kho tren tester** dang chay (AUDCAD H4 holdout, 2.620 co che
   duy nhat) - `nhat_ky/tester_toan_kho_audcad.log`. Doc ket qua PHAI theo
   luat cuc dai-trong-N, va phai lap lai tren EURGBP truoc khi tin.
2. `nhan/doc_pdf.py` + `nhan/doc_anh.py` van MO COI (ca hai co OCR).
3. He dao nguoc tu lich su trade (passview -> tu dang nhap) - chua co.
4. Cham diem tinh chat -> co che quan li ghi vao tung cap.
5. Hai he AUDCAD van CHUA ra demo - CAN NGUOI mo tai khoan demo XM.

## QUET TOAN KHO — ket qua co nghia DAU TIEN

    hon moc AUDCAD : 199/2539  (7,84%)   moc mua-giu  +1,13%/nam
    hon moc EURGBP : 112/2539  (4,41%)   moc ban-giu  +0,36%/nam
    GIAO (hon moc CA HAI): **38**   ky vong neu doc lap 8,8  -> **4,33 lan**

Danh sach giao mach lac: `ou_quay_ve_dsl` ca hai chan, RSI qua mua/qua ban,
pairs_trading mean-reversion. Dinh `ou_quay_ve_dsl_n200_z2_mua` (+7,43/+8,19).

**BA CANH BAO, doc kem hoac dung doc:**
  1. 38 co che nay TUONG QUAN RAT CAO (cung mot ho) -> ~1-2 phat hien doc lap
  2. ky vong 8,8 gia dinh doc lap -> 4,33 lan la CHAN TREN
  3. hai tai san deu la cap cheo FX tren CUNG cua so

**HAI LOI DA SUA, ca hai lam bang ket qua khong doc duoc:**
  - moc mua-giu BIEN MAT o quy mo lon (chi tim trong top 25)
  - chi co MOT moc cho vu tru HAI CHIEU -> co che BAN so voi moc MUA.
    Them `__ban_giu__`. Tren EURGBP: "hon moc" tut **584 -> 123** (4,7 lan).

### VIEC TIEP CUA HUONG NAY
1. Chay 38 co che giao tren tai san THU BA va cua so THU HAI (nua dau) -
   day moi la phep thu that. Hien chung chi qua mot cua so holdung.
2. Chay `nha_may_null` / placebo tren chinh 38 cai nay.
3. Ho nay la RSI/OU mean-reversion tren cap cheo FX - trung voi
   [[ibs-la-hien-tuong-cua-mot-thoi-ky]]. Phai kiem theo THOI KY truoc khi tin.
