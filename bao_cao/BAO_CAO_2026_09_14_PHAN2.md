# BAO CAO 14/09/2026 — PHAN 2: QUAN LI LENH, VA BA LAN SO DEP DEN TU CACH DO

Phan 1 (`BAO_CAO_2026_09_14.md`) la PMG. Phan nay la phan chu du an chot lai giua
phien: *"viec uu tien la xay dung he thong... hom nay code not cho xong he thong
va test logic cua he quan ly lenh va tim ra edge tu no"*.

Bao cao xep theo do nghiem trong cua cai HOC DUOC, khong theo thu tu lam.

---

## 0. DIEU QUAN TRONG NHAT CUA NGAY

**Ba lan trong mot phien, mot con so dep (hoac xau) den tu CACH DO chu khong tu
thi truong. Khong lan nao may bao loi. Ca ba deu "hop li" khi nhin bang mat.**

| # | cho hong | trieu chung | su that |
|---|---|---|---|
| 1 | khong loc chi phi | 12 dong dau bang la EURRUB/EURRUR | cap chet, `cagr_dd20` phat don bay khong lo cho chuoi it bien dong |
| 2 | khong nhin sut giam that | `luoi_dca` 81% o "hon moc", hinh dang "cao nguyen" | sut giam trung vi **95,9%**, te nhat 100%; hon trailing dung 1 diem %/nam |
| 3 | gop du lieu ve NGAY | ghep he cho +20,66%/nam | do tren bar goc: **-2,01%**. Chenh 22 diem, toan bo tu mot buoc resample |
| 4 | cat mang lech lat | "4/5 he qua cong AM o nua sau" | tin hieu nua DAU ghep vao gia nua SAU. Do dung: **4/5 DUONG** |

Cho thu 4 la nghiem trong nhat ve hau qua: toi da bao cao mot la co rang **cong
co the dang cho qua nhung he chi song o nua dau**, va de xuat dung moi viec de
di sua cong. Neu chu du an nghe theo, ca huong di cua du an doi vi mot dong cat
mang sai.

**Khong cai nao trong bon bi phat hien bang cach "nhin ket qua co hop li khong".
Ca bon deu hop li.** Chi phep DOI CHUNG bat duoc.

---

## 1. CODE NOT — quan li lenh du 11/11 ho, khong con treo vao MT5

Ban chay bang Python truoc gio chi lam duoc **6/11 ho**, va chinh no ghi ro vi
sao: *"nam ho con lai can mo phong nhieu vi the - do la viec cua tester"*. Ma
tester thi mot `terminal64.exe` la rang buoc vat li, va 13/09 no khong dang nhap
duoc nen ca ban do nam cho. Tuc **nam ho cua module quan trong nhat treo vao mot
cu bam chuot**.

`nhan/quan_tri_nhieu.py` mo phong `hedge` · `luoi_dca` · `stop_2_dau` ·
`tt_stop_doi` · `thoi_gian` bang Python. Duong di trong nen lay nguyen tu
`pmg_engine` (ba chang `O -> X -> Y -> C`, gia dinh bi quan); luat tung ho danh
gia o CUOI NEN dung nhu `QuanTri()` cua EA.

**Di CHUNG duong tinh tien voi sau ho cu** - xuat dung ba mang `vi_the` /
`loi_tho` / `khoi_luong` ma `vao_lenh.tinh_tien` doc. Khong mo duong tinh tien
thu hai: hai duong thi som muon lech nhau ma khong ai biet.

---

## 2. TEST LOGIC — 31 bai, moi bai co dap an tinh duoc bang giay but

Bat duoc **ba loi trong chinh engine vua viet**:

1. **Engine bo qua chieu cua tin hieu** - moi ro deu vao MUA. Bai test "chay tren
   gia ngau nhien thi phai hoa" bat duoc: `luoi_dca` de ra **-128 diem tu hu
   khong**, chi vi danh mot chieu suot 20.000 nen.
2. **Khoi chot cuoi mau bo quen cac chan da bi cat lo** - `tt_stop_doi` bao
   **+2,0** trong khi su that la **-1,0**.
3. **Dem so lenh theo chan CON SONG luc dong ro** - ro nao bi cat sach ghi
   "0 lenh", dung cai ro lo nang nhat lai vo hinh.

Va **hai phat hien ve chinh bo luat** (khong phai loi code, da ghi thanh test):

- **`hedge` lot bang nhau la KHOA CHET.** Mua@100 + ban@98 -> lai cua ro =
  `(p-100) + (98-p) = -2` voi **moi** gia p. Phoi nhiem rong bang 0 nen lai dong
  bang. Khong co duong nao ve hoa; ro chi thoat khi mot chan cham SL, va luc do
  la thua chac. "Hedge de cuu lenh" khong phai cuu - la dong bang lo roi tra
  them phi.
- **`hedge` co SL chan goc thi chan goc bi cat TRUOC khi kip hoi.** SL 3 ATR nam
  ben trong duong hoi phuc. Cung chuoi gia, chi khac co SL hay khong: khong SL
  -> **lai**; co SL -> **lo**. Giai thich vi sao ca hai ban do (Python va MT5)
  deu xep `hedge` bet bang.

---

## 3. TIM EDGE — bon huong, bon ket qua am

| huong | ket qua |
|---|---|
| PMG (luoi khong tin hieu vao) | ~0. Ky vong = -chi phi, dung nhu li thuyet |
| 11 ho quan tri tren engine te | moi ho sut giam 44-96% -> bang chi tra loi duoc "quan tri nao it te nhat" |
| 11 ho quan tri **tren he DA CO EDGE** | **moi ho AM o trung vi** (-0,29% den -4,99%). 4/147 o hon he goc, 3 trong do la don bay tra hinh |
| trailing tren vang | chet o nua sau (+3,77% -> +0,39%), va EURUSD co cung hinh dang -> chuyen cua mot THOI KY, khong phai cua vang |
| ghep he | **lam loang**: ghep THEM so voi chan don tot nhat trong no = trung vi **-3,16%**, chi 2/20 duong |

**Ket luan ve module quan li lenh, tra loi thang gia thuyet goc cua du an:** tren
he da co edge, moi lop quan tri phu len deu lam te di. Luat thoat goc cua he
(giu N nen) thang ca 11 ho.

Dieu do **khong** co nghia quan tri lenh vo dung - no co nghia **11 ho nay, tren
5 he nay** khong them gi. Va no giai thich luon con so 44-96% sut giam o bang
truoc: do la cua ENGINE VAO te, khong phai cua quan tri.

---

## 4. CAI DUONG DUY NHAT — va no da nam san trong lab

Ca ngay di tim edge moi: bon huong, bon ket qua am. Trong khi do:

| he da qua cong (tu truoc) | toan bo | nua dau | **nua sau** | lenh hd |
|---|---|---|---|---|
| AUDCAD.H4.rsi_dao_chieu | 3,45% | -0,14% | **+19,71%** | 96 |
| EURGBP.H4.ou_quay_ve | 0,28% | -1,38% | **+10,04%** | 175 |
| AUDCAD.H4.ou_quay_ve | 4,52% | +2,54% | **+9,59%** | 167 |
| EURGBP.H4.mat_can_bang_lenh_dong_cua | 4,36% | +4,95% | **+8,58%** | 45 |
| AUDCAD.H4.mat_can_bang_lenh_dong_cua | -1,18% | -0,80% | -2,68% | 44 |

**4/5 duong o nua sau**, chi phi `do_tin = SAN` ca nam.

**BANG TREN CHUA DOC DUOC** - no di kem **don bay 2,9-8,1**, vi sut giam THAT o
nua sau rat nho (-2,6% den -7,3%). Cua so 5,4 nam voi 45-175 lenh thi mot sut
giam -2,62% khong phai uoc luong dang tin cua duoi that. Day lai la bay so 2 o
muc 0, chi o tang cao hon.

**CON SO THAN TRONG** - dung don bay ma TOAN BO du lieu cho phep:

| he | don bay | **lai nua sau** | sut giam nua sau | lenh/tuan |
|---|---|---|---|---|
| AUDCAD.H4.rsi_dao_chieu | 2,39 | **+8,75%** | 8,84% | 0,34 |
| AUDCAD.H4.ou_quay_ve | 2,20 | **+6,79%** | 14,06% | 0,60 |
| EURGBP.H4.mat_can_bang_lenh_dong_cua | 3,13 | **+3,61%** | 8,04% | 0,16 |
| EURGBP.H4.ou_quay_ve | 0,88 | **+3,09%** | 6,38% | 0,63 |
| AUDCAD.H4.mat_can_bang_lenh_dong_cua | 1,37 | -2,01% | 15,44% | 0,16 |

**4/5 duong o nua sau, o don bay chay duoc that (0,9-3,1) va chi phi do duoc.**
Day la con so duy nhat cua ca ngay song qua het cac phep doi chung: cat mang
dung, don bay khong ngoai suy, chi phi `SAN`, sut giam do tren bar goc.

Khiem toc (3-9%/nam) va thua lenh (0,16-0,63 lenh/tuan), nhung that.

`AUDCAD.mat_can_bang` AM ca hai nua nhung van nam trong danh sach qua cong -
dang mot dong trong so van de.

---

## 5. VIEC CHO PHIEN SAU, THEO THU TU

1. **Dua he du dieu kien vao LAN NHANH** (`b uu-tien lan`, bon luat da viet
   thanh code sang nay nhung chua he nao vao). Duong con thieu la
   **MT5 -> demo -> tien that**, khong phai them mot huong nghien cuu nua.
2. **Truy `AUDCAD.mat_can_bang_lenh_dong_cua`** - am ca hai nua ma van trong
   danh sach qua cong.
3. **Do 11 ho theo TUNG THOI KY** thay vi mot bang tong. Ket qua vang hom nay
   noi thang rang bang tong dang giau chuyen thoi ky.
4. Bang 11 ho hien chay tren engine vao te; neu con dung no thi phai **doi engine
   vao**, khong thi bang chi do duoc "it te nhat".

---

## 6. MOT CHOT KY THUAT CHO NGUOI DUNG MAY

`nhan/tran_cpu.py` + `b tran-cpu [60|80|95]`: mot cho khai tran CPU, moi viec
nang tu ha theo. May nay la may CA NHAN cua chu du an - hai lan trong ngay phien
lam viec bi cat ngang de bao "ha CPU xuong".

Cho that su an het may **khong phai so tien trinh** ma la **numpy/BLAS tu mo
nhieu luong moi tien trinh**: 10 tien trinh con tuong la 10/20 luong = 50%, thuc
te an het 20 luong = 98%. Sua bang `OMP_NUM_THREADS=1` (dat TRUOC `import numpy`;
Windows dung `spawn` nen tien trinh con import lai file tu dau).

Do that sau khi sua: trung binh **44%**, cao nhat **60%**, tran khai 80%.
