# EVO - SUC KHOE HE THONG

*2026-09-20 19:22:42*

TOT 15 · XAU 4 · CHUA DO 1

`CHUA_DO` khong phai `XAU`. Mot chi so khong do duoc thi noi la khong
do duoc - quy no ve 'xau' la cach mot bo giam sat tu bia ra van de.

| chi so | gia tri | trang thai | bang chung |
|---|---:|---|---|
| `seeker.ty_le_doc` | 0.0 | XAU | 0/0 tai lieu co ban van |
| `seeker.nguon_rong` | 38 | XAU | rong: arxiv, blog, cnblogs_trung, collective2, crossref, darwinex, elitetrader, etoro, fac |
| `quantlab.kho_co_che` | 4049 | TOT | 4049 co che, 4012 (99%) co truong `co_che` giai thich |
| `quantlab.ho_so_song` | 41.6 | TOT | HO_SO_SONG.json ghi lan cuoi cach day 42 gio |
| `quantlab.ho_so_mua_vu` | 41.6 | TOT | HO_SO_MUA_VU.json ghi lan cuoi cach day 42 gio |
| `quantlab.ho_so_tuong_quan` | 41.6 | TOT | HO_SO_TUONG_QUAN_D1.json ghi lan cuoi cach day 42 gio |
| `quantlab.ho_so_suy_nguoc` | 41.6 | TOT | SUY_NGUOC.json ghi lan cuoi cach day 42 gio |
| `quantlab.ho_so_to_hop` | 41.6 | TOT | TO_HOP.json ghi lan cuoi cach day 42 gio |
| `quantlab.ket_qua` | 0 | XAU | 0 dong trong ket_qua |
| `evo.van_de_mo` | 1 | TOT | 1 MO / 12 da sua |
| `evo.bai_hoc` | 3 | XAU | 3 the bai hoc |
| `evo.finder` | 41.6 | TOT | san_cong_cu = Finder cua so do |
| `xay.hang_doi` | 31 | TOT | {'xong': 23, 'cho': 8} |
| `xay.viec_hong` | 0 | TOT |  |
| `may.mo_coi` | 0 | TOT | 0 tien trinh, 0% CPU |
| `phanh.doc_duoc` | None | CHUA_DO | OperationalError: no such table: he_chay |
| `thong_luong.tang_cam` | 0 | TOT | 9 tang deu co dau ra |
| `dia.con_trong` | 29.5 | TOT | 29.5 GB trong / 252 GB tong (3% da dung) |
| `dia.nao_db` | 0 | TOT | bang `noi_dung` (toan van tai lieu) chiem phan lon - do la du lieu THAT, khong phai rac; m |
| `dia.wal` | 0 | TOT | khong co WAL ton dong |

## Van de + cat nghia + de xuat

### `seeker.ty_le_doc` — tai lieu da LAY DUOC TOAN VAN

**Do duoc:** 0/0 tai lieu co ban van

**Cat nghia:** Tai lieu vao kho nhung khau LAY TOAN VAN khong theo kip. Thuong la hang doi doc bi URL chet chiem cho (da xay ra: 406 URL TradingView chet lam bao 'het ton kho').

**De xuat (chay duoc):**

```
python -m nhan.day_chuyen boc   # lay toan van cho phan con lai
```

### `seeker.nguon_rong` — nguon chua mang ve tai lieu nao

**Do duoc:** rong: arxiv, blog, cnblogs_trung, collective2, crossref, darwinex, elitetrader, etoro, facebook, fxblue

**Cat nghia:** Nguon co the bi CHAN tren may nay, hoac bo doc cua no chua tung duoc goi. Hai chuyen khac han nhau - phai do tung nguon truoc khi goi la 'nguon chet'.

**De xuat (chay duoc):**

```
python -m nhan.kham_pha_nguon   # do lai tung nguon, tach 'chan' khoi 'chua chay'
```

### `quantlab.ket_qua` — ket qua da cham cong

**Do duoc:** 0 dong trong ket_qua

**Cat nghia:** Co che co nhung khong ai cham cong - duong tu kho den cong bi dut.

**De xuat:** chua co lenh san - can nguoi quyet dinh.

### `evo.bai_hoc` — bai hoc da rut

**Do duoc:** 3 the bai hoc

**De xuat:** chua co lenh san - can nguoi quyet dinh.

## Chua do duoc (KHONG phai ket luan am)

- `phanh.doc_duoc`: OperationalError: no such table: he_chay

