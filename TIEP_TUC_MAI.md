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
