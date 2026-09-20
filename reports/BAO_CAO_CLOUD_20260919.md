
---

## Dot 3 (20/09/2026) — ba cho `None` GOP NHIEU NGUYEN NHAN lam mot

Ket thuc goi kiem toan "hong trong im lang". Ba cho con lai deu cung MOT hinh
dang loi, va la dung hinh dang ma LUAT SO 0 cam: **mot phep KHONG DO DUOC di
ra bang cung gia tri voi mot ket luan AM that**.

| Cho | Truoc | Sau |
|---|---|---|
| `do_luc._nguong_fdr` | `except: return None` -> bao cao in `nguong_fdr_hien_tai: null`, doc thanh "ho nay chua bi FDR rang buoc" | tra `(nguong, ly_do)`; bao cao co them `nguong_fdr_ly_do`. Chi mot nguyen nhan that: **khong doc duoc `nao.db`** (`ho_fdr` la ghep chuoi, `nguong_lord` la so hoc thuan - ca hai khong the hong) |
| `doi_khung._hieu_chinh_gop` | `kh = NP._ty_le_kich_hoat(s2, df_d) or 0.0` | gap `None` thi **dung do va tra spec GOC**; bao cao them `kich_hoat_do_duoc` |
| `ngoai_sinh.ty_le_kich_hoat` | hai `except` gop lam mot `None` | ghi `_LY_DO_CUOI`; `chuyen()` tra ban ghi `chua_do_duoc`; `ung_vien()` dem rieng |
| `gop_lop._mot_chan` | BON nhanh `None` gop thanh mot cau "chi dung duoc N chan" | tham so `ghi_ly_do=`; `_ro()` dem rieng `chan_chua_do_duoc` |

### Cho nang nhat: `_hieu_chinh_gop`

`or 0.0` khong chi lam lech con so - no lam ham **tra ve mot spec khong sinh
duoc tin hieu, dan nhan da hieu chinh**:

1. `kh = 0.0 < muc` luon dung -> `lo = d` suot 18 vong, phep do nhi phan bi lai
   ve phia he so LON du khong he co thong tin nao.
2. `tot_kh` khoi tao bang `hien`, ma `hien` cung co the la `None` -> nhanh
   `if tot_kh is None` nhan ngay vong dau -> `tot = s2`.

Ket qua di ra ngoai la `sau_khop_phan_vi: 0.0` - doc y het mot phep do that
bang khong. `dat()` van tra `False` nen khong co PASS gia, nhung `bao["spec"]`
la spec hong va nguoi doc khong co cach nao biet.

Vi `_ap_he_so` chi doi HANG SO nguong (khong doi cau truc spec), neu
`sinh_tu_spec` nem o mot he so thi no nem o moi he so -> gap `None` la bang
chung ve SPEC chu khong ve `d`, nen dung do la dung.

### Mot bai kiem tung XANH VI LY DO SAI

`test_ngoai_sinh.py::test_tai_san_dich_khong_chay_duoc_thi_tra_None` viet
`assertIsNone(chuyen(gt, "US500CASH", "D1"))`. Tren may co du lieu no xanh
dung y dinh (co che theo GIO khong chay tren D1). Tren may KHONG co `data/`
no **cung xanh**, nhung vi tai san GOC nem `FileNotFoundError` - tuc bai kiem
ve co che theo gio thuc ra dang do su vang mat cua thu muc `data/`.

Sau khi tach `CHUA_DO_DUOC`, bai nay do dung dieu no muon do (`dat` phai sai)
va **bo qua** khi chua do duoc. Doi ten thanh `..._thi_KHONG_DAT`.

Day la bang chung truc tiep cho gia tri cua ca goi: tach hai nghia ra khong
chi sua bao cao, no con lo ra mot bai kiem dang cho diem khong.

### Bang chung
- Bon bai moi trong `test_hong_im_lang.py`: **do 4/4 tren code cu, xanh 4/4 tren code moi**.
- Bo test da xay trong phien: **224 passed**.
- `test_ngoai_sinh.py` truoc: 6 do + 1 xanh-gia. Sau: 6 do (y nguyen, deu la
  thieu `data/`) + 1 **skip co ly do**. Khong phat sinh do moi o `test_gop_lop.py`
  (4 truoc, 4 sau) va `test_do_luc.py` (6 truoc, 6 sau).

### Viec chua lam
- Bon bai moi chay tren may KHONG co `data/`/`nao.db`. Tren may chu du an chung
  se di nhanh "do duoc" - can chay lai de xac nhan ca hai nhanh.
- `gann_sq9` va `phuong_sai` van chua co khuon nao trong HEPHAESTUS (2/45 toan hang).

---

## Dot 4 (20/09/2026) — HAI TOAN HANG CUOI CUNG DA CO KHUON

`do_phu` tren lo duc truoc: **43/45** toan hang. Hai cai con lai:

| Toan hang | Co tu | Van de |
|---|---|---|
| `phuong_sai` | ban dau | **72 lan trong ma that** ma may DE khong sinh ra bao gio |
| `gann_sq9` | 08/09/2026 | them de "khong phai viet mot he rieng", nhung chua khuon nao goi -> chua tung di qua cong nao |

Sau: `HP.do_phu(kho=HP.duc(5000))["bo_trong"] == []`. Lo duc **710 -> 714** co che,
**52** co che moi.

### `_khuon_ty_le_phuong_sai` — va cai bay phai tranh

De nhat la dung `phuong_sai` thanh mot ban cua `do_lech`. Nhung
`phan_vi(phuong_sai(n))` va `phan_vi(do_lech(n))` **bang nhau tung bar** (can
bac hai la don dieu tang nen khong doi THU HANG) - mot khuon nhu vay la mot
phep thu duoc tra suat FDR hai lan cho mot cau hoi, va khong cong nao bat
duoc vi ca hai deu hop le va deu kich hoat binh thuong.

Cau hoi RIENG cua phuong sai nam o hai **CHAN TRO**, khong o hai cua so:

    VR(k) = Var(doi k bar) / ( k * Var(doi 1 bar) )

Duoi buoc ngau nhien `VR = 1` dung bang dinh nghia. `VR > 1` = cac buoc cung
dau (tiep dien); `VR < 1` = nguoc dau (hoi ve). Do la phat bieu ve **tu tuong
quan**, khong phai ve do lon bien dong. Ve phai dung `tuyen_tinh(he_so=[k*c])`
nen hai ve cung don vi `gia^2` - khong co nguong theo tai san.

**Hieu chuan HAI CHIEU** (3.000 bar, hat 7, nhieu AR tren loi suat):

| AR tren loi suat | -0,35 | 0,00 | +0,35 |
|---|---|---|---|
| ban `tiep_dien` | 0,000 | 0,090 | **0,615** |
| ban `hoi_ve`    | **0,428** | 0,018 | 0,000 |

Hinh chu X, va cot giua gan im o ca hai ban - dung nhu `VR = 1` doi hoi. Cot
giua la chot quan trong nhat: thieu no thi mot khuon kich hoat 90% moi luc van
"don dieu".

### `_khuon_gann` — thang do la `sqrt(gia)`, va no cat that

Buoc giua hai muc xap xi `2*sqrt(nen)*k*goc/360`, tuc ty le voi **can bac hai**
cua gia. Do 20/09 tren hai chuoi tong hop **cung mot chuoi loi suat, chi khac
muc gia** (`hp_gann_ho_tro_20_*`):

| `goc` | 0,1 | 0,5 | 2,0 | 8,0 | 45,0 | 180,0 |
|---|---|---|---|---|---|---|
| EURUSD (1,08) | 0,208 | 0,022 | **0,000** | 0,000 | 0,000 | 0,000 |
| XAUUSD (2000) | 0,230 | 0,228 | **0,218** | 0,152 | 0,000 | 0,000 |

O `goc = 2` mot ben chet han con ben kia kich hoat 21,8%. Day la ly do `goc`
quet qua **ba bac do lon** (0,1 -> 180) chu khong phai mot dai "hop ly".

Chon chieu HOI VE (khong phai pha vo) vi `_khuon_pha_vo` da hoi cau do voi
Bollinger/Donchian/Kijun; cai RIENG ma Gann tuyen bo la nhung muc hai hoa nay
la noi mot song KET THUC. Ca hai ban deu co `tre(1)` vi `thap_nhat(n)` gom ca
nen dang xet.

### Bang chung
- `test_khuon_vr_va_gann.py`: **9 passed**, trong do co mot bai **hieu chuan
  chieu nguoc** chung minh cai bay `phan_vi(phuong_sai) == phan_vi(do_lech)`
  la co that (`assert_allclose` atol 1e-12 tren >500 bar), va mot bai doi
  moi co che VR khong duoc trung 99% voi bat ky co che `do_lech` nao.
- Bay nhin truoc: moi co che Gann phai co `tre`.
- Moi muc gia trong (1,08 · 150 · 2.000 · 5.000) deu con it nhat mot `goc` song.

### Viec chua lam / da kiem tra la KHONG phai cua minh
- `test_ngu_phap_toan_hang.py::test_van_con_phan_biet_duoc_hai_loai_thieu` do.
  Da doi chieu: **do san tren `main` (bb51292)**, khong lien quan HEPHAESTUS
  (no doc bang `toan_hang_con_thieu` tu corpus SEEKER, khong doc lo duc).
- Ca 52 co che moi moi chi chay tren chuoi TONG HOP. Tren may chu du an phai
  chay `b hepha nap 714 --that` voi du lieu that truoc khi tin con so nao.

---

## Dot 5 (20/09/2026) — MAY DE DANG CHOI TREN NUA SAN

`CLAUDE.md` LUAT SO 0: *"'FX' = KIEU GIAO DICH LONG/SHORT, khong phai chi cap
tien"*. Do la phat bieu ve SAN CHOI, va no rang buoc truc tiep may de.

**Do duoc truoc khi sua**: lo duc 714 co che lech **484 long / 230 short**, va
**10 trong 23 khuon sinh DUNG MOT CHIEU**:

| Khuon | long | short |
|---|---|---|
| `thuan_xu_the` | **84** | 0 |
| `doi_pct` | 24 | 0 |
| `lich_phien` | 12 | 0 |
| `fibo` | 12 | 0 |
| `nen_bien_dong` | 12 | 0 |
| `lich_thang` | 11 | 0 |
| `dong_tien` | 6 | 0 |
| `hoi_ve_vwap` | 6 | 0 |
| `macd` | 4 | 0 |
| `nen_manh` | 4 | 0 |

Vi sao la loi chu khong phai khau vi: tren mot chuoi di len trong mau, mot may
de nghieng ve mua se tim ra "edge" **chi vi so luong phep thu** - ma suat FDR
thi bi tieu that. Nguoc lai, tren mot tai san di xuong no se khong thay gi,
trong khi do dung la nua kia cua san choi.

**Sau khi sua: 968 co che, 484 long / 484 short, moi khuon can dung, 0 trung
ten, 0 khai bao hong.**

### HAI cach guong - dung lan la hong im lang

* Dieu kien **khong co chieu** (lich, nen hep, khoi luong tren trung binh):
  guong bang `_ban_doi_xung` - GIU dieu kien, lat `chieu`. Hai co che do la
  hai **gia thuyet canh tranh** ve cung mot cua so ("thu Hai la ngay mua hay
  ngay ban"), thu rieng chu khong ghep.
* Dieu kien **da co chieu** (`nhanh > cham`, `macd > 0`, `than_nen > 0`):
  phai doi CHINH DIEU KIEN. Lat nhan thoi thi hai co che kich hoat cung bar
  theo hai huong nguoc nhau.

### `fibo`: ghim `huong` la SUA LOI, khong phai them ban

Ban cu de `huong` mac dinh `tu_dong`, tuc muc thoai lui suy tu chieu song gan
nhat - co the tang, co the giam - nhung ca ba co che deu gan `chieu = 1`. Hau
qua: **cung co che do kich hoat MUA khi gia cham muc thoai lui cua mot song
GIAM**, tuc mua dung vao vung ma luan diem cua chinh no noi la co lenh cho BAN
dong lai. Khong sai cu phap, khong nem loi, va trung binh cua hai nua nguoc
nhau la mot con so nho gan khong - hinh dang im lang dien hinh.

### MOT BAI KIEM CUA CHINH TOI XANH VI RONG

Ban dau `test_cap_CO_DIEU_KIEN_KHAC_NHAU_thi_khong_duoc_kich_hoat_trung` ghep
cap theo **hau to** `_ban`. Nhung ten co hai dang (`hp_vot_ban` va
`hp_thuan_ban_ema10_ema14`), nen no duyet **DUNG 0 cap** - xanh 6/6 ma khong
kiem gi. Da them bai `test_co_du_cap_de_bai_nay_co_nghia` doi >= 100 cap va
sua phep ghep cap; nay duyet **114 cap** that.

### VA MOT TIEN DE CUA TOI CUNG SAI

Phep do dau tien bao 103 cap "kich hoat trung", ke ca
`hp_thuan_ema10_ema14` vs `hp_thuan_ban_ema10_ema14` - hai dieu kien **khong
the cung dung**. Nguyen nhan khong phai co che: `sinh_tu_spec` tra chuoi VI
THE, va `giu` giu vi the them nhieu bar sau kich hoat nen hai lenh no o hai
thoi diem khac nhau van chong nhau. Ep `giu = 1` de chuoi tro ve dung cac bar
KICH HOAT: cung hai co che do, trung **0** bar. Bai kiem phai do cai no dinh
do.

### Chot chan con lai
`ghep()` da tu choi ghep hai co che nguoc chieu tu truoc. Nhan doi so ban BAN
lam rui ro do lon hon han, nen `GhepKHONG_DUOC_TRON_HAI_CHIEU` khoa lai, kem
mot bai hieu chuan chieu nguoc (`ghep` cung chieu van phai lam viec).

### Bang chung
- `test_hai_chieu_can_bang.py`: **9 passed**, duyet that 114 cap doi dieu kien
  va 73 cap doi xung may moc.
- Bo test HEPHAESTUS + kiem toan: **155 passed**.
- `do_phu(kho=duc())["bo_trong"] == []` van giu (45/45 toan hang).
