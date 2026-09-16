# EVO - SUC KHOE HE THONG

*2026-09-16 11:37:35*

TOT 21 · XAU 1 · CHUA DO 0

`CHUA_DO` khong phai `XAU`. Mot chi so khong do duoc thi noi la khong
do duoc - quy no ve 'xau' la cach mot bo giam sat tu bia ra van de.

| chi so | gia tri | trang thai | bang chung |
|---|---:|---|---|
| `seeker.ty_le_doc` | 0.667 | TOT | 8055/12078 tai lieu co ban van |
| `seeker.nguon_rong` | 2 | TOT | rong: mql5_ma_nguon, quantconnect |
| `quantlab.kho_co_che` | 4000 | TOT | 4000 co che, 3963 (99%) co truong `co_che` giai thich |
| `quantlab.ho_so_song` | 19.7 | TOT | HO_SO_SONG.json ghi lan cuoi cach day 20 gio |
| `quantlab.ho_so_mua_vu` | 73.2 | TOT | HO_SO_MUA_VU.json ghi lan cuoi cach day 73 gio |
| `quantlab.ho_so_tuong_quan` | 93.5 | TOT | HO_SO_TUONG_QUAN_D1.json ghi lan cuoi cach day 94 gio |
| `quantlab.ho_so_suy_nguoc` | 88.5 | TOT | SUY_NGUOC.json ghi lan cuoi cach day 89 gio |
| `quantlab.ho_so_to_hop` | 60.8 | TOT | TO_HOP.json ghi lan cuoi cach day 61 gio |
| `quantlab.ket_qua` | 1284 | TOT | 1284 dong trong ket_qua |
| `evo.van_de_mo` | 23 | TOT | 23 MO / 109 da sua |
| `evo.bai_hoc` | 238 | TOT | 238 the bai hoc |
| `evo.finder` | 40.7 | TOT | san_cong_cu = Finder cua so do |
| `xay.hang_doi` | 31 | TOT | {'xong': 23, 'cho': 8} |
| `xay.viec_hong` | 0 | TOT |  |
| `may.mo_coi` | 2 | XAU | 2 tien trinh, 34% CPU |
| `phanh.chua_khai` | 0 | TOT | 1/1 he da khai han muc |
| `phanh.vua_ngat` | 0 | TOT | chua he nao vuot tran |
| `thong_luong.tang_cam` | 0 | TOT | 9 tang deu co dau ra |
| `thong_luong.nut_that` | ban doc -> thanh phan 4.1% | TOT | 6907 vao -> 285 ra. Day la cho dang gioi han san luong ca he - noi rong cho khac khong lam |
| `dia.con_trong` | 25.1 | TOT | 25.1 GB trong / 119 GB tong (79% da dung) |
| `dia.nao_db` | 1521 | TOT | bang `noi_dung` (toan van tai lieu) chiem phan lon - do la du lieu THAT, khong phai rac; m |
| `dia.wal` | 0 | TOT | khong co WAL ton dong |

## Van de + cat nghia + de xuat

### `may.mo_coi` — tien trinh mo coi dang an CPU

**Do duoc:** 2 tien trinh, 34% CPU

**Cat nghia:** Tien trinh mo coi an het CPU -> bo dieu toc cua qwen tu choi phong viec -> he nam im voi bang viec day. Khong loi, khong canh bao. Nguon goc thuong la `nohup ... &`: cha thoat nhung Pool de lai worker, va Pool SINH LAI khi con chet nen phai giet CA CAY tu goc.

**De xuat (chay duoc):**

```
python -m nhan.don_mo_coi --don
```

