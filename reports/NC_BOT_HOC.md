# DAU TRUONG BOT TU HOC - chuoi co dap an

*2026-09-29 02:42:45 · `b nc bot 5` (nhan/nc_bot_hoc.dau_truong), 100000 buoc hoc moi bot*

Bot kieu quang cao (A) va bot can than (B) hoc tren kham pha, thi tren xac nhan -> niem phong (chi mo niem phong khi xac nhan DAT). DAT = >= 20 lenh va lai sau phi > 0. So la so chuoi DAT tren 5 hat moi kich ban.

| kich ban | edge that | bot A | bot B | loi cu (tu lai, khong biet truoc) | Avg(1000) luc hoc A | Avg(1000) luc hoc B |
|---|---|---:|---:|---:|---|---|
| NHIEU | KHONG | 0/5 | 0/5 | 0/5 | +21.4..+28.2 | +10.0..+16.4 |
| BETA | KHONG | 0/5 | 0/5 | 0/5 | +24.6..+28.0 | +10.1..+14.4 |
| HOI_QUY | co | 0/5 | 0/5 | 5/5 | +24.8..+30.9 | +12.8..+15.5 |
| HOI_QUY_YEU | co | 0/5 | 0/5 | 1/5 | +25.1..+28.6 | +11.1..+15.4 |
| LOC | co | 1/5 | 5/5 | 3/5 (mo xe lenh tim dung bo loc 5/5) | +27.8..+34.9 | +17.1..+20.9 |

## Tung lan chay

| bot | chuoi | Avg(1000) cuoi | t kham pha | xac nhan bps (lenh) | niem phong bps (lenh) | ti le mua np | DAT |
|---|---|---:|---:|---:|---:|---:|---|
| A | TONG_HOP_NHIEU_1 | 24.88 | 28.97 | -6.01 (330) | -1.88 (322) | 0.51 | - |
| B | TONG_HOP_NHIEU_1 | 12.72 | 6.38 | -1.56 (297) | -7.73 (292) | 0.46 | - |
| A | TONG_HOP_NHIEU_2 | 25.68 | 32.27 | -7.19 (332) | -4.91 (327) | 0.53 | - |
| B | TONG_HOP_NHIEU_2 | 16.01 | 8.99 | -3.12 (295) | -1.11 (292) | 0.6 | - |
| A | TONG_HOP_NHIEU_3 | 28.24 | 30.76 | -4.03 (332) | -2.89 (332) | 0.51 | - |
| B | TONG_HOP_NHIEU_3 | 16.45 | 6.16 | -4.91 (309) | -3.35 (303) | 0.51 | - |
| A | TONG_HOP_NHIEU_4 | 25.96 | 31.8 | -1.87 (308) | 0.68 (309) | 0.52 | - |
| B | TONG_HOP_NHIEU_4 | 13.5 | 4.89 | -4.36 (307) | -5.6 (316) | 0.51 | - |
| A | TONG_HOP_NHIEU_5 | 21.37 | 27.52 | -7.28 (315) | -2.21 (319) | 0.47 | - |
| B | TONG_HOP_NHIEU_5 | 9.99 | 6.39 | -6.94 (280) | -9.32 (287) | 0.48 | - |
| A | TONG_HOP_BETA_1 | 25.7 | 32.71 | -2.77 (348) | -0.17 (348) | 0.48 | - |
| B | TONG_HOP_BETA_1 | 13.1 | 7.25 | -2.34 (319) | -6.9 (313) | 0.55 | - |
| A | TONG_HOP_BETA_2 | 24.61 | 29.82 | -5.83 (323) | -3.47 (334) | 0.48 | - |
| B | TONG_HOP_BETA_2 | 12.61 | 6.22 | -0.63 (300) | -1.52 (303) | 0.47 | - |
| A | TONG_HOP_BETA_3 | 25.06 | 32.14 | -3.57 (322) | 1.19 (328) | 0.59 | - |
| B | TONG_HOP_BETA_3 | 14.45 | 8.22 | -7.46 (309) | -2.3 (308) | 0.56 | - |
| A | TONG_HOP_BETA_4 | 27.96 | 33.79 | -2.76 (323) | -1.68 (334) | 0.56 | - |
| B | TONG_HOP_BETA_4 | 10.06 | 8.06 | 1.98 (317) | -1.43 (322) | 0.55 | - |
| A | TONG_HOP_BETA_5 | 27.19 | 28.89 | -4.49 (320) | 0.11 (324) | 0.64 | - |
| B | TONG_HOP_BETA_5 | 12.11 | 7.83 | -5.56 (294) | -1.95 (293) | 0.53 | - |
| A | TONG_HOP_HOI_QUY_1 | 30.88 | 28.71 | -5.41 (339) | 3.98 (330) | 0.61 | - |
| B | TONG_HOP_HOI_QUY_1 | 15.47 | 7.72 | -2.79 (307) | 2.04 (308) | 0.58 | - |
| A | TONG_HOP_HOI_QUY_2 | 26.07 | 30.56 | -6.2 (337) | -1.86 (349) | 0.43 | - |
| B | TONG_HOP_HOI_QUY_2 | 13.6 | 6.69 | -4.34 (318) | -3.6 (311) | 0.54 | - |
| A | TONG_HOP_HOI_QUY_3 | 29.19 | 31.36 | -5.06 (331) | 0.33 (334) | 0.56 | - |
| B | TONG_HOP_HOI_QUY_3 | 12.81 | 9.28 | -4.4 (318) | -6.17 (319) | 0.64 | - |
| A | TONG_HOP_HOI_QUY_4 | 30.32 | 29.57 | -2.78 (325) | -3.3 (326) | 0.52 | - |
| B | TONG_HOP_HOI_QUY_4 | 14.49 | 7.4 | -3.0 (330) | -4.24 (331) | 0.48 | - |
| A | TONG_HOP_HOI_QUY_5 | 24.84 | 28.11 | -5.03 (334) | -2.89 (329) | 0.49 | - |
| B | TONG_HOP_HOI_QUY_5 | 15.01 | 7.25 | -7.87 (308) | -0.69 (305) | 0.54 | - |
| A | TONG_HOP_HOI_QUY_YEU_1 | 25.07 | 28.6 | -1.63 (338) | -5.16 (324) | 0.52 | - |
| B | TONG_HOP_HOI_QUY_YEU_1 | 12.98 | 8.33 | -2.71 (301) | -0.51 (304) | 0.47 | - |
| A | TONG_HOP_HOI_QUY_YEU_2 | 25.36 | 30.39 | 2.08 (337) | -5.72 (332) | 0.47 | - |
| B | TONG_HOP_HOI_QUY_YEU_2 | 13.78 | 6.88 | -6.52 (293) | -7.11 (292) | 0.32 | - |
| A | TONG_HOP_HOI_QUY_YEU_3 | 28.65 | 31.52 | -2.08 (323) | -1.64 (326) | 0.48 | - |
| B | TONG_HOP_HOI_QUY_YEU_3 | 11.13 | 7.78 | -4.51 (303) | -0.18 (303) | 0.51 | - |
| A | TONG_HOP_HOI_QUY_YEU_4 | 26.53 | 31.96 | -2.38 (313) | -6.25 (316) | 0.53 | - |
| B | TONG_HOP_HOI_QUY_YEU_4 | 15.43 | 5.67 | -2.89 (320) | -0.52 (312) | 0.65 | - |
| A | TONG_HOP_HOI_QUY_YEU_5 | 26.29 | 30.2 | -6.12 (325) | -1.88 (324) | 0.57 | - |
| B | TONG_HOP_HOI_QUY_YEU_5 | 12.88 | 7.15 | -3.75 (308) | -2.35 (311) | 0.53 | - |
| A | TONG_HOP_LOC_1 | 29.0 | 31.51 | 2.68 (311) | 0.46 (311) | 0.54 | DAT |
| B | TONG_HOP_LOC_1 | 17.07 | 9.17 | 1.03 (300) | 2.76 (300) | 0.49 | DAT |
| A | TONG_HOP_LOC_2 | 27.76 | 30.01 | 4.8 (318) | -3.83 (317) | 0.52 | - |
| B | TONG_HOP_LOC_2 | 18.5 | 8.1 | 3.88 (294) | 0.93 (304) | 0.52 | DAT |
| A | TONG_HOP_LOC_3 | 34.88 | 30.35 | 2.28 (324) | -5.04 (318) | 0.46 | - |
| B | TONG_HOP_LOC_3 | 20.11 | 8.9 | 1.01 (306) | 0.99 (297) | 0.47 | DAT |
| A | TONG_HOP_LOC_4 | 31.6 | 32.06 | 4.03 (333) | -0.13 (340) | 0.49 | - |
| B | TONG_HOP_LOC_4 | 20.93 | 11.12 | 6.66 (308) | 3.12 (305) | 0.49 | DAT |
| A | TONG_HOP_LOC_5 | 28.98 | 30.81 | -2.93 (322) | -1.17 (323) | 0.57 | - |
| B | TONG_HOP_LOC_5 | 17.76 | 6.08 | 7.12 (304) | 1.36 (306) | 0.43 | DAT |

Doc: Avg(1000) luc hoc - con so quang cao khoe - duong ca tren NHIEU THUAN. No do viec bot nho du lieu da thay, khong do edge. Chi cot DAT (xac nhan roi niem phong) la cau tra loi.
