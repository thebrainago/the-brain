# SWAP - THUOC DO "SAU PHI QUA DEM" (09/10/2026)

Doc truoc khi tin bat ky con so `DAT` / lai nao do bang MT5 tester cua luoi / DCA / martingale.

## 1. Phat hien (do that, khong phai suy luan)

MT5 tester **khong ghi swap**: cot Swap = 0 tuyet doi o 286/286 hang hieu chuan da luu va o 3 bao cao tester
that doc lap (khong phai "it" - la dung 0). Tai khoan that (XM) tru / cong swap moi dem. He qua:

- Con so lai cua tester la **truoc swap**. Luoi / DCA giu lenh lau nen chiu swap nhieu nhat: do uoc luong
  ~4-5 %/nam. Tren 61 o hieu chuan tester-duong thi **22 o thanh <= 0** sau swap.
- Engine `nhan/luoi.py` co tru swap (`phi_nam_mua/ban`) nen lech tester ~3 diem %/nam o rieng khoan nay -
  mot phan "lech" cu thuc ra la tester thieu, khong phai engine sai.
- Cong `DAT` cua `ea_tho` (lai sau phi + maxDD < 80%) truoc 09/10 doc tren thuoc do truoc swap -> **cac DAT
  tester cu cua luoi / DCA co the cao hon tai khoan that vai diem %/nam**. Xem lai chung khi co du lieu.

## 2. Da lam gi (code)

| Cho | Thay doi |
|---|---|
| `nhan/swap_uoc.py` (moi) | Uoc swap tu CHINH bang lenh tester: dem nua dem (00:00 gio may chu, thu Tu x3, thu Bay/CN 0; ma khong phai FX tinh lien tuc), he so tien K uoc tu P&L tester (>= 20 lenh dong), tach `phoi_bay` (khong phu thuoc ty le) va `ap_ty_le`. |
| `nhan/ea_tho.py` | `phan_quyet(..., swap=)`: lai sau swap moi xet DAT; `cagr_pct` la so SAU swap, `cagr_truoc_swap_pct` la so tester goc. Canh bao: swap + maxDD sat tran 80%, DAT nho carry duong. |
| `nhan/hieu_chuan_luoi.py` | So sanh engine <-> tester co them dong "sau swap" (`ra["swap"]`, `ra["so_khoa_swap"]` = [tester sau swap, swap uoc, engine swap]). Phan tester van cache `PHIEN_BAN="1"` - may nha KHONG phai chay lai tester. |
| `qwen/cau_trang.py`, `qwen/cau_git.py` | Danh sach trang cho `nhan.swap_uoc --quet reports/hieu_chuan --ra reports/hieu_chuan/swap_*.json`; the nang luc `swap-v1` (don chi chay o may co ma moi). |
| `nhan/nc_cong_cu.py` | Mo ta cong cu `ea_tho_chay` noi ro lai da SAU swap. |

## 3. Quy tac (khong duoc pha)

1. **Khong doan ty le.** Khong co ty le swap/nam cua ma (`luoi.QC_AUDCAD` hoac `chi_phi.phi_cua`) -> `khong_uoc_duoc`, khong cong so nao.
2. **Khong tinh hai lan.** Tester CO ghi swap khac 0 -> dung so DO (`nguon = "do"`), khong cong them uoc.
3. **Niem phong chan khi mu swap.** Doan `niem_phong` ma bao cao co bang Deals doc duoc nhung swap khong uoc duoc ->
   `CHUA_DO_DUOC` loai `ha_tang`; **khong tieu lan niem phong mot lan duy nhat**. Bao cao chi co phan tom tat (khong bang lenh) thi
   khong chan (khong co gi de uoc) nhung `goi_ten_dung` ghi "CHUA tinh swap".
4. **maxDD khong sua** (tester khong ve duong von sau swap): chi canh bao khi `maxDD + toan bo swap` >= 80%.
5. **Swap DUONG (carry) cung tinh doi xung** nhung bi canh bao: ty le la bang HIEN TAI cua san, khong phai ty le lich su.

## 4. Doc ket qua the nao

Trong `chi_so` cua ket qua `ea_tho_chay`:
`swap_nguon` ('do' | 'uoc' | 'khong_uoc_duoc'), `swap_tien` (tien tai khoan, am = ton), `lai_sau_swap`,
`cagr_truoc_swap_pct` (so tester goc), `swap_ly`, `swap_ty_le_nguon`. Thieu cac khoa nay = ket qua cu (truoc 09/10) hoac
khong co bang lenh -> lai la **truoc swap**.

## 5. Gioi han trung thuc

- Ty le swap la bang HIEN TAI cua XM, ap cho ca lich su (xap xi). Mot ma doi ty le theo nam thi con so chi dung ve cap do lon.
- Ma khong phai FX tinh swap lien tuc theo ngay lich (chua biet ngay x3 cua tung san) - sai nho so voi rollover that.
- K (tien/ don vi gia/ lot) uoc tu P&L tester: can >= 20 lenh dong. It hon -> khong uoc.
- Chua co duong von sau swap -> maxDD chi canh bao, chua chinh.
- Bang lenh tester nam o may nha (`*_lenh.csv.gz`, khong vao git). Linux/cloud KHONG tu chay duoc: phai nho may nha gom.

## 6. May nha lam gi

1. Mot lan: cap nhat ma (hai thu `20261008-094857-6bd4` va `NHA-HOI-PHUC-08102026`).
2. Don gom (an toan, NHE): `python -m nhan.swap_uoc --quet reports/hieu_chuan --ra reports/hieu_chuan/swap_gom.json`
   -> A_mua / A_ban cua moi hang da luu; cloud doc, doi ty le tai cho, khong can bang lenh. Nhan ket qua vao so tay `b nc`.
3. Mot lan `b nc cc ea_tho_chay` voi ma moi se co `chi_so.swap_*` ngay.
