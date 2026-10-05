# S1 - THU CHUYEN BOT SANG THI TRUONG KHAC: KET QUA GIAI DOAN 2 (05/10/2026)

**Doc truoc (loi thuong).**
1. Thi nghiem chay tren the gioi NHAN TAO (co dap an dung de do), nen day la ket qua ve CO CHE chuyen / tim tham so, **khong phai bang chung loi nhuan** va khong noi bot nao co lai that.
2. Cach chuyen co ban (T0: doi khoang cach theo ti le bien do / chi phi, giu so tang) **tot hon han "khong doi gi"**: sai lech trung vi 0,047 so voi 0,212 (B0, giu nguyen) va 0,600 (B1). Day la ket qua tot.
3. **Tim kiem thong minh (SMART) KHONG thang tim ngau nhien (RANDT)** theo nguong da dong bang - **xau hon**: o ca 3 do rong (top 1/4/12) khoang tin cay cua hieu SMART - RANDT nam han tren 0 (+0,049 / +0,034 / +0,023), SMART chi tot hon RANDT o 1 - 3 trong 14 tang.
4. Tim kiem thong minh cung **khong vuot T0** (tuc cach chuyen co ban): hieu +0,025 (top 1, xau hon) roi gan 0 o top 4 / 12. Ngay ca tim het luoi (FULL, 0,056 - 0,075) cung khong tot hon T0 (0,047) - phan lon gia tri nam o cach chuyen ban dau, khong o tim them.
5. SMART chi thang ro khi so voi tim ngau nhien KHONG co diem khoi dau T0 (RAND / RAND_S, o ngan sach nho: -0,061 / -0,079) - nghia la tim thong minh co ich khi chua co cach chuyen tot, dung nhu mong doi, nhung khong them gi khi da co T0.
6. Ket luan theo nguong dong bang (plan_hash `cf3680039615c56f`): **KHONG dat "thong minh hon ngau nhien"**. Khuyen nghi: giu T0 + cach dich co so (w = 1, tam I6) lam mac dinh; khong dau tu them vao tim kiem thong minh cho buoc nay. Quyet S0 doi hay giu thuoc chu du an.

## Con so chinh (sai lech so voi dap an, thap hon = tot hon; trung vi tren 168 cap)
| Quy trinh | trung vi | Ghi chu |
|---|---|---|
| T0 (cach chuyen co ban) | 0,047 | tot nhat hoac ngang tot nhat |
| RANDT top 1 / 4 / 12 | 0,054 / 0,050 / 0,047 | ngau nhien co khoi dau T0 |
| SMART top 1 / 4 / 12 | 0,087 / 0,078 / 0,070 | tim thong minh |
| FULL_PLAT 1 / 4 / 12 | 0,063 / 0,069 / 0,075 | tim het luoi |
| RAND top 1 / 4 / 12 | 0,100 / 0,094 / 0,078 | ngau nhien khong khoi dau T0 |
| B0 giu nguyen | 0,212 | |
| B1 | 0,600 | |
Cap doi (14 tang = 7 kich ban x 2 phong cach): SMART vs RANDT hieu +0,049 [0,028; 0,071] (top 1). SMART vs B0 / B1: -0,21 / -0,47 (thang, dat nguong 0,8).

## Gioi han (khong duoc quen)
- The gioi tao ra **nang chi phi hon thuc te** (nguong dong bang ghi ro); so tuyet doi khong mang ra thi truong that duoc.
- Z0 (the gioi ma dap an dung CHINH LA cach khong doi gi): T0 va B0 dung 0,000, nhung SMART lech 0,058 - 0,063 va RANDT 0,009 - tuc **tim kiem thong minh lam HONG dap an da dung** (xau hon tim ngau nhien). Day la mot ly do nua de khong tin vao buoc tim them.
- The gioi NHIEU (N0, N0_re: khong co dap an) chi do ty le "dat gia"; ty le dat sau xac nhan cua B0 chi 15,6%, FULL tot hon (32% - 44%) - xem `nhieu`. Khong ket luan loi nhuan.
- Hang o duoi 2 buoc nen (ty_le_duoi_phan_giai) la CHUA_DO_DUOC, khong phai am: B0 7%, B1 21%, cac quy trinh tim 0%.
- Chua co hieu chuan tester that; moi thu o day chay tren mo phong. Khong niem phong gi.

Tep: `reports/thu_chuyen/p2/` (21 tep, 12 hat x 2 phong cach x kich ban + nhieu), `reports/thu_chuyen/p2_tong_hop.json`.
