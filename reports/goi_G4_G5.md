# GOI G4 + G5 · 16/09/2026

## G4 — DANH MUC LA CONG BAT BUOC

### Chan that: he chi co MOT thanh phan

`danh_muc_hien_tai("PASS")` tra ve:

```
n = 1 · cum = [["AUDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55"]]
tuong_quan_duoi_lon_nhat = 0.0 · ghep_co_hon_cai_tot_nhat = false
mua_giu = null · "chua co moc mua-giu - khong ket luan duoc gi ve %/nam"
```

**Khong the bat `danh_muc` lam cong bat buoc khi ca he chi co mot chan.** Do la
chan that cua G4, va no nam o TREN: chi mot gia thuyet trong so co chuoi holdout
dung lai duoc.

### Da sua: mot chan phai mang nhan CHUA_DO_DUOC

Cai nguy khong phai viec tinh mot chan, ma la **bang ket qua doc y het mot danh
muc da duoc do**: moi so bang dung so cua chan duy nhat, con cot tuong quan dep
chi vi khong co gi de tuong quan voi.

`CHAN_TOI_THIEU = 2` + `du_chan_de_ghep()`. `ghep()` dan `trang_thai:
CHUA_DO_DUOC` + `ly_do_chua_do`.

### Mot lan sua sai, va bo test bat duoc

Ban dau toi **chan thang** `ghep()` khi n < 2. Hai bai test co san do ngay:
chung goi `ghep()` voi mot chan de kiem nhanh so voi mua-giu — viec hop le.
Doi sang DAN NHAN thay vi chan: ca hai xanh lai, va cai nguy van duoc xu ly.

### Chua lam

- Doi don vi co ban cua pheu thanh `ho1 x ho2`: `du_chan_quan_tri` (G3-A) da co
  nhung chua noi vao duong GHI SO.
- Kiem lai "6,14% -> 20,25%/nam cung DD" bang tester: can >= 2 chan.

---

## G5 — TANG SAN PHAM

### 5.1 Danh sach chan VPS: 27 -> 25 cho (do that)

`san_sang_vps.duong_dan_go_cung` dem ca `_luu_tru/` — thu muc script mo coi
vua chuyen ra o goi G3-D. Chung **khong nam tren duong chay nao**, nen mot
duong dan go cung trong do khong chan viec chuyen VPS.

Them `_luu_tru` vao `BO_QUA`. Con **25 cho / 50 lan**, va day la so THAT:
`chup_darwinex.py` x6 · `chay_tester_z5.py` x5 · `cross_pair_quet.py` x4 ·
`ea_tu_dong.py` x4 · `mt5_chay_ichimoku.py` x4 · `chi_phi.py` x2 ...

Mot danh sach viec co muc gia khong dung thi nguoi doc bo qua ca danh sach.

### 5.2 Cat 60% dung luong phai mang len VPS

`san_sang_vps` bao phai mang **1,77 GB**, trong do `nao.db` la 1,59 GB. Do
bang `freelist_count`:

```
389.491 trang · 231.684 trang TRONG (59,5%)
1,595 GB tong · 0,949 GB trong · 0,646 GB du lieu that
```

Them `so.nen_gon(dich)` dung `VACUUM INTO`. Do that:

```
nen gon: 1.59 GB -> 0.64 GB (tiet kiem 0.95 GB) · 5 giay
```

Chon `VACUUM INTO` chu khong `VACUUM`:
- nguon CHI DOC — khong co luc nao DB dang chay bi viet lai;
- khong can cho trong bang kich thuoc DB tren cung o dia;
- tien trinh khac dang ghi cung khong sao — ban ra la anh chup.

Dung duoc ngay cho **hai viec**: sao luu gon (backup API o goi G0 chep ca trang
trong, ton 1,60 GB cho 0,65 GB du lieu), va mang len VPS.

### 5.3 Chua lam

- EA nhieu slot nap danh muc tu G4: G4 chua co danh muc >= 2 chan.
- `so_lenh` chay PAPER va doi chieu tung lenh voi backtest cung ky.
- `suy_giam` vao nhip ngay + canh bao ve dien thoai.
- Khong bat tien that — dung nguyen tac cua goi G5.

## Test

`test_danh_muc_chan.py` 6 bai · `test_so_ghi_lo.py` 11 bai (them 3 cho nen gon:
khong dong vao ban goc · tu choi ghi de · do trang trong tra du khoa).
Hoi quy `danh_muc/bang_he/cong_ra_tien`: 46 passed.
