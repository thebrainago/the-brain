# GOI G3-A — CHAN QUAN TRI BAT BUOC · 16/09/2026

**Noi ngan:** cong da dung va da chay tren du lieu that. Nhung phep chay dau
tien tra ve mot ket qua **nguoc voi gia dinh cua ke hoach**, va do moi la thu
dang gia nhat cua goi nay.

## Da lam gi

`nhan/dap_quan_tri.py` them ba thu:

1. **`BO_BAT_BUOC`** — ba bo luat toi thieu moi tin hieu vao phai di qua:
   `sl2_tp4_hue1` · `sl2_trail1` · `sl2_tp6_hue2_trail2`. Chung phu ca **dat hue**
   (luat duy nhat song ngoai mau) lan **trailing** (lai holdout x4,8 khi co CHO).
2. **`luat_co_cho(bar_tv, ten)`** — bo luat can CHO ma he thoat qua nhanh thi
   danh **THIEU CHO**, khong phai chay roi bao ket qua kem. `trail_tu_atr = 1.0`
   doi gia di 1 ATR **roi** hoi lai moi cat; mot lenh giu 1-2 bar thi ca hai
   viec do khong kip xay ra. Nguong: `bar_tv < 3`.
3. **`du_chan_quan_tri(ds)`** — cong: >= 3 bo luat da chay, co it nhat mot bo
   co dat hue va mot bo co trailing. Tra ve ly do tung dieu kien, khong chi
   True/False.

`so_luat` gio gan them `co_cho` / `ly_do_thieu_cho` vao moi dong.

## Chay that: AUDCAD H4, 20.902 bar (2013-02 -> 2026-07)

Tin hieu RSI dao chieu (n14, vao <30, ra >55) — gan voi he dang co trong bang.

| luat | lenh | bar_tv | cagr% | **cagr@DD20** | hon moc | cho |
|---|---|---|---|---|---|---|
| **khong_gi** | 249 | 20 | 1,55 | **3,45** | co | |
| sl2_tp4 | 332 | 16 | 1,17 | 2,32 | co | |
| sl2_tp4_hue1 | 393 | 10 | 0,86 | 1,61 | co | |
| sl2_tp6_hue2_trail2 | 345 | 14 | 0,80 | 1,52 | co | |
| sl2_tp4_chot1 | 332 | 16 | 0,75 | 1,46 | co | |
| sl3_trail2 | 294 | 20 | 0,72 | 1,20 | co | |
| sl2_trail1 | 485 | 7 | 0,20 | 0,25 | co | |
| chot_nhanh_sl1_tp1 | 1.116 | 2 | −1,52 | −1,22 | khong | **THIEU CHO** |

Cong quan tri: **DAT** (7 bo da chay · 2 co hue · 3 co trail · 0 thieu cho
trong nhom bat buoc).

## Ket qua nguoc voi gia dinh — va no hop ly

**Khong quan tri gi lai tot nhat** (3,45 so voi 2,32 cua bo tot nhat co quan tri).
Moi bo luat them vao deu **lam giam** lai tren cung ngan sach sut giam.

Khong mau thuan voi cac phep do cu, vi chung do tren **ho khac**:
- "entry sai van cho 92-97%/nam" do tren **luoi/DCA** — ho khong co diem thoat,
  quan tri la thu duy nhat dinh doat ket cuc.
- "trailing lai holdout x4,8" do tren he **xu huong** — co cho de gia chay.

Con day la **hoi quy**: tin hieu tu no da co diem ra (RSI > 55). Dat SL vao la
cat dung nhung lenh sap quay dau — tuc cat dung phan edge nam o. Bo
`chot_nhanh_sl1_tp1` cho thay ro nhat: 1.116 lenh, giu trung vi 2 bar, **am**.

=> Ket luan dung cua G3-A khong phai "quan tri lam he tot len", ma la:
**quan tri phai hop HO co che**, va bay gio he do duoc dieu do thay vi gia dinh.

## Rui ro con lai

- Moi chay tren MOT tin hieu / MOT tai san. Chua quet ca kho.
- Chua noi cong vao duong GHI SO: hien `du_chan_quan_tri` la ham goi duoc,
  chua ai bat buoc goi truoc khi `dang_ky_gia_thuyet`. Buoc sau.
- `BAR_TOI_THIEU_CHO_TRAIL = 3` la con so suy tu co che (1 ATR di + hoi lai),
  chua do bang quet. Nen do: ti le kich hoat trailing theo `bar_tv`.
- Ket qua tren la ban Python; chua qua MT5 tester.

## Test

`test_chan_quan_tri.py` — 10 bai, pass het. Dang chu y:
- ba bo bat buoc **deu ton tai that** trong `BO_LUAT` (tranh go ten sai roi cong
  khong bao gio mo)
- chan khi thieu dat hue · chan khi thieu trailing · chan khi chay < 3 bo
- `khong_gi` **khong** tinh la mot bo quan tri (no la MOC doi chieu)
- he giu 1 bar thi trailing bi danh **THIEU CHO**, khong phai AM
- chua do duoc `bar_tv` thi **khong ket luan**
