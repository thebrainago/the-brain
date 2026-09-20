
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
