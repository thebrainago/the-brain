# Hinh dang co phan biet duoc voi ngau nhien khong?

> Cung mot luoi lan can, chay tren holdout THAT va tren chuoi NULL sinh
> tu chinh no. Cot `p` = ty le chuoi null dat toi hoac hon gia tri that
> (co +1 hieu chinh, nen p nho nhat la 1/(so_null+1)). Khong tieu suat
> FDR, khong cap phan quyet.

- do duoc: **279/368** ung vien (alpha duong 115 · alpha am 164)

**Chi dem tren ung vien co ALPHA DUONG** — mot he lo tien deu hon null cua no thi khong phai phat hien:
- **alpha o tam**: trung vi p = 0.208 · p<=0,05: **7/115** (ky vong ngau nhien 5.8)
- **ty le o duong**: trung vi p = 0.178 · p<=0,05: **11/115** (ky vong ngau nhien 5.8)
- **o tot nhat**: trung vi p = 0.287 · p<=0,05: **3/115** (ky vong ngau nhien 5.8)

## Alpha DUONG (xep theo p cua alpha o tam)

| ung vien | hinh dang that | alpha tam | null p95 | p(alpha) | p(ty le duong) | p(boi dinh) |
|---|---|---:|---:|---:|---:|---:|
| `EURGBP.H4.mua_qua_dem.gio_vao20_gio_ra14` | CAI GAI - dinh cao gap 330.5 lan trung vi lan can | 11.129 | 0.397 | 0.0099 | 0.0891 | 1.0 |
| `AUDCAD.D1.bollinger_ve.n50_k2.0` | SUON DOC - 96% duong, dinh gap 2.3 lan | 3.561 | 2.804 | 0.0198 | 0.1188 | 0.802 |
| `AUDCAD.H1.lap_gap.nguong0.001` | CAI GAI - da so lan can AM | 0.409 | -0.609 | 0.0297 | 0.0594 | 0.0297 |
| `AUDCAD.H1.lap_gap.nguong0.003` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.5 lan | 0.699 | 0.543 | 0.0297 | 0.0495 | 0.8317 |
| `EURGBP.D1.cuoi_thang.truoc2_sau2` | CAI GAI - dinh cao gap 3.3 lan trung vi lan can | 1.151 | 0.879 | 0.0396 | 0.0693 | 0.8614 |
| `NZDCAD.H1.lap_gap.nguong0.003` | CAO NGUYEN - 80% lan can duong, dinh chi gap 1.7 lan | 0.417 | 0.232 | 0.0396 | 0.0495 | 0.9505 |
| `EURGBP.H4.ou_quay_ve.n200_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.5 lan | 3.028 | 2.853 | 0.0495 | 0.3069 | 0.4158 |
| `EURCAD.H4.bollinger_ve.n20_k2.0` | CAI GAI - dinh cao gap 3.2 lan trung vi lan can | 2.534 | 2.411 | 0.0594 | 0.0792 | 0.8713 |
| `AUDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55` | SUON DOC - 95% duong, dinh gap 2.5 lan | 3.944 | 3.862 | 0.0594 | 0.1584 | 0.3267 |
| `EURGBP.H4.bollinger_ve.n50_k2.0` | CAO NGUYEN - 96% lan can duong, dinh chi gap 1.6 lan | 3.303 | 3.291 | 0.0594 | 0.2178 | 0.4554 |
| `GBPCAD.H1.lap_gap.nguong0.001` | CAI GAI - dinh cao gap 5.1 lan trung vi lan can | 0.102 | -0.207 | 0.0594 | 0.0495 | 0.9802 |
| `AUDCAD.H1.ou_quay_ve.n100_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.3 lan | 4.091 | 3.873 | 0.0594 | 0.2277 | 0.6337 |
| `NZDCAD.H1.lap_gap.nguong0.005` | SUON DOC - 100% duong, dinh gap 2.1 lan | 0.457 | 0.457 | 0.0594 | 0.0891 | 0.8812 |
| `AUDCAD.H1.rsi_dao_chieu.n14_vao25_ra_60` | CAI GAI - dinh cao gap 3.2 lan trung vi lan can | 2.652 | 2.699 | 0.0693 | 0.0693 | 0.5545 |
| `NZDCAD.H4.bollinger_ve.n20_k2.5` | CAI GAI - dinh cao gap 3.7 lan trung vi lan can | 2.568 | 2.677 | 0.0693 | 0.1287 | 0.7576 |
| `US500CASH.D1.ibs_bat_day.nguong0.2_giu2` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.8 lan | 4.782 | 5.147 | 0.0792 | 0.0396 | 0.6634 |
| `EURGBP.D1.bollinger_ve.n50_k2.0` | SUON DOC - 100% duong, dinh gap 2.0 lan | 2.626 | 3.265 | 0.0891 | 0.1683 | 0.495 |
| `GBPCAD.H4.lap_gap.nguong0.001` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.5 lan | 0.865 | 1.425 | 0.0891 | 0.0792 | 0.9208 |
| `AUDNZD.H4.lap_gap.nguong0.005` | CAI GAI - dinh cao gap 4.1 lan trung vi lan can | 0.054 | 0.115 | 0.0891 | 0.099 | 0.9703 |
| `AUDCHF.H4.ou_quay_ve.n200_z2.0` | SUON DOC - 96% duong, dinh gap 2.0 lan | 3.302 | 3.37 | 0.0891 | 0.2079 | 0.7129 |
| `EURGBP.D1.cuoi_thang.truoc1_sau4` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.7 lan | 1.064 | 1.193 | 0.099 | 0.0594 | 0.7624 |
| `US500CASH.D1.ibs_bat_day.nguong0.3_giu1` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.8 lan | 4.49 | 6.016 | 0.099 | 0.0792 | 0.703 |
| `AUDCHF.H4.ou_quay_ve.n100_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.6 lan | 3.194 | 3.749 | 0.099 | 0.0891 | 0.6337 |
| `EURCAD.H4.rsi_dao_chieu.n14_vao25_ra_60` | CAI GAI - dinh cao gap 4.5 lan trung vi lan can | 1.187 | 1.819 | 0.1089 | 0.1782 | 0.5842 |
| `AUDCHF.D1.ibs_bat_day.nguong0.15_giu1` | CAO NGUYEN - 80% lan can duong, dinh chi gap 1.9 lan | 1.601 | 1.935 | 0.1089 | 0.1584 | 0.7426 |
| `AUDCHF.D1.ibs_bat_day.nguong0.2_giu1` | SUON DOC - 73% duong, dinh gap 1.9 lan | 1.891 | 2.427 | 0.1089 | 0.2178 | 0.7129 |
| `AUDCAD.H4.lap_gap.nguong0.003` | CAO NGUYEN - 80% lan can duong, dinh chi gap 1.5 lan | 0.129 | 0.456 | 0.1089 | 0.0396 | 0.9307 |
| `NZDCAD.H1.ou_quay_ve.n200_z2.0` | CAI GAI - da so lan can AM | 1.401 | 2.493 | 0.1089 | 0.297 | 0.0594 |
| `EURCAD.H4.bollinger_ve.n50_k2.0` | SUON DOC - 96% duong, dinh gap 2.3 lan | 2.308 | 3.259 | 0.1188 | 0.1287 | 0.7525 |
| `US500M.H4.donchian.n55` | CAI GAI - dinh cao gap 5.5 lan trung vi lan can | 7.322 | 8.502 | 0.1188 | 0.3069 | 0.9406 |
| `AUDCAD.H1.lap_gap.nguong0.005` | SUON DOC - 100% duong, dinh gap 2.1 lan | 0.328 | 0.432 | 0.1188 | 0.1287 | 0.8182 |
| `US500M.D1.ichimoku_cheo.tenkan9_kijun26` | CAO NGUYEN - 96% lan can duong, dinh chi gap 1.4 lan | 9.93 | 12.778 | 0.1287 | 0.0891 | 0.7327 |
| `AUDNZD.D1.momentum_ema.n10` | CAI GAI - dinh cao gap 7.5 lan trung vi lan can | 0.19 | 1.499 | 0.1287 | 0.1089 | 0.9802 |
| `EURGBP.H4.ou_quay_ve.n100_z2.0` | CAI GAI - dinh cao gap 3.7 lan trung vi lan can | 2.313 | 3.05 | 0.1287 | 0.2871 | 0.8515 |
| `AUDCHF.H1.lap_gap.nguong0.005` | CAO NGUYEN - 80% lan can duong, dinh chi gap 1.5 lan | 0.337 | 0.689 | 0.1287 | 0.1485 | 0.8317 |
| `AUDCAD.D1.bollinger_ve.n20_k2.0` | CAI GAI - dinh cao gap 3.4 lan trung vi lan can | 0.768 | 1.938 | 0.1386 | 0.1089 | 0.8119 |
| `AUDCHF.H4.bollinger_ve.n20_k2.0` | CAI GAI - dinh cao gap 6.0 lan trung vi lan can | 2.299 | 3.05 | 0.1386 | 0.099 | 0.9208 |
| `NZDCAD.H1.rsi_dao_chieu.n14_vao25_ra_60` | CAI GAI - dinh cao gap 11.0 lan trung vi lan can | 0.606 | 1.249 | 0.1386 | 0.0693 | 0.8614 |
| `EURCAD.H1.ou_quay_ve.n100_z2.0` | CAI GAI - dinh cao gap 4.3 lan trung vi lan can | 0.645 | 1.642 | 0.1386 | 0.1386 | 0.9505 |
| `AUDCAD.H4.ou_quay_ve.n50_z2.5` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.5 lan | 4.333 | 5.753 | 0.1386 | 0.2871 | 0.3663 |
| `EURCAD.H4.ou_quay_ve.n200_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.6 lan | 1.916 | 3.372 | 0.1485 | 0.1683 | 0.6535 |
| `AUDCAD.H4.ou_quay_ve.n200_z2.0` | SUON DOC - 92% duong, dinh gap 2.4 lan | 2.904 | 3.699 | 0.1485 | 0.4158 | 0.7426 |
| `AUDCHF.H1.cuoi_thang.truoc1_sau4` | CAI GAI - da so lan can AM | 0.298 | 1.267 | 0.1683 | 0.2673 | 0.0297 |
| `NZDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55` | CAI GAI - dinh cao gap 3.9 lan trung vi lan can | 1.661 | 2.229 | 0.1683 | 0.0396 | 0.6337 |
| `EURCAD.H4.ou_quay_ve.n100_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.7 lan | 1.399 | 2.833 | 0.1683 | 0.1089 | 0.6832 |
| `EURCAD.H1.ou_quay_ve.n200_z2.0` | SUON DOC - 84% duong, dinh gap 2.7 lan | 1.471 | 3.223 | 0.1683 | 0.1683 | 0.8119 |
| `GBPCAD.H4.lap_gap.nguong0.003` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.0 lan | 0.604 | 1.415 | 0.1683 | 0.1089 | 0.7426 |
| `EURGBP.H1.ou_quay_ve.n200_z2.0` | SUON DOC - 84% duong, dinh gap 2.3 lan | 1.22 | 2.654 | 0.1683 | 0.2277 | 0.8 |
| `EURCAD.H4.ou_quay_ve.n50_z2.5` | CAI GAI - dinh cao gap 3.1 lan trung vi lan can | 1.46 | 2.897 | 0.1782 | 0.198 | 0.7525 |
| `EURGBP.H4.rsi_dao_chieu.n14_vao30_ra_55` | SUON DOC - 97% duong, dinh gap 2.6 lan | 1.39 | 2.043 | 0.1782 | 0.0792 | 0.3069 |
| `AUDCAD.H1.ou_quay_ve.n200_z2.0` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.2 lan | 2.754 | 5.005 | 0.1782 | 0.2277 | 0.4752 |
| `NZDCAD.H4.lap_gap.nguong0.005` | SUON DOC - 60% duong, dinh gap 2.0 lan | 0.098 | 0.471 | 0.1782 | 0.1188 | 0.9208 |
| `EURNZD.H4.rsi_dao_chieu.n7_vao30_ra_55` | CAI GAI - da so lan can AM | 0.884 | 2.704 | 0.1881 | 0.396 | 0.2178 |
| `AUDCAD.H4.bollinger_ve.n50_k2.0` | SUON DOC - 96% duong, dinh gap 2.5 lan | 3.444 | 5.472 | 0.198 | 0.2673 | 0.7624 |
| `US500CASH.H4.donchian.n55` | CAI GAI - dinh cao gap 4.2 lan trung vi lan can | 4.208 | 12.83 | 0.198 | 0.3069 | 0.9604 |
| `NZDCAD.H4.ou_quay_ve.n200_z2.0` | SUON DOC - 88% duong, dinh gap 2.3 lan | 1.614 | 2.75 | 0.198 | 0.2277 | 0.7525 |
| `NZDCAD.D1.bollinger_ve.n20_k2.5` | CAI GAI - dinh cao gap 14.3 lan trung vi lan can | 1.309 | 2.451 | 0.2079 | 0.198 | 0.8864 |
| `AUDNZD.H1.lap_gap.nguong0.005` | CAI GAI - dinh cao gap 3.5 lan trung vi lan can | 0.082 | 0.171 | 0.2079 | 0.3069 | 0.9438 |
| `EURNZD.H4.ou_quay_ve.n100_z2.0` | CAI GAI - da so lan can AM | 1.397 | 3.329 | 0.2079 | 0.3564 | 0.0297 |
| `EURCAD.H4.rsi_dao_chieu.n7_vao30_ra_55` | CAI GAI - dinh cao gap 18.1 lan trung vi lan can | 0.356 | 1.832 | 0.2178 | 0.1584 | 0.9604 |
| `AUDCAD.D1.bollinger_ve.n20_k2.5` | CAI GAI - dinh cao gap 6.6 lan trung vi lan can | 0.482 | 1.44 | 0.2178 | 0.1485 | 0.7579 |
| `AUDCHF.H4.bollinger_ve.n20_k2.5` | CAI GAI - dinh cao gap 6.2 lan trung vi lan can | 0.606 | 3.872 | 0.2178 | 0.198 | 0.8866 |
| `EURNZD.D1.bollinger_ve.n50_k2.0` | CAI GAI - da so lan can AM | 0.424 | 2.094 | 0.2178 | 0.3366 | 0.0297 |
| `YH_NASDAQ.D1.momentum_ema.n50` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.3 lan | 2.015 | 5.809 | 0.2277 | 0.2277 | 0.7129 |
| `NZDCAD.H4.bollinger_ve.n50_k2.0` | CAI GAI - da so lan can AM | 1.409 | 3.975 | 0.2376 | 0.3168 | 0.0297 |
| `XAUUSDM.H1.cuoi_thang.truoc1_sau4` | CAI GAI - da so lan can AM | 0.028 | 5.383 | 0.2376 | 0.4455 | 0.3465 |
| `EURGBP.H1.lap_gap.nguong0.005` | CAO NGUYEN - 80% lan can duong, dinh chi gap 2.0 lan | 0.077 | 0.216 | 0.2376 | 0.2277 | 0.7791 |
| `NZDCAD.H4.ou_quay_ve.n100_z2.0` | CAI GAI - dinh cao gap 81.4 lan trung vi lan can | 1.131 | 3.594 | 0.2376 | 0.3564 | 1.0 |
| `AUDNZD.H4.rsi_dao_chieu.n14_vao25_ra_60` | CAI GAI - dinh cao gap 23.5 lan trung vi lan can | 0.551 | 1.01 | 0.2475 | 0.2673 | 0.9286 |
| `NZDCAD.H4.rsi_dao_chieu.n7_vao30_ra_55` | CAI GAI - dinh cao gap 4.3 lan trung vi lan can | 0.597 | 2.219 | 0.2475 | 0.0891 | 0.7822 |
| `GBPCAD.H1.lap_gap.nguong0.005` | CAO NGUYEN - 100% lan can duong, dinh chi gap 1.7 lan | 0.141 | 0.401 | 0.2475 | 0.1782 | 0.7374 |
| `GBPCAD.D1.bollinger_ve.n50_k2.0` | SUON DOC - 96% duong, dinh gap 2.6 lan | 1.665 | 4.081 | 0.2574 | 0.2178 | 0.7723 |
| `EURGBP.H1.cuoi_thang.truoc1_sau4` | CAI GAI - da so lan can AM | 0.032 | 1.223 | 0.2574 | 0.297 | 0.0099 |
| `AUDCAD.H4.rsi_dao_chieu.n14_vao25_ra_60` | CAI GAI - dinh cao gap 3.8 lan trung vi lan can | 0.967 | 1.815 | 0.2574 | 0.2673 | 0.3267 |
| `AUDCHF.D1.ibs_bat_day.nguong0.2_giu2` | SUON DOC - 80% duong, dinh gap 2.2 lan | 0.875 | 2.706 | 0.2574 | 0.1683 | 0.7426 |
| `AUDCHF.D1.bollinger_ve.n20_k2.0` | SUON DOC - 96% duong, dinh gap 2.2 lan | 3.447 | 5.381 | 0.2574 | 0.1683 | 0.5347 |
| `GBPCAD.H1.lap_gap.nguong0.003` | SUON DOC - 80% duong, dinh gap 2.1 lan | 0.038 | 0.643 | 0.2574 | 0.2277 | 0.8614 |
| `EURCAD.H4.rsi_dao_chieu.n14_vao30_ra_55` | CAI GAI - dinh cao gap 5.2 lan trung vi lan can | 0.655 | 2.028 | 0.2673 | 0.2475 | 0.7525 |
| `XAUUSDM.D1.ichimoku_cheo.tenkan20_kijun60` | CAI GAI - da so lan can AM | 0.62 | 8.077 | 0.2673 | 0.3267 | 0.0792 |
| `EURGBP.H4.ou_quay_ve.n50_z2.5` | CAI GAI - dinh cao gap 3.1 lan trung vi lan can | 1.476 | 3.283 | 0.2673 | 0.3762 | 0.7723 |
| `NZDCAD.H4.ou_quay_ve.n50_z2.5` | CAI GAI - dinh cao gap 11.7 lan trung vi lan can | 0.935 | 2.642 | 0.2673 | 0.3663 | 0.9901 |
| `EURGBP.D1.cuoi_thang.truoc3_sau3` | SUON DOC - 92% duong, dinh gap 2.8 lan | 0.323 | 1.309 | 0.2772 | 0.0594 | 0.7525 |
| `AUDCAD.D1.ichimoku_cheo.tenkan9_kijun26_chi_muaTrue` | CAI GAI - dinh cao gap 15.7 lan trung vi lan can | 0.457 | 1.811 | 0.2772 | 0.4158 | 0.9505 |
| `EURCAD.D1.rsi_dao_chieu.n7_vao30_ra_55` | CAI GAI - dinh cao gap 3.3 lan trung vi lan can | 1.084 | 2.394 | 0.2871 | 0.0495 | 0.6733 |
| `US500CASH.H4.momentum_ema.n100` | CAI GAI - dinh cao gap 3.5 lan trung vi lan can | 1.138 | 10.673 | 0.297 | 0.3366 | 0.9505 |
| `US500CASH.H4.sma_cheo.nhanh20_cham100` | CAI GAI - dinh cao gap 10.9 lan trung vi lan can | 0.151 | 10.319 | 0.297 | 0.2574 | 0.9802 |
| `EURGBP.H4.cuoi_thang.truoc1_sau4` | CAO NGUYEN - 80% lan can duong, dinh chi gap 1.9 lan | 0.508 | 2.024 | 0.3069 | 0.3762 | 0.703 |
| `EURGBP.D1.rsi_dao_chieu.n7_vao30_ra_55` | CAO NGUYEN - 99% lan can duong, dinh chi gap 2.0 lan | 1.264 | 2.725 | 0.3069 | 0.1782 | 0.4653 |
| `AUDCHF.H4.bollinger_ve.n50_k2.0` | CAI GAI - dinh cao gap 12.4 lan trung vi lan can | 0.253 | 2.488 | 0.3069 | 0.2079 | 0.9505 |
| `EURGBP.H1.ou_quay_ve.n50_z2.5` | SUON DOC - 84% duong, dinh gap 3.0 lan | 0.727 | 3.226 | 0.3069 | 0.1683 | 0.8416 |
| `AUDCAD.D1.rsi_dao_chieu.n7_vao30_ra_55` | SUON DOC - 96% duong, dinh gap 2.0 lan | 0.813 | 2.087 | 0.3168 | 0.1782 | 0.396 |
| `US500M.D1.sma_cheo.nhanh5_cham20` | CAO NGUYEN - 96% lan can duong, dinh chi gap 1.8 lan | 0.853 | 13.007 | 0.3168 | 0.1386 | 0.7129 |
| `EURGBP.H1.ou_quay_ve.n100_z2.0` | CAI GAI - dinh cao gap 3.1 lan trung vi lan can | 0.248 | 2.986 | 0.3168 | 0.2574 | 0.9307 |
| `AUDCHF.D1.cuoi_thang.truoc3_sau3` | SUON DOC - 88% duong, dinh gap 2.4 lan | 0.523 | 2.226 | 0.3366 | 0.1089 | 0.7228 |
| `NZDCAD.H4.rsi_dao_chieu.n14_vao25_ra_60` | CAI GAI - dinh cao gap 6.1 lan trung vi lan can | 0.572 | 1.502 | 0.3366 | 0.0396 | 0.4896 |
| `NZDCAD.D1.rsi_dao_chieu.n7_vao30_ra_55` | CAI GAI - da so lan can AM | 0.432 | 2.229 | 0.3465 | 0.4851 | 0.0792 |
| `AUDCHF.D1.cuoi_thang.truoc1_sau4` | SUON DOC - 100% duong, dinh gap 2.3 lan | 0.307 | 1.982 | 0.3564 | 0.0594 | 0.7327 |
| `EURCAD.D1.bollinger_ve.n20_k2.0` | CAI GAI - dinh cao gap 3.5 lan trung vi lan can | 0.765 | 3.16 | 0.3663 | 0.1782 | 0.7228 |
| `EURGBP.H4.rsi_dao_chieu.n14_vao25_ra_60` | CAI GAI - dinh cao gap 5.9 lan trung vi lan can | 0.573 | 1.566 | 0.3762 | 0.1188 | 0.5859 |
| `EURNZD.H1.lap_gap.nguong0.005` | CAI GAI - dinh cao gap 3.7 lan trung vi lan can | 0.02 | 0.449 | 0.3762 | 0.3267 | 0.87 |
| `US500M.H4.bollinger_ve.n20_k2.0` | CAI GAI - dinh cao gap 52.8 lan trung vi lan can | 5.345 | 15.471 | 0.3861 | 0.495 | 0.98 |
| `US500M.H4.bollinger_ve.n20_k2.5` | SUON DOC - 84% duong, dinh gap 2.9 lan | 2.758 | 14.052 | 0.3861 | 0.1881 | 0.5644 |
| `EURNZD.D1.ichimoku_cheo.tenkan9_kijun26_chi_muaTrue` | CAI GAI - da so lan can AM | 0.091 | 1.509 | 0.396 | 0.396 | 0.1089 |
| `US500CASH.H4.bollinger_ve.n20_k2.5` | CAI GAI - dinh cao gap 5.0 lan trung vi lan can | 2.71 | 10.932 | 0.396 | 0.0396 | 0.6832 |
| `AUDCHF.D1.rsi_dao_chieu.n7_vao30_ra_55` | SUON DOC - 88% duong, dinh gap 3.0 lan | 0.899 | 2.774 | 0.4158 | 0.198 | 0.505 |
| `EURNZD.H4.rsi_dao_chieu.n14_vao25_ra_60` | CAI GAI - dinh cao gap 10.5 lan trung vi lan can | 0.212 | 1.456 | 0.4158 | 0.2376 | 0.7879 |
| `US500M.H4.rsi_dao_chieu.n7_vao30_ra_55` | CAI GAI - dinh cao gap 3.6 lan trung vi lan can | 3.172 | 9.965 | 0.4158 | 0.3069 | 0.7426 |
| `AUDCHF.D1.bollinger_ve.n50_k2.0` | CAI GAI - dinh cao gap 5.6 lan trung vi lan can | 0.777 | 4.141 | 0.4356 | 0.3762 | 0.8614 |
| `GBPCAD.H4.bollinger_ve.n20_k2.5` | CAI GAI - dinh cao gap 7.3 lan trung vi lan can | 0.137 | 3.988 | 0.4455 | 0.2673 | 0.88 |
| `EURGBP.H4.cuoi_thang.truoc3_sau3` | CAI GAI - dinh cao gap 6.8 lan trung vi lan can | 0.231 | 1.69 | 0.4554 | 0.4653 | 0.901 |
| `EURGBP.H1.rsi_dao_chieu.n14_vao30_ra_55` | SUON DOC - 96% duong, dinh gap 2.2 lan | 0.373 | 1.956 | 0.4554 | 0.0297 | 0.5446 |
| `XAUUSDM.H4.rsi_dao_chieu.n14_vao25_ra_60` | CAI GAI - da so lan can AM | 0.012 | 5.215 | 0.4752 | 0.8119 | 0.35 |
| `US500CASH.H4.rsi_dao_chieu.n7_vao30_ra_55` | CAI GAI - dinh cao gap 3.1 lan trung vi lan can | 1.035 | 7.5 | 0.495 | 0.2574 | 0.6634 |
| `GBPCAD.H1.rsi_dao_chieu.n14_vao25_ra_60` | CAI GAI - da so lan can AM | 0.003 | 1.788 | 0.5446 | 0.3564 | 0.0396 |
| `EURGBP.H1.rsi_dao_chieu.n14_vao25_ra_60` | CAI GAI - dinh cao gap 3.7 lan trung vi lan can | 0.005 | 1.49 | 0.5644 | 0.0495 | 0.5446 |

## Alpha AM — p nho o day nghia la LO IT HON NULL, khong phai edge

| ung vien | alpha tam | null p95 | p(alpha) |
|---|---:|---:|---:|
| `AUDNZD.H1.lap_gap.nguong0.001` | -1.296 | -2.499 | 0.0099 |
| `AUDNZD.H4.lap_gap.nguong0.001` | -2.388 | -5.205 | 0.0099 |
| `NZDCAD.H1.lap_gap.nguong0.001` | -0.688 | -4.085 | 0.0099 |
| `XAUUSDM.H1.lap_gap.nguong0.001` | -5.898 | -16.363 | 0.0198 |
| `XAUUSDM.H4.lap_gap.nguong0.001` | -7.668 | -18.459 | 0.0198 |
| `XAUUSDM.H4.lap_gap.nguong0.003` | -4.058 | -16.103 | 0.0198 |
| `XAUUSDM.H4.lap_gap.nguong0.005` | -1.439 | -10.091 | 0.0198 |
| `NZDCAD.H4.lap_gap.nguong0.001` | -0.955 | -1.969 | 0.0297 |
| `AUDNZD.H4.lap_gap.nguong0.003` | -0.367 | -0.519 | 0.0396 |
| `XAUUSDM.H1.lap_gap.nguong0.003` | -2.578 | -4.489 | 0.0396 |
| `EURNZD.H1.lap_gap.nguong0.001` | -1.256 | -1.352 | 0.0594 |
| `NZDCAD.H4.lap_gap.nguong0.003` | -0.029 | 0.048 | 0.0693 |
| `XAUUSDM.H1.lap_gap.nguong0.005` | -0.553 | -0.36 | 0.0693 |
| `AUDCAD.H4.lap_gap.nguong0.001` | -0.787 | -0.275 | 0.0792 |
| `NZDCAD.H1.ou_quay_ve.n100_z2.0` | -0.133 | -0.019 | 0.099 |
| `AUDCHF.H4.lap_gap.nguong0.003` | -1.408 | -0.05 | 0.1089 |
| `AUDCHF.H4.lap_gap.nguong0.005` | -0.018 | 0.451 | 0.1089 |
| `AUDCHF.H1.lap_gap.nguong0.001` | -6.404 | -4.968 | 0.1287 |
| `AUDNZD.D1.momentum_ema.n20` | -0.811 | 0.094 | 0.1782 |
| `EURCAD.H4.lap_gap.nguong0.001` | -0.682 | 0.679 | 0.1881 |
| `GBPCAD.D1.ibs_bat_day.nguong0.2_giu2` | -1.319 | 0.228 | 0.198 |
| `EURCAD.H1.lap_gap.nguong0.001` | -0.998 | 0.831 | 0.2079 |
| `EURNZD.H4.lap_gap.nguong0.001` | -2.393 | 0.208 | 0.2079 |
| `EURCAD.D1.ibs_bat_day.nguong0.2_giu2` | -0.59 | 0.934 | 0.2178 |
| `EURGBP.D1.ibs_bat_day.nguong0.2_giu2` | -0.036 | 0.729 | 0.2178 |

## Khong do duoc (89)

- 84 ung vien: khong co tham so -> khong co lan can de do
- 4 ung vien: FileNotFoundError: khong co du lieu cho RO:CHI_SO_MY+VANG. Co: AUDCAD,
- 1 ung vien: FileNotFoundError: khong co du lieu cho RO:CHI_SO_MY. Co: AUDCAD, AUDC
