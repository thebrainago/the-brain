# Bang tom tat luoi/DCA cua nguoi thang MQL5 - cai dat HIEN TAI (tu 2025-07-01)

Nguon: export chinh thuc /signals/ID/export/positions, lay bang thao tac man hinh tren Chrome that (04/10/2026). Tep tho o du_lieu_cao/mql5/ (gitignore, KHONG vao git). `boc_lich_su` ma = symbol chinh, M15, gt_id 4. Phi = hoa hong + swap tren lai gop (CHUA co spread). maxDD cong bo CHUA lay (can trang tom tat). Cai dat la GIA THUYET suy tu lenh, khong phai su that.

| id | symbol | lenh | lai rong sau phi (USD) | phi/lai gop | buoc | he so buoc | TP | kieu lot / he so | lot goc | tran tang | % lai tu ro 1 lenh | ro (thua) | che do |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1975768 | AUDCAD | 140 | 937.65 | 0.219 | 25.8 | 0.98 | - | cong / 0.07 | 0.10 | 9 | 55 | 62 (12) | hai_chieu |
| 2184802 | AUDCAD | 335 | 865.84 | 0.212 | 30.1 | - | - | cong / 0.14 | 0.03 | 9 | 56 | 178 (4) | hai_chieu |
| 1059619 | NZDCAD | 191 | 932.56 | 0.143 | 27.1 | 1.02 | - | None / - | 0.11 | 7 | 41 | 94 (23) | hai_chieu |
| 1502590 | GBPAUD | 168 | 495.93 | 0.319 | - | - | - | None / - | - | None | 100 | 168 (8) | None |
| 956328 | USDJPY | 229 | 19.73 | 0.543 | - | - | - | None / - | - | None | -61 | 109 (30) | None |
| 2126101 | EURUSD | 370 | 298.79 | 0.180 | - | - | - | None / - | - | None | 58 | 202 (22) | None |
| 1627034 | EURUSD | 257 | 2316.44 | 0.155 | - | - | - | None / - | - | None | 43 | 152 (9) | None |
| 2196457 | GOLD(XAU) | 580 | 6656.97 | -0.000 | - | - | - | None / - | - | None | -1 | 157 (59) | None |
| 2195619 | XAUUSD | 534 | 4382.23 | 0.009 | - | - | - | None / - | - | None | -3 | 156 (66) | None |
| 2084890 | XAUUSD | 286 | 4566.17 | 0.019 | - | - | - | None / - | - | None | 4 | 77 (41) | None |

## Doc (nha, 04/10/2026)
- Chi 3/10 con ra cau truc luoi ro: 1975768 va 2184802 (AUDCAD), 1059619 (NZDCAD). Hai con AUDCAD: buoc 25,8 / 30,1 pip, lot cong 0,07 / 0,14, tran tang 9 - GAN NHAU nhung KHAC con 2023752 (buoc 21, he so lot 0,25, tran 5, TP 7,6). Chua co cum chat; chua du de noi "tac gia doc lap chon cung cai dat".
- 7 con con lai (GBPAUD, USDJPY, 2 EURUSD, 3 vang): engine khong suy ra tham so luoi (tham so = -). Vang: phi/lai gop ~0 va ty le lai tu ro 1 lenh ~0 -> co the khong phai luoi theo ro; USDJPY 956328 lai rong chi 19,7 USD, phi 54% lai gop.
- "% lai tu ro 1 lenh" am o 956328: ro 1 lenh LO, lai den tu ro nhieu tang. Gia tri 100 o 1502590 la ro 1 lenh chiem toan bo lai.
- Tong thu lai nhung con nay trong cua so 2025-07..2026-10 chi la mo ta, khong phai bang chung (nguoi thang chon theo ket qua).
