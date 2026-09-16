# GOI G3-D — DON GOC `lab/` · 16/09/2026

**Noi ngan:** no that 84 -> **65**. Khong xoa file nao; 19 file chuyen vao
`_luu_tru/` va them 10 docstring.

## Cach chon file de chuyen — ba dieu kien, du CA BA

1. `b kien-truc` xep vao nhom **no that** (khong phai `test_*`, khong phai
   `_*.py` chay tay);
2. **mo coi**: khong duong chay nao toi duoc (`b.py`, `dieu_phoi.py`,
   `day_viec.py`, `qwen/NHIEM_VU.json`, `.cmd`/`.bat`);
3. **khong file `.py` nao import**, va khong tai lieu nao nhac den.

Dieu kien 3 la cho de sai nhat. Lan quet dau: **40/40 file "co nhac den"** — va
nhin ky thi ho nhac trong `BAN_DO.md`, `KIEN_TRUC.md`, `INVENTORY_THE_BRAIN.md`,
`nhat_ky/`, ban giao cu. Do la nhung ban **LIET KE tu sinh**: chung ke moi file
co trong lab, ke ca file chet. Dem chung la tham chieu thi **khong file nao doi
duoc**, va ca phep do tro thanh vo nghia.

Sau khi bo cac ban liet ke tu sinh: **19 khong tham chieu that** (chuyen),
**21 co** (giu lai).

## Da chuyen (19)

`bao_cao_hen_gio` · `chay_backtest` · `chay_gop_vs_don` · `chien_luoc_mr_tf` ·
`chien_luoc_trend` · `dang_ky_alphavantage` · `do_spread_hang_loat` ·
`doc_for_ds` · `doc_otp_gmail` · `gen_kiem_ke` · `lay_api_darwinex` ·
`lay_api_darwinex_v2` · `lo_mot_gio` · `nap_darwinex_api` · `nap_lai_ban_tho` ·
`p_null_vs_ung_vien` · `placebo_d1` · `tele_gate` · `xac_nhan_d1`

`git mv` chu khong `rm`: `git log --follow` doc duoc het, va dua nguoc lai la
mot lenh. `_luu_tru/DOC_TRUOC.md` ghi dieu kien va canh bao **dung khoi phuc
nguyen xi** — phan lon chung trung viec voi `nhan/` (`nguon_telegram` so voi
`nhan/telegram`, `nguon_kham_pha` so voi `nhan/kham_pha_nguon`).

## Giu lai (21) va ly do

Co tai lieu THAT nhac den: `DAI_CUONG.md`, `MULTI_AGENT.md`, `KHUNG.md`,
`roles/QUANTLAB.md`, `config/tai_nguyen.json`, `BAN_GIAO.json`, `HANDOFF*.md`.
Chuyen chung di la lam hong mot huong dan dang dung. Chung can xu ly TUNG CAI:
hoac noi vao duong chay, hoac sua tai lieu truoc roi moi chuyen.

## Docstring (10 file)

`chien_luoc_mr` · `doc_email` · `vao_web` · `nhan/nha_may_null` · va 6 file
`test_*_v2`. Muc 4.1 cua `b kien-truc`: **25 -> 15**, va 15 con lai deu da nam
trong `_luu_tru/`.

## So truoc / sau

| | Truoc | Sau |
|---|---|---|
| File goc `lab/` | 362 | 348 |
| — `test_*` (dung cho) | 147 | 152 |
| — `_*.py` chay tay | 131 | 131 |
| — **no that** | **84** | **65** |
| Khong khai vai tro | 25 | **15** (deu trong `_luu_tru/`) |

## Rui ro con lai

- 65 file no van con, trong do 32 **dang tren duong chay** (khong phai no ve
  chuc nang, ma la "dang o goc thay vi trong `nhan/`"). Chuyen chung can sua
  import — viec rui ro hon, nen tach ra lam sau.
- 21 file co tai lieu nhac den chua dung toi.
- Khong file nao bi xoa, nen dia khong giam. Muc tieu goi nay la **doc duoc**,
  khong phai tiet kiem cho.

## Test

`-k "ban_do or kien_truc or bang_he or slot or ghi_an_toan or so_ghi_lo or
quan_tri or ngan_sach"` -> **180 passed, 1 skipped**. `pytest --co` thu gom ca
bo: khong loi import nao sau khi di chuyen.
