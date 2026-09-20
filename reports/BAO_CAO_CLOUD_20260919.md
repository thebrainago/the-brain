
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
